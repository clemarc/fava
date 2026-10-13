"""Synthetic resolution, resume, policy and real signed-history fixtures."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/sdd'))
import integration
import ledger
import lifecycle
import milestone
import signatures
import sdd
from test_checks import ROADMAP, SPEC, TASKS

ROADMAP_DECIMAL = ROADMAP.replace('R1', 'R3.5')


class ResolverTests(unittest.TestCase):
    def context(self):
        result = milestone.resolve('r3.5', {'specs/demo/roadmap.md': ROADMAP_DECIMAL})
        result.update(execution=None, prs=[])
        return result

    def test_decimal_normalization_does_not_infer_numbering(self):
        result = self.context()
        self.assertEqual(result['id'], 'R3.5')
        self.assertEqual(result['feature'], 'specs/demo-01-read')
        self.assertEqual(result['milestone_branch'], 'milestone/r3.5')
        self.assertEqual(result['preparation_branch'], 'prepare/r3.5')
        self.assertEqual(milestone.normalize(' r3.5 '), 'R3.5')
        for value in ['R03.5', 'R3.05', 'R3.0', 'R3.5.1', 'R3.5x']:
            with self.assertRaises(ValueError): milestone.normalize(value)

    def test_unknown_and_ambiguous_identifiers(self):
        with self.assertRaisesRegex(ValueError, 'unknown'):
            milestone.resolve('R7', {'roadmap': ROADMAP_DECIMAL})
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            milestone.resolve('R3.5', {'one': ROADMAP_DECIMAL, 'two': ROADMAP_DECIMAL})

    def test_interrupted_work_resumes_but_closed_completed_and_wrong_targets_stop(self):
        context = self.context()
        context['execution'] = dict(milestone='R3.5', feature=context['feature'],
                                    milestone_branch=context['milestone_branch'], state='preparing')
        context['prs'] = [dict(number=10, head='prepare/r3.5', base='milestone/r3.5', state='open', merged=None)]
        self.assertIsNone(milestone.reconcile(context, 'prepare'))
        with self.assertRaisesRegex(ValueError, 'must merge'):
            milestone.reconcile(context, 'implement')
        context['prs'][0].update(state='closed', merged='fixture-time')
        self.assertIsNone(milestone.reconcile(context, 'implement'))
        with self.assertRaisesRegex(ValueError, 'already merged'):
            milestone.reconcile(context, 'prepare')
        context['prs'][0]['merged'] = None
        with self.assertRaisesRegex(ValueError, 'retired'):
            milestone.reconcile(context, 'prepare')
        context['prs'][0]['base'] = 'main'
        with self.assertRaisesRegex(ValueError, 'wrong target'):
            milestone.reconcile(context, 'prepare')
        context['execution']['state'] = 'completed'
        with self.assertRaisesRegex(ValueError, 'completed'):
            milestone.reconcile(context, 'implement')

    def test_existing_branch_and_dirty_divergent_checkouts(self):
        context = self.context()
        context.update(target_sha='head', branches={'refs/heads/prepare/r3.5': 'head'})
        with patch.object(milestone, 'git', return_value=''), patch.object(milestone.subprocess, 'run') as run:
            milestone.checkout(Path('/fixture'), context, 'prepare/r3.5')
            self.assertEqual(run.call_args.args[0], ['git', '-C', '/fixture', 'switch', 'prepare/r3.5'])
        with patch.object(milestone, 'git', return_value=' M owner.txt'), patch.object(milestone.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'dirty'):
                milestone.checkout(Path('/fixture'), context, 'prepare/r3.5')
            run.assert_not_called()
        context['branches']['refs/remotes/origin/prepare/r3.5'] = 'newer'
        with patch.object(milestone, 'git', return_value=''):
            with self.assertRaisesRegex(ValueError, 'divergence'):
                milestone.checkout(Path('/fixture'), context, 'prepare/r3.5')

    def test_latest_preparation_uses_merge_chronology_not_response_position(self):
        context = self.context()
        old = dict(number=10, head='prepare/r3.5', merged='2026-10-13T10:00:00Z', merge_sha='old')
        amendment = dict(number=11, head='prepare/r3.5', merged='2026-10-13T11:00:00Z', merge_sha='new')
        for ordering in [[amendment, old], [old, amendment]]:
            context['prs'] = ordering
            self.assertEqual(milestone.latest_preparation(context)['merge_sha'], 'new')
        context['prs'] = [old, dict(amendment, merged=old['merged'])]
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            milestone.latest_preparation(context)


class IntegrationTests(unittest.TestCase):
    def evidence(self):
        return dict(head='head', target='target', validated_head='head', validated_target='target',
                    base='milestone/r3.5', milestone_branch='milestone/r3.5', state='OPEN', draft=False,
                    **{k: True for k in ['scope', 'dependencies', 'trailers', 'signatures', 'protected_target', 'structural_drift',
                                         'semantic_drift', 'independent_review', 'findings_disposed']},
                    checks={k: 'SUCCESS' for k in ['sdd-quality', 'tooling-validation', 'ci-applicability',
                                                  'ci-required', 'ios-build-test']},
                    native_required=True, simulator_tests=4, macos_build=True, codex_configured=True,
                    codex_available=True, codex_review_head='head', codex_review_complete=True)

    def test_valid_current_evidence_and_every_gate_fails_closed(self):
        good = self.evidence()
        self.assertEqual(integration.evaluate(good), [])
        cases = dict(base='main', validated_head='old', validated_target='old-target', scope=False,
                     signatures=False, protected_target=False, dependencies=False, independent_review=False, semantic_drift=False,
                     structural_drift=False, findings_disposed=False, simulator_tests=0, macos_build=False,
                     codex_review_head='old', codex_review_complete=False, blocked_findings=['P1'],
                     correction_cycles=3, draft=True, state='CLOSED')
        for key, value in cases.items():
            with self.subTest(gate=key):
                bad = dict(good, **{key: value})
                self.assertTrue(integration.evaluate(bad))
        for name in good['checks']:
            bad = copy.deepcopy(good); bad['checks'][name] = 'SKIPPED'
            self.assertTrue(integration.evaluate(bad))

    def test_unavailable_bot_needs_evidence_and_does_not_replace_independent_review(self):
        evidence = self.evidence()
        evidence.update(codex_available=False, codex_review_complete=False)
        self.assertTrue(integration.evaluate(evidence))
        evidence['codex_unavailability_evidence'] = 'actual settings/error report'
        self.assertEqual(integration.evaluate(evidence), [])
        evidence['independent_review'] = False
        self.assertTrue(integration.evaluate(evidence))

    def test_native_matrix_requires_both_actual_named_jobs(self):
        phone = dict(name='ios-build-test / ios-build-test (iPhone)', conclusion='SUCCESS')
        tablet = dict(name='ios-build-test / ios-build-test (iPad)', conclusion='SUCCESS')
        self.assertEqual(integration.check_results([phone, tablet])['ios-build-test'], 'SUCCESS')
        self.assertEqual(integration.check_results([phone])['ios-build-test'], 'INCOMPLETE')
        for state in ['FAILURE', 'SKIPPED', '', None]:
            self.assertEqual(integration.check_results([phone, dict(tablet, conclusion=state)])['ios-build-test'], 'INCOMPLETE')

    def test_bot_reaction_cannot_survive_an_edited_request_or_precede_it(self):
        head = 'a' * 40
        request = dict(issue_url='https://api.github.com/repos/clemarc/fava/issues/10', body='@codex review ' + head,
                       created_at='2026-10-13T10:00:00Z', updated_at='2026-10-13T10:00:00Z')
        reaction = dict(content='+1', user={'login': 'chatgpt-codex-connector[bot]'}, created_at='2026-10-13T10:01:00Z')
        self.assertTrue(integration.fresh_bot_reaction(request, [reaction], head, 10))
        for bad in [dict(request, updated_at='2026-10-13T10:02:00Z'), dict(request, body='@codex review ' + 'b'*40),
                    dict(request, body=request['body'] + ' ' + 'b'*40), dict(request, issue_url=request['issue_url']+'1')]:
            self.assertFalse(integration.fresh_bot_reaction(bad, [reaction], head, 10))
        self.assertFalse(integration.fresh_bot_reaction(request, [dict(reaction, created_at='2026-10-13T09:00:00Z')], head, 10))

    def test_ledger_retired_ids_completion_and_history(self):
        data = dict(schema=1, milestone='R3.5', feature='specs/demo-01-read', milestone_branch='milestone/r3.5',
                    specification_base='a' * 40, planning_revision=None, state='preparing', retired_task_ids=[],
                    tasks={t: {'state': 'pending'} for t in ['T001', 'T002', 'T003']})
        self.assertEqual(ledger.validate(data, data['feature'], TASKS), [])
        for key, value in [('state', 'completed'), ('retired_task_ids', ['T002']), ('milestone_branch', 'main')]:
            bad = dict(data, **{key: value})
            self.assertTrue(ledger.validate(bad, data['feature'], TASKS))
        old = copy.deepcopy(data)
        old['tasks']['T002'] = {'state': 'integrated', 'merge_sha': 'b' * 40}
        self.assertTrue(ledger.history_errors(old, data))

    def test_physical_acceptance_alone_cannot_complete_unfinished_tasks(self):
        data = dict(schema=1, milestone='R3.5', feature='specs/demo-01-read', milestone_branch='milestone/r3.5',
                    specification_base='a'*40, planning_revision='b'*40, state='completed', retired_task_ids=[],
                    physical_acceptance={'iPhone': 'device evidence', 'iPad': 'device evidence'},
                    tasks={t: {'state': 'pending'} for t in ['T001', 'T002', 'T003']})
        for state in ['pending', 'working', 'review', 'blocked']:
            data['tasks']['T003']['state'] = state
            self.assertTrue(any('every retained task' in error for error in ledger.validate(data, data['feature'], TASKS)))
        data['tasks'] = {t: {'state': 'integrated', 'merge_sha': 'c'*40, 'pr': 'PR', 'evidence': ['CI']} for t in data['tasks']}
        self.assertEqual(ledger.validate(data, data['feature'], TASKS.replace('[ ]', '[X]')), [])


class SignedLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key_temp = tempfile.TemporaryDirectory(prefix='fava-synthetic-signing-')
        cls.key_dir = Path(cls.key_temp.name)
        cls.env = dict(os.environ, GNUPGHOME=str(cls.key_dir))
        subprocess.run(['gpg', '--batch', '--passphrase', '', '--quick-generate-key',
                        'Synthetic Fixture <fixture@example.invalid>', 'rsa2048', 'sign', '1d'],
                       env=cls.env, check=True, capture_output=True)
        keys = subprocess.check_output(['gpg', '--batch', '--with-colons', '--list-keys'], env=cls.env, text=True)
        cls.fingerprint = next(line.split(':')[9] for line in keys.splitlines() if line.startswith('fpr:'))
        cls.public = cls.key_dir / 'public.asc'
        cls.public.write_bytes(subprocess.check_output(['gpg', '--armor', '--export', cls.fingerprint], env=cls.env))

    @classmethod
    def tearDownClass(cls): cls.key_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.feature = 'specs/demo-01-read'
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Synthetic Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.signingkey', self.fingerprint)
        self.put('.specify/memory/constitution.md', 'fixture')
        self.put('specs/demo/roadmap.md', ROADMAP_DECIMAL)
        self.put(self.feature + '/spec.md', SPEC.replace('entry R1', 'entry R3.5'))
        self.baseline = self.commit('specification')
        self.git('switch', '-c', 'milestone/r3.5')
        self.git('switch', '-c', 'prepare/r3.5')
        self.put(self.feature + '/plan.md', 'Derived design FR-001 FR-002')
        self.put(self.feature + '/tasks.md', TASKS)
        self.put(self.feature + '/preparation-review.md', 'reviewed synthetic design')
        self.data = dict(schema=1, milestone='R3.5', feature=self.feature, milestone_branch='milestone/r3.5',
                         specification_base=self.baseline, planning_revision=None, state='preparing',
                         retired_task_ids=[], tasks={t: {'state': 'pending'} for t in ['T001', 'T002', 'T003']})
        self.put(self.feature + '/execution.json', json.dumps(self.data))
        self.prep_head = self.commit('planning')
        self.git('switch', 'milestone/r3.5')
        self.git('merge', '--no-ff', '-S', '-m', 'owner review\n\nSDD-Type: planning', 'prepare/r3.5')
        self.planning = self.git('rev-parse', 'HEAD')
        self.data.update(planning_revision=self.planning, state='implementing')
        self.put(self.feature + '/execution.json', json.dumps(self.data))
        self.commit('planning')
        self.put('Fava/Reader.swift', '// synthetic source')
        self.git('add', '.')
        self.git('commit', '-qm', f'feat: fixture\n\nSpec: {self.feature}\nTask: T003\nImplements: FR-001 FR-002')
        self.source = self.git('rev-parse', 'HEAD')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], env=self.env, stderr=subprocess.PIPE, text=True).strip()

    def put(self, path, text):
        target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text)

    def commit(self, kind):
        self.git('add', '.'); self.git('commit', '--allow-empty', '-qm', 'fixture\n\nSDD-Type: ' + kind)
        return self.git('rev-parse', 'HEAD')

    def proof(self):
        with patch.multiple(signatures, KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
            return lifecycle.planning_ref(self.root, self.baseline, self.source, self.feature, sdd.git)

    def test_real_signed_owner_merge_permits_promotion_with_plan_absent_in_base(self):
        self.assertEqual(self.proof(), self.planning)
        with patch.multiple(signatures, KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
            self.assertEqual(sdd.validate_repo(self.root, self.baseline), [])

    def test_branch_and_trailer_cannot_replace_owner_approval(self):
        self.data['planning_revision'] = self.prep_head
        self.git('switch', '--detach', self.source + '^')
        self.put(self.feature + '/execution.json', json.dumps(self.data))
        self.commit('planning')
        self.source = self.commit('planning')
        with self.assertRaisesRegex(ValueError, 'owner two-parent merge'):
            self.proof()

    def test_wrong_signer_or_owner_is_not_approval(self):
        self.assertFalse(signatures.verify(self.root, self.planning))
        with patch.multiple(signatures, KEY=self.public, FINGERPRINT=self.fingerprint):
            self.assertFalse(signatures.owner_merge(self.root, self.planning, sdd.git))

    def test_final_two_parent_main_merge_preserves_planning_chronology(self):
        self.git('switch', 'main')
        self.git('merge', '--no-ff', '-S', '-m', f'owner promotion\n\nSpec: {self.feature}\nTask: T003\nImplements: FR-001 FR-002', 'milestone/r3.5')
        self.source = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.proof(), self.planning)
        with patch.multiple(signatures, KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
            self.assertEqual(sdd.validate_repo(self.root, self.baseline), [])

    def test_unreviewed_mapping_change_cannot_use_previous_planning(self):
        self.git('switch', '--detach', self.source + '^')
        self.put(self.feature + '/tasks.md', TASKS.replace('Fava/Reader.swift', 'Fava/Different.swift'))
        self.commit('planning')
        self.source = self.commit('planning')
        with self.assertRaisesRegex(ValueError, 'mappings changed'):
            self.proof()

    def test_planning_after_source_is_not_retroactive_approval(self):
        self.data['planning_revision'] = self.source
        self.git('switch', '--detach', self.source + '^')
        self.put(self.feature + '/execution.json', json.dumps(self.data))
        self.commit('planning')
        self.source = self.commit('planning')
        with self.assertRaisesRegex(ValueError, 'must precede'):
            self.proof()


if __name__ == '__main__': unittest.main()

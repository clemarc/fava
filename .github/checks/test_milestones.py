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

    def test_other_milestone_uses_its_own_directory_and_branch_fields(self):
        roadmap = ROADMAP_DECIMAL + ROADMAP_DECIMAL.splitlines()[-1].replace('R3.5', 'R4').replace('demo-01-read', 'demo-02-next') + '\n'
        result = milestone.resolve(' r4 ', {'specs/demo/roadmap.md': roadmap})
        self.assertEqual((result['id'], result['feature'], result['milestone_branch'], result['task_branch_prefix']),
                         ('R4', 'specs/demo-02-next', 'milestone/r4', 'task/r4/'))

    def test_preparation_resume_budget_needs_history_protection_and_actual_owner_evidence(self):
        result = self.context()
        result.update(main_sha='a'*40, prs=[dict(number=10, head='prepare/r3.5', state='open', sha='b'*40)],
                      execution={'preparation_prs': {'10': dict(branch='prepare/r3.5', correction_cycles=3, heads=['c'*40])}})
        rules = [dict(type=t) for t in ['required_signatures', 'non_fast_forward', 'deletion']]
        approval = dict(type='fava-correction-authorization', phase='prepare', milestone='R3.5', max_cycles=4)
        comment = dict(issue_url='https://api.github.com/repos/clemarc/fava/issues/10', user={'login':'clemarc'}, body=json.dumps(approval))
        def api(*args): return rules if '/rules/' in args[-1] else comment
        with patch.object(milestone, 'github', side_effect=api), patch.object(milestone, 'ancestor', return_value=True), patch.object(milestone, 'git', return_value=''):
            resumed = milestone.preparation_progress(Path('/fixture'), result)
            self.assertEqual(resumed['correction_cycles'], 3)
            self.assertFalse(resumed['next_round_authorized'])
            record = result['execution']['preparation_prs']['10']
            record.update(correction_cycles=4, owner_extra_cycles=True)
            with self.assertRaisesRegex(ValueError, 'exhausted'): milestone.preparation_progress(Path('/fixture'), result)
            record['owner_extra_cycles'] = {'comment_id':123}
            self.assertEqual(milestone.preparation_progress(Path('/fixture'), result)['maximum_cycles'], 4)
            for bad in [dict(approval, phase='implement'), dict(approval, milestone='R4'), dict(approval, max_cycles=3)]:
                comment['body'] = json.dumps(bad)
                with self.assertRaisesRegex(ValueError, 'exhausted'): milestone.preparation_progress(Path('/fixture'), result)
            comment['body'] = json.dumps(approval)
            comment['issue_url'] += '1'
            with self.assertRaisesRegex(ValueError, 'exhausted'): milestone.preparation_progress(Path('/fixture'), result)
            record['correction_cycles'] = 3
            rules.clear()
            with self.assertRaisesRegex(ValueError, 'protections'): milestone.preparation_progress(Path('/fixture'), result)
            result['execution']['preparation_prs'].clear()
            with self.assertRaisesRegex(ValueError, 'missing'): milestone.preparation_progress(Path('/fixture'), result)

    def test_preparation_history_is_append_only_and_cannot_reset(self):
        entry = dict(branch='prepare/r3.5', correction_cycles=3, heads=['a'*40])
        old = {'preparation_prs': {'10': entry}}
        for entries in [{}, {'10':dict(entry, correction_cycles=0)}, {'10':dict(entry, heads=['b'*40])}]:
            self.assertTrue(ledger.history_errors(old, {'preparation_prs': entries}))
        self.assertEqual(ledger.history_errors(old, {'preparation_prs': {'10':dict(entry, correction_cycles=4, heads=['a'*40,'b'*40])}}), [])

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
                     correction_cycles=4, draft=True, state='CLOSED')
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
        for checks in [[], [dict(name='ios-build-test', conclusion='SUCCESS')]]:
            self.assertEqual(integration.check_results(checks)['ios-build-test'], 'INCOMPLETE')
            evidence = self.evidence()
            evidence['checks'].update(integration.check_results(checks))
            self.assertTrue(integration.evaluate(evidence))

    def test_durable_task_limits_override_omitted_or_favorable_report_fields(self):
        data = {'tasks': {'T002': {'state': 'review', 'correction_cycles': 2},
                          'T003': {'state': 'blocked', 'correction_cycles': 4}}}
        self.assertEqual(integration.durable_task_limits(data, data, {'T002'}), [])
        evidence = self.evidence()
        evidence['task_limit_blockers'] = integration.durable_task_limits(data, data, {'T002', 'T003'})
        self.assertTrue(any('exhausted' in e for e in integration.evaluate(evidence)))
        evidence.update(correction_cycles=0, owner_extra_cycles=True)
        self.assertTrue(any('blocked' in e for e in integration.evaluate(evidence)))
        data['tasks']['T003']['owner_extra_cycles'] = True
        data['tasks']['T003']['state'] = 'review'
        self.assertTrue(integration.durable_task_limits(data, data, {'T003'}))
        self.assertEqual(integration.durable_task_limits(data, data, {'T002', 'T003'}, {'T003': 4}), [])
        self.assertTrue(integration.durable_task_limits(data, data, {'T099'}))
        for count in [-1, '3', True]:
            data['tasks']['T003']['correction_cycles'] = count
            self.assertTrue(integration.durable_task_limits(data, data, {'T003'}))

    def test_third_fix_round_can_integrate_but_fourth_needs_verified_authorization(self):
        data = {'tasks': {'T003': {'state': 'review', 'correction_cycles': 3}}}
        self.assertEqual(integration.durable_task_limits(data, data, {'T003'}), [])
        self.assertEqual(integration.evaluate(dict(self.evidence(), correction_cycles=3)), [])
        data['tasks']['T003']['correction_cycles'] = 4
        data['tasks']['T003']['owner_extra_cycles'] = True
        self.assertTrue(integration.durable_task_limits(data, data, {'T003'}))
        self.assertEqual(integration.durable_task_limits(data, data, {'T003'}, {'T003': 4}), [])
        data['tasks']['T003']['state'] = 'blocked'
        self.assertTrue(integration.durable_task_limits(data, data, {'T003'}, {'T003': 4}))

    def test_pr_cannot_erase_target_blockers_or_reuse_integrated_task(self):
        target = {'tasks': {'T003': {'state': 'blocked', 'correction_cycles': 4}}}
        head = {'tasks': {'T003': {'state': 'review', 'correction_cycles': 0, 'owner_extra_cycles': True}}}
        errors = integration.durable_task_limits(target, head, {'T003'})
        self.assertTrue(any('target task is blocked' in e for e in errors))
        self.assertTrue(any('cannot decrease' in e for e in errors))
        self.assertTrue(any('exhausted' in e for e in errors))
        for where in [target, head]:
            where['tasks']['T003'].update(state='integrated', correction_cycles=2)
        self.assertTrue(any('integrated' in e for e in integration.durable_task_limits(target, head, {'T003'})))

    def test_extra_cycles_need_actual_owner_comment_from_target(self):
        authorization = {'tasks': {'T003': {'owner_extra_cycles': {'comment_id': 123}}}}
        approval = dict(type='fava-correction-authorization', milestone='R3.5', tasks=['T003'], max_cycles=4)
        comment = dict(issue_url='https://api.github.com/repos/clemarc/fava/issues/10',
                       user={'login': 'clemarc'}, body=json.dumps(approval))
        with patch.object(integration, 'github', return_value=comment):
            self.assertEqual(integration.verified_owner_limits(authorization, {'T003'}, 10, 'R3.5'), {'T003': 4})
            self.assertEqual(integration.verified_owner_limits(authorization, {'T003'}, 11, 'R3.5'), {})
            self.assertEqual(integration.verified_owner_limits(authorization, {'T003'}, 10, 'R4'), {})
        for wrong in [dict(comment, user={'login': 'worker'}), dict(comment, body='true'),
                      dict(comment, body=json.dumps(dict(approval, max_cycles=3))),
                      dict(comment, body=json.dumps(dict(approval, tasks=['T999'])))]:
            with patch.object(integration, 'github', return_value=wrong):
                self.assertEqual(integration.verified_owner_limits(authorization, {'T003'}, 10, 'R3.5'), {})
        with patch.object(integration, 'github') as api:
            self.assertEqual(integration.verified_owner_limits({'tasks': {'T003': {'owner_extra_cycles': True}}}, {'T003'}, 10, 'R3.5'), {})
            api.assert_not_called()

    def test_correction_history_cannot_be_reset_by_checkpoint(self):
        old = {'tasks': {'T003': {'state': 'blocked', 'correction_cycles': 4}}}
        new = {'tasks': {'T003': {'state': 'review', 'correction_cycles': 0}}}
        self.assertTrue(any('cannot decrease' in e for e in ledger.history_errors(old, new)))
        new['tasks']['T003']['correction_cycles'] = 4
        self.assertEqual(ledger.history_errors(old, new), [])

    def test_pr_history_cannot_disappear_reset_or_change_task_identity(self):
        entry = dict(branch='task/r3.5/t003', tasks=['T003'], correction_cycles=3, heads=['a'*40])
        old = {'task_prs': {'10': entry}}
        new = copy.deepcopy(old)
        new['task_prs']['10'].update(correction_cycles=4, heads=['a'*40, 'b'*40])
        self.assertEqual(ledger.history_errors(old, new), [])
        for changed in [{}, {'10': dict(entry, correction_cycles=0)},
                        {'10': dict(entry, heads=['b'*40])}, {'10': dict(entry, tasks=['T002'])}]:
            self.assertTrue(ledger.history_errors(old, {'task_prs': changed}))

    def test_registered_pr_budget_rejects_rewritten_heads_and_head_only_reset(self):
        target = {'task_prs': {'10': dict(branch='task/r3.5/t003', tasks=['T003'], correction_cycles=3, heads=['prior'])}}
        head = {'tasks': {'T003': {'correction_cycles': 3}}}
        args = (Path('/fixture'), target, head, 10, 'task/r3.5/t003', {'T003'}, 'head')
        with patch.object(integration, 'ancestor', return_value=True):
            self.assertEqual(integration.registered_pr_errors(*args), [])
            head['tasks']['T003']['correction_cycles'] = 0
            self.assertTrue(integration.registered_pr_errors(*args))
            self.assertTrue(integration.registered_pr_errors(Path('/fixture'), target, head, 11, 'task/r3.5/t003', {'T003'}, 'head'))
        head['tasks']['T003']['correction_cycles'] = 3
        with patch.object(integration, 'ancestor', return_value=False):
            self.assertTrue(any('discarded' in e for e in integration.registered_pr_errors(*args)))

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
        self.source_path = getattr(self, 'source_path', 'Fava/Reader.swift')
        self.put(self.feature + '/tasks.md', TASKS.replace('Fava/Reader.swift', self.source_path))
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
        self.put(self.source_path, '// synthetic source')
        self.git('add', '.')
        kind = '\nSDD-Type: tooling' if self.source_path.startswith(('docs/', 'tools/')) else ''
        self.git('commit', '-qm', f'feat: fixture\n\nSpec: {self.feature}\nTask: T003\nImplements: FR-001 FR-002' + kind)
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

    def test_intermediate_head_counter_reset_fails_full_repository_validation(self):
        self.data['tasks']['T003']['correction_cycles'] = 3
        self.put(self.feature + '/execution.json', json.dumps(self.data))
        third = self.commit('planning')
        self.data['tasks']['T003']['correction_cycles'] = 0
        self.put(self.feature + '/execution.json', json.dumps(self.data))
        reset = self.commit('planning')
        self.assertTrue(any('cannot decrease' in e for e in ledger.transition_errors(self.root, reset, self.feature + '/execution.json', sdd.git)))
        self.assertEqual(ledger.transition_errors(self.root, third, self.feature + '/execution.json', sdd.git), [])
        with patch.multiple(signatures, KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
            self.assertTrue(any('cannot decrease' in e for e in sdd.validate_repo(self.root, self.baseline)))

    def task_merge(self):
        self.git('branch', 'task/r3.5/t003', self.source)
        self.git('switch', '-c', 'fixture-integration', self.source + '^')
        kind = '\nSDD-Type: tooling' if self.source_path.startswith(('docs/', 'tools/')) else ''
        self.git('merge', '--no-ff', '-S', '-m', f'integrate\n\nSpec: {self.feature}\nTask: T003\nImplements: FR-001 FR-002' + kind, 'task/r3.5/t003')
        return self.git('rev-parse', 'HEAD')

    def test_checkpoint_cannot_reuse_another_tasks_actual_merge(self):
        merge = self.task_merge()
        record = dict(merge_sha=merge)
        self.assertEqual(ledger.task_merge_errors(self.root, self.feature, 'T003', record, merge, sdd.git), [])
        self.assertTrue(ledger.task_merge_errors(self.root, self.feature, 'T002', record, merge, sdd.git))
        # Even a forged union trailer cannot turn T003 source into T002 work.
        self.git('commit', '--amend', '-S', '-m', f'integrate\n\nSpec: {self.feature}\nTask: T002 T003\nImplements: FR-001 FR-002')
        forged = self.git('rev-parse', 'HEAD')
        self.assertTrue(ledger.task_merge_errors(self.root, self.feature, 'T002', dict(merge_sha=forged), forged, sdd.git))

    def test_reviewed_non_application_task_can_integrate_on_its_exact_paths(self):
        for path in ['docs/note.md', 'tools/check.py']:
            self.source_path = path
            self.setUp()
            merge = self.task_merge()
            self.assertEqual(ledger.task_merge_errors(self.root, self.feature, 'T003', dict(merge_sha=merge), merge, sdd.git), [])
            self.assertTrue(ledger.task_merge_errors(self.root, self.feature, 'T002', dict(merge_sha=merge), merge, sdd.git))
            with patch.multiple(signatures, KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
                self.assertEqual(sdd.validate_repo(self.root, self.baseline), [])

    def test_pure_target_import_preserves_worker_scope_and_rejects_extra_edits(self):
        self.git('branch', 'worker', self.source)
        self.git('switch', '-c', 'target-moved', self.source + '^')
        self.put('FavaTests/ReadTests.swift', '// target T002 work')
        self.git('add', '.')
        self.git('commit', '-qm', f'target work\n\nSpec: {self.feature}\nTask: T002\nImplements: FR-001 FR-002')
        target = self.git('rev-parse', 'HEAD')
        self.git('switch', 'worker')
        self.git('merge', '--no-ff', '-S', '-m', f'import target\n\nSpec: {self.feature}\nTask: T002\nImplements: FR-001 FR-002', 'target-moved')
        head = self.git('rev-parse', 'HEAD')
        commits = self.git('rev-list', f'{target}..{head}').splitlines()
        self.assertEqual(integration.represented_task_ids(self.root, commits, target), ({'T003'}, []))
        self.put('Fava/Unscoped.swift', '// extra merge edit')
        self.git('add', '.')
        self.git('commit', '--amend', '-S', '--no-edit')
        changed = self.git('rev-parse', 'HEAD')
        self.assertTrue(integration.represented_task_ids(self.root, self.git('rev-list', f'{target}..{changed}').splitlines(), target)[1])

    def test_integrated_record_requires_exact_pr_head_target_and_task_evidence(self):
        merge = self.task_merge()
        parent = self.git('rev-parse', merge + '^1')
        record = dict(merge_sha=merge, pr='https://github.com/clemarc/fava/pull/10', integration_comment=123,
                      evidence=['https://github.com/clemarc/fava/pull/10#issuecomment-123'])
        report = dict(validated_head=self.source, validated_target=parent, tasks=['T003'])
        comment = dict(issue_url='https://api.github.com/repos/clemarc/fava/issues/10', user={'login': 'clemarc'},
                       html_url=record['evidence'][0], body=json.dumps(report))
        def api(*args):
            if '/pulls/' in args[-1]: return {'head': {'sha': self.source}}
            if '/commits/' in args[-1]: return {'commit': {'verification': {'verified': True, 'reason': 'valid'}}}
            return comment
        args = (self.root, self.feature, 'milestone/r3.5', 'T003', record, merge)
        with patch.object(milestone, 'merged_pr', return_value=record['pr']), patch.object(milestone, 'github', side_effect=api):
            self.assertEqual(milestone.integrated_task_errors(*args), [])
            for bad in [dict(report, tasks=['T002']), dict(report, validated_head='old'), dict(report, validated_target='old')]:
                comment['body'] = json.dumps(bad)
                self.assertTrue(milestone.integrated_task_errors(*args))
            comment['body'] = json.dumps(report)
            comment['issue_url'] += '1'
            self.assertTrue(milestone.integrated_task_errors(*args))

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

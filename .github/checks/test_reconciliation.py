"""Real signed synthetic histories for the single historical trailer exception."""
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
import reconciliation
import milestone
import sdd
import signatures
from test_checks import ROADMAP, SPEC


class SignedReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key_temp = tempfile.TemporaryDirectory(prefix='fava-synthetic-reconciliation-')
        cls.key_dir = Path(cls.key_temp.name)
        cls.env = dict(os.environ, GNUPGHOME=str(cls.key_dir))
        subprocess.run(['gpg', '--batch', '--passphrase', '', '--quick-generate-key',
                        'Synthetic Fixture <fixture@example.invalid>', 'rsa2048', 'sign', '1d'],
                       env=cls.env, check=True, capture_output=True)
        keys = subprocess.check_output(['gpg', '--batch', '--with-colons', '--list-keys'],
                                       env=cls.env, text=True)
        cls.fingerprint = next(line.split(':')[9] for line in keys.splitlines() if line.startswith('fpr:'))
        cls.public = cls.key_dir / 'public.asc'
        cls.public.write_bytes(subprocess.check_output(['gpg', '--armor', '--export', cls.fingerprint],
                                                      env=cls.env))

    @classmethod
    def tearDownClass(cls):
        subprocess.run(['gpgconf', '--kill', 'gpg-agent'], env=cls.env, capture_output=True)
        cls.key_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fava-reconciliation-history-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Synthetic Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.signingkey', self.fingerprint)
        self.git('config', 'gpg.format', 'openpgp')
        self.put('docs/baseline.md', 'Synthetic approved baseline\n')
        self.put('.specify/memory/constitution.md', 'Synthetic constitution\n')
        self.put('specs/demo/roadmap.md', ROADMAP.replace('R1', 'R3.5'))
        self.put('specs/demo-01-read/spec.md', SPEC.replace('entry R1', 'entry R3.5'))
        self.baseline = self.commit('baseline\n\nSDD-Type: process')
        self.put('specs/demo-01-read/plan.md', 'Synthetic reviewed preparation\n')
        self.prep = self.commit('preparation\n\nSDD-Type: planning')
        self.missing_message = 'docs: synthetic owner preparation merge\n'
        self.historical = self.merge(self.prep, [self.baseline, self.prep], self.missing_message)
        self.record = copy.deepcopy(reconciliation.RECORD)
        self.record.update(merge=self.historical, parents=[self.baseline, self.prep],
                           tree=self.git('rev-parse', self.historical + '^{tree}'),
                           message=sdd.git(self.root, 'show', '-s', '--format=%B', self.historical))
        self.record_text = json.dumps(self.record, indent=2) + '\n'
        self.addCleanup(patch.stopall)
        patch.multiple(reconciliation, RECORD=self.record, RECORD_TEXT=self.record_text).start()
        patch.multiple(signatures, KEY=self.public, FINGERPRINT=self.fingerprint,
                       OWNER_EMAIL='fixture@example.invalid').start()
        self.git('switch', '--detach', self.baseline)
        self.put(reconciliation.RECORD_PATH, self.record_text)
        self.proposal = self.commit('propose reconciliation\n\nSDD-Type: process')
        self.adoption = self.merge(self.proposal, [self.baseline, self.proposal],
                                   'owner adopts reconciliation\n\nSDD-Type: process')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], env=self.env,
                                       stderr=subprocess.PIPE, text=True).strip()

    def put(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self, message):
        self.git('add', '.')
        self.git('commit', '--allow-empty', '-q', '-S', '-m', message)
        return self.git('rev-parse', 'HEAD')

    def merge(self, tree_ref, parents, message, signed=True, email=None):
        args = ['-c', 'user.email=' + (email or 'fixture@example.invalid'), 'commit-tree']
        if signed:
            args.append('-S')
        args.append(self.git('rev-parse', tree_ref + '^{tree}'))
        for parent in parents:
            args.extend(['-p', parent])
        args.extend(['-m', message])
        return self.git(*args)

    def effective(self, sha=None, base=None, head=None):
        return reconciliation.commit_message(self.root, base or self.adoption, head or self.adoption,
                                             sha or self.historical, sdd.git)

    def assert_not_reconciled(self, sha=None, base=None, head=None):
        sha = sha or self.historical
        self.assertEqual(self.effective(sha, base, head), sdd.git(self.root, 'show', '-s', '--format=%B', sha))

    def assert_invalid_planning_message(self, message):
        self.assertTrue(sdd.validate_commit(message, ['specs/demo-01-read/plan.md'],
                                            lambda path: self.git('show', self.prep + ':' + path)))

    def test_exact_signed_owner_merge_reconciles_only_after_signed_adoption(self):
        self.assertTrue(signatures.verify(self.root, self.historical))
        self.assertTrue(signatures.verify(self.root, self.adoption))
        self.assertTrue(reconciliation.historical_merge(self.root, self.historical, sdd.git))
        self.assertEqual(reconciliation.adoption_merge(self.root, self.adoption, self.adoption, sdd.git),
                         self.adoption)
        original = sdd.git(self.root, 'show', '-s', '--format=%B', self.historical)
        self.assert_invalid_planning_message(original)
        effective = self.effective()
        self.assertEqual(sdd.trailers(effective), {'SDD-Type': ['planning']})
        self.assertEqual(sdd.validate_commit(effective, ['specs/demo-01-read/plan.md'], lambda path: ''), [])
        self.assertEqual(sdd.git(self.root, 'show', '-s', '--format=%B', self.historical), original)

    def test_repository_validation_uses_adopted_exception_and_rejects_future_omission(self):
        self.git('switch', '--detach', self.adoption)
        self.git('merge', '--no-ff', '-S', '-m', 'retain preparation history\n\nSDD-Type: planning', self.historical)
        promoted = self.git('rev-parse', 'HEAD')
        self.assertEqual(sdd.validate_repo(self.root, self.adoption, promoted), [])
        # The same introduced history fails when adoption is not in the base.
        errors = sdd.validate_repo(self.root, self.baseline, promoted)
        self.assertTrue(any('commit ' + self.historical[:12] + ':' in error and 'SDD-Type' in error for error in errors))
        self.put('docs/future.md', 'Future missing trailer\n')
        future = self.commit('future missing trailer')
        errors = sdd.validate_repo(self.root, self.adoption, future)
        self.assertTrue(any('commit ' + future[:12] + ':' in error and 'SDD-Type' in error for error in errors))
        self.assertFalse(any('commit ' + self.historical[:12] + ':' in error for error in errors))

    def test_runtime_rechecks_historical_preparation_after_valid_planning_amendment(self):
        self.git('switch', '--detach', self.historical)
        self.put('specs/demo-01-read/plan.md', 'Synthetic amended preparation\n')
        amended_source = self.commit('planning amendment\n\nSDD-Type: planning')
        amendment = self.merge(amended_source, [self.historical, amended_source],
                               'owner planning amendment\n\nSDD-Type: planning')
        old = dict(number=14, head='prepare/r3.5', merged='2026-10-16T20:36:14Z', merge_sha=self.historical)
        new = dict(number=15, head='prepare/r3.5', merged='2026-10-17T20:36:14Z', merge_sha=amendment)
        context = dict(prs=[new, old], preparation_branch='prepare/r3.5',
                       main_sha=self.adoption, target_sha=amendment)
        self.assertEqual(milestone.latest_preparation(context), new)
        # A good latest amendment does not excuse the old unadopted omission.
        with self.assertRaisesRegex(ValueError, 'retained preparation PR #14'):
            milestone.preparation_trailers(self.root, context)
        self.git('switch', '--detach', amendment)
        self.git('merge', '--no-ff', '-S', '-m', 'import governance\n\nSDD-Type: process', self.adoption)
        context['target_sha'] = self.git('rev-parse', 'HEAD')
        with patch.object(milestone, 'merged_pr', return_value='https://example.invalid/owner-main-adoption') as live:
            self.assertEqual(milestone.preparation_trailers(self.root, context), [
                dict(sha=self.adoption, pr='https://example.invalid/owner-main-adoption', historical_merge=self.historical)])
            live.assert_called_once_with('clemarc/fava', self.adoption, 'main')
        # Live approval on another destination/owner must still stop startup.
        with patch.object(milestone, 'merged_pr', side_effect=ValueError('wrong live adoption destination')):
            with self.assertRaisesRegex(ValueError, 'wrong live adoption destination'):
                milestone.preparation_trailers(self.root, context)
        bad = self.merge(amended_source, [self.historical, amended_source], 'future untrailered amendment')
        context['prs'] = [dict(new, merge_sha=bad), old]
        with self.assertRaisesRegex(ValueError, 'retained preparation PR #15'):
            milestone.preparation_trailers(self.root, context)

    def test_proposal_or_pending_adoption_does_not_activate_exception(self):
        for base, head in [(self.baseline, self.proposal), (self.baseline, self.adoption),
                           (self.proposal, self.proposal), (self.proposal, self.adoption)]:
            with self.subTest(base=base, head=head):
                self.assertIsNone(reconciliation.adoption_merge(self.root, base, head, sdd.git))
                self.assert_not_reconciled(base=base, head=head)

    def test_record_must_be_exact_in_both_validation_revisions(self):
        for content in [None, self.record_text + '\n', self.record_text.replace('R3.5', 'R4')]:
            with self.subTest(content=content):
                self.git('switch', '--detach', self.adoption)
                if content is None:
                    self.git('rm', reconciliation.RECORD_PATH)
                else:
                    self.put(reconciliation.RECORD_PATH, content)
                changed = self.commit('alter record\n\nSDD-Type: process')
                self.assertFalse(reconciliation.record_at(self.root, changed, sdd.git))
                for base, head in [(changed, changed), (self.adoption, changed), (changed, self.adoption)]:
                    self.assert_not_reconciled(base=base, head=head)

    def test_historical_identity_fields_are_all_immutable(self):
        alternatives = {
            'merge': self.prep,
            'parents': [self.prep, self.baseline],
            'tree': self.git('rev-parse', self.baseline + '^{tree}'),
            'message': self.record['message'] + 'changed\n',
        }
        for field, value in alternatives.items():
            with self.subTest(field=field), patch.object(reconciliation, 'RECORD', dict(self.record, **{field: value})):
                self.assertFalse(reconciliation.historical_merge(self.root, self.historical, sdd.git))
                self.assert_not_reconciled()
        other = self.merge(self.prep, [self.baseline, self.prep], 'different historical message')
        self.assert_not_reconciled(other)

    def test_historical_merge_requires_signed_owner_and_exact_two_parent_source_tree(self):
        variants = [
            self.merge(self.prep, [self.baseline, self.prep], self.missing_message, signed=False),
            self.merge(self.prep, [self.baseline, self.prep], self.missing_message, email='other@example.invalid'),
            self.merge(self.prep, [self.baseline], self.missing_message),
            self.merge(self.prep, [self.baseline, self.prep, self.proposal], self.missing_message),
            self.merge(self.baseline, [self.baseline, self.prep], self.missing_message),
        ]
        for sha in variants:
            with self.subTest(sha=sha):
                # Bind every immutable field to the candidate, so rejection must
                # come from ownership, signature, parent count or source-tree proof.
                record = dict(self.record, merge=sha,
                              parents=self.git('show', '-s', '--format=%P', sha).split(),
                              tree=self.git('rev-parse', sha + '^{tree}'),
                              message=sdd.git(self.root, 'show', '-s', '--format=%B', sha))
                with patch.object(reconciliation, 'RECORD', record):
                    self.assertFalse(reconciliation.historical_merge(self.root, sha, sdd.git))

    def test_wrong_trusted_signing_key_rejects_historical_and_adoption(self):
        with patch.object(signatures, 'FINGERPRINT', '0' * 40):
            self.assertFalse(signatures.verify(self.root, self.historical))
            self.assertFalse(reconciliation.historical_merge(self.root, self.historical, sdd.git))
            self.assertIsNone(reconciliation.adoption_merge(self.root, self.adoption, self.adoption, sdd.git))
            self.assert_not_reconciled()

    def test_adoption_requires_signed_owner_two_parents_and_governance_trailer(self):
        variants = [
            self.merge(self.proposal, [self.baseline, self.proposal], 'unsigned\n\nSDD-Type: process', signed=False),
            self.merge(self.proposal, [self.baseline, self.proposal], 'wrong owner\n\nSDD-Type: process', email='other@example.invalid'),
            self.merge(self.proposal, [self.proposal], 'one parent\n\nSDD-Type: process'),
            self.merge(self.proposal, [self.baseline, self.proposal, self.prep], 'three parents\n\nSDD-Type: process'),
        ]
        for message in ['no terminal trailer', 'bad kind\n\nSDD-Type: planning',
                        'duplicate\n\nSDD-Type: process\nSDD-Type: tooling',
                        'nonterminal\n\nSDD-Type: process\n\ntrailing prose']:
            variants.append(self.merge(self.proposal, [self.baseline, self.proposal], message))
        for sha in variants:
            with self.subTest(sha=sha):
                self.assertIsNone(reconciliation.adoption_merge(self.root, sha, sha, sdd.git))
                self.assert_not_reconciled(base=sha, head=sha)
        tooling = self.merge(self.proposal, [self.baseline, self.proposal], 'tooling adoption\n\nSDD-Type: tooling')
        self.assertEqual(reconciliation.adoption_merge(self.root, tooling, tooling, sdd.git), tooling)

    def test_adoption_record_must_be_absent_in_first_parent_and_exact_in_source(self):
        self.git('switch', '--detach', self.baseline)
        self.put(reconciliation.RECORD_PATH, self.record_text.replace('R3.5', 'R4'))
        previous = self.commit('different prior record\n\nSDD-Type: process')
        for parent in [self.proposal, previous]:
            adoption = self.merge(self.proposal, [parent, self.proposal], 'replace record\n\nSDD-Type: process')
            self.assertIsNone(reconciliation.adoption_merge(self.root, adoption, adoption, sdd.git))
        for source in [self.baseline, previous]:
            adoption = self.merge(self.proposal, [self.baseline, source], 'invent record in merge\n\nSDD-Type: process')
            self.assertIsNone(reconciliation.adoption_merge(self.root, adoption, adoption, sdd.git))

    def test_adoption_rejects_merge_only_edits_and_native_source(self):
        self.git('switch', '--detach', self.proposal)
        self.put('docs/unreviewed.md', 'Extra merge-only edit\n')
        changed = self.commit('extra tree\n\nSDD-Type: process')
        adoption = self.merge(changed, [self.baseline, self.proposal], 'merge edits\n\nSDD-Type: process')
        self.assertIsNone(reconciliation.adoption_merge(self.root, adoption, adoption, sdd.git))
        for path in ['Fava/Injected.swift', 'FavaTests/InjectedTests.swift', 'Fava.xcodeproj/project.pbxproj']:
            with self.subTest(path=path):
                self.git('switch', '--detach', self.proposal)
                self.put(path, '// Synthetic source-bearing governance proposal\n')
                source = self.commit('source proposal\n\nSDD-Type: process')
                adoption = self.merge(source, [self.baseline, source], 'source adoption\n\nSDD-Type: process')
                self.assertIsNone(reconciliation.adoption_merge(self.root, adoption, adoption, sdd.git))
                self.assert_not_reconciled(base=adoption, head=adoption)

    def test_source_bearing_historical_merge_cannot_receive_planning_exception(self):
        self.git('switch', '--detach', self.prep)
        self.put('Fava/Injected.swift', '// Synthetic application source\n')
        source = self.commit('source without task trailers')
        historical = self.merge(source, [self.baseline, source], self.missing_message)
        record = dict(self.record, merge=historical, parents=[self.baseline, source],
                      tree=self.git('rev-parse', historical + '^{tree}'))
        with patch.object(reconciliation, 'RECORD', record):
            self.assertFalse(reconciliation.historical_merge(self.root, historical, sdd.git))
            self.assert_not_reconciled(historical)

    def test_future_missing_trailers_are_not_reconciled(self):
        self.git('switch', '--detach', self.adoption)
        self.put('specs/demo-01-read/plan.md', 'Future untrailered planning\n')
        future = self.commit('future missing planning trailer')
        self.assert_not_reconciled(future, head=future)
        self.assert_invalid_planning_message(self.effective(future, head=future))
        self.put('Fava/Injected.swift', '// Future untrailered source\n')
        source = self.commit('future missing implementation trailers')
        self.assert_not_reconciled(source, head=source)
        self.assertTrue(sdd.validate_commit(self.effective(source, head=source), ['Fava/Injected.swift'], lambda path: ''))

    def test_adoption_is_found_when_imported_as_second_parent_history(self):
        self.git('switch', '--detach', self.historical)
        self.git('merge', '--no-ff', '-S', '-m', 'import governance\n\nSDD-Type: process', self.adoption)
        imported = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.git('rev-parse', imported + '^2'), self.adoption)
        self.assertNotEqual(self.git('rev-parse', imported + '^{tree}'),
                            self.git('rev-parse', self.adoption + '^{tree}'))
        self.assertEqual(reconciliation.adoption_merge(self.root, imported, imported, sdd.git), self.adoption)
        self.assertEqual(sdd.trailers(self.effective(base=imported, head=imported)), {'SDD-Type': ['planning']})

    def test_copying_exact_record_without_adoption_ancestry_does_not_activate_exception(self):
        self.assertTrue(reconciliation.record_at(self.root, self.proposal, sdd.git))
        self.assertTrue(reconciliation.record_at(self.root, self.adoption, sdd.git))
        self.assertIsNone(reconciliation.adoption_merge(self.root, self.adoption, self.proposal, sdd.git))
        self.assert_not_reconciled(base=self.adoption, head=self.proposal)
        self.git('switch', '--detach', self.historical)
        self.put(reconciliation.RECORD_PATH, self.record_text)
        copied = self.commit('copy exact record without owner adoption\n\nSDD-Type: process')
        self.assertTrue(reconciliation.record_at(self.root, copied, sdd.git))
        self.assertIsNone(reconciliation.adoption_merge(self.root, self.adoption, copied, sdd.git))
        self.assert_not_reconciled(base=self.adoption, head=copied)

    def test_ambiguous_introducing_merges_cannot_activate_exception(self):
        other = self.merge(self.proposal, [self.baseline, self.proposal],
                           'independent duplicate adoption\n\nSDD-Type: process')
        combined = self.merge(self.proposal, [self.adoption, other], 'combine histories\n\nSDD-Type: process')
        self.assertIsNone(reconciliation.adoption_merge(self.root, combined, combined, sdd.git))
        self.assert_not_reconciled(base=combined, head=combined)


if __name__ == '__main__':
    unittest.main()

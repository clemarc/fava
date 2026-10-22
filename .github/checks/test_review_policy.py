"""Signed synthetic policy adoption and retained legacy review selection."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_reconciliation as fixtures
import review_policy
import sdd
import signatures


class ReviewPolicyTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.SignedReconciliationTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.SignedReconciliationTests.tearDownClass.__func__)
    git = fixtures.SignedReconciliationTests.git
    put = fixtures.SignedReconciliationTests.put
    commit = fixtures.SignedReconciliationTests.commit
    merge = fixtures.SignedReconciliationTests.merge

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fava-review-policy-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Synthetic Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.signingkey', self.fingerprint)
        self.git('config', 'gpg.format', 'openpgp')
        self.put('docs/baseline.md', 'Synthetic baseline\n')
        self.baseline = self.commit('baseline\n\nSDD-Type: process')
        self.put(review_policy.RECORD_PATH, review_policy.RECORD_TEXT)
        self.proposal = self.commit('propose policy\n\nSDD-Type: tooling')
        self.adoption = self.merge(self.proposal, [self.baseline, self.proposal],
                                   'owner adopts policy\n\nSDD-Type: tooling')
        self.addCleanup(patch.stopall)
        patch.multiple(signatures, KEY=self.public, FINGERPRINT=self.fingerprint,
                       OWNER_EMAIL='fixture@example.invalid').start()

    def select(self, target=None, head=None, verify=None):
        return review_policy.policy_for(self.root, target or self.adoption,
                                        head or self.adoption, sdd.git,
                                        verify_pr=verify or (lambda repo, sha, dest: 'https://github.com/clemarc/fava/pull/36'))

    def test_signed_owner_main_adoption_then_import_selects_new_policy(self):
        calls = []
        self.assertEqual(self.select(verify=lambda *args: calls.append(args)), review_policy.CODEX_ONLY)
        self.assertEqual(calls, [('clemarc/fava', self.adoption, 'main')])
        self.git('switch', '--detach', self.baseline)
        self.put('docs/milestone.md', 'Existing milestone history\n')
        milestone = self.commit('milestone\n\nSDD-Type: planning')
        self.git('merge', '--no-ff', '-S', '-m', 'import approved policy\n\nSDD-Type: tooling', self.adoption)
        imported = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.select(imported, imported), review_policy.CODEX_ONLY)
        self.assertEqual(self.select(self.baseline, self.proposal), review_policy.LEGACY)
        self.assertNotEqual(milestone, imported)

    def test_head_only_or_old_retained_target_cannot_adopt_new_policy(self):
        for head in [self.proposal, self.adoption]:
            self.assertEqual(self.select(self.baseline, head), review_policy.LEGACY)
        with self.assertRaisesRegex(ValueError, 'signed owner-adopted'):
            self.select(self.proposal, self.proposal)

    def test_unsigned_wrong_owner_or_non_main_merge_cannot_adopt(self):
        for signed, email in [(False, None), (True, 'other@example.invalid')]:
            merge = self.merge(self.proposal, [self.baseline, self.proposal],
                               'adopt\n\nSDD-Type: tooling', signed=signed, email=email)
            with self.assertRaisesRegex(ValueError, 'signed owner-adopted'):
                self.select(merge, merge)
        def wrong_pr(*args):
            raise ValueError('not owner merged into main')
        with self.assertRaisesRegex(ValueError, 'signed owner-adopted'):
            self.select(verify=wrong_pr)

    def test_altered_policy_missing_head_or_application_adoption_blocks(self):
        self.put(review_policy.RECORD_PATH, review_policy.RECORD_TEXT + ' ')
        altered = self.commit('alter policy\n\nSDD-Type: tooling')
        for target, head in [(altered, altered), (self.adoption, altered), (self.adoption, self.baseline)]:
            with self.assertRaisesRegex(ValueError, 'unsupported, altered or absent'):
                self.select(target, head)
        self.put(review_policy.RECORD_PATH, review_policy.RECORD_TEXT)
        self.put('Fava/Injected.swift', '// synthetic application change\n')
        source = self.commit('source with policy\n\nSDD-Type: tooling')
        merge = self.merge(source, [self.baseline, source], 'adopt\n\nSDD-Type: tooling')
        with self.assertRaisesRegex(ValueError, 'signed owner-adopted'):
            self.select(merge, merge)

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import sdd


class PilotTests(unittest.TestCase):
    feature = sorted(sdd.PILOT_FEATURES)[0]
    message = 'feat: fixture\n\nDelivery-Pilot: healthkit-r1-r3'

    def test_unrelated_feature_and_missing_authorization_keep_normal_gate(self):
        base = sdd.PILOT_APPROVAL
        with patch.object(sdd, 'git') as git:
            self.assertEqual(sdd.pilot_planning_ref('.', base, 'head', 'specs/demo-01-read', self.message), base)
            self.assertEqual(sdd.pilot_planning_ref('.', base, 'head', self.feature, 'feat: fixture'), base)
            self.assertEqual(sdd.pilot_planning_ref('.', 'later-base', 'head', self.feature, self.message), 'later-base')
            self.assertEqual(sdd.pilot_planning_ref('.', base, base, self.feature, self.message), base)
            git.assert_not_called()

    def test_recorded_history_and_prior_plan_and_tasks_are_required(self):
        base = sdd.PILOT_APPROVAL
        with patch.object(sdd, 'git', return_value='parent\n') as git:
            self.assertEqual(sdd.pilot_planning_ref('.', base, 'head', self.feature, self.message), 'parent')
            self.assertEqual(git.call_count, 6)
        for failure in range(6):
            calls = ['parent\n'] * 6
            calls[failure] = subprocess.CalledProcessError(1, 'git')
            with patch.object(sdd, 'git', side_effect=calls):
                self.assertEqual(sdd.pilot_planning_ref('.', base, 'head', self.feature, self.message), base)


class PilotHistoryTests(unittest.TestCase):
    feature = PilotTests.feature
    message = PilotTests.message

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.directory = self.root / self.feature
        self.directory.mkdir(parents=True)
        (self.directory / 'spec.md').write_text('Approved fixture contract\n')
        self.approval = self.commit('approved fixture')
        self.write_planning()
        self.planning = self.commit('initial planning fixture')
        (self.root / 'source.txt').write_text('original implementation\n')
        self.implementation = self.commit('implementation fixture')
        (self.root / 'checkpoint.txt').write_text('recorded delivery\n')
        self.delivery_head = self.commit('delivery checkpoint fixture')
        for name in ('plan.md', 'tasks.md'):
            (self.directory / name).unlink()
        self.future_base = self.commit('future base without derived planning')
        self.write_planning()
        self.future_planning = self.commit('unmerged future planning fixture')
        (self.root / 'source.txt').write_text('future implementation\n')
        self.future_implementation = self.commit('future implementation fixture')

    def git(self, *args):
        return subprocess.check_output(
            ['git', '-C', str(self.root), *args], stderr=subprocess.PIPE,
            text=True).strip()

    def commit(self, message):
        self.git('add', '-A')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-qm', message)
        return self.git('rev-parse', 'HEAD')

    def write_planning(self):
        for name in ('plan.md', 'tasks.md'):
            (self.directory / name).write_text('Derived fixture\n')

    def resolve(self, base, sha):
        with patch.multiple(sdd, PILOT_APPROVAL=self.approval,
                            PILOT_DELIVERY_HEAD=self.delivery_head):
            return sdd.pilot_planning_ref(
                self.root, base, sha, self.feature, self.message)

    def test_original_delivery_keeps_its_preceding_planning_checkpoint(self):
        self.assertEqual(self.resolve(self.approval, self.implementation), self.planning)

    def test_future_pr_cannot_reuse_the_trailer_for_unmerged_planning(self):
        self.assertEqual(self.resolve(self.future_base, self.future_implementation),
                         self.future_base)

    def test_original_base_cannot_extend_the_recorded_delivery(self):
        self.assertEqual(self.resolve(self.approval, self.future_implementation),
                         self.approval)

    def test_fork_from_original_planning_is_outside_the_recorded_delivery(self):
        self.git('checkout', '-q', '--detach', self.planning)
        (self.root / 'source.txt').write_text('unapproved fork implementation\n')
        fork = self.commit('fork fixture')
        self.assertEqual(self.resolve(self.approval, fork), self.approval)

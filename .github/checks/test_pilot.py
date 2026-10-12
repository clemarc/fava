import unittest
from unittest.mock import patch

import sdd


class PilotTests(unittest.TestCase):
    feature = sorted(sdd.PILOT_FEATURES)[0]
    message = 'feat: fixture\n\nDelivery-Pilot: healthkit-r1-r3'

    def test_unrelated_feature_and_missing_authorization_keep_normal_gate(self):
        with patch.object(sdd, 'git') as git:
            self.assertEqual(sdd.pilot_planning_ref('.', 'base', 'head', 'specs/demo-01-read', self.message), 'base')
            self.assertEqual(sdd.pilot_planning_ref('.', 'base', 'head', self.feature, 'feat: fixture'), 'base')
            git.assert_not_called()

    def test_approved_ancestor_and_prior_plan_and_tasks_are_required(self):
        with patch.object(sdd, 'git', return_value='parent\n') as git:
            self.assertEqual(sdd.pilot_planning_ref('.', 'base', 'head', self.feature, self.message), 'parent')
            self.assertEqual(git.call_count, 5)
        import subprocess
        for failure in range(5):
            calls = ['parent\n'] * 5
            calls[failure] = subprocess.CalledProcessError(1, 'git')
            with patch.object(sdd, 'git', side_effect=calls):
                self.assertEqual(sdd.pilot_planning_ref('.', 'base', 'head', self.feature, self.message), 'base')

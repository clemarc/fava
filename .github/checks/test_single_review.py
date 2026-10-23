"""Codex-only assessments retain full checks and findings without a subagent."""
import copy
import unittest
from unittest.mock import patch

import test_integration_history as history
import test_milestones as fixtures
from test_milestones import integration
from review_policy import CODEX_ONLY, LEGACY


class SingleReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        history.RetainedGateTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        history.RetainedGateTests.tearDownClass()

    def setUp(self):
        self.case = history.RetainedGateTests(methodName='runTest')
        self.addCleanup(self.case.doCleanups)
        self.case.setUp()
        self.case.start_task()
        self.case.evidence()
        self.case.report.pop('independent_review_comment')
        self.case.report.pop('independent_review_url')
        self.case.report.update(review_policy=CODEX_ONLY, findings=[],
                                native=copy.deepcopy(self.case.review['native']))

    def assess(self, policy=CODEX_ONLY):
        with patch.object(integration, 'policy_for', return_value=policy):
            return self.case.assess()

    def test_complete_current_and_retained_assessments_without_independent_report(self):
        self.assertEqual(self.assess(), [])
        self.case.complete()
        with patch.object(integration, 'policy_for', return_value=CODEX_ONLY):
            self.assertEqual(self.case.reconcile_completion(), [])

    def test_report_cannot_claim_new_policy_on_legacy_target(self):
        self.assertTrue(self.assess(LEGACY))
        self.case.report.pop('review_policy')
        self.assertTrue(self.assess(LEGACY))  # Old independent gate remains.
        self.assertTrue(self.assess())  # New reports must name adopted policy.

    def test_actual_findings_need_complete_timely_coordinator_disposition(self):
        url = 'https://github.com/clemarc/fava/pull/10#discussion_r500'
        self.case.comments = [dict(html_url=url, body='Synthetic P1', created_at=self.case.at(self.case.clock + 3))]
        self.assertTrue(self.assess())
        self.case.report['findings'] = [dict(url=url, rationale='Fixed and verified', evidence=['synthetic test'],
                                            disposition='fixed', head=self.case.head, target=self.case.target)]
        self.assertEqual(self.assess(), [])
        for seconds in [5, 6]:
            self.case.comments[0]['created_at'] = self.case.at(self.case.clock + seconds)
            self.assertTrue(self.assess())
        self.case.comments[0]['created_at'] = self.case.at(self.case.clock + 3)
        self.case.report['findings'][0]['target'] = 'stale'
        self.assertTrue(self.assess())

    def test_native_interpretation_and_exact_head_bot_completion_still_required(self):
        native = self.case.report.pop('native')
        self.assertTrue(self.assess())
        self.case.report['native'] = native
        self.assertEqual(self.assess(), [])
        self.case.bot[0]['commit_id'] = 'stale'
        self.assertTrue(self.assess())

    def test_evaluate_cannot_waive_bot_unavailability_under_new_policy(self):
        good = fixtures.IntegrationTests().evidence()
        good.update(review_policy=CODEX_ONLY, independent_review=False)
        self.assertEqual(integration.evaluate(good), [])
        for changes in [dict(codex_available=False, codex_unavailability_evidence='actual outage'),
                        dict(codex_configured=False), dict(codex_review_complete=False)]:
            self.assertTrue(integration.evaluate(dict(good, **changes)))

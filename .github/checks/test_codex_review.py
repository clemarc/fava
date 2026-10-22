"""Bounded review scheduling, immutable proof and resumable request history."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/sdd'))
import codex_review as review


class CodexReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fava-review-scheduling-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Synthetic Fixture')
        self.git('-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-qm', 'synthetic')
        self.head = self.git('rev-parse', 'HEAD')
        self.start = datetime(2026, 10, 22, 10, tzinfo=timezone.utc)
        self.head_time = self.start - timedelta(seconds=1)
        self.comments, self.reviews, self.reactions = [], [], {}
        self.now = self.start + timedelta(minutes=21)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True).strip()

    def at(self, seconds=0):
        return (self.start + timedelta(seconds=seconds)).isoformat().replace('+00:00', 'Z')

    def request(self, ident=1, seconds=0, head=None, marked=False):
        head = head or self.head
        return dict(id=ident, issue_url='https://api.github.com/repos/clemarc/fava/issues/36',
                    html_url=f'https://github.com/clemarc/fava/pull/36#issuecomment-{ident}',
                    user={'login': 'clemarc'}, created_at=self.at(seconds), updated_at=self.at(seconds),
                    body=review.request_body(head, ident - 1) if marked else '@codex review ' + head)

    def summary(self, status='running', head=None):
        state = dict(code_review=dict(commit_sha=head or self.head, status=status))
        return dict(id=50, user=dict(login=review.BOT, id=review.BOT_ID, type='Bot'),
                    body='<!-- codex-review-state:v1 ' + json.dumps(state) + ' -->',
                    created_at=self.at(1), updated_at=self.at(1))

    def receipt(self):
        return dict(id=2, issue_url='https://api.github.com/repos/clemarc/fava/issues/36',
                    html_url='https://github.com/clemarc/fava/pull/36#issuecomment-2',
                    user=dict(login=review.BOT, id=review.BOT_ID, type='Bot'),
                    performed_via_github_app=dict(slug='chatgpt-codex-connector', id=1144995),
                    created_at=self.at(20), updated_at=self.at(20),
                    body="<!-- codex-review-receipt:v1 -->\n\nCodex Review: Didn't find any major issues. Fine!\n\n"
                         + '**Reviewed commit:** `' + self.head[:10] + '`')

    def plan(self):
        return review.plan(self.root, self.head, 36, self.head_time, self.comments, self.reviews,
                           self.reactions, self.now)

    def test_initial_request_and_marker_have_only_one_full_sha(self):
        self.assertEqual(self.plan()['decision'], 'request')
        self.comments = [self.request(marked=True)]
        self.now = self.start + timedelta(minutes=1)
        result = self.plan()
        self.assertEqual(result['decision'], 'wait')
        self.assertEqual(result['request_comments'], [1])

    def test_active_summary_never_creates_a_duplicate_after_timeout(self):
        for status in ['running', 'in_progress', 'queued', 'pending']:
            self.comments = [self.request(), self.summary(status)]
            self.assertEqual(self.plan()['decision'], 'wait')

    def test_summary_completed_is_not_completion_proof(self):
        self.comments = [self.request(), self.summary('completed')]
        self.assertEqual(self.plan()['decision'], 'blocked')
        self.assertIsNone(self.plan()['completion'])

    def test_unacknowledged_timeout_has_exactly_one_retry_across_restarts(self):
        self.comments = [self.request()]
        self.assertEqual(self.plan()['decision'], 'retry')
        self.comments += [self.request(2, 20 * 60, marked=True)]
        result = self.plan()
        self.assertEqual(result['decision'], 'wait')
        self.assertEqual(result['retry_count'], 1)
        # Plain historical requests count too; a new marker cannot reset budget.
        self.comments[1] = self.request(2, 20 * 60)
        self.assertEqual(self.plan()['decision'], 'wait')

    def test_failure_retries_once_without_waiting_for_timeout(self):
        self.now = self.start + timedelta(minutes=2)
        for state in ['failed', 'error', 'cancelled', 'canceled']:
            self.comments = [self.request(), self.summary(state)]
            self.assertEqual(self.plan()['decision'], 'retry')

    def test_deadline_never_resets_on_retry_or_running_summary(self):
        self.comments = [self.request(), self.request(2, 20 * 60), self.summary()]
        self.now = self.start + timedelta(minutes=45)
        result = self.plan()
        self.assertEqual(result['decision'], 'blocked')
        self.assertEqual(result['age_seconds'], 45 * 60)

    def test_auto_trigger_running_without_manual_request_also_has_bounded_wait(self):
        self.comments = [self.summary()]
        self.assertEqual(self.plan()['decision'], 'wait')
        self.now = self.start + timedelta(minutes=46)
        result = self.plan()
        self.assertEqual(result['decision'], 'blocked')
        self.assertEqual(result['age_basis'], 'head_commit')
        # A newly edited running summary cannot reset that fallback deadline.
        self.comments[0]['updated_at'] = self.now.isoformat()
        self.assertEqual(self.plan()['decision'], 'blocked')

    def test_auto_completion_without_request_can_establish_fresh_request_proof(self):
        self.comments = [self.summary('completed'), self.receipt()]
        result = self.plan()
        self.assertEqual(result['decision'], 'request')
        self.assertEqual(result['attempt'], 0)
        self.assertIsNone(result['completion'])

    def test_unknown_summary_status_does_not_guess_retry_eligibility(self):
        for requests in [[], [self.request()]]:
            self.comments = requests + [self.summary('unexpected-status')]
            self.assertEqual(self.plan()['decision'], 'blocked')

    def test_failed_second_attempt_blocks_without_third_request(self):
        failed = self.summary('failed')
        failed['updated_at'] = self.at(20 * 60 + 1)
        self.comments = [self.request(), self.request(2, 20 * 60), failed]
        result = self.plan()
        self.assertEqual(result['decision'], 'blocked')
        self.assertEqual(result['retry_count'], 1)

    def test_prior_attempt_failure_cannot_fail_new_retry_before_it_runs(self):
        for state in ['failed', 'error', 'cancelled', 'canceled']:
            failed = self.summary(state)
            self.comments = [self.request(), failed]
            self.assertEqual(self.plan()['decision'], 'retry')
            retry = self.request(2, 20 * 60, marked=True)
            self.comments.append(retry)
            for at in [1, 20 * 60]:
                failed['updated_at'] = self.at(at)
                result = self.plan()
                self.assertEqual(result['decision'], 'wait')
                self.assertTrue(result['summary_stale'])
            failed['updated_at'] = self.at(20 * 60 + 1)
            self.assertEqual(self.plan()['decision'], 'blocked')

    def test_prior_auto_completion_cannot_block_fresh_manual_request(self):
        completed = self.summary('completed')
        self.comments = [completed]
        self.assertEqual(self.plan()['decision'], 'request')
        self.comments.append(self.request(seconds=2))
        self.now = self.start + timedelta(minutes=1)
        result = self.plan()
        self.assertEqual(result['decision'], 'wait')
        self.assertTrue(result['summary_stale'])
        completed['updated_at'] = self.at(3)
        self.assertEqual(self.plan()['decision'], 'blocked')

    def test_edited_multi_sha_and_wrong_pr_requests_require_reconciliation(self):
        for changes in [dict(updated_at=self.at(2)),
                        dict(body='@codex review ' + self.head + ' ' + 'a' * 40),
                        dict(issue_url='https://api.github.com/repos/clemarc/fava/issues/99')]:
            self.comments = [dict(self.request(), **changes)]
            self.assertEqual(self.plan()['decision'], 'blocked')

    def test_head_movement_ignores_old_requests_and_old_running_summary(self):
        self.comments = [self.request(head='a' * 40), self.summary(head='a' * 40)]
        self.assertEqual(self.plan()['decision'], 'request')

    def test_receipt_completes_only_with_actual_bot_identity_and_immutable_sha_binding(self):
        self.comments = [self.request(), self.receipt()]
        self.assertEqual(self.plan()['decision'], 'complete')
        for changes in [dict(updated_at=self.at(21)),
                        dict(user=dict(login=review.BOT, id=999, type='Bot')),
                        dict(body=self.receipt()['body'].replace(self.head[:10], 'a' * 10))]:
            self.comments = [self.request(), dict(self.receipt(), **changes)]
            self.assertNotEqual(self.plan()['decision'], 'complete')

    def test_review_completion_is_bound_to_bot_head_and_time(self):
        actual = dict(id=3, user=dict(login=review.BOT, id=review.BOT_ID, type='Bot'),
                      commit_id=self.head, state='COMMENTED', submitted_at=self.at(10), html_url='review/3')
        self.reviews = [actual]
        self.assertEqual(self.plan()['decision'], 'complete')
        for changes in [dict(commit_id='a' * 40), dict(state='PENDING'), dict(state='DISMISSED'),
                        dict(submitted_at=self.at(-2)), dict(user={'login': review.BOT})]:
            self.reviews = [dict(actual, **changes)]
            self.assertNotEqual(self.plan()['decision'], 'complete')

    def test_reaction_requires_actual_bot_and_current_request(self):
        self.comments = [self.request()]
        actual = dict(content='+1', user=dict(login=review.BOT, id=review.BOT_ID, type='Bot'), created_at=self.at(10))
        self.reactions = {1: [actual]}
        self.assertEqual(self.plan()['decision'], 'complete')
        self.reactions = {1: [dict(actual, created_at=self.at(-2))]}
        self.assertNotEqual(self.plan()['decision'], 'complete')

    def test_retry_write_rechecks_live_state_and_posts_at_most_once(self):
        initial = dict(self.plan(), decision='retry', attempt=1)
        api_calls = []
        def api(*args):
            api_calls.append(args)
            return {'id': 5}
        with patch.object(review, 'inspect_review', side_effect=[initial, dict(initial, decision='complete')]):
            self.assertEqual(review.run(self.root, 36, retry=True, api=api)['decision'], 'complete')
        self.assertEqual(api_calls, [])
        with patch.object(review, 'inspect_review', return_value=initial):
            result = review.run(self.root, 36, retry=True, api=api)
        self.assertEqual(result['posted_comment'], 5)
        self.assertEqual(len(api_calls), 1)
        self.assertIn('@codex review ' + self.head, api_calls[0][-1])

    def test_ambiguous_post_does_not_resend_and_next_call_reconciles_visible_comment(self):
        eligible = dict(self.plan(), decision='retry', attempt=1)
        with patch.object(review, 'inspect_review', return_value=eligible):
            api = unittest.mock.Mock(side_effect=ValueError('timeout'))
            self.assertEqual(review.run(self.root, 36, retry=True, api=api)['decision'], 'reconcile')
            self.assertEqual(api.call_count, 1)
        self.comments = [self.request(), self.request(2, 20 * 60, marked=True)]
        with patch.object(review, 'inspect_review', return_value=self.plan()):
            api = unittest.mock.Mock()
            self.assertEqual(review.run(self.root, 36, retry=True, api=api)['decision'], 'wait')
            api.assert_not_called()

    def test_read_only_invocation_never_posts(self):
        with patch.object(review, 'inspect_review', return_value=dict(self.plan(), decision='retry', attempt=1)):
            api = unittest.mock.Mock()
            self.assertEqual(review.run(self.root, 36, api=api)['decision'], 'retry')
            api.assert_not_called()


if __name__ == '__main__':
    unittest.main()

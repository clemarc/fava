"""Immutable Codex completion receipts, exact SHA binding and retained gates."""
import copy
from datetime import timedelta
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/sdd'))
import integration
import sdd
import test_integration_history as history


BOT = 'chatgpt-codex-connector[bot]'
FOOTER = '''<details> <summary>ℹ️ About Codex in GitHub</summary>
<br/>

[Your team has set up Codex to review pull requests in this repo](https://chatgpt.com/codex/cloud/settings/general). Reviews are triggered when you
- Open a pull request for review
- Mark a draft as ready
- Comment "@codex review".

If Codex has suggestions, it will comment; otherwise it will react with 👍.




Codex can also answer questions or update the PR. Try commenting "@codex address that feedback".

</details>'''


def request(head, at, number=10):
    return dict(id=125, issue_url=f'https://api.github.com/repos/clemarc/fava/issues/{number}',
                html_url=f'https://github.com/clemarc/fava/pull/{number}#issuecomment-125',
                user={'login': 'clemarc'}, body='@codex review\n\nReview full head ' + head,
                created_at=at, updated_at=at)


def receipt(head, at, number=10):
    return dict(id=126, issue_url=f'https://api.github.com/repos/clemarc/fava/issues/{number}',
                html_url=f'https://github.com/clemarc/fava/pull/{number}#issuecomment-126',
                user={'login': BOT, 'type': 'Bot'},
                performed_via_github_app={'slug': 'chatgpt-codex-connector', 'id': 1144995},
                body="<!-- codex-review-receipt:v1 -->\n\nCodex Review: Didn't find any major issues. Nice work!\n\n"
                     + '**Reviewed commit:** `' + head[:10] + '`\n\n' + FOOTER,
                created_at=at, updated_at=at)


class ReceiptBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fava-synthetic-receipt-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Synthetic Fixture')
        self.git('-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-qm', 'synthetic head')
        self.head = self.git('rev-parse', 'HEAD')
        self.request = request(self.head, '2026-10-17T08:21:17Z')
        self.receipt = receipt(self.head, '2026-10-17T08:21:19Z')
        self.head_time = integration.timestamp('2026-10-17T08:21:16Z')
        self.report_time = integration.timestamp('2026-10-17T08:21:20Z')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.PIPE,
                                       text=True).strip()

    def proof(self, request=None, receipt=None):
        return integration.fresh_bot_receipt(self.root, self.request if request is None else request,
                                             self.receipt if receipt is None else receipt,
                                             self.head, 10, self.head_time, self.report_time)

    def test_observed_v1_completion_binds_real_git_prefix_and_full_head(self):
        original = self.receipt['body']
        for suffix in ['Nice work!', 'Delightful!', 'Swish!', 'Excellent progress!',
                       '[P1] A correctness issue still needs a disposition.']:
            with self.subTest(suffix=suffix):
                self.receipt['body'] = original.replace('Nice work!', suffix)
                self.assertTrue(self.proof())
        self.receipt['body'] = original.replace(' Nice work!', '')
        self.assertTrue(self.proof())
        self.receipt['body'] = self.receipt['body'].replace(self.head[:10], self.head)
        self.assertTrue(self.proof())
        self.receipt['body'] = self.receipt['body'].split('\n\n<details>')[0]
        self.assertTrue(self.proof())

    def test_request_requires_owner_same_pr_exactly_one_full_head_and_command(self):
        for changes in [dict(user={'login': 'outsider'}), dict(issue_url=self.request['issue_url'] + '1'),
                        dict(updated_at='2026-10-17T08:21:18Z'),
                        dict(body='Please review ' + self.head),
                        dict(body='@codex review ' + self.head[:10]),
                        dict(body='@codex review ' + 'f' * 40),
                        dict(body=self.request['body'] + '\nTarget ' + 'f' * 40),
                        dict(body=self.request['body'] + '\n' + self.head),
                        dict(body='@codex address feedback ' + self.head),
                        dict(created_at=None, updated_at=None)]:
            with self.subTest(changes=changes):
                self.assertFalse(self.proof(request=dict(self.request, **changes)))

    def test_receipt_requires_bot_app_same_pr_canonical_id_and_no_edits(self):
        for changes in [dict(user={'login': 'outsider', 'type': 'Bot'}),
                        dict(user={'login': BOT, 'type': 'User'}),
                        dict(performed_via_github_app={'slug': 'untrusted', 'id': 1144995}),
                        dict(performed_via_github_app={'slug': 'chatgpt-codex-connector', 'id': 1}),
                        dict(performed_via_github_app=None),
                        dict(issue_url=self.receipt['issue_url'] + '1'),
                        dict(updated_at='2026-10-17T08:21:20Z'),
                        dict(html_url='https://github.com/clemarc/fava/pull/10'),
                        dict(id=True), dict(id=0), dict(id=127),
                        dict(created_at=None, updated_at=None)]:
            with self.subTest(changes=changes):
                self.assertFalse(self.proof(receipt=dict(self.receipt, **changes)))

    def test_only_exact_stable_completed_versioned_verdict_is_proof(self):
        body = self.receipt['body']
        for invalid in [body.replace('v1', 'v2'), body.replace('<!-- codex-review-receipt:v1 -->\n\n', ''),
                        body.replace("Didn't find any major issues. Nice work!", 'Review requested.'),
                        body.replace("Didn't find any major issues. Nice work!", 'Review is still pending.'),
                        body.replace("Didn't find any major issues. Nice work!", 'Found issues: [P1] fix this.'),
                        body.replace("Didn't find any major issues.", "Didn't finish reviewing."),
                        body.replace('Nice work!', 'A closing phrase\nA separate line'),
                        body.replace('Nice work!', 'A closing phrase\rA separate line'),
                        body.replace('Nice work!', 'A closing phrase\r\nA separate line'),
                        body.replace('**Reviewed commit:**', '**Reviewing commit:**'),
                        body.replace(self.head[:10], self.head[:9]),
                        body.replace(self.head[:10], 'f' * 10),
                        body + '\nAdditional top-level findings: [P1] broken',
                        body + '\n<!-- codex-review-receipt:v1 -->',
                        body.replace('\n\n<details>', '\n\n**Reviewed commit:** `' + self.head[:10] + '`\n\n<details>'),
                        '👍', 'Code review in progress', '', None]:
            with self.subTest(body=invalid):
                self.assertFalse(self.proof(receipt=dict(self.receipt, body=invalid)))

    def test_strict_head_request_receipt_report_chronology(self):
        for created in ['2026-10-17T08:21:16Z', '2026-10-17T08:21:19Z',
                        '2026-10-17T08:21:20Z', '2026-10-17T08:21:17', 'not a date']:
            with self.subTest(request_at=created):
                self.assertFalse(self.proof(request=dict(self.request, created_at=created, updated_at=created)))
        for created in ['2026-10-17T08:21:16Z', '2026-10-17T08:21:17Z',
                        '2026-10-17T08:21:20Z', '2026-10-17T08:21:21Z',
                        '2026-10-17T08:21:19', 'not a date']:
            with self.subTest(receipt_at=created):
                self.assertFalse(self.proof(receipt=dict(self.receipt, created_at=created, updated_at=created)))

    def test_unknown_or_ambiguous_git_object_prefix_is_not_proof(self):
        for objects in ['', self.head + '\n' + 'f' * 40 + '\n', 'f' * 40 + '\n']:
            with self.subTest(objects=objects), patch.object(sdd, 'git', return_value=objects) as git:
                self.assertFalse(self.proof())
                git.assert_called_once_with(self.root, 'rev-parse', '--disambiguate=' + self.head[:10])
        with patch.object(sdd, 'git', side_effect=subprocess.CalledProcessError(128, ['git'])):
            self.assertFalse(self.proof())


class ReceiptAssessmentTests(unittest.TestCase):
    """Reuse signed-history helpers without inheriting unrelated test methods."""
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
        self.case.bot = []
        self.request = request(self.case.head, self.case.at(self.case.clock + 1))
        self.receipt = receipt(self.case.head, self.case.at(self.case.clock + 3))
        self.case.report.update(codex_request_comment=125, codex_receipt_comment=126)
        self.case.review['findings'] = [dict(url=self.receipt['html_url'], rationale='Positive completion receipt inspected',
                                            evidence=[self.receipt['html_url']], disposition='not-actionable',
                                            head=self.case.head, target=self.case.target)]
        self.reactions = []
        self.issue_comments = []
        self.independent_comments = {}
        original = self.case.api

        def api(*args):
            endpoint = args[-1]
            for ident, comment in self.independent_comments.items():
                if endpoint.endswith(f'/comments/{ident}'):
                    return comment
            if endpoint.endswith('/issues/10/comments?per_page=100'):
                return [self.issue_comments]
            if endpoint.endswith('/comments/125/reactions'):
                return self.reactions
            if endpoint.endswith('/comments/125'):
                return self.request
            if endpoint.endswith('/comments/126'):
                return self.receipt
            return original(*args)
        self.case.api = api

    def retain_independent_report(self, ident, seconds):
        url = f'https://github.com/clemarc/fava/pull/10#issuecomment-{ident}'
        self.independent_comments[ident] = dict(self.case.review_comment, id=ident,
                                                html_url=url, created_at=self.case.at(seconds),
                                                updated_at=self.case.at(seconds),
                                                body=json.dumps(self.case.review))
        self.case.report.update(independent_review_comment=ident, independent_review_url=url)

    def assert_prelisted_finding_requires_later_independent_report(self):
        published_clock = self.case.clock
        self.case.complete()
        for offset in [2, 3, 4]:
            with self.subTest(independent_offset=offset):
                # Each alternative retains a separate immutable JSON comment.
                # Its prelisted URL cannot establish inspection of future content.
                self.retain_independent_report(130 + offset, published_clock + offset)
                for errors in [self.case.assess(), self.case.reconcile_completion()]:
                    if offset <= 3:
                        self.assertTrue(any('findings_disposed' in e for e in errors), errors)
                    else:
                        self.assertEqual(errors, [])

    def test_prelisted_receipt_url_requires_strictly_later_independent_report(self):
        self.assert_prelisted_finding_requires_later_independent_report()

    def test_prelisted_inline_issue_and_review_findings_require_later_report_for_each_proof(self):
        self.case.report.pop('codex_receipt_comment')
        published_clock = self.case.clock
        event_time = self.case.at(published_clock + 3)
        self.case.complete()
        for proof in ['review', 'reaction']:
            for kind in ['inline', 'issue', 'review']:
                with self.subTest(proof=proof, kind=kind):
                    self.case.bot = []
                    self.case.comments = []
                    self.issue_comments = []
                    self.reactions = []
                    if proof == 'review':
                        self.case.bot = [dict(user={'login': BOT}, commit_id=self.case.head,
                                              state='COMMENTED', submitted_at=event_time, body='',
                                              html_url='https://github.com/clemarc/fava/pull/10#pullrequestreview-1')]
                    else:
                        self.reactions = [dict(content='+1', user={'login': BOT}, created_at=event_time)]
                    url = 'https://github.com/clemarc/fava/pull/10#' + kind + '-finding'
                    body = '[P1] Synthetic correctness finding requiring independent inspection.'
                    if kind == 'review':
                        self.case.bot.append(dict(user={'login': 'independent-finding-reviewer'}, commit_id=self.case.head,
                                                  state='CHANGES_REQUESTED', submitted_at=event_time,
                                                  body=body, html_url=url))
                    else:
                        comment = dict(user={'login': BOT}, created_at=event_time, html_url=url, body=body)
                        if kind == 'inline':
                            self.case.comments = [comment]
                        else:
                            self.issue_comments = [comment]
                    self.case.review['findings'] = [dict(url=url, head=self.case.head, target=self.case.target,
                                                        disposition='not-actionable', rationale='Independent inspection '
                                                        'found this synthetic finding concerns deferred scope.',
                                                        evidence=[url])]
                    for offset in [2, 3, 4]:
                        self.retain_independent_report(140 + offset, published_clock + offset)
                        for errors in [self.case.assess(), self.case.reconcile_completion()]:
                            if offset <= 3:
                                self.assertTrue(any('findings_disposed' in e for e in errors), errors)
                            else:
                                self.assertEqual(errors, [])

    def assert_actual_finding_cutoff_boundary(self, retained):
        published_clock = self.case.clock
        receipt_dispositions = copy.deepcopy(self.case.review['findings'])
        if retained:
            self.case.complete()
        cutoff = integration.timestamp(self.case.pr['merged_at'] if retained else self.case.cutoff)
        for proof_index, proof in enumerate(['receipt', 'review', 'reaction']):
            for kind_index, kind in enumerate(['inline', 'issue', 'review']):
                for delta in [-1, 0, 1]:
                    with self.subTest(retained=retained, proof=proof, kind=kind, cutoff_delta=delta):
                        self.case.bot = []
                        self.reactions = []
                        self.case.comments = []
                        self.issue_comments = []
                        self.case.report.pop('codex_receipt_comment', None)
                        if proof == 'receipt':
                            self.case.report['codex_receipt_comment'] = 126
                        elif proof == 'review':
                            self.case.bot = [dict(user={'login': BOT}, commit_id=self.case.head,
                                                  state='COMMENTED', submitted_at=self.case.at(published_clock + 3),
                                                  body='', html_url='https://github.com/clemarc/fava/pull/10#pullrequestreview-1')]
                        else:
                            self.reactions = [dict(content='+1', user={'login': BOT},
                                                   created_at=self.case.at(published_clock + 3))]
                        event_time = (cutoff + timedelta(seconds=delta)).isoformat()
                        url = f'https://github.com/clemarc/fava/pull/10#{proof}-{kind}-{delta}-finding'
                        body = '[P1] Synthetic finding at the integration cutoff boundary.'
                        if kind == 'review':
                            self.case.bot.append(dict(user={'login': 'synthetic-finding-reviewer'}, commit_id=self.case.head,
                                                      state='CHANGES_REQUESTED', submitted_at=event_time,
                                                      body=body, html_url=url))
                        else:
                            comment = dict(user={'login': BOT}, created_at=event_time, html_url=url, body=body)
                            if kind == 'inline':
                                self.case.comments = [comment]
                            else:
                                self.issue_comments = [comment]
                        self.case.review['findings'] = copy.deepcopy(receipt_dispositions) if proof == 'receipt' else []
                        self.case.review['findings'].append(dict(url=url, head=self.case.head, target=self.case.target,
                                                                disposition='not-actionable', rationale='Prelisted synthetic '
                                                                'finding URL cannot establish prior inspection.',
                                                                evidence=[url]))
                        ident = 200 + proof_index * 9 + kind_index * 3 + delta + 1
                        self.retain_independent_report(ident, published_clock + 4)
                        errors = self.case.reconcile_completion() if retained else self.case.assess()
                        if delta <= 0:
                            self.assertTrue(any('findings_disposed' in e for e in errors), errors)
                        else:
                            self.assertEqual(errors, [])

    def test_direct_actual_findings_include_cutoff_second_for_every_proof(self):
        self.assert_actual_finding_cutoff_boundary(retained=False)

    def test_retained_actual_findings_include_merge_second_but_ignore_later_events(self):
        self.assert_actual_finding_cutoff_boundary(retained=True)

    def test_full_signed_assessment_accepts_receipt_and_reconciles_retained_history(self):
        self.assertEqual(self.case.assess(), [])
        self.case.complete()
        self.assertEqual(self.case.reconcile_completion(), [])

    def test_swish_receipt_proves_current_and_retained_completion(self):
        self.receipt['body'] = self.receipt['body'].replace('Nice work!', 'Swish!')
        self.assertEqual(self.case.assess(), [])
        self.case.complete()
        self.assertEqual(self.case.reconcile_completion(), [])

    def test_novel_closing_phrase_proves_current_and_retained_completion(self):
        self.receipt['body'] = self.receipt['body'].replace('Nice work!', 'Excellent progress!')
        self.assertEqual(self.case.assess(), [])
        self.case.complete()
        self.assertEqual(self.case.reconcile_completion(), [])

    def test_receipt_suffix_or_body_findings_require_current_independent_disposition(self):
        original = self.receipt['body']
        for body in [original.replace('Nice work!', '[P1] A correctness issue requires a fix.'),
                     original.replace('<br/>', '<br/>\n\n[P1] A correctness issue requires a fix.')]:
            with self.subTest(body=body):
                self.receipt['body'] = body
                self.case.review['findings'] = []
                errors = self.case.assess()
                self.assertTrue(any('findings_disposed' in e for e in errors), errors)
                self.assertFalse(any('pending/stale' in e for e in errors), errors)
                finding = dict(url=self.receipt['html_url'], head=self.case.head, target=self.case.target,
                               disposition='not-actionable', rationale='Independent inspection found this synthetic '
                               'finding refers to deferred behavior, not a contract violation.',
                               evidence=[self.receipt['html_url']])
                self.case.review['findings'] = [dict(finding, head='f' * 40)]
                self.assertTrue(any('findings_disposed' in e for e in self.case.assess()))
                self.case.review['findings'] = [finding]
                self.assertEqual(self.case.assess(), [])

    def test_root_reaction_summary_or_report_boolean_cannot_replace_receipt(self):
        self.case.report.pop('codex_receipt_comment')
        self.case.report.update(codex_review_complete=True, codex_review_head=self.case.head)
        self.case.view['reactions'] = {'+1': 1}
        self.assertTrue(any('pending/stale' in e for e in self.case.assess()))
        self.case.report['codex_receipt_comment'] = 126
        self.receipt['updated_at'] = self.case.at(self.case.clock + 4)
        self.assertTrue(any('pending/stale' in e for e in self.case.assess()))

    def test_receipt_never_bypasses_pending_native_or_finding_gates(self):
        self.assertEqual(self.case.assess(), [])
        original = copy.deepcopy(self.case.checks)
        self.case.checks[0].update(status='in_progress', conclusion=None, completed_at=None)
        self.assertTrue(any('sdd-quality' in e for e in self.case.assess()))
        self.case.checks = original
        self.case.review['native']['ios-build-test / ios-build-test (iPad)']['tests'] = 0
        self.assertTrue(any('nonzero simulator' in e for e in self.case.assess()))
        self.case.review['native']['ios-build-test / ios-build-test (iPad)']['tests'] = 41
        self.case.comments = [dict(html_url='https://github.com/clemarc/fava/pull/10#discussion_r1',
                                   body='[P1] actual unresolved correctness finding',
                                   created_at=self.case.at(self.case.clock + 3))]
        self.assertTrue(any('findings_disposed' in e for e in self.case.assess()))
        self.case.comments = []
        self.issue_comments = [dict(html_url='https://github.com/clemarc/fava/pull/10#issuecomment-127',
                                    user={'login': BOT}, body='[P1] separate issue-comment finding',
                                    created_at=self.case.at(self.case.clock + 3))]
        self.assertTrue(any('findings_disposed' in e for e in self.case.assess()))
        self.issue_comments = []
        self.case.review['findings'] = []
        self.assertTrue(any('findings_disposed' in e for e in self.case.assess()))

    def test_receipt_and_request_fail_closed_in_complete_assessment(self):
        for which, changes in [('request', dict(body='@codex review ' + self.case.head + ' ' + 'f' * 40)),
                               ('request', dict(user={'login': 'outsider'})),
                               ('receipt', dict(user={'login': 'outsider', 'type': 'Bot'})),
                               ('receipt', dict(issue_url='https://api.github.com/repos/clemarc/fava/issues/11')),
                               ('receipt', dict(id=127)),
                               ('receipt', dict(created_at=self.case.report_comment['created_at'],
                                                updated_at=self.case.report_comment['created_at']))]:
            with self.subTest(which=which, changes=changes):
                original = getattr(self, which)
                setattr(self, which, dict(original, **changes))
                self.assertTrue(any('pending/stale' in e for e in self.case.assess()))
                setattr(self, which, original)

    def assert_unresolved_issue_finding_blocks_actual_proof(self):
        self.case.report.pop('codex_receipt_comment')
        self.case.review['findings'] = []
        self.assertEqual(self.case.assess(), [])
        self.issue_comments = [dict(html_url='https://github.com/clemarc/fava/pull/10#issuecomment-127',
                                    user={'login': BOT}, body='[P1] actual issue-comment correctness finding',
                                    created_at=self.case.at(self.case.clock + 3))]
        errors = self.case.assess()
        self.assertTrue(any('findings_disposed' in e for e in errors), errors)
        self.assertFalse(any('pending/stale' in e for e in errors), errors)
        self.case.complete()
        self.assertTrue(any('findings_disposed' in e for e in self.case.reconcile_completion()))

    def test_review_proof_cannot_hide_issue_findings_by_omitting_receipt_id(self):
        self.case.bot = [dict(user={'login': BOT}, commit_id=self.case.head, state='COMMENTED',
                              submitted_at=self.case.at(self.case.clock + 3), body='',
                              html_url='https://github.com/clemarc/fava/pull/10#pullrequestreview-1')]
        self.assert_unresolved_issue_finding_blocks_actual_proof()

    def test_reaction_proof_cannot_hide_issue_findings_by_omitting_receipt_id(self):
        self.reactions = [dict(content='+1', user={'login': BOT},
                               created_at=self.case.at(self.case.clock + 3))]
        self.assert_unresolved_issue_finding_blocks_actual_proof()


if __name__ == '__main__':
    unittest.main()

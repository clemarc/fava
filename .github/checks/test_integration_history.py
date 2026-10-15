"""Complete signed task lifecycle with synthetic GitHub evidence; no credentials."""
import copy
from datetime import datetime, timedelta, timezone
import json
import unittest
from unittest.mock import patch

import test_milestones as fixtures
from test_milestones import TASKS, integration, milestone, ledger, sdd, signatures


class RetainedGateTests(fixtures.SignedLifecycleTests):
    # Inherit real signed planning/promotion fixtures as well as their helpers.
    def git(self, *args):
        if args[0] in {'commit', 'merge'}:
            self.clock += 60
            self.env.update(GIT_AUTHOR_DATE=self.at(self.clock), GIT_COMMITTER_DATE=self.at(self.clock))
        result = super().git(*args)
        if args[0] == 'init':
            super().git('config', 'commit.gpgsign', 'true')
        return result

    @staticmethod
    def at(seconds):
        return (datetime(2020, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)).isoformat()

    def setUp(self):
        self.clock = 0
        self.env = dict(type(self).env)
        self.reviewed_tasks = TASKS.replace(' (depends on T002)', '')
        super().setUp()

    def put(self, path, text):
        super().put(path, text)
        if path == '.specify/memory/constitution.md':
            super().put('Fava.xcodeproj/project.pbxproj', '// synthetic classification marker only')

    def start_task(self):
        self.git('branch', 'task/r3.5/t003', self.source)
        self.git('switch', '-c', 'target', self.source + '^')
        self.opened = self.at(self.clock + 1)
        self.data['tasks']['T003'].update(state='review', correction_cycles=0)
        self.data['task_prs'] = {'10': dict(branch='task/r3.5/t003', tasks=['T003'], correction_cycles=0, heads=[self.source])}
        self.put(self.feature + '/execution.json', json.dumps(self.data))
        self.target = self.commit('planning')
        self.import_target()

    def import_target(self):
        self.git('switch', 'task/r3.5/t003')
        self.git('merge', '--no-ff', '-S', '-m', 'import\n\nSDD-Type: planning', 'target')
        self.head = self.git('rev-parse', 'HEAD')

    def reserve(self):
        self.git('switch', 'target')
        rec = self.data['task_prs']['10']
        rec['correction_cycles'] += 1
        rec['heads'].append(self.head)
        self.data['tasks']['T003']['correction_cycles'] = rec['correction_cycles']
        self.put(self.feature + '/execution.json', json.dumps(self.data))
        self.target = self.commit('planning')

    def fix(self):
        self.put(self.source_path, '// synthetic correction ' + str(self.clock))
        self.git('add', '.')
        kind = '\nSDD-Type: tooling' if self.source_path.startswith(('docs/', 'tools/')) else ''
        self.git('commit', '-qm', f'fix: fixture\n\nSpec: {self.feature}\nTask: T003\nImplements: FR-001 FR-002' + kind)
        self.head = self.git('rev-parse', 'HEAD')

    def progress(self):
        return ledger.task_publication_progress(self.root, self.target, self.head, self.feature + '/execution.json', 10, self.opened, sdd.git)

    def evidence(self):
        now = self.clock
        names = ['sdd-quality', 'tooling-validation', 'ci-applicability', 'ci-required',
                 'ios-build-test / ios-build-test (iPhone)', 'ios-build-test / ios-build-test (iPad)']
        self.checks = [dict(id=i + 1, name=name, head_sha=self.head, app={'slug': 'github-actions'},
                            started_at=self.at(now + 1), completed_at=self.at(now + 2),
                            status='completed', conclusion='success', details_url=f'https://github.com/clemarc/fava/actions/runs/1/job/{i}')
                       for i, name in enumerate(names)]
        self.report = dict(validated_head=self.head, validated_target=self.target, tasks=['T003'],
                           semantic_drift=True, findings_disposed=True, check_run_ids=[r['id'] for r in self.checks],
                           independent_review_comment=124,
                           independent_review_url='https://github.com/clemarc/fava/pull/10#issuecomment-124')
        self.review = dict(head=self.head, target=self.target, worker='worker', reviewer='independent',
                           semantic_drift=True, findings_disposed=True, findings=[],
                           native={c['name']: dict(build_succeeded=True, tests=41, job_url=c['details_url']) for c in self.checks[-2:]})
        def comment(ident, seconds):
            return dict(issue_url='https://api.github.com/repos/clemarc/fava/issues/10', user={'login': 'clemarc'},
                        html_url=f'https://github.com/clemarc/fava/pull/10#issuecomment-{ident}',
                        created_at=self.at(seconds), updated_at=self.at(seconds))
        self.report_comment = comment(123, now + 5)
        self.review_comment = comment(124, now + 4)
        self.bot = [dict(user={'login': 'chatgpt-codex-connector[bot]'}, commit_id=self.head,
                         state='COMMENTED', submitted_at=self.at(now + 3), body='', html_url='https://github.com/review/1')]
        self.comments = []
        self.pr = dict(number=10, created_at=self.opened, head={'sha':self.head, 'ref':'task/r3.5/t003'},
                       base={'ref':'milestone/r3.5'}, merged_at=None)
        self.context = dict(id='R3.5', feature=self.feature, ledger=self.feature + '/execution.json',
                            task_branch_prefix='task/r3.5/', checkpoint_branch_prefix='checkpoint/r3.5/',
                            target_sha=self.target, main_sha=self.baseline, milestone_branch='milestone/r3.5',
                            execution=copy.deepcopy(self.data), preparation_approval={'sha':self.planning})
        self.view = dict(number=10, state='OPEN', isDraft=False, headRefName='task/r3.5/t003',
                         headRefOid=self.head, baseRefName='milestone/r3.5', baseRefOid=self.target)
        self.cutoff = self.at(now + 6)

    def api(self, *args):
        endpoint = args[-1]
        if '/rules/branches/' in endpoint:
            return [dict(type=t, ruleset_id=1, ruleset_source_type='Repository', ruleset_source='clemarc/fava')
                    for t in ['required_signatures', 'non_fast_forward', 'deletion']] + [
                dict(type='pull_request', parameters={'required_review_thread_resolution': True}),
                dict(type='required_status_checks', parameters=dict(strict_required_status_checks_policy=True,
                     required_status_checks=[{'context':'ci-required'}]))]
        if '/rulesets/' in endpoint:
            return getattr(self, 'protection', dict(enforcement='active', bypass_actors=[],
                           created_at='2019-01-01T00:00:00Z', updated_at='2019-01-01T00:00:00Z',
                           rules=[{'type':t} for t in ['required_signatures', 'non_fast_forward', 'deletion']]))
        if '/check-runs?' in endpoint: return [{'check_runs':self.checks}]
        if '/commits/' in endpoint:
            valid = signatures.verify(self.root, endpoint.rsplit('/', 1)[-1])
            return {'commit': {'verification': {'verified':valid, 'reason':'valid' if valid else 'unsigned'}}}
        if endpoint.endswith('/pulls/10'): return self.pr
        if '/pulls/10/comments?' in endpoint: return [self.comments]
        if '/pulls/10/reviews?' in endpoint: return [self.bot]
        if endpoint.endswith('/comments/123'): return dict(self.report_comment, body=json.dumps(self.report))
        if endpoint.endswith('/comments/321'): return self.authorization
        if endpoint.endswith('/comments/322'): return self.later_authorization
        if endpoint.endswith('/comments/124'): return dict(self.review_comment, body=json.dumps(self.review))
        raise AssertionError('unexpected API ' + str(args))

    def assess(self):
        with patch.object(integration, 'github', side_effect=self.api), patch.multiple(signatures,
                KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
            try:
                return integration.assess_revision(self.root, self.context, self.view, 123, self.cutoff)[1]
            except (ValueError, KeyError, TypeError) as error:
                return [str(error)]

    def complete(self):
        self.git('switch', 'target')
        kind = '\nSDD-Type: tooling' if self.source_path.startswith(('docs/', 'tools/')) else ''
        self.git('merge', '--no-ff', '-S', '-m', f'integrate\n\nSpec: {self.feature}\nTask: T003\nImplements: FR-001 FR-002' + kind, 'task/r3.5/t003')
        self.merge = self.git('rev-parse', 'HEAD')
        self.pr.update(merged_at=self.at(self.clock), merge_commit_sha=self.merge)
        self.record = dict(state='integrated', correction_cycles=self.data['tasks']['T003']['correction_cycles'],
                           merge_sha=self.merge, pr='https://github.com/clemarc/fava/pull/10',
                           integration_comment=123, evidence=[self.report_comment['html_url']])

    def reconcile_completion(self, target=None):
        with patch.object(milestone, 'github', side_effect=self.api), patch.object(integration, 'github', side_effect=self.api), \
             patch.object(milestone, 'merged_pr', return_value=self.record['pr']), \
             patch.object(integration, 'inspect', side_effect=AssertionError('resolver recursion')), \
             patch.multiple(signatures, KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
            return milestone.integrated_task_errors(self.root, self.feature, 'milestone/r3.5', 'T003', self.record, target or self.merge)

    def test_complete_registration_import_reservation_integration_checkpoint_resume(self):
        self.start_task()
        self.assertEqual(self.progress()['completed_corrections'], 0)
        self.reserve()
        self.assertTrue(self.progress()['pending_reservation'])  # Crash before import.
        self.import_target()
        self.assertTrue(self.progress()['pending_reservation'])  # Crash after import.
        # A further automatic target import does not consume the reservation.
        self.git('switch', 'target'); self.put(self.feature + '/decision-log.md', 'DEC-001: fixture')
        self.target = self.commit('planning'); self.import_target()
        self.assertTrue(self.progress()['pending_reservation'])
        self.fix()
        self.assertEqual({k:v for k,v in self.progress().items() if k != 'reservations'},
                         dict(correction_cycles=1, completed_corrections=1, pending_reservation=False))
        self.evidence()
        self.assertEqual(self.assess(), [])
        self.complete()
        self.assertEqual(self.reconcile_completion(), [])
        self.data['tasks']['T003'] = self.record
        self.put(self.feature + '/execution.json', json.dumps(self.data))
        self.put(self.feature + '/tasks.md', self.reviewed_tasks.replace('- [ ] T003', '- [X] T003'))
        checkpoint = self.commit('planning')
        self.assertEqual(self.reconcile_completion(checkpoint), [])
        self.assertEqual(ledger.transition_errors(self.root, checkpoint, self.feature + '/execution.json', sdd.git), [])

    def test_documentation_and_tooling_tasks_pass_full_completion(self):
        for path in ['docs/note.md', 'tools/check.py']:
            self.source_path = path
            self.setUp(); self.start_task(); self.evidence()
            self.assertEqual(self.assess(), [])
            self.complete()
            self.assertEqual(self.reconcile_completion(), [])

    def test_missing_edited_unauthorized_late_or_identity_only_reports_fail(self):
        self.start_task(); self.evidence(); self.complete()
        self.assertEqual(self.reconcile_completion(), [])
        for which in ['report_comment', 'review_comment']:
            original = copy.deepcopy(getattr(self, which))
            for changes in [dict(user={'login':'outsider'}), dict(updated_at=self.at(self.clock + 1)),
                            dict(created_at=self.at(self.clock), updated_at=self.at(self.clock)),
                            dict(created_at=None, updated_at=None)]:
                setattr(self, which, dict(original, **changes))
                self.assertTrue(self.reconcile_completion())
            setattr(self, which, original)
        original = self.report
        self.report = {k:original[k] for k in ['validated_head', 'validated_target', 'tasks']}
        self.assertTrue(self.reconcile_completion())
        self.report = original
        self.review['semantic_drift'] = False
        self.assertTrue(self.reconcile_completion())

    def test_failed_pending_late_ci_and_later_reruns(self):
        self.start_task(); self.evidence(); self.complete()
        good = copy.deepcopy(self.checks)
        for changes in [dict(conclusion='failure'), dict(status='in_progress', completed_at=None),
                        dict(completed_at=self.pr['merged_at']), dict(head_sha='f'*40),
                        dict(app={'slug':'untrusted'})]:
            self.checks = copy.deepcopy(good); self.checks[0].update(changes)
            self.assertTrue(self.reconcile_completion())
        self.checks = copy.deepcopy(good)
        for status in ['success', 'failure', None]:
            self.checks.append(dict(good[0], id=77, started_at=self.at(self.clock + 1),
                                    completed_at=self.at(self.clock + 2), conclusion=status))
            self.assertEqual(self.reconcile_completion(), [])
            self.checks.pop()
        # A rerun started before merge invalidates the earlier success, even if
        # it only completes after merge. A later success cannot repair it.
        self.checks.append(dict(good[0], id=77, started_at=self.at(self.clock - 1), completed_at=self.at(self.clock + 2)))
        self.assertTrue(self.reconcile_completion())

    def test_reviews_findings_native_and_signed_history_are_actual_gates(self):
        self.start_task(); self.evidence(); self.complete()
        saved = copy.deepcopy(self.bot)
        self.bot[0]['submitted_at'] = self.pr['merged_at']
        self.assertTrue(self.reconcile_completion())
        self.bot = saved
        self.comments = [dict(html_url='https://github.com/finding/1', body='P1', created_at=self.report_comment['created_at'])]
        self.assertTrue(self.reconcile_completion())
        self.comments = []
        self.review['native']['ios-build-test / ios-build-test (iPad)']['tests'] = 0
        self.assertTrue(self.reconcile_completion())

    def test_unreserved_skipped_duplicate_or_rewritten_publications_fail(self):
        self.start_task(); self.fix()
        with self.assertRaisesRegex(ValueError, 'unreserved'): self.progress()
        self.reserve()  # This cannot retroactively authorize the preceding fix.
        with self.assertRaises(ValueError): self.progress()

    def test_merge_cannot_discard_reviewed_task_tree(self):
        self.start_task(); self.evidence(); self.complete()
        self.git('rm', self.source_path)
        self.git('commit', '--amend', '-S', '--no-edit')
        changed = self.git('rev-parse', 'HEAD')
        self.assertTrue(ledger.task_merge_errors(self.root, self.feature, 'T003', dict(merge_sha=changed), changed, sdd.git))

    def test_late_or_edited_extra_cycle_authorization_fails(self):
        record = {'tasks': {'T003': {'owner_extra_cycles': {'comment_id':321}}}}
        authorization = dict(type='fava-correction-authorization', milestone='R3.5', tasks=['T003'], max_cycles=4)
        comment = dict(issue_url='https://api.github.com/repos/clemarc/fava/issues/10', user={'login':'clemarc'},
                       created_at=self.at(10), updated_at=self.at(10), body=json.dumps(authorization))
        with patch.object(integration, 'github', return_value=comment):
            self.assertEqual(integration.verified_owner_limits(record, {'T003'}, 10, 'R3.5', integration.timestamp(self.at(20))), {'T003':4})
            self.assertEqual(integration.verified_owner_limits(record, {'T003'}, 10, 'R3.5', integration.timestamp(self.at(10))), {})
            comment['updated_at'] = self.at(15)
            self.assertEqual(integration.verified_owner_limits(record, {'T003'}, 10, 'R3.5', integration.timestamp(self.at(20))), {})

    def test_two_successive_corrections_and_resolver_resume(self):
        self.start_task()
        for count in (1, 2):
            self.reserve(); self.import_target()
            self.assertTrue(self.progress()['pending_reservation'])
            self.fix()
            self.assertEqual(self.progress()['completed_corrections'], count)
        self.evidence()
        self.assertEqual(self.assess(), [])
        result = dict(self.context, prs=[dict(number=10, state='open', head='task/r3.5/t003', sha=self.head)])
        with patch.object(milestone, 'github', side_effect=self.api), patch.multiple(signatures,
                KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
            resumed = milestone.task_progress(self.root, result)['10']
            self.assertEqual(resumed['state'], 'published')
            self.assertEqual(resumed['correction_cycles'], 2)

    def test_successful_retry_before_report_preserves_failed_attempt(self):
        self.start_task(); self.evidence()
        self.checks.append(dict(self.checks[0], id=99, started_at=self.at(self.clock),
                               completed_at=self.at(self.clock + 1), conclusion='failure'))
        self.assertEqual(self.assess(), [])
        self.complete()
        self.assertEqual(self.reconcile_completion(), [])

    def test_mixed_shared_path_history_cannot_launder_reverted_ownership(self):
        self.start_task()
        self.git('rm', self.source_path)
        self.git('commit', '-qm', f'revert own work\n\nSpec: {self.feature}\nTask: T003\nImplements: FR-001 FR-002')
        self.put(self.source_path, '// different task supplies surviving change')
        self.git('add', '.')
        self.git('commit', '-qm', f'other task\n\nSpec: {self.feature}\nTask: T002\nImplements: FR-001 FR-002')
        head = self.git('rev-parse', 'HEAD')
        rows = {r[0]:r for r in sdd.task_rows(self.reviewed_tasks.replace('FavaTests/ReadTests.swift', self.source_path))}
        commits = self.git('rev-list', f'{self.target}..{head}').splitlines()
        self.assertTrue(ledger.task_delta_errors(self.root, self.feature, {'T003'}, commits, self.target, rows, sdd.git, head))

    def test_resume_enforces_cap_before_publication_and_retains_first_reservation_time(self):
        self.start_task()
        for _ in range(3):
            self.reserve(); self.import_target(); self.fix()
        self.evidence()
        def resume():
            result = dict(self.context, execution=copy.deepcopy(self.data), target_sha=self.target,
                          prs=[dict(number=10, state='open', head='task/r3.5/t003', sha=self.head)])
            with patch.object(milestone, 'github', side_effect=self.api), patch.object(integration, 'github', side_effect=self.api), \
                 patch.multiple(signatures, KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
                return milestone.task_progress(self.root, result)['10']
        self.assertFalse(resume()['next_round_authorized'])
        self.assertEqual(resume()['maximum_cycles'], 3)
        self.data['tasks']['T003']['owner_extra_cycles'] = {'comment_id':321}
        self.authorization = dict(issue_url='https://api.github.com/repos/clemarc/fava/issues/10', user={'login':'clemarc'},
                                  created_at=self.at(self.clock + 1), updated_at=self.at(self.clock + 1),
                                  body=json.dumps(dict(type='fava-correction-authorization', milestone='R3.5', tasks=['T003'], max_cycles=4)))
        self.reserve()
        first_reservation = self.target
        self.assertEqual(resume()['state'], 'resume-reserved-fix')
        self.authorization['created_at'] = self.authorization['updated_at'] = self.at(self.clock + 1)
        with self.assertRaisesRegex(ValueError, 'budget exhausted'): resume()
        # Later metadata cannot shift the original reservation's authorization deadline.
        self.data['task_prs']['10']['note'] = 'later metadata'
        self.put(self.feature + '/execution.json', json.dumps(self.data))
        self.target = self.commit('planning')
        self.assertEqual(self.progress()['reservations'][4], first_reservation)
        with self.assertRaisesRegex(ValueError, 'budget exhausted'): resume()
        self.authorization['created_at'] = self.authorization['updated_at'] = self.at(1)
        self.assertEqual(resume()['maximum_cycles'], 4)
        # A distinct later grant extends round five without rewriting round four's proof.
        self.import_target(); self.fix()
        self.later_authorization = dict(self.authorization, created_at=self.at(self.clock + 1),
                                       updated_at=self.at(self.clock + 1),
                                       body=json.dumps(dict(type='fava-correction-authorization', milestone='R3.5', tasks=['T003'], max_cycles=5)))
        self.data['tasks']['T003']['owner_extra_cycles'] = {'comment_id':322}
        self.reserve()
        self.pr['head']['sha'] = self.head
        self.assertEqual(resume()['maximum_cycles'], 5)
        prior = copy.deepcopy(self.authorization)
        for change in ({'created_at':self.at(self.clock), 'updated_at':self.at(self.clock)},
                       {'updated_at':self.at(self.clock)}, {'body':'{}'}):
            self.authorization = dict(prior, **change)
            with self.assertRaisesRegex(ValueError, 'budget exhausted'): resume()
        self.authorization = prior
        self.assertEqual(resume()['state'], 'resume-reserved-fix')
        del self.data['tasks']['T003']['owner_extra_cycles']
        with self.assertRaisesRegex(ValueError, 'budget exhausted'): resume()

    def test_pure_import_can_retain_other_prs_multiple_valid_reservations(self):
        self.start_task()
        old = copy.deepcopy(self.data)
        self.git('switch', 'target')
        entry = dict(branch='task/r3.5/t002', tasks=['T002'], correction_cycles=0, heads=[self.source])
        self.data['task_prs']['12'] = entry
        path = self.feature + '/execution.json'
        for count in range(3):
            if count:
                entry['correction_cycles'] = count
                entry['heads'].append(self.git('rev-parse', 'HEAD'))
            self.put(path, json.dumps(self.data))
            self.target = self.commit('planning')
            self.assertEqual(ledger.transition_errors(self.root, self.target, path, sdd.git), [])
        self.import_target()
        self.assertEqual(ledger.target_import(self.root, self.head, self.target, sdd.git), (True, []))
        self.assertEqual(ledger.transition_errors(self.root, self.head, path, sdd.git), [])
        self.assertEqual(ledger.history_errors(old, self.data, publication=False), [])
        self.assertTrue(ledger.history_errors(old, self.data))  # A single publication still cannot jump.
        with patch.multiple(signatures, KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
            self.assertEqual(sdd.validate_repo(self.root, self.baseline), [])
        # A first ledger cannot hide an initial count > zero either.
        self.git('switch', '--detach', self.baseline)
        self.put(path, json.dumps(self.data))
        forged = self.commit('planning')
        self.assertTrue(ledger.transition_errors(self.root, forged, path, sdd.git))

    def test_merge_cannot_manufacture_reservations_from_invalid_origins(self):
        self.start_task()
        path = self.feature + '/execution.json'
        self.git('switch', 'target')
        entry = dict(branch='task/r3.5/t002', tasks=['T002'], correction_cycles=0,
                     spacer=list(range(20)), heads=[self.source])
        self.data['task_prs']['12'] = entry
        self.put(path, json.dumps(self.data, indent=2))
        base = self.commit('planning')
        self.git('switch', '-c', 'count-side', base)
        entry['correction_cycles'] = 1
        self.put(path, json.dumps(self.data, indent=2))
        count_side = self.commit('planning')
        self.assertTrue(ledger.transition_errors(self.root, count_side, path, sdd.git))
        self.git('switch', '-c', 'heads-side', base)
        entry['correction_cycles'] = 0
        entry['heads'].append(base)
        self.put(path, json.dumps(self.data, indent=2))
        heads_side = self.commit('planning')
        self.assertTrue(ledger.transition_errors(self.root, heads_side, path, sdd.git))
        self.git('merge', '--no-ff', '-S', '-m', 'automatic synthesis\n\nSDD-Type: planning', 'count-side')
        merge = self.git('rev-parse', 'HEAD')
        self.assertEqual(ledger.target_import(self.root, merge, count_side, sdd.git), (True, []))
        self.assertTrue(ledger.transition_errors(self.root, merge, path, sdd.git))
        with patch.multiple(signatures, KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
            self.assertTrue(sdd.validate_repo(self.root, self.baseline))
        entry.update(correction_cycles=2, heads=[self.source, base, count_side])
        self.put(path, json.dumps(self.data, indent=2)); self.git('add', '.')
        self.git('commit', '--amend', '-S', '--no-edit')
        altered = self.git('rev-parse', 'HEAD')
        self.assertTrue(ledger.target_import(self.root, altered, count_side, sdd.git)[1])
        self.assertTrue(ledger.transition_errors(self.root, altered, path, sdd.git))

    def test_initial_registration_requires_protected_signed_preopening_history(self):
        self.start_task(); self.evidence()
        self.pr['head']['sha'] = self.source
        result = dict(self.context, target_sha=self.git('rev-parse', self.source + '^'),
                      execution=dict(self.data, task_prs={}),
                      prs=[dict(number=10, state='open', head='task/r3.5/t003', sha=self.source)])
        def resume(api=None):
            with patch.object(milestone, 'github', side_effect=api or self.api), patch.multiple(signatures,
                    KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
                return milestone.task_progress(self.root, result)['10']
        self.assertEqual(resume()['state'], 'registration-required')
        good = self.api('api', 'repos/clemarc/fava/rulesets/1')
        initial_time = self.git('show', '-s', '--format=%cI', self.source)
        for changed in [dict(updated_at=initial_time), dict(created_at=self.at(self.clock), updated_at=self.at(self.clock)),
                        dict(enforcement='disabled'), dict(bypass_actors=[{'actor_id':1}]),
                        dict(updated_at=None), dict(rules=[])]:
            self.protection = dict(good, **changed)
            with self.assertRaisesRegex(ValueError, 'owner reconciliation'): resume()
        self.protection = good
        def unsigned(*args):
            if args[-1].endswith('/commits/' + self.source):
                return {'commit': {'verification': {'verified':False, 'reason':'unsigned'}}}
            return self.api(*args)
        with self.assertRaisesRegex(ValueError, 'signature'): resume(unsigned)
        self.pr['created_at'] = initial_time
        with self.assertRaisesRegex(ValueError, 'owner reconciliation'): resume()

    def test_preparation_extra_round_requires_immutable_prior_authorization(self):
        self.source_path = 'docs/note.md'; self.setUp()
        opened = self.at(self.clock + 1)
        self.data['preparation_prs'] = {'10':dict(branch='prepare/r3.5', correction_cycles=0,
                                               heads=[self.source], owner_extra_cycles={'comment_id':321})}
        path = self.feature + '/execution.json'
        self.put(path, json.dumps(self.data)); self.commit('planning')
        authorization_time = self.at(self.clock + 1)
        for count in range(1, 5):
            record = self.data['preparation_prs']['10']
            record['heads'].append(self.git('rev-parse', 'HEAD'))
            record['correction_cycles'] = count
            self.put(path, json.dumps(self.data)); self.put(self.source_path, '// artifact fix ' + str(count))
            head = self.commit('planning')
        self.authorization = dict(issue_url='https://api.github.com/repos/clemarc/fava/issues/10', user={'login':'clemarc'},
                                  created_at=authorization_time, updated_at=authorization_time,
                                  body=json.dumps(dict(type='fava-correction-authorization', phase='prepare', milestone='R3.5', max_cycles=4)))
        result = dict(id='R3.5', main_sha=self.baseline, target_sha=self.baseline, ledger=path, preparation_branch='prepare/r3.5',
                      execution=self.data, prs=[dict(number=10, head='prepare/r3.5', state='open', sha=head)])
        def api(*args):
            if args[-1].endswith('/pulls/10'): return {'created_at':opened}
            return self.api(*args)
        def resume():
            with patch.object(milestone, 'github', side_effect=api), patch.multiple(signatures,
                    KEY=self.public, FINGERPRINT=self.fingerprint, OWNER_EMAIL='fixture@example.invalid'):
                return milestone.preparation_progress(self.root, result)
        self.assertEqual(resume()['maximum_cycles'], 4)
        extra_time = self.at(self.clock)
        self.authorization['created_at'] = self.authorization['updated_at'] = extra_time
        with self.assertRaisesRegex(ValueError, 'limit exhausted'): resume()
        self.data['linear'] = {'state':'pending'}
        self.put(path, json.dumps(self.data)); result['prs'][0]['sha'] = self.commit('planning')
        with self.assertRaisesRegex(ValueError, 'limit exhausted'): resume()  # Later metadata cannot move deadline.
        self.authorization['created_at'] = authorization_time
        with self.assertRaisesRegex(ValueError, 'limit exhausted'): resume()  # Edited same-ID authorization.
        self.authorization['updated_at'] = authorization_time
        self.assertEqual(resume()['maximum_cycles'], 4)
        self.later_authorization = dict(self.authorization, created_at=self.at(self.clock + 1),
                                       updated_at=self.at(self.clock + 1),
                                       body=json.dumps(dict(type='fava-correction-authorization', phase='prepare', milestone='R3.5', max_cycles=5)))
        record = self.data['preparation_prs']['10']
        record['owner_extra_cycles'] = {'comment_id':322}
        record['heads'].append(self.git('rev-parse', 'HEAD'))
        record['correction_cycles'] = 5
        self.put(path, json.dumps(self.data)); self.put(self.source_path, '// artifact fix 5')
        result['prs'][0]['sha'] = self.commit('planning')
        self.assertEqual(resume()['maximum_cycles'], 5)
        prior = copy.deepcopy(self.authorization)
        for change in ({'created_at':extra_time, 'updated_at':extra_time},
                       {'updated_at':extra_time}, {'body':'{}'}):
            self.authorization = dict(prior, **change)
            with self.assertRaisesRegex(ValueError, 'limit exhausted'): resume()
        self.authorization = prior
        self.assertEqual(resume()['maximum_cycles'], 5)
        protection = self.api('api', 'repos/clemarc/fava/rulesets/1')
        self.protection = dict(protection, updated_at=extra_time)
        with self.assertRaisesRegex(ValueError, 'owner reconciliation'): resume()

    def test_counter_jumps_and_nonzero_initial_registration_fail(self):
        entry = dict(branch='task/r3.5/t003', tasks=['T003'], correction_cycles=0, heads=['a'*40])
        old = {'task_prs':{'10':entry}}
        self.assertEqual(ledger.history_errors({}, old), [])
        for count, heads in [(1,['a'*40]), (3,['a'*40]), (2,['a'*40,'b'*40]), (1,['b'*40,'a'*40])]:
            new = {'task_prs':{'10':dict(entry, correction_cycles=count, heads=heads)}}
            self.assertTrue(ledger.history_errors(old, new))
            self.assertTrue(ledger.history_errors({}, new))

    def test_replayed_and_fully_reverted_task_has_no_surviving_completion(self):
        self.start_task()
        self.git('switch', 'target')
        self.put(self.source_path, '// synthetic source')
        self.commit('tooling')
        target = self.git('rev-parse', 'HEAD')
        rows = {r[0]:r for r in sdd.task_rows(self.reviewed_tasks)}
        commits = self.git('rev-list', f'{target}..{self.head}').splitlines()
        self.assertTrue(ledger.task_delta_errors(self.root, self.feature, {'T003'}, commits, target, rows, sdd.git, self.head))
        self.git('switch', 'task/r3.5/t003'); self.git('rm', self.source_path)
        self.git('commit', '-qm', f'revert\n\nSpec: {self.feature}\nTask: T003\nImplements: FR-001 FR-002')
        reverted = self.git('rev-parse', 'HEAD')
        commits = self.git('rev-list', f'{self.target}..{reverted}').splitlines()
        self.assertTrue(ledger.task_delta_errors(self.root, self.feature, {'T003'}, commits, self.target, rows, sdd.git, reverted))


if __name__ == '__main__': unittest.main()

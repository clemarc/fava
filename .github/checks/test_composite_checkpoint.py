"""Inactive composite preview: atomic deltas, proof gates and no activation."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/sdd'))
import ledger

TARGET,HEAD,MERGE,OLD_HEAD=(c*40 for c in 'abcd')
FEATURE='specs/demo-01-read'
TASKS='''## Phase 2: User Story 1
- [ ] T001 [US1] Implement Fava/A.swift (FR-001)
- [ ] T002 [US1] Implement Fava/B.swift (FR-001) (depends on T001)
'''


class CompositeTests(unittest.TestCase):
    def setUp(self):
        self.context=dict(id='R3.5',feature=FEATURE,ledger=FEATURE+'/execution.json',target_sha=TARGET,
                          milestone_branch='milestone/r3.5',checkpoint_branch_prefix='checkpoint/r3.5/')
        self.before=dict(schema=1,milestone='R3.5',feature=FEATURE,milestone_branch='milestone/r3.5',
                         specification_base='e'*40,planning_revision='f'*40,state='implementing',
                         tasks={'T001':dict(state='review',correction_cycles=0),'T002':dict(state='pending',correction_cycles=0)},
                         task_prs={'10':dict(branch='task/r3.5/t001',tasks=['T001'],heads=[OLD_HEAD],correction_cycles=0)},
                         checkpoints=[])
        self.after=copy.deepcopy(self.before)
        self.after['tasks']['T001'].update(state='integrated',pr='https://github.com/clemarc/fava/pull/10',
            merge_sha=MERGE,integration_comment=123,evidence=['https://github.com/clemarc/fava/pull/10#issuecomment-123'])
        self.after['task_prs']['11']=dict(branch='task/r3.5/t002',tasks=['T002'],heads=[HEAD],correction_cycles=0)
        self.after['checkpoints']=[dict(id='C900',kind='task-completion-registration',branch='checkpoint/r3.5/c900',
            completion=dict(tasks=['T001']),registration=dict(tasks=['T002'],task_pr='https://github.com/clemarc/fava/pull/11',initial_head=HEAD))]
        self.tasks_after=TASKS.replace('[ ] T001','[X] T001')
        self.verify=Mock(return_value=[]);self.signed=Mock(return_value=True)
        self.actual_head=HEAD;self.live_target=TARGET;self.ancestry=True
        self.commit_time='2026-10-24T10:00:00Z';self.commit_verified=True
        self.history=Mock();self.commits=[HEAD];self.bad_ancestor=None
        self.pr_reads=0;self.move_successor=False
        self.approved_tasks=TASKS

    def api(self,*args):
        path=args[-1]
        if '/git/ref/' in path:return dict(object=dict(sha=self.live_target))
        if '/pulls/' in path:
            self.pr_reads+=1
            head='f'*40 if self.move_successor and self.pr_reads>1 else self.actual_head
            return dict(state='open',merged_at=None,created_at='2026-10-24T11:00:00Z',
                head=dict(sha=head,ref='task/r3.5/t002'),base=dict(ref='milestone/r3.5'),
                html_url='https://github.com/clemarc/fava/pull/11')
        return dict(commit=dict(committer=dict(date=self.commit_time),verification=dict(
            verified=self.commit_verified and not path.endswith(str(self.bad_ancestor)),reason='valid')))

    def git(self,root,*args):
        if args==('show',TARGET+':'+FEATURE+'/execution.json'):return json.dumps(self.before)
        if args==('show',TARGET+':'+FEATURE+'/tasks.md'):return TASKS
        if args==('show','f'*40+':'+FEATURE+'/tasks.md'):return self.approved_tasks
        if args[0]=='merge-base':
            if not self.ancestry:raise subprocess.CalledProcessError(1,args)
            return ''
        if args[0]=='rev-list':return '\n'.join(self.commits)
        if args[0] in {'diff','diff-tree'}:return 'Fava/B.swift'
        if args[:3]==('show','-s','--format=%P'):return TARGET
        if args[:3]==('show','-s','--format=%B'):
            return 'feat: successor\n\nSpec: '+FEATURE+'\nTask: T002\nImplements: FR-001\n'
        raise AssertionError(args)

    def candidate(self,successor=11):
        return ledger.composite_candidate(Path('/synthetic'),self.context,self.before,self.after,TASKS,
            self.tasks_after,['T001'],successor,git=self.git,api=self.api,completion_verifier=self.verify,
            signed=self.signed,history_protection=self.history)

    def invalid(self):
        result=self.candidate();self.assertFalse(result['valid_for_review']);self.assertTrue(result['errors'])
        self.assertFalse(result['accepted']);self.assertFalse(result['activation_enabled'])

    def test_valid_atomic_completion_plus_registration_remains_disabled(self):
        before,after=copy.deepcopy(self.before),copy.deepcopy(self.after)
        result=self.candidate()
        self.assertTrue(result['valid_for_review'],result['errors'])
        self.assertFalse(result['accepted']);self.assertFalse(result['activation_enabled'])
        self.assertEqual(len(result['candidate_digest']),64)
        self.assertEqual(self.before,before);self.assertEqual(self.after,after)
        self.verify.assert_called_once()

    def test_invalid_predecessor_completion_and_missing_independent_evidence(self):
        self.verify.return_value=['actual milestone integration or report missing'];self.invalid()
        self.verify.return_value=[];del self.after['tasks']['T001']['merge_sha'];self.invalid()

    def test_invalid_successor_initial_head_and_late_publication(self):
        self.actual_head='e'*40;self.invalid()
        self.actual_head=HEAD;self.commit_time='2026-10-24T12:00:00Z';self.invalid()
        self.commit_time='2026-10-24T10:00:00Z';self.commit_verified=False;self.invalid()

    def test_stale_target_fails_before_proof(self):
        self.live_target='e'*40;self.invalid();self.verify.assert_not_called()

    def test_duplicate_completion_and_registration(self):
        self.before['tasks']['T001']=copy.deepcopy(self.after['tasks']['T001']);self.invalid()
        self.setUp();self.before['task_prs']['11']=copy.deepcopy(self.after['task_prs']['11']);self.invalid()

    def test_partial_completion_or_registration_is_not_a_candidate(self):
        self.after['tasks']['T001']=copy.deepcopy(self.before['tasks']['T001']);self.invalid()
        self.setUp();del self.after['task_prs']['11'];self.invalid()
        self.setUp();self.tasks_after=TASKS;self.invalid()

    def test_interrupted_publication_and_lost_ack_never_activate_or_expose_partial_state(self):
        first=self.candidate();second=self.candidate()
        self.assertEqual(first['candidate_digest'],second['candidate_digest'])
        cases=[(dict(target=TARGET,mutation_pending=True),'reconcile_publication_before_retry'),
               (dict(target=TARGET,canonical_digest=first['base_digest'],published_digest=first['candidate_digest']),
                'reuse_existing_candidate_and_refresh_gates'),
               (dict(target=TARGET,published_digest=first['candidate_digest']),'reuse_existing_candidate_and_refresh_gates'),
               (dict(target=TARGET,canonical_digest=first['candidate_digest']),'verify_existing_composite_merge'),
               (dict(target=TARGET,canonical_digest='partial'),'blocked_partial_or_conflicting_canonical_state'),
               (dict(target=TARGET,checkpoint_result='failure'),'reconcile_failed_checkpoint_before_standalone_fallback'),
               (dict(target='f'*40),'rebuild_against_fresh_target')]
        for observation,action in cases:
            result=ledger.composite_recovery_preview(first,observation)
            self.assertFalse(result['accepted']);self.assertFalse(result['activation_enabled'])
            self.assertEqual(result['next_action'],action)

    def test_failed_or_multiple_checkpoint_delta_is_rejected(self):
        self.after['checkpoints']=[];self.invalid()
        self.setUp();self.after['checkpoints'].append(copy.deepcopy(self.after['checkpoints'][0]));self.invalid()
        self.setUp();self.after['checkpoints'][0]['registration']['initial_head']='f'*40;self.invalid()

    def test_standalone_completion_fallback_has_no_new_permission(self):
        result=self.candidate(successor=None)
        self.assertEqual(result['next_action'],'assess_standalone_completion')
        self.assertFalse(result['accepted']);self.assertFalse(result['activation_enabled'])

    def test_correction_reservations_and_counters_remain_unchanged(self):
        self.after['task_prs']['10']['correction_cycles']=1
        self.after['task_prs']['10']['heads'].append(HEAD);self.invalid()
        self.setUp();self.after['tasks']['T001']['correction_cycles']=1;self.invalid()

    def test_retained_head_and_predecessor_ancestry_enforced(self):
        self.after['task_prs']['10']['heads']=['e'*40];self.invalid()
        self.setUp();self.ancestry=False;self.invalid()

    def test_dependency_and_unrelated_delta_rejected(self):
        self.after['tasks']['T002']['state']='integrated';self.invalid()
        self.setUp();self.after['linear']=dict(state='verified');self.invalid()

    def test_intermediate_state_is_not_an_active_ledger_state(self):
        self.before['state']='INTEGRATED_PENDING_COMPLETION'
        self.assertIn('unknown milestone state',ledger.validate(self.before,FEATURE,TASKS))

    def test_history_protection_and_every_introduced_signature_required(self):
        self.history.side_effect=ValueError('history protection absent');self.invalid()
        self.history.side_effect=None;self.commits.append('e'*40);self.bad_ancestor='e'*40;self.invalid()
        self.bad_ancestor=None;self.assertTrue(self.candidate()['valid_for_review'])
        self.signed.assert_any_call(Path('/synthetic'),'e'*40)

    def test_successor_head_movement_during_validation_blocks_candidate(self):
        self.move_successor=True;self.invalid()

    def test_scope_and_dependencies_must_match_reviewed_planning_revision(self):
        self.approved_tasks=TASKS.replace('Fava/B.swift','Fava/Approved.swift');self.invalid()
        self.approved_tasks=TASKS.replace(' (depends on T001)','');self.invalid()


if __name__=='__main__':unittest.main()

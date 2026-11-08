"""Interrupted coordinator sessions never turn saved observations into approval."""
import copy
import fcntl
import hashlib
import io
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/sdd'))
import recovery
import milestone

HEAD, TARGET, MERGE, RESERVATION = (c * 40 for c in 'abcd')


def context():
    return dict(id='R3.5', feature='specs/demo-01-work', ledger='specs/demo-01-work/execution.json',
                target_sha=TARGET, milestone_branch='milestone/r3.5',
                task_branch_prefix='task/r3.5/', checkpoint_branch_prefix='checkpoint/r3.5/',
                execution=dict(tasks={'T001':dict(state='review')},task_prs={
                    '10':dict(tasks=['T001'],correction_cycles=1)}),
                task_progress={'10':dict(state='published',correction_cycles=1,reservations={1:RESERVATION})},
                branches={'refs/remotes/origin/task/r3.5/t001':HEAD})


def observation():
    return dict(pr=dict(number=10, state='open', merged=False, merge_commit_sha=None,
                        head=dict(sha=HEAD,ref='task/r3.5/t001'),base=dict(ref='milestone/r3.5')),
                checkout_head=HEAD, check_digest='checks', review_digest='reviews',
                native=dict(state='checks_only_acceptance_not_verified',jobs=[]))


def retained_fixture(context, message=None, checkpoint=False):
    feature=context['feature']
    canonical=dict(planning_revision='e'*40,specification_base='f'*40,
                   task_prs={'10':dict(tasks=['T001'])})
    if message is None:
        message=('chore: checkpoint\n\nSDD-Type: planning\n' if checkpoint else
                 f'feat: task\n\nSpec: {feature}\nTask: T001\nImplements: FR-001\n')
    def git(root,*args):
        if args[:3]==('show','-s','--format=%P'):return TARGET+' '+HEAD
        if args[:3]==('show','-s','--format=%T'):return '1'*40
        if args[:3]==('show','-s','--format=%B'):return message
        if args[:2]==('diff','--name-only'):
            return feature+'/execution.json' if checkpoint else 'Fava/A.swift'
        raise AssertionError(args)
    def read(root,ref,path):
        if path==context['ledger']:return json.dumps(canonical)
        if path.endswith('/spec.md'):return '- **FR-001**: first.\n- **FR-002**: second.\n'
        if path.endswith('/tasks.md'):
            return ('## Phase 2: User Story 1\n'
                    '- [ ] T001 [US1] Implement Fava/A.swift (FR-001)\n'
                    '- [ ] T002 [US1] Implement Fava/B.swift (FR-002)\n')
        raise AssertionError(path)
    return canonical,git,read


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.root=Path('/synthetic')
        self.context=context(); self.observation=observation()
        self.old=recovery.snapshot(self.context,self.observation,'implement',report=123)
        self.proof=dict(pr=10,merge_sha=MERGE,head=HEAD,target=TARGET,evidence_comment=123)

    def recover(self, gate=None, publication=None):
        return recovery.recover(self.root,self.context,self.old,self.observation,
                                gate=gate or Mock(return_value=self.proof),
                                publication=publication or Mock())

    def merged(self, checkpoint=False):
        self.observation['pr'].update(merged=True,state='closed',merge_commit_sha=MERGE,
            merged_at='2026-10-24T10:00:00Z',merged_by=dict(login='clemarc'))
        if checkpoint:
            self.observation['pr']['head']['ref']='checkpoint/r3.5/c016'
            self.old['branch']='checkpoint/r3.5/c016'

    def test_current_observation_only_permits_assessment(self):
        result=self.recover()
        self.assertEqual(result['next_action'],'assess_current_head')
        self.assertEqual(result['verified_evidence'],[])
        self.assertEqual(self.old['correction_count'],1)
        self.assertEqual(self.old['reservation'],RESERVATION)

    def test_publication_succeeded_acknowledgement_lost(self):
        self.old['ambiguous_mutation']=dict(kind='publication',branch='task/r3.5/t001',
            parent=TARGET,tree=MERGE,message_sha256='e'*64)
        publish=Mock(return_value=dict(state='verified_applied',action='refresh_current_evidence',commit=HEAD))
        result=self.recover(publication=publish)
        publish.assert_called_once()
        self.assertEqual(result['publication']['commit'],HEAD)
        self.assertEqual(result['next_action'],'refresh_current_evidence')

    def test_unobserved_publication_never_bypasses_canonical_blocks_or_reservations(self):
        self.old['ambiguous_mutation']=dict(kind='publication',branch='task/r3.5/t001',
            parent=TARGET,tree=MERGE,message_sha256='e'*64)
        publication=Mock(return_value=dict(state='not_observed',action='reassess_before_expected_head_publication'))
        self.context['task_progress']['10']['state']='blocked'
        result=self.recover(publication=publication)
        self.assertEqual(result['state'],'blocked'); self.assertIsNone(result['next_action'])
        self.context['task_progress']['10'].update(state='published',correction_cycles=0)
        with self.assertRaises(ValueError):self.recover(publication=publication)
        self.context['task_progress']['10'].update(correction_cycles=1,pending_reservation=True,reservations={})
        with self.assertRaises(ValueError):self.recover(publication=publication)

    def test_checkpoint_merged_before_local_update(self):
        self.merged(checkpoint=True)
        gate=Mock(return_value=self.proof)
        result=self.recover(gate=gate)
        gate.assert_called_once()
        self.assertEqual(result['next_action'],'refresh_canonical_state')
        self.assertEqual(result['last_verified_checkpoint']['merge_sha'],MERGE)

    def test_merge_intent_preserves_canonical_blocker(self):
        self.old['ambiguous_mutation']=dict(kind='merge',pr=10,head=HEAD,target=TARGET,evidence_comment=123)
        self.context['task_progress']['10']['state']='blocked'
        result=self.recover()
        self.assertEqual(result['state'],'blocked')
        self.assertIsNone(result['next_action'])
        self.assertFalse(result['mutation_resolved'])

    def test_publication_intent_must_belong_to_selected_pr(self):
        self.old['ambiguous_mutation']=dict(kind='publication',branch='task/r3.5/other',
            parent=TARGET,tree=MERGE,message_sha256='e'*64)
        publication=Mock()
        with self.assertRaisesRegex(ValueError,'another PR branch'):
            self.recover(publication=publication)
        publication.assert_not_called()

    def test_merged_publication_always_verifies_merge_and_completion(self):
        self.old['ambiguous_mutation']=dict(kind='publication',branch='task/r3.5/t001',
            parent=TARGET,tree=MERGE,message_sha256='e'*64)
        self.merged()
        publication=Mock(return_value=dict(state='verified_applied',action='refresh_current_evidence',commit=HEAD))
        gate=Mock(return_value=self.proof)
        result=self.recover(gate=gate,publication=publication)
        gate.assert_called_once_with(self.root,self.context,self.observation['pr'],123)
        self.assertEqual(result['next_action'],'prepare_standalone_completion_checkpoint')
        self.assertTrue(result['mutation_resolved'])
        with self.assertRaisesRegex(ValueError,'independent proof'):
            self.recover(gate=Mock(side_effect=ValueError('missing independent proof')),publication=publication)
        publication.return_value['commit']=TARGET
        with self.assertRaisesRegex(ValueError,'differs from merged PR head'):
            self.recover(publication=publication)

    def test_merged_unobserved_publication_survives_cli_handoff(self):
        self.old['ambiguous_mutation']=dict(kind='publication',branch='task/r3.5/t001',
            parent=TARGET,tree=MERGE,message_sha256='e'*64)
        self.merged()
        publication=Mock(return_value=dict(state='not_observed',action='reassess_before_expected_head_publication'))
        gate=Mock(return_value=self.proof)
        outcome=self.recover(gate=gate,publication=publication)
        gate.assert_called_once()
        self.assertEqual(outcome['state'],'blocked')
        self.assertIsNone(outcome['next_action'])
        self.assertFalse(outcome['mutation_resolved'])
        self.assertEqual(outcome['verified_evidence'],[self.proof])
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);prior=root/'prior.json';prior.write_text(json.dumps(self.old))
            with (patch.object(sys,'argv',['milestone.py','R3.5','--phase','implement','--root',temp,
                    '--recover',str(prior),'--handoff']),patch.object(milestone,'inspect',return_value=self.context),
                    patch.object(recovery,'live_observation',return_value=self.observation),
                    patch.object(recovery,'recover',return_value=outcome),redirect_stdout(io.StringIO())):
                with self.assertRaises(SystemExit) as stopped:milestone.main()
                self.assertEqual(stopped.exception.code,1)
            saved=json.loads((root/'artifacts/sdd-session/r3.5/snapshot.json').read_text())
            self.assertEqual(saved['ambiguous_mutation'],self.old['ambiguous_mutation'])
            self.assertEqual(saved['pending_transition'],'blocked')

    def test_reserved_correction_is_resumed_without_increment(self):
        self.context['task_progress']['10'].update(state='resume-reserved-fix',pending_reservation=True)
        result=self.recover()
        self.assertEqual(result['next_action'],'resume_existing_reserved_round')
        self.assertEqual(result['correction_count'],1)
        self.assertEqual(result['reservation'],RESERVATION)
        self.assertIn('verified_pure_target_import_before_source_publication',result['missing_requirements'])
        del self.context['task_progress']['10']['reservations'][1]
        with self.assertRaises(ValueError):self.recover()

    def test_merged_task_missing_completion_uses_retained_gates(self):
        self.merged()
        gate=Mock(return_value=self.proof)
        self.assertEqual(self.recover(gate=gate)['next_action'],'prepare_standalone_completion_checkpoint')
        gate.assert_called_once()
        with self.assertRaises(ValueError):self.recover(gate=Mock(side_effect=ValueError('missing independent proof')))
        self.context['execution']['tasks']['T001'].update(state='integrated',merge_sha=MERGE)
        self.assertEqual(self.recover()['next_action'],'refresh_canonical_state')
        self.context['execution']['task_prs']['10']['tasks'].append('T002')
        self.context['execution']['tasks']['T002']=dict(state='review')
        self.assertEqual(self.recover()['next_action'],'prepare_standalone_completion_checkpoint')

    def test_review_ci_head_target_or_checkout_changes_invalidate_snapshot(self):
        for key in ['check_digest','review_digest','checkout_head']:
            original=self.observation[key]; self.observation[key]='changed'
            result=self.recover()
            self.assertIn(key,result['stale_fields'])
            self.assertEqual(result['next_action'],'refresh_current_evidence')
            self.observation[key]=original
        self.observation['pr']['head']['sha']=MERGE
        self.context['target_sha']=RESERVATION
        self.assertEqual(set(self.recover()['stale_fields']),{'head','target'})

    def test_inline_comment_edits_and_replies_invalidate_live_review_digest(self):
        self.context['prs']=[dict(number=10,sha=HEAD,head='task/r3.5/t001')]
        inline=[dict(id=50,body='original finding',updated_at='2026-10-24T09:00:00Z')]
        def api(*args):
            path=args[-1]
            if '/git/ref/' in path:return {'object':{'sha':TARGET}}
            if 'check-runs' in path:return [{'check_runs':[]}]
            if path.endswith('/comments?per_page=100'):
                return [inline] if '/pulls/' in path else [[]]
            if '/reviews?' in path:return [[]]
            return self.observation['pr']
        with patch.object(milestone,'git',return_value=HEAD):
            before=recovery.live_observation(self.root,self.context,10,api)
            old=recovery.snapshot(self.context,before,'implement')
            inline[0].update(body='edited finding',updated_at='2026-10-24T10:00:00Z')
            after=recovery.live_observation(self.root,self.context,10,api)
            result=recovery.recover(self.root,self.context,old,after)
            self.assertIn('review_digest',result['stale_fields'])
            self.assertEqual(result['next_action'],'refresh_current_evidence')
            reply_baseline=recovery.snapshot(self.context,after,'implement')
            inline.append(dict(id=51,in_reply_to_id=50,body='new reply'))
            replied=recovery.live_observation(self.root,self.context,10,api)
            self.assertIn('review_digest',recovery.recover(self.root,self.context,reply_baseline,replied)['stale_fields'])

    def test_lost_merge_acknowledgement_requires_exact_intended_parents(self):
        self.old['ambiguous_mutation']=dict(kind='merge',pr=10,head=HEAD,target=TARGET,evidence_comment=123)
        self.assertEqual(self.recover()['next_action'],'reassess_before_guarded_merge')
        self.merged()
        self.assertEqual(self.recover()['next_action'],'prepare_standalone_completion_checkpoint')
        with self.assertRaises(ValueError):self.recover(gate=Mock(return_value=dict(self.proof,target=RESERVATION)))

    def test_wrong_identity_closed_pr_blocked_task_and_decreased_count(self):
        for field,value in [('schema_version',2),('milestone','R9'),('pr',99),('branch','other')]:
            old=self.old[field]; self.old[field]=value
            with self.assertRaises(ValueError):self.recover()
            self.old[field]=old
        self.observation['pr']['state']='closed'
        with self.assertRaises(ValueError):self.recover()
        self.observation['pr']['state']='open'
        self.context['task_progress']['10']['state']='blocked'
        self.assertEqual(self.recover()['state'],'blocked')
        self.context['task_progress']['10'].update(state='published',correction_cycles=0)
        with self.assertRaises(ValueError):self.recover()

    def test_publication_actual_signature_tree_parent_and_message_are_required(self):
        mutation=dict(kind='publication',branch='task/r3.5/t001',parent=TARGET,tree=MERGE,
                      message_sha256=hashlib.sha256(b'message').hexdigest())
        def api(*args):
            return {'object':{'sha':HEAD}} if 'git/ref' in args[-1] else dict(
                author={'login':'clemarc'},commit={'verification':{'verified':True,'reason':'valid'}})
        def git(root,*args):return {'--format=%P':TARGET,'--format=%T':MERGE,'--format=%B':'message'}[args[2]]
        with patch.object(milestone,'git',side_effect=git),patch('signatures.verify',return_value=True):
            self.assertEqual(recovery.reconcile_publication(self.root,self.context,mutation,api)['state'],'verified_applied')
            for field in ['parent','tree','message_sha256']:
                changed=dict(mutation,**{field:'f'*len(mutation[field])})
                with self.assertRaises(ValueError):recovery.reconcile_publication(self.root,self.context,changed,api)
        with patch.object(milestone,'git',side_effect=git),patch('signatures.verify',return_value=False):
            with self.assertRaises(ValueError):recovery.reconcile_publication(self.root,self.context,mutation,api)

    def test_writer_archives_history_and_compacts_current_without_touching_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            target=Path(recovery.save(root,self.old))
            current=target.with_name('CURRENT.md')
            current.write_text('verbose historical note\n'*100)
            recovery.save(root,self.old,dict(next_action='refresh_current_evidence'))
            self.assertLess(len(current.read_text().splitlines()),10)
            self.assertTrue(any('verbose historical note' in p.read_text() for p in target.parent.joinpath('archive').glob('*CURRENT.md')))
            self.assertEqual(json.loads(target.read_text())['pr'],10)
            self.assertFalse((root/'specs').exists())
            with target.with_name('.writer-lock').open('a') as lock:
                fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):recovery.save(root,self.old)
            subprocess.run([sys.executable,'-c',
                'import fcntl,os,sys; f=open(sys.argv[1],"a"); fcntl.flock(f,fcntl.LOCK_EX); os._exit(0)',
                str(target.with_name('.writer-lock'))],check=True)
            recovery.save(root,self.old)

    def test_actual_merge_recovery_reuses_historical_assessor_and_signature_gates(self):
        self.merged()
        canonical,git,read=retained_fixture(self.context)
        api=Mock(return_value=dict(commit=dict(verification=dict(verified=True,reason='valid'))))
        with patch.object(milestone,'git',side_effect=git), patch.object(
                milestone,'ancestor',return_value=True), patch.object(milestone,'read',side_effect=read), patch(
                'signatures.verify',return_value=True), patch('integration.assess_revision',return_value=({},[])) as assess:
            proof=recovery.verify_merged(self.root,self.context,self.observation['pr'],123,api)
            self.assertEqual(proof['merge_sha'],MERGE)
            self.assertEqual(assess.call_args.args[1]['main_sha'],canonical['specification_base'])
            self.assertEqual(assess.call_args.args[1]['target_sha'],TARGET)
            self.assertEqual(assess.call_args.args[4],self.observation['pr']['merged_at'])
            assess.return_value=({},['independent evidence missing'])
            with self.assertRaises(ValueError):recovery.verify_merged(self.root,self.context,self.observation['pr'],123,api)
            with patch('signatures.verify',return_value=False):
                with self.assertRaises(ValueError):recovery.verify_merged(self.root,self.context,self.observation['pr'],123,api)

    def test_actual_task_merge_requires_its_exact_registered_trailers(self):
        self.merged();feature=self.context['feature']
        messages=['feat: task only title\n',
                  f'feat: task\n\nSpec: {feature}\nTask: T001\nImplements: FR-002\n',
                  f'feat: task\n\nSpec: {feature}\nTask: T002\nImplements: FR-002\n',
                  f'feat: task\n\nSpec: {feature}\nTask: T001 T002\nImplements: FR-001 FR-002\n',
                  'feat: task\n\nSpec: specs/demo-02-other\nTask: T001\nImplements: FR-001\n']
        api=Mock(return_value=dict(commit=dict(verification=dict(verified=True,reason='valid'))))
        for message in messages:
            with self.subTest(message=message):
                _,git,read=retained_fixture(self.context,message)
                with (patch.object(milestone,'git',side_effect=git),patch.object(milestone,'read',side_effect=read),
                      patch.object(milestone,'ancestor',return_value=True),patch('signatures.verify',return_value=True),
                      patch('integration.assess_revision') as assess):
                    with self.assertRaisesRegex(ValueError,'merge trailers failed'):
                        recovery.verify_merged(self.root,self.context,self.observation['pr'],123,api)
                    assess.assert_not_called()

    def test_actual_merge_requires_authoritative_owner_merger(self):
        self.merged()
        for actor in [None,{},dict(login='someone-else')]:
            with self.subTest(actor=actor):
                self.observation['pr']['merged_by']=actor
                with patch.object(milestone,'git') as git,patch('integration.assess_revision') as assess:
                    with self.assertRaisesRegex(ValueError,'owner identity'):
                        recovery.verify_merged(self.root,self.context,self.observation['pr'],123,Mock())
                    git.assert_not_called();assess.assert_not_called()

    def test_actual_checkpoint_merge_requires_planning_trailer(self):
        self.merged(checkpoint=True)
        api=Mock(return_value=dict(commit=dict(verification=dict(verified=True,reason='valid'))))
        for trailer,valid in [('planning',True),('roadmap',False),('',False)]:
            _,git,read=retained_fixture(self.context,'chore: checkpoint\n\n'+(
                'SDD-Type: '+trailer+'\n' if trailer else ''),checkpoint=True)
            with (patch.object(milestone,'git',side_effect=git),patch.object(milestone,'read',side_effect=read),
                  patch.object(milestone,'ancestor',return_value=True),patch('signatures.verify',return_value=True),
                  patch('integration.assess_revision',return_value=({},[])) as assess):
                if valid:
                    self.assertEqual(recovery.verify_merged(self.root,self.context,self.observation['pr'],123,api)['merge_sha'],MERGE)
                    assess.assert_called_once()
                else:
                    with self.assertRaisesRegex(ValueError,'merge trailers failed'):
                        recovery.verify_merged(self.root,self.context,self.observation['pr'],123,api)
                    assess.assert_not_called()

    def test_mutation_envelope_rejects_extra_content_credentials_and_bad_ids(self):
        for mutation in [dict(kind='publication',token='forbidden'),dict(kind='merge',pr=True,head=HEAD,target=TARGET,evidence_comment=123),
                         dict(kind='delete',pr=10), dict(kind='publication',branch='task/r3.5/t001',
                             parent=HEAD,tree=TARGET,message_sha256=None)]:
            with self.assertRaises(ValueError):recovery.pending_mutation(mutation)

    def test_signed_merge_only_edits_are_rejected_before_assessing_parents(self):
        self.merged()
        def git(root,*args):
            if args[:3]==('show','-s','--format=%P'):return TARGET+' '+HEAD
            if args[:3]==('show','-s','--format=%T'):
                return ('1' if args[-1]==HEAD else '2')*40
            raise AssertionError(args)
        api=Mock(return_value=dict(commit=dict(verification=dict(verified=True,reason='valid'))))
        with (patch.object(milestone,'git',side_effect=git),patch.object(milestone,'ancestor',return_value=True),
              patch('signatures.verify',return_value=True),patch('integration.assess_revision') as assess):
            with self.assertRaisesRegex(ValueError,'tree differs'):
                recovery.verify_merged(self.root,self.context,self.observation['pr'],123,api)
            assess.assert_not_called()

    def test_cli_supplied_report_recovers_merged_snapshot_saved_before_report(self):
        self.merged();self.old['evidence_comment']=None
        original_recover=recovery.recover
        def verify(root,context,pr,report):
            if report!=123:raise ValueError('actual milestone merge and independent evidence required')
            return self.proof
        gate=Mock(side_effect=verify)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);prior=root/'prior.json';prior.write_text(json.dumps(self.old))
            original=prior.read_text()
            with (patch.object(sys,'argv',['milestone.py','R3.5','--phase','implement','--root',temp,
                    '--recover',str(prior),'--session-report','123','--handoff']),
                  patch.object(milestone,'inspect',return_value=self.context),
                  patch.object(recovery,'live_observation',return_value=self.observation),
                  patch.object(recovery,'recover',side_effect=lambda *a:original_recover(*a,gate=gate)),
                  redirect_stdout(io.StringIO())):
                with self.assertRaises(SystemExit) as stopped:milestone.main()
                self.assertEqual(stopped.exception.code,0)
            self.assertEqual(gate.call_args.args[-1],123)
            saved=json.loads((root/'artifacts/sdd-session/r3.5/snapshot.json').read_text())
            self.assertEqual(saved['evidence_comment'],123)
            self.assertEqual(saved['pending_transition'],'prepare_standalone_completion_checkpoint')
            self.assertEqual(prior.read_text(),original)

    def test_cli_supplied_report_cannot_replace_ambiguous_merge_report_intent(self):
        self.merged();self.old['evidence_comment']=None
        self.old['ambiguous_mutation']=dict(kind='merge',pr=10,head=HEAD,target=TARGET,evidence_comment=124)
        original_recover=recovery.recover;gate=Mock(return_value=dict(self.proof,evidence_comment=124))
        with tempfile.TemporaryDirectory() as temp:
            prior=Path(temp)/'prior.json';prior.write_text(json.dumps(self.old))
            with (patch.object(sys,'argv',['milestone.py','R3.5','--phase','implement','--root',temp,
                    '--recover',str(prior),'--session-report','123','--handoff']),
                  patch.object(milestone,'inspect',return_value=self.context),
                  patch.object(recovery,'live_observation',return_value=self.observation),
                  patch.object(recovery,'recover',side_effect=lambda *a:original_recover(*a,gate=gate)),
                  patch.object(recovery,'save') as save,redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO())):
                with self.assertRaises(SystemExit) as stopped:milestone.main()
                self.assertEqual(stopped.exception.code,1)
                save.assert_not_called()
            self.assertEqual(gate.call_args.args[-1],124)

    def test_cli_null_snapshot_cannot_be_replaced_as_a_fresh_handoff(self):
        with tempfile.TemporaryDirectory() as temp:
            snapshot=Path(temp)/'snapshot.json'; snapshot.write_text('null')
            with (patch.object(sys,'argv',['milestone.py','R3.5','--phase','implement',
                 '--recover',str(snapshot),'--session-pr','10','--handoff']), patch.object(
                    milestone,'inspect',return_value=self.context), patch.object(recovery,'save') as save,
                    redirect_stderr(io.StringIO())):
                with self.assertRaises(SystemExit) as stopped:milestone.main()
                self.assertEqual(stopped.exception.code,1)
                save.assert_not_called()
            self.assertEqual(snapshot.read_text(),'null')

    def test_retired_pr_cannot_resume_through_ambiguous_publication(self):
        self.observation['pr']['state']='closed'
        self.old['ambiguous_mutation']=dict(kind='publication',branch='task/r3.5/t001',
            parent=TARGET,tree=MERGE,message_sha256='e'*64)
        publication=Mock(return_value=dict(state='not_observed',action='reassess_before_expected_head_publication'))
        with self.assertRaisesRegex(ValueError,'owner reconciliation'):self.recover(publication=publication)
        publication.assert_not_called()

    def test_cli_retains_verified_merge_report_across_second_interruption(self):
        self.merged()
        self.old['evidence_comment']=None
        self.old['ambiguous_mutation']=dict(kind='merge',pr=10,head=HEAD,target=TARGET,evidence_comment=123)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); prior=root/'prior.json';prior.write_text(json.dumps(self.old))
            outcome=dict(state='reconciled',verified_evidence=[self.proof],mutation_resolved=True,
                         next_action='prepare_standalone_completion_checkpoint')
            with (patch.object(sys,'argv',['milestone.py','R3.5','--phase','implement','--root',temp,
                    '--recover',str(prior),'--handoff']),patch.object(milestone,'inspect',return_value=self.context),
                    patch.object(recovery,'live_observation',return_value=self.observation),
                    patch.object(recovery,'recover',return_value=outcome),redirect_stdout(io.StringIO())):
                with self.assertRaises(SystemExit) as stopped:milestone.main()
                self.assertEqual(stopped.exception.code,0)
            saved=json.loads((root/'artifacts/sdd-session/r3.5/snapshot.json').read_text())
            self.assertEqual(saved['evidence_comment'],123)
            self.assertIsNone(saved['ambiguous_mutation'])
            gate=Mock(return_value=self.proof)
            resumed=recovery.recover(root,self.context,saved,self.observation,gate=gate)
            self.assertEqual(gate.call_args.args[-1],123)
            self.assertEqual(resumed['next_action'],'prepare_standalone_completion_checkpoint')


if __name__=='__main__':unittest.main()

"""Default-off scheduling preserves full native acceptance and correction runs."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/sdd'))
import native_scheduling as scheduling
import aggregate
import native
from test_checks import ROADMAP

HEAD, TARGET, IMPORT, REGISTRATION, PARENT = (c*40 for c in 'abcde')
FEATURE='specs/demo-01-read'


class SchedulingTests(unittest.TestCase):
    def setUp(self):
        self.head=HEAD; self.enabled=['R3.5']; self.source_time='2026-10-24T09:00:00+00:00'
        self.signed=Mock(return_value=True)
        self.record=None; self.carried=False; self.corrupt_merge=False
        self.event=dict(repository=dict(full_name='clemarc/fava'),pull_request=dict(number=10,
            created_at='2026-10-24T10:00:00Z',head=dict(ref='task/r3.5/t001',sha=HEAD,repo=dict(full_name='clemarc/fava')),
            base=dict(ref='milestone/r3.5',sha=TARGET)))
        self.progress=Mock(return_value=dict(reservations={0:REGISTRATION},correction_cycles=0))

    def git(self,root,*args):
        if args==('rev-parse','HEAD'):return self.head
        if args[0]=='ls-tree':return 'specs/demo/roadmap.md\n'
        if args[0]=='merge-base':
            if args[-2]==REGISTRATION and not self.carried:raise subprocess.CalledProcessError(1,args)
            return ''
        if args[0]=='merge-tree':return 'f'*40
        if args[0]=='rev-parse':return '0'*40 if self.corrupt_merge else 'f'*40
        if args[0]=='show' and args[1]=='-s':
            if args[2]=='--format=%cI':return self.source_time
            return HEAD+' '+TARGET if args[-1]==IMPORT else PARENT
        if args[0]=='show':
            ref,path=args[1].split(':',1)
            if path=='.github/native-scheduling.json':
                self.assertEqual(ref,TARGET)
                return json.dumps(dict(schema=1,enabled_milestones=self.enabled))
            if path.endswith('roadmap.md'):return ROADMAP.replace('R1','R3.5')
            if path==FEATURE+'/execution.json':
                return json.dumps(dict(milestone='R3.5',milestone_branch='milestone/r3.5',
                    task_prs={'10':self.record} if self.record and (ref==TARGET or self.carried) else {}))
        raise AssertionError(args)

    def decide(self):return scheduling.decide(Path('/synthetic'),self.event,self.git,self.signed,self.progress)

    def register(self):
        self.record=dict(branch='task/r3.5/t001',heads=[HEAD],tasks=['T001'],correction_cycles=0)

    def imported(self):
        self.head=IMPORT; self.event['pull_request']['head']['sha']=IMPORT; self.carried=True

    def test_default_off_and_head_config_cannot_activate(self):
        self.enabled=[]
        self.assertTrue(self.decide()['acceptance'])
        self.signed.assert_not_called()

    def test_initial_source_defers_to_explicit_compilation_feedback(self):
        result=self.decide()
        self.assertFalse(result['acceptance']); self.assertTrue(result['compile_feedback'])
        self.assertFalse(aggregate.validate('success','success','success','skipped','required'))

    def test_registration_must_be_canonical_and_imported(self):
        self.register()
        self.assertFalse(self.decide()['acceptance'])
        self.imported()
        result=self.decide()
        self.assertTrue(result['acceptance']); self.assertFalse(result['compile_feedback'])
        self.progress.assert_called_with(Path('/synthetic'),TARGET,IMPORT,FEATURE+'/execution.json',10,
                                         self.event['pull_request']['created_at'],self.git)
        # Repeating unchanged imported-head evidence still requires both families.
        self.assertTrue(self.decide()['acceptance'])

    def test_pure_import_before_registration_still_defers(self):
        self.imported()
        self.assertFalse(self.decide()['acceptance'])

    def test_corrections_always_run_native_with_or_without_valid_registration(self):
        self.source_time='2026-10-24T11:00:00+00:00'
        self.assertTrue(self.decide()['acceptance'])
        self.register();self.record['correction_cycles']=1
        self.imported()
        self.assertTrue(self.decide()['acceptance'])

    def test_equal_second_timezone_and_unsigned_evidence_do_not_defer(self):
        for stamp in ['2026-10-24T10:00:00+00:00','2026-10-24T09:00:00']:
            self.source_time=stamp;self.assertTrue(self.decide()['acceptance'])
        self.source_time='2026-10-24T09:00:00+00:00';self.signed.return_value=False
        self.assertTrue(self.decide()['acceptance'])

    def test_forks_other_targets_and_checkout_mismatch_run_full(self):
        self.event['pull_request']['head']['repo']['full_name']='other/fava'
        self.assertTrue(self.decide()['acceptance'])
        self.event['pull_request']['head']['repo']['full_name']='clemarc/fava'
        self.event['pull_request']['base']['ref']='main'
        self.assertTrue(self.decide()['acceptance'])
        self.event['pull_request']['base']['ref']='milestone/r3.5'
        self.head=IMPORT
        self.assertTrue(self.decide()['acceptance'])

    def test_uncertain_registration_or_conflicted_import_runs_full(self):
        self.register();self.record['heads']=[]
        self.assertTrue(self.decide()['acceptance'])
        self.register();self.imported();self.corrupt_merge=True
        self.assertTrue(self.decide()['acceptance'])
        self.corrupt_merge=False;self.progress.side_effect=ValueError('missing durable registration')
        self.assertTrue(self.decide()['acceptance'])

    def test_cancellations_timeouts_and_missing_native_never_pass_aggregate(self):
        for outcome in ['skipped','cancelled','failure','timed_out','']:
            self.assertFalse(aggregate.validate('success','success','success',outcome,'required'))

    def test_feedback_compiles_without_simulator_tests_or_shared_products(self):
        with patch.object(native.sys,'platform','darwin'),patch.object(native,'tracked',return_value=[]),patch.object(
                native,'validate_config',return_value=['-project','Fava.xcodeproj','-scheme','Fava']),patch.object(
                native,'run') as run:
            native.compile_feedback()
        commands=[c.args[0] for c in run.call_args_list]
        self.assertTrue(any('build' in c and 'generic/platform=iOS Simulator' in c for c in commands))
        self.assertFalse(any('test' in c or 'test-without-building' in c or 'simctl' in c for c in commands))


if __name__=='__main__':unittest.main()

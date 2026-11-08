"""Measurements observe gates without storing proof or changing their results."""
from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/sdd'))
import metrics
import milestone


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.path=self.root/'artifacts/metrics.jsonl'

    def tearDown(self):self.temp.cleanup()

    def read(self):return [json.loads(x) for x in self.path.read_text().splitlines()]

    def test_disabled_has_no_output_or_semantic_change(self):
        @metrics.measured('fixture')
        def gate():raise ValueError('gate rejection')
        with self.assertRaisesRegex(ValueError,'gate rejection'),metrics.invocation('test'):
            gate()
        self.assertFalse(self.path.exists())
        self.assertIsNone(metrics.ACTIVE.get())

    def test_nested_spans_counts_per_invocation_only_and_no_raw_payloads(self):
        @metrics.measured('fixture',historical='always')
        def gate():
            for _ in range(2):metrics.historical_record(('private-body', 'a'*40))
            metrics.historical_record(('private-body', 'a'*40),deduplicated=True)
            metrics.immutable_object('signature','a'*40)
            metrics.immutable_object('signature','a'*40)
            return 'original-result'
        with metrics.invocation('test',self.path):
            with metrics.invocation('diagnostic',self.root/'never.json'):
                self.assertEqual(gate(),'original-result')
        result=self.read()[0]
        self.assertEqual(result['historical_records_visited'],3)
        self.assertEqual(result['historical_object_inspections'],2)
        self.assertEqual(result['repeated_historical_object_inspections'],1)
        self.assertEqual(result['per_invocation_deduplications'],1)
        self.assertEqual(result['repeated_immutable_object_verifications'],1)
        self.assertEqual(result['spans']['fixture']['calls'],1)
        self.assertNotIn('private-body',self.path.read_text())
        self.assertNotIn('a'*40,self.path.read_text())
        self.assertFalse((self.root/'never.json').exists())
        with metrics.invocation('test',self.path):gate()
        first,second=self.read()
        self.assertNotEqual(first['invocation_id'],second['invocation_id'])
        self.assertEqual(first['historical_records_visited'],second['historical_records_visited'])

    def test_github_pages_requests_duration_and_error_without_credentials(self):
        with metrics.invocation('test',self.path),patch.dict('os.environ',FAVA_GITHUB_API_TOKEN='private-secret'),patch.object(
                subprocess,'run',return_value=subprocess.CompletedProcess([],0,'[[{"body":"private-response"}],[]]','')):
            self.assertEqual(len(milestone.github('api','--paginate','--slurp','repos/example/repo/issues')),2)
        result=self.read()[0]
        self.assertEqual(result['github_commands'],1)
        self.assertEqual(result['github_request_count'],2)
        self.assertGreaterEqual(result['github_duration_seconds'],0)
        self.assertNotIn('private',self.path.read_text())

    def test_opaque_and_failed_commands_do_not_claim_exact_request_count(self):
        with metrics.invocation('test',self.path):
            with metrics.github_request(['pr','view','1']) as request:request['response']={}
            with self.assertRaises(ValueError),metrics.github_request(['api','repos/private']):
                raise ValueError('private response')
        result=self.read()[0]
        self.assertIsNone(result['github_request_count'])
        self.assertEqual(result['github_request_count_lower_bound'],1)
        self.assertEqual(result['github_errors'],1)
        self.assertEqual(result['retries'],0)
        self.assertNotIn('private',self.path.read_text())

    def test_historical_calls_are_excluded_from_live_refresh(self):
        @metrics.measured('gate',historical=True,live=True)
        def gate(root,context,pr,evidence,cutoff=None):
            with metrics.github_request(['api','repos/example/repo/pulls/1']) as request:request['response']={}
        with metrics.invocation('test',self.path):gate(None,None,None,None,'2026-01-01T00:00:00Z')
        self.assertEqual(self.read()[0]['live_gate_refresh_seconds'],0)
        with metrics.invocation('test',self.path):gate(None,None,None,None)
        self.assertGreater(self.read()[1]['live_gate_refresh_seconds'],0)

    def test_actual_retained_preparation_wrapper_is_not_live_gate_refresh(self):
        context=dict(prs=[dict(head='prepare/r3.5',merged='2026-01-01T00:00:00Z',number=1,merge_sha='a'*40)],
                     preparation_branch='prepare/r3.5',execution=dict(preparation_prs={'1':{}}),ledger='specs/demo/execution.json')
        with metrics.invocation('test',self.path),patch.dict('os.environ',FAVA_GITHUB_API_TOKEN='private'),patch.object(
                subprocess,'run',return_value=subprocess.CompletedProcess([],0,'{}','')),patch.object(
                    milestone,'git',side_effect=ValueError('stop after historical API')):
            with self.assertRaises(ValueError):milestone.retained_preparation_progress(self.root,context)
        result=self.read()[0]
        self.assertEqual(result['github_commands'],1)
        self.assertEqual(result['historical_records_visited'],1)
        self.assertEqual(result['live_gate_refresh_seconds'],0)

    def test_measurement_write_failure_preserves_original_gate_rejection(self):
        with redirect_stderr(io.StringIO()) as error,patch.object(metrics.os,'open',side_effect=PermissionError()):
            with self.assertRaisesRegex(ValueError,'original rejection'),metrics.invocation('test',self.path):
                raise ValueError('original rejection')
        self.assertIn('gate result unchanged',error.getvalue())
        self.assertIsNone(metrics.ACTIVE.get())

    def test_exit_status_and_purpose_are_preserved(self):
        for code in [0,1]:
            with self.assertRaises(SystemExit),metrics.invocation('test',self.path):raise SystemExit(code)
            self.assertEqual(self.read()[-1]['invocation_failed'],bool(code))
        with self.assertRaises(ValueError),metrics.invocation('https://private.invalid/?token=secret',self.path):pass


if __name__=='__main__':unittest.main()

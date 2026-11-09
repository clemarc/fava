import copy
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

import native
import native_spike


class NativeSpikeTests(unittest.TestCase):
    def report(self, family):
        return {
            'family': family, 'source_sha': 'a' * 40, 'workflow_run_id': '42',
            'workflow_run_attempt': '3', 'artifact_name': 'products-42',
            'archive_sha256': 'b' * 64, 'result_bundle_present': True,
            'test_count': 13, 'mandatory_suites': {'FavaTests': True, 'FavaUITests': True},
        }

    def assess(self, iphone, ipad):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            phone, tablet = root / 'phone.json', root / 'tablet.json'
            phone.write_text(json.dumps(iphone))
            tablet.write_text(json.dumps(ipad))
            return native_spike.assess(SimpleNamespace(
                iphone_report=phone, ipad_report=tablet, source_sha='a' * 40,
                workflow_run_id='42', workflow_run_attempt='3', artifact_name='products-42',
                archive_sha256='b' * 64))

    def test_assess_accepts_two_complete_device_reports(self):
        self.assertIsNone(self.assess(self.report('iPhone'), self.report('iPad')))

    def test_assess_fails_closed_for_incomplete_or_wrong_evidence(self):
        phone, tablet = self.report('iPhone'), self.report('iPad')
        alternatives = [
            ('duplicate family', phone, dict(tablet, family='iPhone')),
            ('wrong source', dict(phone, source_sha='c' * 40), tablet),
            ('wrong attempt', phone, dict(tablet, workflow_run_attempt='4')),
            ('wrong artifact', dict(phone, artifact_name='other'), tablet),
            ('wrong digest', phone, dict(tablet, archive_sha256='d' * 64)),
            ('missing result', dict(phone, result_bundle_present=False), tablet),
            ('zero tests', phone, dict(tablet, test_count=0)),
            ('missing unit suite', dict(phone, mandatory_suites={'FavaTests': False, 'FavaUITests': True}), tablet),
            ('missing UI suite', phone, dict(tablet, mandatory_suites={'FavaTests': True})),
        ]
        for name, changed_phone, changed_tablet in alternatives:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    self.assess(copy.deepcopy(changed_phone), copy.deepcopy(changed_tablet))

    def test_manifest_detects_mode_and_symbolic_link_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'products'
            root.mkdir()
            executable = root / 'runner'
            executable.write_text('test')
            executable.chmod(0o755)
            (root / 'host').symlink_to('runner')
            manifest = native_spike.tree_manifest(root)
            native_spike.verify_tree_manifest(root, manifest)
            executable.chmod(0o644)
            with self.assertRaises(ValueError):
                native_spike.verify_tree_manifest(root, manifest)

    def test_test_products_command_uses_the_xctestrun_without_project_or_scheme(self):
        command = native_spike.test_without_building_command('products', 'platform=iOS Simulator,id=A', 'result.xcresult')
        self.assertIn('-testProductsPath', command)
        self.assertNotIn('-project', command)
        self.assertNotIn('-workspace', command)
        self.assertNotIn('-scheme', command)

    def test_timing_evidence_is_best_effort_machine_readable(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'timing.json'
            timings = native.Timings('iPhone')
            with timings.phase('build_execution'):
                pass
            timings.unknown('simulator_boot_and_readiness', 'not separately measured')
            timings.write(path)
            payload = json.loads(path.read_text())
            self.assertEqual(payload['family'], 'iPhone')
            self.assertGreaterEqual(payload['whole_job_seconds'], 0)
            self.assertEqual([event['status'] for event in payload['events']], ['completed', 'unknown'])


if __name__ == '__main__':
    unittest.main()

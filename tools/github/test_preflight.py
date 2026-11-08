"""Capability probes never mutate GitHub or promote incomplete evidence."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import preflight


class PreflightTests(unittest.TestCase):
    def test_transport_and_authorization_are_distinct_and_sanitized(self):
        for message, state in [
            ('proxyconnect tcp: Forbidden https://secret.invalid/?token=private', 'temporarily_unavailable'),
            ('HTTP 403 Forbidden private-token', 'authorization_blocked'),
            ('HTTP 401 Bad credentials', 'authorization_blocked'),
            ('HTTP 503 private response', 'temporarily_unavailable'),
            ('unknown command private', 'unsupported'),
            ('unexpected private response', 'not_checked'),
        ]:
            result = preflight.failure(message)
            self.assertEqual(result['state'], state)
            self.assertNotIn('private', json.dumps(result))
            self.assertNotIn('https', json.dumps(result))

    def test_subprocess_failures_are_bounded_and_sanitized(self):
        probe = preflight.Probe(Path.cwd())
        for error, state in [(FileNotFoundError(), 'unsupported'),
                             (PermissionError(), 'temporarily_unavailable'),
                             (subprocess.TimeoutExpired('private', 20), 'temporarily_unavailable')]:
            with patch.object(subprocess, 'run', side_effect=error):
                result, output = probe.run(['fixture'])
                self.assertEqual(result['state'], state)
                self.assertEqual(output, '')
        with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess(
                ['fixture'], 1, 'private', 'HTTP 403')) as run:
            result, output = probe.run(['fixture'])
            self.assertEqual(result['state'], 'authorization_blocked')
            self.assertEqual(output, '')
            self.assertEqual(run.call_args.kwargs['timeout'], 20)

    def graphql(self, payload):
        probe = preflight.Probe(Path.cwd())
        with patch.dict(os.environ, FAVA_GITHUB_API_TOKEN='fixture', GH_DEBUG='api'), patch.object(
                probe, 'run', return_value=(preflight.evidence('supported', 'fixture'),
                                            json.dumps(payload))) as run:
            result = preflight.graphql(probe, '/gh', 'clemarc/fava', True)
            self.assertEqual(run.call_args.args[1]['GH_DEBUG'], '')
            self.assertEqual(run.call_args.args[1]['GH_TOKEN'], 'fixture')
            self.assertTrue(run.call_args.args[0][-1].startswith('query=query {'))
        return result

    def test_graphql_requires_complete_error_free_data(self):
        good = dict(data=dict(viewer=dict(login='fixture'), repository=dict(viewerPermission='WRITE')))
        self.assertEqual(self.graphql(good)['state'], 'supported')
        self.assertEqual(self.graphql(dict(good, errors=[dict(type='FORBIDDEN')]))['state'],
                         'authorization_blocked')
        for payload in [None, [], 'ambiguous', dict(good, errors=[dict(message='private')]), {},
                        dict(data=dict(viewer=None, repository=None)),
                        dict(data=dict(viewer=dict(login=''), repository=dict(viewerPermission='WRITE'))),
                        dict(data=dict(viewer=dict(login='fixture'), repository=dict(viewerPermission='UNKNOWN')))]:
            self.assertEqual(self.graphql(payload)['state'], 'not_checked')

    def test_no_network_or_binding_means_no_probe(self):
        probe = preflight.Probe(Path.cwd())
        with patch.object(probe, 'run') as run, patch.dict(os.environ, {}, clear=True):
            self.assertEqual(preflight.graphql(probe, '/gh', 'clemarc/fava', False)['state'], 'not_checked')
            self.assertEqual(preflight.graphql(probe, '/gh', 'clemarc/fava', True)['state'], 'authorization_blocked')
            self.assertEqual(preflight.graphql(probe, None, 'clemarc/fava', True)['state'], 'unsupported')
            run.assert_not_called()

    def report(self, inventory=None, access=None):
        with tempfile.TemporaryDirectory() as directory, patch.object(preflight.shutil, 'which', return_value=None), patch.object(
                preflight, 'graphql', return_value=access or preflight.evidence('not_checked', 'fixture')):
            return preflight.report(Path(directory), 'clemarc/fava', connector_tools=inventory)

    def test_inventory_is_interface_evidence_only(self):
        report = self.report(['mcp__codex_apps__github_create_pull_request',
                              'mcp__codex_apps__github_merge_pull_request'])
        self.assertEqual(report['connectors']['pr_create']['state'], 'supported')
        self.assertEqual(report['connectors']['pr_create']['authorization'], 'not_checked')
        self.assertEqual(report['connectors']['logs']['state'], 'unsupported')
        self.assertIsNotNone(report['routes']['pr_create']['fallback'])
        self.assertEqual(report['routes']['pr_create']['fallback_condition'], 'read_authoritative_state_first')
        self.assertIsNone(report['routes']['merge']['fallback'])
        self.assertIsNone(report['routes']['publication']['fallback'])
        self.assertEqual(self.report()['connectors']['logs']['state'], 'not_checked')

    def test_read_permission_never_proves_publication(self):
        for permission in ['ADMIN', 'WRITE', 'READ']:
            report = self.report(access=preflight.evidence('supported', 'fixture', permission=permission))
            self.assertEqual(report['publication']['state'],
                             'authorization_blocked' if permission == 'READ' else 'not_checked')
        self.assertEqual(self.report(access=preflight.evidence(
            'temporarily_unavailable', 'fixture'))['publication']['state'], 'temporarily_unavailable')

    def test_missing_tools_and_helpers_are_explicit(self):
        report = self.report()
        self.assertTrue(all(v['state'] == 'unsupported' for v in report['executables'].values()))
        self.assertTrue(all(v['state'] == 'unsupported' for v in report['helpers'].values()))
        self.assertTrue(all(v['state'] == 'unsupported' for v in report['gh_commands'].values()))
        self.assertEqual(report['git']['head']['state'], 'unsupported')
        self.assertEqual(report['signing']['state'], 'not_checked')

    def test_report_only_runs_read_only_commands_and_never_starts_agent(self):
        calls = []

        def run(probe, args, env=None):
            calls.append(args)
            value = 'fixture version 2.3.4' if '--version' in args else ''
            return preflight.evidence('supported', 'fixture'), value

        with tempfile.TemporaryDirectory() as directory, patch.object(preflight.shutil, 'which', side_effect=lambda name: '/' + name), patch.object(
                preflight.Probe, 'run', run):
            # An unavailable HEAD keeps this synthetic test outside the real key verifier.
            original = run

            def no_head(probe, args, env=None):
                if 'rev-parse' in args:
                    return preflight.evidence('not_checked', 'fixture'), ''
                return original(probe, args, env)

            with patch.object(preflight.Probe, 'run', no_head):
                report = preflight.report(Path(directory), 'clemarc/fava')
        self.assertEqual(report['executables']['git']['version'], '2.3.4')
        self.assertIn(['/gpg-connect-agent', '--no-autostart', '/bye'], calls)
        for args in calls:
            self.assertTrue('--version' in args or '--help' in args or
                            args[0] == '/git' or '--no-autostart' in args)
        self.assertEqual(report['publication']['state'], 'not_checked')

    def test_missing_signature_helper_with_head_and_gpg_does_not_crash(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
                preflight.shutil, 'which', side_effect=lambda name: '/' + name), patch.object(
                preflight.Probe, 'run', return_value=(preflight.evidence('supported', 'fixture'), 'a' * 40)):
            report = preflight.report(Path(directory), 'clemarc/fava')
        self.assertEqual(report['signing']['state'], 'unsupported')
        self.assertEqual(report['helpers']['tools/sdd/signatures.py']['state'], 'unsupported')


if __name__ == '__main__':
    unittest.main()

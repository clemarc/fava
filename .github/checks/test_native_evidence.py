"""Synthetic exact-head/attempt native proof, transport and partial-data cases."""
import copy
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/sdd'))
import native
import native_evidence as ne

HEAD = 'a' * 40
REPO = 'clemarc/fava'


def summary(family='iPhone', **changes):
    counts = dict(passedTests=4, failedTests=0, skippedTests=0, expectedFailures=0)
    return dict(totalTestCount=4, result='Passed', **counts,
                devicesAndConfigurations=[dict(device=dict(deviceName=family + ' 17',
                                                            platform='iOS Simulator'), **counts)], **changes)


def log(family='iPhone'):
    lines = [f'[command]/opt/homebrew/bin/git checkout --progress --force {HEAD}',
             '** BUILD SUCCEEDED **', '** TEST SUCCEEDED **',
             '+ xcrun xcresulttool get test-results summary --path artifacts/FavaTests.xcresult',
             *json.dumps(summary(family), indent=2).splitlines(), 'Cleaning up orphan processes']
    return '\n'.join('2026-10-24T11:00:00.0000000Z ' + line for line in lines)


def job(family='iPhone', **changes):
    identity = 101 if family == 'iPhone' else 102
    result = dict(id=identity, run_id=12, run_attempt=2, head_sha=HEAD,
                  name=f'ios-build-test / ios-build-test ({family})', labels=['macos-26'],
                  html_url=f'https://github.com/{REPO}/actions/runs/12/job/{identity}',
                  status='completed', conclusion='success', started_at='2026-10-24T10:00:00Z',
                  completed_at='2026-10-24T11:00:00Z', steps=[dict(
                      name='Build and test on an available simulator', conclusion='success')])
    return dict(result, **changes)


RUN = dict(id=12, run_attempt=2, head_sha=HEAD, path='.github/workflows/sdd-quality.yml')


def fallback(response=None, **changes):
    return dict(dict(repository=REPO, run_id=12, attempt=2, job_id=101,
                     response=response or dict(structuredContent=dict(content=log()))), **changes)


class NativeParsingTests(unittest.TestCase):
    def test_actual_format_and_gh_decoration(self):
        for text in [log(), '\n'.join('ios-job\tBuild and test\t' + x for x in log().splitlines())]:
            result = native.log_evidence(text, HEAD, 'iPhone')
            self.assertEqual(result['tests'], 4)
            self.assertTrue(result['build_succeeded'])

    def test_missing_identity_tail_summary_or_conflicting_results_fail_closed(self):
        for text in [log().replace(HEAD, 'b' * 40), log().replace('Cleaning up orphan processes', ''),
                     log().split('totalTestCount')[0], log() + '\n** TEST FAILED **',
                     log() + '\n+ xcrun xcresulttool get test-results summary --path artifacts/FavaTests.xcresult']:
            with self.subTest(text=text[-50:]), self.assertRaises(ValueError):
                native.log_evidence(text, HEAD, 'iPhone')

    def test_invalid_nonzero_and_device_counts(self):
        for modify in [lambda r:r.update(totalTestCount=True), lambda r:r.update(totalTestCount=0),
                       lambda r:r.update(failedTests=1), lambda r:r.update(result='Unknown'),
                       lambda r:r['devicesAndConfigurations'][0].update(passedTests=99),
                       lambda r:r['devicesAndConfigurations'][0]['device'].update(platform='iOS')]:
            value = summary()
            modify(value)
            with self.assertRaises(ValueError): native.evidence_summary(value, 'iPhone')
        with self.assertRaises(ValueError): native.evidence_summary(summary(), 'iPad')


class JobEvidenceTests(unittest.TestCase):
    def inspect(self, candidate=None, run=None, logs=None, connector=None):
        return ne.inspect_job(REPO, run or RUN, candidate or job(), 12, 2, HEAD, 'iPhone',
                              logs or (lambda *_:log()), connector)

    def test_success_requires_actual_native_execution(self):
        self.assertEqual(self.inspect()['outcome'], 'verified_successful')
        for candidate in [job(steps=[]), job(steps=[dict(name='ci-required', conclusion='success')])]:
            self.assertEqual(self.inspect(candidate)['outcome'], 'incomplete')
        self.assertEqual(self.inspect(logs=lambda *_: log().replace('** BUILD SUCCEEDED **',''))['outcome'], 'incomplete')

    def test_identity_attempt_job_family_workflow_and_platform(self):
        for changes in [dict(run_attempt=1), dict(run_id=99), dict(head_sha='b'*40),
                        dict(name='ci-required'), dict(labels=['ubuntu-24.04']),
                        dict(html_url='https://evil.invalid/12')]:
            self.assertEqual(self.inspect(job(**changes))['outcome'], 'incomplete')
        for changes in [dict(head_sha='b'*40), dict(run_attempt=3)]:
            self.assertEqual(self.inspect(run=dict(RUN, **changes))['outcome'], 'superseded')
        self.assertEqual(self.inspect(run=dict(RUN, path='other.yml'))['outcome'], 'incomplete')

    def test_cancellation_and_timeout_are_never_test_failures(self):
        for conclusion in ['cancelled', 'timed_out']:
            self.assertEqual(self.inspect(job(conclusion=conclusion), logs=lambda *_:self.fail())['outcome'], conclusion)
        self.assertEqual(self.inspect(job(status='in_progress', conclusion=None))['outcome'], 'incomplete')
        self.assertEqual(self.inspect(job(conclusion='skipped'))['outcome'], 'unknown')
        self.assertEqual(self.inspect(job(conclusion='startup_failure'))['outcome'], 'infrastructure_error')

    def test_failed_requires_failure_evidence(self):
        self.assertEqual(self.inspect(job(conclusion='failure'))['outcome'], 'unknown')
        self.assertEqual(self.inspect(job(conclusion='failure'), logs=lambda *_:log()+'\n** TEST FAILED **')['outcome'], 'verified_failed')

    def test_connector_fallback_and_unavailable(self):
        def unavailable(*_): raise ne.RetrievalError('retrieval_failed')
        result = self.inspect(logs=unavailable)
        self.assertEqual(result['outcome'], 'unavailable')
        self.assertEqual(result['next_action']['job_id'], 101)
        result = self.inspect(logs=unavailable, connector=fallback())
        self.assertEqual(result['outcome'], 'verified_successful')
        self.assertEqual([d['tool'] for d in result['diagnostics']], ['gh_run_view', 'github_connector_job_logs'])
        self.assertEqual(self.inspect(logs=lambda *_:'partial', connector=fallback())['outcome'],
                         'verified_successful')
        self.assertIsNotNone(self.inspect(logs=lambda *_:'partial')['next_action'])
        for marker in ['** BUILD SUCCEEDED **', '** TEST SUCCEEDED **']:
            self.assertEqual(self.inspect(logs=lambda *_:log().replace(marker,''),
                                          connector=fallback())['outcome'], 'verified_successful')
        failed_log=log()+'\n** TEST FAILED **'
        self.assertEqual(self.inspect(job(conclusion='failure'),logs=lambda *_:'partial',
                                      connector=fallback(response=dict(structuredContent=dict(content=failed_log))))['outcome'],
                         'verified_failed')
        for envelope in [fallback(attempt=1), fallback(job_id=102), fallback(repository='other/repo'),
                         fallback(response=dict(isError=True)), fallback(response=dict(content=[]))]:
            self.assertEqual(self.inspect(logs=unavailable, connector=envelope)['outcome'], 'unavailable')

    def test_checkout_failure_is_infrastructure_even_without_checkout_log(self):
        candidate=job(conclusion='failure',steps=[dict(name='Run actions/checkout@pinned',conclusion='failure')])
        self.assertEqual(self.inspect(candidate,logs=lambda *_:self.fail())['outcome'],'infrastructure_error')

    def test_partial_and_ambiguous_connector_content(self):
        self.assertEqual(ne.connector_log(dict(structuredContent=dict(content=log()),
                                               content=[dict(type='text', text='Action completed.')])), log())
        self.assertEqual(ne.connector_log(dict(content=[dict(type='text', text=log())])), log())
        chunks = [dict(offset=0, text='ab'), dict(offset=2, text='ç')]
        self.assertEqual(ne.connector_log(dict(structuredContent=dict(content=chunks,total_bytes=4))), 'abç')
        for response in [dict(truncated=True), dict(structuredContent=dict(content=chunks,total_bytes=3)),
                         dict(structuredContent=dict(content=log(),truncated=True)),
                         dict(structuredContent=dict(content=log(),complete=False)),
                         dict(structuredContent=dict(content=list(reversed(chunks)),total_bytes=4)),
                         dict(structuredContent=dict(content=[dict(offset=2,text='partial')],total_bytes=7))]:
            with self.assertRaises(ne.RetrievalError): ne.connector_log(response)
        result = self.inspect(logs=lambda *_:'Action completed.')
        self.assertEqual(result['outcome'], 'incomplete')

    def test_all_skipped_or_zero_tests_never_accept(self):
        for total in [0, 4]:
            value = summary()
            value.update(totalTestCount=total, passedTests=0, skippedTests=total)
            value['devicesAndConfigurations'][0].update(passedTests=0, skippedTests=total)
            text = log().replace(json.dumps(summary(),indent=2).replace('\n','\n2026-10-24T11:00:00.0000000Z '),
                                 json.dumps(value,indent=2).replace('\n','\n2026-10-24T11:00:00.0000000Z '))
            self.assertEqual(self.inspect(logs=lambda *_:text)['outcome'], 'incomplete')


class FakeAPI:
    def __init__(self):
        self.jobs = [job(f) for f in ne.FAMILIES]
        self.refreshed = dict(RUN)
        self.artifacts = []
        self.payload = b'invalid zip'

    def api(self, path):
        if path.startswith('actions/jobs/'):
            return next(j for j in self.jobs if j['id'] == int(path.rsplit('/',1)[1]))
        return self.refreshed

    def pages(self, path, key):
        return self.artifacts if key == 'artifacts' else self.jobs

    def logs(self, run, identity): return log('iPhone' if identity == 101 else 'iPad')
    def artifact(self, identity): return self.payload


class CollectionTests(unittest.TestCase):
    def collect(self, api): return ne.collect(api, REPO, 12, 2, HEAD)

    def test_both_families_and_optional_missing_artifact(self):
        result = self.collect(FakeAPI())
        self.assertTrue(result['accepted'])
        self.assertEqual(len(result['artifacts']), 2)

    def test_missing_duplicate_family_or_changed_attempt_block_acceptance(self):
        for jobs in [[job()], [job(), job(), job('iPad')]]:
            api = FakeAPI(); api.jobs = jobs
            self.assertFalse(self.collect(api)['accepted'])
        api = FakeAPI(); api.refreshed['run_attempt'] = 3
        self.assertFalse(self.collect(api)['accepted'])

    def artifact_api(self, total=4, filename='test-summary.log'):
        api = FakeAPI()
        api.artifacts = [dict(id=55, name=f'ios-diagnostics-iPhone-{HEAD}',expired=False,
                              workflow_run=dict(id=12,head_sha=HEAD), created_at='2026-10-24T10:59:00Z')]
        value = summary()
        value['totalTestCount'] = value['passedTests'] = total
        value['devicesAndConfigurations'][0]['passedTests'] = total
        output = io.BytesIO()
        with zipfile.ZipFile(output,'w') as archive: archive.writestr(filename,json.dumps(value))
        api.payload=output.getvalue()
        return api

    def test_optional_artifact_download_content_and_contradiction(self):
        result=self.collect(self.artifact_api())
        self.assertTrue(result['accepted'])
        self.assertEqual(result['artifacts'][0]['category'],'retrieved_archive_validated')
        self.assertFalse(self.collect(self.artifact_api(total=99))['accepted'])
        self.assertTrue(self.collect(self.artifact_api(filename='../test-summary.log'))['accepted'])
        api=self.artifact_api(); api.artifacts[0]['workflow_run']['head_sha']='b'*40
        self.assertEqual(self.collect(api)['artifacts'][0]['category'],'artifact_identity_or_expiry_invalid')
        api=self.artifact_api(); api.artifacts[0]['created_at']='2025-01-01T00:00:00Z'
        self.assertEqual(self.collect(api)['artifacts'][0]['category'],'artifact_attempt_not_established')

    def test_corrupt_compressed_optional_artifact_is_structured(self):
        api=self.artifact_api()
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('test-summary.log',json.dumps(summary()))
        payload=bytearray(output.getvalue())
        offset=30+len('test-summary.log')
        payload[offset:offset+3]=b'\xff\xff\xff'
        api.payload=bytes(payload)
        result=self.collect(api)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['artifacts'][0]['category'],'invalid_artifact_archive')


if __name__ == '__main__': unittest.main()

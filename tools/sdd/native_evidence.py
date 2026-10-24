"""Collect exact-attempt native evidence. Connector fallback is an explicit handoff."""
import argparse
from datetime import datetime
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit
import zipfile
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '.github/checks'))
from native import log_evidence, evidence_summary, evidence_log_text

FAMILIES = ('iPhone', 'iPad')
OUTCOMES = {'verified_successful', 'verified_failed', 'cancelled', 'timed_out',
            'incomplete', 'unavailable', 'superseded', 'infrastructure_error', 'unknown'}
MAX_RESPONSE = 64 * 1024 * 1024


class RetrievalError(Exception):
    def __init__(self, category, hostname='api.github.com'):
        self.category, self.hostname = category, hostname


def diagnostic(tool, category, destination_hostname='api.github.com', **identity):
    # Identity fields are supplied from validated metadata, never raw errors.
    return dict(tool=tool, destination_hostname=destination_hostname, category=category, **identity)


def connector_log(response):
    """Accept complete MCP text or explicit ordered chunks, never action summaries."""
    if not isinstance(response, dict) or response.get('isError') or response.get('truncated'):
        raise RetrievalError('connector_error_or_truncation')
    structured = response.get('structuredContent')
    if isinstance(structured, dict) and (structured.get('truncated') or structured.get('complete') is False):
        raise RetrievalError('connector_error_or_truncation')
    if isinstance(structured, dict) and 'content' in structured:
        value = structured['content']
    else:
        blocks = response.get('content', [])
        if not isinstance(blocks, list) or not blocks or any(
                not isinstance(b, dict) or b.get('type') != 'text' or not isinstance(b.get('text'), str)
                for b in blocks):
            raise RetrievalError('ambiguous_connector_response')
        value = ''.join(b['text'] for b in blocks)
    if isinstance(value, list):
        chunks, offset = [], 0
        for chunk in value:
            if (not isinstance(chunk, dict) or set(chunk) != {'offset', 'text'}
                    or type(chunk['offset']) is not int or chunk['offset'] != offset
                    or not isinstance(chunk['text'], str)):
                raise RetrievalError('incomplete_or_unordered_chunks')
            chunks.append(chunk['text'])
            offset += len(chunk['text'].encode('utf-8'))
        value = ''.join(chunks)
        if not structured or structured.get('total_bytes') != offset:
            raise RetrievalError('incomplete_chunks')
    if not isinstance(value, str) or not value or len(value.encode('utf-8')) > MAX_RESPONSE:
        raise RetrievalError('empty_or_oversized_logs')
    return value


class GitHub:
    def __init__(self, repository):
        self.repository = repository

    def command(self, args, binary=False):
        if not os.environ.get('FAVA_GITHUB_API_TOKEN'):
            raise RetrievalError('authorization_blocked')
        try:
            result = subprocess.run(['gh', *args], capture_output=True, timeout=90,
                                    env=dict(os.environ, GH_TOKEN=os.environ['FAVA_GITHUB_API_TOKEN'], GH_DEBUG=''))
        except (OSError, subprocess.TimeoutExpired):
            raise RetrievalError('transport_unavailable') from None
        if result.returncode:
            error = result.stderr.decode('utf-8', errors='replace').lower()
            category = 'authorization_blocked' if any(s in error for s in ('http 401', 'http 403', 'bad credentials')) else 'retrieval_failed'
            hosts = [urlsplit(url).hostname for url in re.findall(r'https?://[^\s)]+', error)]
            host = next((h for h in reversed(hosts) if h and re.fullmatch(r'[a-z0-9.-]+', h)), 'api.github.com')
            raise RetrievalError(category, host)
        if len(result.stdout) > MAX_RESPONSE:
            raise RetrievalError('oversized_response')
        if binary:
            return result.stdout
        try:
            return result.stdout.decode('utf-8')
        except UnicodeError:
            raise RetrievalError('invalid_encoding') from None

    def api(self, path):
        try:
            return json.loads(self.command(['api', f'repos/{self.repository}/{path}']))
        except ValueError:
            raise RetrievalError('invalid_json') from None

    def pages(self, path, key):
        values = []
        for page in range(1, 1001):
            data = self.api(f'{path}?per_page=100&page={page}')
            entries = data.get(key) if isinstance(data, dict) else None
            if not isinstance(entries, list):
                raise RetrievalError('invalid_page')
            values.extend(entries)
            if len(entries) < 100:
                return values
        raise RetrievalError('pagination_limit')

    def logs(self, run, job):
        return self.command(['run', 'view', str(run), '--repo', self.repository,
                             '--job', str(job), '--log'])

    def artifact(self, artifact):
        return self.command(['api', f'repos/{self.repository}/actions/artifacts/{artifact}/zip'], binary=True)


def validate_identity(repository, run, job, run_id, attempt, head, family):
    if run.get('head_sha') != head:
        return 'superseded', 'run_head_changed'
    if run.get('run_attempt') != attempt:
        return 'superseded', 'run_attempt_changed'
    if (run.get('id') != run_id or run.get('path') != '.github/workflows/sdd-quality.yml'
            or job.get('run_id') != run_id or job.get('run_attempt') != attempt
            or job.get('head_sha') != head
            or job.get('name') != f'ios-build-test / ios-build-test ({family})'
            or job.get('html_url') != f'https://github.com/{repository}/actions/runs/{run_id}/job/{job.get("id")}'
            or not any(str(label).startswith('macos-') for label in job.get('labels', []))):
        return 'incomplete', 'inconsistent_run_or_job_identity'
    return None, None


def inspect_job(repository, run, job, run_id, attempt, head, family, get_logs, fallback=None):
    identity = dict(run_id=run_id, attempt=attempt, job_id=job.get('id'), family=family)
    result = dict(identity, head=head, job_url=job.get('html_url'), outcome='unknown',
                  started_at=job.get('started_at'), completed_at=job.get('completed_at'),
                  diagnostics=[], next_action=None)
    outcome, reason = validate_identity(repository, run, job, run_id, attempt, head, family)
    if outcome:
        return dict(result, outcome=outcome, reason=reason)
    conclusion = job.get('conclusion')
    if conclusion in {'cancelled', 'timed_out'}:
        return dict(result, outcome=conclusion, reason='authoritative_job_conclusion')
    if job.get('status') != 'completed':
        return dict(result, outcome='incomplete', reason='job_not_completed')
    if conclusion in {'startup_failure', 'action_required', 'stale'}:
        return dict(result, outcome='infrastructure_error', reason='authoritative_job_conclusion')
    if conclusion not in {'success', 'failure'}:
        return dict(result, outcome='unknown', reason='non_accepting_job_conclusion')
    if conclusion == 'failure' and any(
            s.get('conclusion') == 'failure' and (s.get('name') == 'Set up job' or
            'actions/checkout@' in s.get('name', '')) for s in job.get('steps', [])):
        return dict(result, outcome='infrastructure_error', reason='setup_failed')
    tool = 'gh_run_view'
    try:
        log = get_logs(run_id, job['id'])
    except RetrievalError as error:
        result['diagnostics'].append(diagnostic(tool, error.category, error.hostname, **identity))
        if fallback is None:
            return dict(result, outcome='unavailable', reason='logs_unavailable', next_action=dict(
                operation='github_fetch_workflow_job_logs', repo_full_name=repository,
                job_id=job['id'], run_id=run_id, attempt=attempt, head=head))
        tool = 'github_connector_job_logs'
        try:
            if (fallback.get('repository'), fallback.get('run_id'), fallback.get('attempt'),
                    fallback.get('job_id')) != (repository, run_id, attempt, job['id']):
                raise RetrievalError('connector_identity_mismatch')
            log = connector_log(fallback.get('response'))
        except (RetrievalError, AttributeError) as error:
            category = error.category if isinstance(error, RetrievalError) else 'invalid_connector_envelope'
            result['diagnostics'].append(diagnostic(tool, category, **identity))
            return dict(result, outcome='unavailable', reason='all_log_routes_failed')
    result['diagnostics'].append(diagnostic(tool, 'retrieved', **identity))

    def incomplete(reason):
        if tool == 'gh_run_view' and fallback is not None:
            def incomplete_route(*_):
                raise RetrievalError('incomplete_standard_route_log')
            return inspect_job(repository, run, job, run_id, attempt, head, family,
                               incomplete_route, fallback)
        return dict(result, outcome='incomplete', reason=reason, next_action=dict(
            operation='github_fetch_workflow_job_logs', repo_full_name=repository,
            job_id=job['id'], run_id=run_id, attempt=attempt, head=head) if tool == 'gh_run_view' else None)

    # Failures need actual failure content; cancellation is handled before parsing.
    if conclusion == 'failure':
        try:
            failure_text = evidence_log_text(log, head)
        except ValueError:
            return incomplete('incomplete_native_failure_log')
        if re.search(r'^\*\* (?:BUILD|TEST) FAILED \*\*$', failure_text, re.M):
            return dict(result, outcome='verified_failed', reason='native_failure_in_complete_job_log')
        return dict(result, outcome='unknown', reason='failure_not_established_from_logs')
    steps = job.get('steps', [])
    native = [s for s in steps if s.get('name') == 'Build and test on an available simulator']
    if len(native) != 1 or native[0].get('conclusion') != 'success':
        return dict(result, outcome='incomplete', reason='mandatory_native_step_not_successful')
    try:
        parsed = log_evidence(log, head, family)
    except ValueError as error:
        return incomplete(str(error))
    if not parsed['build_succeeded'] or not parsed['test_succeeded']:
        return incomplete('mandatory_build_or_test_marker_missing')
    if parsed['tests'] < 1 or parsed['failed']:
        return dict(result, outcome='incomplete', reason='mandatory_native_results_not_established')
    return dict(result, outcome='verified_successful', reason='complete_native_log_verified', **parsed)


def diagnostics_artifacts(api, run_id, head, attempt, jobs):
    """Optional diagnostics do not override independently complete log evidence."""
    results = []
    try:
        artifacts = api.pages(f'actions/runs/{run_id}/artifacts', 'artifacts')
    except RetrievalError as error:
        return [diagnostic('gh_artifact_metadata', error.category, error.hostname, run_id=run_id, attempt=attempt)]
    for job in jobs:
        family = job['family']
        selected = [a for a in artifacts if a.get('name') == f'ios-diagnostics-{family}-{head}']
        identity = dict(run_id=run_id, attempt=attempt, job_id=job['job_id'], family=family)
        if len(selected) != 1:
            results.append(diagnostic('gh_artifact_metadata', 'missing_or_ambiguous_optional_artifact', **identity))
            continue
        artifact = selected[0]
        artifact_id = artifact.get('id')
        identity['artifact_id'] = artifact_id
        workflow = artifact.get('workflow_run', {})
        if (type(artifact_id) is not int or artifact.get('expired') is not False
                or workflow.get('id') != run_id or workflow.get('head_sha') != head):
            results.append(diagnostic('gh_artifact_metadata', 'artifact_identity_or_expiry_invalid', **identity))
            continue
        try:
            start, end, created = (datetime.fromisoformat(value.replace('Z', '+00:00'))
                                   for value in (job.get('started_at'), job.get('completed_at'),
                                                 artifact.get('created_at')))
            if not start <= created <= end:
                raise ValueError()
        except (AttributeError, TypeError, ValueError):
            results.append(diagnostic('gh_artifact_metadata', 'artifact_attempt_not_established', **identity))
            continue
        try:
            archive = api.artifact(artifact_id)
            with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
                entries = zipped.infolist()
                # Never extract paths or persist potentially sensitive log/archive content.
                if len(entries) > 10000 or sum(i.file_size for i in entries) > 256 * 1024 * 1024 or any(
                        Path(i.filename).is_absolute() or '..' in Path(i.filename).parts for i in entries):
                    raise RetrievalError('unsafe_or_oversized_artifact')
                if zipped.testzip() is not None:
                    raise RetrievalError('corrupt_artifact')
                summaries = [i for i in entries if i.filename.endswith('test-summary.log')]
                if len(summaries) != 1 or summaries[0].file_size > 1024 * 1024:
                    raise RetrievalError('optional_artifact_summary_missing')
                try:
                    parsed = evidence_summary(json.loads(zipped.read(summaries[0])), family)
                except (ValueError, UnicodeError):
                    raise RetrievalError('optional_artifact_summary_invalid') from None
                if job['outcome'] == 'verified_successful' and any(
                        parsed[k] != job.get(k) for k in parsed):
                    raise RetrievalError('contradictory_artifact_summary')
            results.append(diagnostic('gh_artifact_download', 'retrieved_archive_validated', **identity))
        except (RetrievalError, zipfile.BadZipFile, OSError, RuntimeError, zlib.error, NotImplementedError) as error:
            category = error.category if isinstance(error, RetrievalError) else 'invalid_artifact_archive'
            results.append(diagnostic('gh_artifact_download', category,
                                      error.hostname if isinstance(error, RetrievalError) else 'api.github.com', **identity))
    return results


def collect(api, repository, run_id, attempt, head, connector=None):
    try:
        run = api.api(f'actions/runs/{run_id}')
        jobs = api.pages(f'actions/runs/{run_id}/attempts/{attempt}/jobs', 'jobs')
        results = []
        for family in FAMILIES:
            matching = [j for j in jobs if j.get('name') == f'ios-build-test / ios-build-test ({family})']
            if len(matching) != 1:
                results.append(dict(family=family, job_id=None, outcome='incomplete', reason='missing_or_ambiguous_native_job'))
                continue
            job = matching[0]
            fallback = (connector or {}).get(str(job['id']))
            results.append(inspect_job(repository, run, job, run_id, attempt, head, family, api.logs, fallback))
        artifacts = diagnostics_artifacts(api, run_id, head, attempt, results)
        refreshed = api.api(f'actions/runs/{run_id}')
        if refreshed.get('head_sha') != head or refreshed.get('run_attempt') != attempt:
            for result in results:
                result.update(outcome='superseded', reason='run_changed_during_collection')
        for result in results:
            if result['outcome'] == 'verified_successful':
                fresh_job = api.api(f'actions/jobs/{result["job_id"]}')
                if (validate_identity(repository, refreshed, fresh_job, run_id, attempt, head,
                                      result['family'])[0] is not None
                        or fresh_job.get('status') != 'completed' or fresh_job.get('conclusion') != 'success'):
                    result.update(outcome='superseded', reason='job_changed_during_collection')
        for artifact in artifacts:
            if artifact['category'] == 'contradictory_artifact_summary':
                for result in results:
                    if result['job_id'] == artifact['job_id']:
                        result.update(outcome='incomplete', reason='contradictory_artifact_summary')
        success = all(r['outcome'] == 'verified_successful' for r in results)
        return dict(schema_version=1, repository=repository, run_id=run_id, attempt=attempt,
                    head=head, accepted=success, jobs=results, artifacts=artifacts,
                    blockers=[dict(family=r['family'], outcome=r['outcome'], reason=r['reason'])
                              for r in results if r['outcome'] != 'verified_successful'])
    except (RetrievalError, KeyError, TypeError, AttributeError) as error:
        return dict(schema_version=1, accepted=False, repository=repository, run_id=run_id,
                    attempt=attempt, head=head, jobs=[], artifacts=[], blockers=[dict(
                        outcome='unavailable', reason=error.category if isinstance(error, RetrievalError)
                        else 'invalid_authoritative_metadata')])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='clemarc/fava')
    parser.add_argument('--run', type=int, required=True)
    parser.add_argument('--attempt', type=int, required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--connector-responses', type=Path,
                        help='JSON object keyed by job ID; bound envelopes from current connector calls')
    args = parser.parse_args()
    if (not re.fullmatch('[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repository)
            or not re.fullmatch('[0-9a-f]{40}', args.head) or args.run < 1 or args.attempt < 1):
        parser.error('require repository, full head SHA and positive run/attempt')
    connector = json.loads(args.connector_responses.read_text()) if args.connector_responses else None
    result = collect(GitHub(args.repository), args.repository, args.run, args.attempt, args.head, connector)
    print(json.dumps(result, sort_keys=True, separators=(',', ':')))
    raise SystemExit(0 if result['accepted'] else 1)


if __name__ == '__main__':
    main()

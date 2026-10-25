"""Opt-in measurement only. No response bodies, credentials or persistent proof reuse."""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
import json
import os
from pathlib import Path
import re
import sys
import time
import uuid

ACTIVE = ContextVar('fava_sdd_measurement', default=None)
MODE = ContextVar('fava_sdd_measurement_mode', default=None)
PURPOSES = {'resolve', 'integration', 'recovery', 'diagnostic', 'benchmark', 'test'}


def historical_record(key, deduplicated=False):
    state = ACTIVE.get()
    if state is None:
        return
    state['historical_records_visited'] += 1
    seen = state['_historical']
    if key in seen:
        state['repeated_historical_object_visits'] += 1
        if not deduplicated:
            state['repeated_historical_object_inspections'] += 1
    seen.add(key)
    if deduplicated:
        state['per_invocation_deduplications'] += 1
    else:
        state['historical_object_inspections'] += 1


def immutable_object(kind, identity):
    state = ACTIVE.get()
    if state is not None:
        state['immutable_object_verifications'] += 1
        key = (kind, identity)
        if key in state['_immutable']:
            state['repeated_immutable_object_verifications'] += 1
        state['_immutable'].add(key)


@contextmanager
def github_request(args):
    """Measure the shared gh boundary; opaque CLI commands remain explicit."""
    state = ACTIVE.get()
    details = {'response': None, 'failed': False}
    if state is None:
        yield details
        return
    started = time.perf_counter()
    failed = False
    try:
        yield details
    except BaseException:
        failed = True
        raise
    finally:
        elapsed = time.perf_counter() - started
        state['github_commands'] += 1
        state['github_duration_seconds'] += elapsed
        if failed or details['failed']:
            state['github_errors'] += 1
        api = len(args) > 1 and args[0] == 'api'
        # gh api makes one request per returned page; gh pr view can issue an
        # opaque number of GraphQL requests. Never label command count as HTTP.
        if api and not failed and not details['failed']:
            count = len(details['response']) if '--paginate' in args and '--slurp' in args and isinstance(details['response'], list) else 1
            state['github_request_count_lower_bound'] += max(count, 1)
        else:
            if not failed and not details['failed']:
                state['github_request_count_lower_bound'] += 1
            state['github_request_count_exact'] = False
        endpoint = next((a for a in args if isinstance(a, str) and a.startswith('repos/')), '')
        immutable = re.fullmatch(r'repos/[^/]+/[^/]+/commits/([0-9a-f]{40})', endpoint)
        if immutable:
            immutable_object('github_commit', immutable[1])
        elif MODE.get() == 'live':
            state['live_gate_refresh_seconds'] += elapsed


def measured(name, historical=False, live=False):
    def decorate(function):
        @wraps(function)
        def call(*args, **kwargs):
            state = ACTIVE.get()
            if state is None:
                return function(*args, **kwargs)
            mode = 'historical' if historical == 'always' or historical and (
                kwargs.get('cutoff') is not None or len(args) > 4 and args[4] is not None) else ('live' if live else 'other')
            token = MODE.set(mode)
            started = time.perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                state['spans'].setdefault(name, dict(calls=0, seconds=0.0))
                state['spans'][name]['calls'] += 1
                state['spans'][name]['seconds'] += time.perf_counter() - started
                MODE.reset(token)
        return call
    return decorate


@contextmanager
def invocation(purpose, output=None):
    if output is None or ACTIVE.get() is not None:
        yield
        return
    # Purposes are caller labels only: disallow URLs, newlines and API text.
    if purpose not in PURPOSES:
        raise ValueError('measurement purpose must be an approved operation label')
    state = dict(schema_version=1, invocation_id=str(uuid.uuid4()), purpose=purpose,
                 observed_at=datetime.now(timezone.utc).isoformat(), wall_seconds=0.0,
                 historical_records_visited=0, historical_object_inspections=0,
                 repeated_historical_object_visits=0,
                 repeated_historical_object_inspections=0, per_invocation_deduplications=0,
                 immutable_object_verifications=0, repeated_immutable_object_verifications=0,
                 github_commands=0, github_request_count_lower_bound=0,
                 github_request_count_exact=True, github_duration_seconds=0.0,
                 live_gate_refresh_seconds=0.0, github_errors=0, retries=0,
                 invocation_failed=False, spans={}, _historical=set(), _immutable=set())
    token = ACTIVE.set(state)
    started = time.perf_counter()
    try:
        yield
    except SystemExit as error:
        state['invocation_failed'] = bool(error.code)
        raise
    except BaseException:
        state['invocation_failed'] = True
        raise
    finally:
        state['wall_seconds'] = time.perf_counter() - started
        ACTIVE.reset(token)
        payload = {k:v for k,v in state.items() if not k.startswith('_')}
        payload['github_request_count'] = (state['github_request_count_lower_bound']
                                           if state['github_request_count_exact'] else None)
        # Measurements must not replace a gate exception or convert a failed
        # validation into success. Output failure is a separate sanitized note.
        try:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
            try:
                os.write(fd, (json.dumps(payload, sort_keys=True, separators=(',', ':'))+'\n').encode())
            finally:
                os.close(fd)
        except OSError:
            print('SDD measurement output unavailable; gate result unchanged.', file=sys.stderr)

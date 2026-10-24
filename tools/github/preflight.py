"""Read-only Cloud capability evidence; never authorizes or retries mutations."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

STATES = {'supported', 'unsupported', 'authorization_blocked',
          'temporarily_unavailable', 'not_checked'}
COMMANDS = {
    'graphql': ['api', 'graphql'], 'pr_read': ['pr', 'view'],
    'pr_create': ['pr', 'create'], 'comment': ['pr', 'comment'],
    'merge': ['pr', 'merge'], 'logs': ['run', 'view'],
    'artifacts': ['run', 'download'],
}
CONNECTORS = {
    'pr_read': 'github_fetch_pr', 'pr_create': 'github_create_pull_request',
    'comment': 'github_add_comment_to_issue', 'merge': 'github_merge_pull_request',
    'logs': 'github_fetch_workflow_job_logs',
    'artifacts': 'github_download_workflow_artifact',
}
HELPERS = ['tools/github/prepare-commit.py',
           'tools/github/create-commit-on-branch.graphql',
           'tools/sdd/milestone.py', 'tools/sdd/integration.py',
           'tools/sdd/signatures.py', 'tools/sdd/github-web-flow.asc',
           '.github/checks/sdd.py', '.github/checks/native.py',
           '.github/checks/aggregate.py', '.github/checks/tooling.py']


def evidence(state, reason, **fields):
    assert state in STATES
    return dict(state=state, reason=reason, **fields)


def failure(text):
    """Classify in memory; never retain raw errors, URLs or response bodies."""
    text = text.lower()
    if any(s in text for s in ('unknown command', 'unknown flag', 'unrecognized option')):
        return evidence('unsupported', 'required_interface_missing')
    if any(s in text for s in ('proxyconnect', 'connection refused', 'socket: operation',
                               'timeout', 'timed out', 'resolve host', 'tls handshake',
                               'http 429', 'http 500', 'http 502', 'http 503', 'http 504',
                               'ipc connect call failed', 'no running gpg-agent')):
        return evidence('temporarily_unavailable', 'transport_or_service_failure')
    if any(s in text for s in ('http 401', 'http 403', 'bad credentials',
                               'requires authentication', 'resource not accessible',
                               'forbidden')):
        return evidence('authorization_blocked', 'authentication_or_permission_denied')
    return evidence('not_checked', 'unclassified_probe_failure')


class Probe:
    def __init__(self, root):
        self.root = root

    def run(self, args, env=None):
        try:
            result = subprocess.run(args, cwd=self.root, env=env, capture_output=True,
                                    text=True, timeout=20)
        except subprocess.TimeoutExpired:
            return evidence('temporarily_unavailable', 'probe_timeout'), ''
        except FileNotFoundError:
            return evidence('unsupported', 'executable_missing'), ''
        except OSError:
            return evidence('temporarily_unavailable', 'execution_blocked'), ''
        if result.returncode:
            return failure(result.stderr + result.stdout), ''
        return evidence('supported', 'probe_succeeded'), result.stdout.strip()


def graphql(probe, gh, repository, enabled):
    if not enabled:
        return evidence('not_checked', 'network_probe_not_requested')
    if not gh:
        return evidence('unsupported', 'gh_missing')
    if not os.environ.get('FAVA_GITHUB_API_TOKEN'):
        return evidence('authorization_blocked', 'configured_binding_missing')
    owner, name = repository.split('/')
    query = ('query { viewer { login } repository(owner:' + json.dumps(owner)
             + ',name:' + json.dumps(name) + ') { viewerPermission } }')
    status, output = probe.run([gh, 'api', 'graphql', '-f', 'query=' + query],
                              dict(os.environ, GH_TOKEN=os.environ['FAVA_GITHUB_API_TOKEN'],
                                   GH_DEBUG=''))
    if status['state'] != 'supported':
        return status
    try:
        data = json.loads(output)
        # Partial GraphQL data and HTTP 200 errors never establish readiness.
        if data.get('errors'):
            errors = data['errors']
            if isinstance(errors, list) and any(isinstance(error, dict) and (
                    error.get('type') in {'FORBIDDEN', 'UNAUTHORIZED'} or
                    isinstance(error.get('extensions'), dict) and
                    error['extensions'].get('code') in {'FORBIDDEN', 'UNAUTHORIZED'})
                    for error in errors):
                return evidence('authorization_blocked', 'graphql_permission_denied')
            return evidence('not_checked', 'graphql_errors')
        login = data['data']['viewer']['login']
        permission = data['data']['repository']['viewerPermission']
        if not isinstance(login, str) or not login or permission not in {
                'READ', 'TRIAGE', 'WRITE', 'MAINTAIN', 'ADMIN'}:
            raise ValueError()
    except (ValueError, KeyError, TypeError, AttributeError):
        return evidence('not_checked', 'incomplete_or_invalid_graphql_response')
    return evidence('supported', 'read_only_repository_probe', permission=permission)


def report(root, repository, network=False, connector_tools=None):
    probe = Probe(root)
    binaries = {}
    for name in ('git', 'gh', 'gpg', 'gpgconf', 'gpg-connect-agent'):
        path = shutil.which(name)
        status, output = probe.run([path, '--version']) if path else (
            evidence('unsupported', 'executable_missing'), '')
        # Only version banners are persisted, never arbitrary CLI response text.
        banner = output.splitlines()[0] if output else ''
        version = re.search(r'\b\d+\.\d+(?:\.\d+)?\b', banner)
        binaries[name] = dict(status, path=path, version=version[0] if version else None)
    commands = {}
    gh = binaries['gh']['path']
    for operation, args in COMMANDS.items():
        commands[operation] = (probe.run([gh, *args, '--help'])[0] if gh else
                               evidence('unsupported', 'gh_missing'))
    access = graphql(probe, gh, repository, network)
    connectors = {}
    routes = {}
    for operation, suffix in CONNECTORS.items():
        tool = 'mcp__codex_apps__' + suffix
        connectors[operation] = evidence(
            'not_checked' if connector_tools is None else
            'supported' if tool in connector_tools else 'unsupported',
            'inventory_not_supplied' if connector_tools is None else 'session_tool_inventory',
            tool=tool, authorization='not_checked')
        # Inventory/help prove exposed interfaces only. Read probes and exact
        # mutation evidence remain mandatory at the point of use.
        routes[operation] = dict(
            preferred='gh', preferred_interface=commands[operation]['state'],
            fallback=tool if connectors[operation]['state'] == 'supported' and
            operation != 'merge' else None,
            fallback_condition='read_authoritative_state_first' if operation in
            {'pr_create', 'comment'} else 'retrieval_failure',
            authorization='not_checked')
    routes['merge'].update(fallback=None, fallback_condition='no_unguarded_merge_fallback')
    routes['publication'] = dict(preferred='gh_graphql_createCommitOnBranch', fallback=None,
                                 authorization='not_checked',
                                 ambiguous_response='inspect_branch_parent_tree_message_signature_before_retry')
    state = {}
    git = binaries['git']['path']
    for key, args in {
        'head': ['rev-parse', '--verify', 'HEAD'],
        'branch': ['symbolic-ref', '--quiet', '--short', 'HEAD'],
        'worktrees': ['worktree', 'list', '--porcelain'],
        'changes': ['status', '--porcelain'],
    }.items():
        status, output = probe.run([git, *args]) if git else (
            evidence('unsupported', 'git_missing'), '')
        state[key] = dict(status)
        if status['state'] == 'supported':
            state[key]['value'] = output
    # Use the existing pinned-key verifier, including its no-autostart policy.
    signing = evidence('not_checked', 'head_or_gpg_unavailable')
    if state['head']['state'] == 'supported' and binaries['gpg']['state'] == 'supported':
        try:
            helper = root / 'tools/sdd/signatures.py'
            if not helper.is_file():
                raise FileNotFoundError()
            spec = importlib.util.spec_from_file_location('fava_preflight_signatures', helper)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            valid = module.verify(root, state['head']['value'])
            signing = evidence('supported' if valid else 'not_checked',
                               'pinned_head_signature_verified' if valid else 'head_signature_not_verified')
        except FileNotFoundError:
            signing = evidence('unsupported', 'signature_verifier_prerequisite_missing')
        except (OSError, ImportError, subprocess.SubprocessError):
            signing = evidence('temporarily_unavailable', 'signature_verifier_unavailable')
    agent = evidence('not_checked', 'public_key_verification_does_not_require_private_agent')
    agent_path = binaries['gpg-connect-agent']['path']
    if agent_path:
        agent = probe.run([agent_path, '--no-autostart', '/bye'])[0]
    permission = access.get('permission')
    publication = evidence('not_checked', 'mutation_and_workflow_permissions_require_actual_publication')
    if access['state'] != 'supported':
        publication = dict(access)
    elif permission not in {'WRITE', 'MAINTAIN', 'ADMIN'}:
        publication = evidence('authorization_blocked', 'repository_contents_write_not_available')
    return dict(schema_version=1, observed_at=datetime.now(timezone.utc).isoformat(),
                repository=repository, executables=binaries, gh_commands=commands,
                graphql_access=access, publication=publication, connectors=connectors,
                routes=routes, git=state, signing=signing, gpg_agent=agent,
                helpers={p: evidence('supported' if (root / p).is_file() else 'unsupported',
                                     'file_present' if (root / p).is_file() else 'file_missing')
                         for p in HELPERS})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='clemarc/fava')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--network', action='store_true', help='read-only authorized GraphQL probe')
    parser.add_argument('--connector-tools', type=Path, help='JSON array of current session tool names')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repository):
        parser.error('repository must be owner/name')
    inventory = None
    if args.connector_tools:
        inventory = json.loads(args.connector_tools.read_text())
        if not isinstance(inventory, list) or not all(isinstance(x, str) for x in inventory):
            parser.error('connector inventory must be an array of tool names')
    print(json.dumps(report(args.root.resolve(), args.repository, args.network, inventory),
                     sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    main()

"""One owner-adopted historical trailer reconciliation; no general exception API."""
import json
import subprocess

from signatures import owner_merge

RECORD_PATH = 'docs/decisions/003-r35-preparation-merge-reconciliation.json'
RECORD = {
    'schema': 1,
    'milestone': 'R3.5',
    'preparation_pr': 'https://github.com/clemarc/fava/pull/14',
    'destination': 'milestone/r3.5',
    'merge': '9a2d3272a0e3d88952946459d7864b72affdc62f',
    'parents': [
        '922b9c9ab0c25559bfd327fff1b74127e1952f31',
        '2817c07c11ba5ba718b53cb267786c0123922137',
    ],
    'tree': 'b2661ee7a90e06057e01e49a9105e3d53de0bdcd',
    'message': 'docs: prepare R3.5 retained history and contextual launch (#14)\n',
    'accepted_trailer': 'SDD-Type: planning',
    'activation': 'Signed owner governance merge into main; unchanged record in validation base and head.',
}
RECORD_TEXT = json.dumps(RECORD, indent=2) + '\n'


def record_at(root, ref, git):
    try:
        return git(root, 'show', f'{ref}:{RECORD_PATH}') == RECORD_TEXT
    except subprocess.CalledProcessError:
        return False


def historical_merge(root, sha, git):
    """Match all immutable identity fields and independently verify the owner."""
    if sha != RECORD['merge']:
        return False
    from sdd import implementation_paths
    try:
        return (git(root, 'show', '-s', '--format=%P', sha).split() == RECORD['parents']
                and git(root, 'rev-parse', sha + '^{tree}').strip() == RECORD['tree']
                and git(root, 'rev-parse', sha + '^2^{tree}').strip() == RECORD['tree']
                and git(root, 'show', '-s', '--format=%B', sha) == RECORD['message']
                and owner_merge(root, sha, git)
                and not implementation_paths(git(root, 'diff', '--name-only', sha + '^1', sha).splitlines()))
    except subprocess.CalledProcessError:
        return False


def adoption_merge(root, base, head, git):
    """Find signed adoption in the base, including history imported as a parent.

    CI proves signed ancestry offline; the resolver also verifies the actual PR
    destination is main. As elsewhere, the shared owner identity is a process
    boundary, not proof that a human operated the credential.
    """
    if not record_at(root, base, git) or not record_at(root, head, git):
        return None
    from sdd import implementation_paths, trailers
    matches = []
    for sha in git(root, 'rev-list', '--merges', base).splitlines():
        parents = git(root, 'show', '-s', '--format=%P', sha).split()
        if len(parents) != 2 or not record_at(root, sha, git) or not record_at(root, parents[1], git):
            continue
        # An edited/different previous record is not a fresh adoption either.
        try:
            git(root, 'cat-file', '-e', f'{parents[0]}:{RECORD_PATH}')
            continue
        except subprocess.CalledProcessError:
            pass
        try:
            git(root, 'merge-base', '--is-ancestor', sha, head)
        except subprocess.CalledProcessError:
            continue
        paths = git(root, 'diff', '--name-only', parents[0], sha).splitlines()
        if (owner_merge(root, sha, git)
                and trailers(git(root, 'show', '-s', '--format=%B', sha)).get('SDD-Type') in [['process'], ['tooling']]
                and not implementation_paths(paths)
                and git(root, 'rev-parse', sha + '^{tree}').strip()
                    == git(root, 'rev-parse', parents[1] + '^{tree}').strip()):
            matches.append(sha)
    return matches[0] if len(matches) == 1 else None


def commit_message(root, base, head, sha, git):
    """Supply only the recorded missing trailer after adopted, signed proof.

    The original commit/message is never modified. Pending-message validation
    still calls validate_commit directly and cannot obtain this exception.
    """
    message = git(root, 'show', '-s', '--format=%B', sha)
    if historical_merge(root, sha, git) and adoption_merge(root, base, head, git):
        return message.rstrip() + '\n\n' + RECORD['accepted_trailer'] + '\n'
    return message

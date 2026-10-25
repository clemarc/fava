"""Select review gates from owner-adopted target history, never a report claim."""
import json
import subprocess

from signatures import owner_merge
from metrics import historical_record, measured

LEGACY = 'independent-and-codex-v1'
CODEX_ONLY = 'codex-only-v1'
RECORD_PATH = 'docs/decisions/004-codex-only-review-policy.json'
RECORD = {
    'schema': 1,
    'review_policy': CODEX_ONLY,
    'activation': 'Signed owner governance merge into main, imported unchanged into the milestone target before new integration evidence.',
}
RECORD_TEXT = json.dumps(RECORD, indent=2) + '\n'


def record(root, ref, git):
    try:
        return git(root, 'show', f'{ref}:{RECORD_PATH}')
    except subprocess.CalledProcessError:
        return None


@measured('review_policy_history', historical='always')
def policy_for(root, target, head, git, verify_pr=None):
    """Old targets retain old gates; new policy needs signed, actual main adoption.

    The complete introduced policy bytes must survive in both target and head.
    An implementation PR cannot activate its own new policy, and replaying an
    old integration continues to inspect its original pre-integration target.
    """
    target_record = record(root, target, git)
    if target_record is None:
        return LEGACY
    if target_record != RECORD_TEXT or record(root, head, git) != RECORD_TEXT:
        raise ValueError('review policy record is unsupported, altered or absent from head')
    if verify_pr is None:
        from milestone import merged_pr
        verify_pr = merged_pr
    from sdd import implementation_paths, trailers
    matches = []
    for sha in git(root, 'rev-list', '--merges', target).splitlines():
        historical_record(('review_policy', sha))
        parents = git(root, 'show', '-s', '--format=%P', sha).split()
        if (len(parents) != 2 or record(root, sha, git) != RECORD_TEXT
                or record(root, parents[1], git) != RECORD_TEXT
                or record(root, parents[0], git) is not None):
            continue
        try:
            git(root, 'merge-base', '--is-ancestor', sha, head)
        except subprocess.CalledProcessError:
            continue
        paths = git(root, 'diff', '--name-only', parents[0], sha).splitlines()
        if (not owner_merge(root, sha, git)
                or trailers(git(root, 'show', '-s', '--format=%B', sha)).get('SDD-Type') not in [['process'], ['tooling']]
                or implementation_paths(paths)
                or git(root, 'rev-parse', sha + '^{tree}').strip()
                    != git(root, 'rev-parse', parents[1] + '^{tree}').strip()):
            continue
        try:
            verify_pr('clemarc/fava', sha, 'main')
        except ValueError:
            continue
        matches.append(sha)
    if len(matches) != 1:
        raise ValueError('review policy needs one signed owner-adopted PR merge into main in target history')
    return CODEX_ONLY

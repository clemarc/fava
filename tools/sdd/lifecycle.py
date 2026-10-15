"""Git proof that reviewed milestone planning preceded source implementation."""
import json
from pathlib import Path
import re
import subprocess

from signatures import owner_merge


def planning_ref(root, base, sha, feature, git):
    parent = git(root, 'rev-parse', sha + '^1').strip()
    try:
        ledger = json.loads(git(root, 'show', f'{parent}:{feature}/execution.json'))
    except subprocess.CalledProcessError:
        parents = git(root, 'show', '-s', '--format=%P', sha).split()
        if len(parents) != 2:
            return base  # Legacy normal lifecycle; no new pilot exception.
        # Main promotion's first parent deliberately lacks milestone planning.
        # The reviewed execution history must precede it on the second parent.
        parent = parents[1]
        try:
            ledger = json.loads(git(root, 'show', f'{parent}:{feature}/execution.json'))
        except subprocess.CalledProcessError:
            return base
    except json.JSONDecodeError:
        raise ValueError('invalid execution ledger')
    from milestone import normalize, resolve, ancestor
    milestone = normalize(ledger.get('milestone', ''))
    if ledger.get('feature') != feature or ledger.get('milestone_branch') != 'milestone/' + milestone.lower():
        raise ValueError('execution identity contradicts feature/branch')
    baseline, planning = ledger.get('specification_base', ''), ledger.get('planning_revision', '')
    if not all(isinstance(ref, str) and re.fullmatch(r'[0-9a-f]{40}', ref) for ref in [baseline, planning]):
        raise ValueError('implementation requires full specification_base and planning_revision SHAs')
    if not ancestor(root, baseline, base) or not ancestor(root, planning, parent):
        raise ValueError('approved main baseline/planning merge must precede implementation')
    if not owner_merge(root, planning, git):
        raise ValueError('planning_revision must be an independently verified signed owner two-parent merge')
    first = git(root, 'rev-parse', planning + '^1').strip()
    second = git(root, 'rev-parse', planning + '^2').strip()
    if not ancestor(root, baseline, first):
        raise ValueError('preparation merge target lacks approved specification baseline')
    roadmaps = {p: git(root, 'show', f'{baseline}:{p}') for p in
                git(root, 'ls-tree', '-r', '--name-only', baseline).splitlines() if p.endswith('/roadmap.md')}
    if resolve(milestone, roadmaps)['feature'] != feature:
        raise ValueError('ledger milestone is not the canonical roadmap directory')
    from sdd import implementation_paths
    if implementation_paths(git(root, 'diff', '--name-only', first, planning).splitlines()):
        raise ValueError('preparation merge contains application implementation')
    for artifact in ['spec.md', 'plan.md', 'tasks.md', 'execution.json', 'preparation-review.md']:
        git(root, 'cat-file', '-e', f'{second}:{feature}/{artifact}')
    prep_ledger = json.loads(git(root, 'show', f'{second}:{feature}/execution.json'))
    if any(prep_ledger.get(key) != ledger.get(key) for key in ['milestone', 'feature', 'milestone_branch', 'specification_base']):
        raise ValueError('reviewed preparation ledger contradicts execution baseline')
    contract = git(root, 'show', f'{baseline}:{feature}/spec.md')
    if any(git(root, 'show', f'{ref}:{feature}/spec.md') != contract for ref in [first, second, planning, parent]):
        raise ValueError('approved specification baseline changed before implementation')
    for artifact in ['plan.md', 'tasks.md']:
        approved = git(root, 'show', f'{planning}:{feature}/{artifact}')
        normalize = lambda text: re.sub(r'^- \[[ xX]\]', '- [ ]', text, flags=re.M) if artifact == 'tasks.md' else text
        if any(normalize(git(root, 'show', f'{ref}:{feature}/{artifact}')) != normalize(approved) for ref in [parent, sha]):
            raise ValueError('plan/task mappings changed without a new owner-reviewed planning revision')
    # First preparation has no implementation. Later owner-reviewed amendments
    # may follow already reviewed source, but may not introduce source themselves.
    # Validate preceding target history separately through each commit's own proof.
    try:
        previous = json.loads(git(root, 'show', f'{first}:{feature}/execution.json'))
        prior_review = previous.get('planning_revision')
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        prior_review = None
    earlier = first if prior_review else baseline
    if prior_review and (not ancestor(root, prior_review, first) or not owner_merge(root, prior_review, git)):
        raise ValueError('planning amendment lacks a verified preceding review')
    for introduced in git(root, 'rev-list', f'{earlier}..{planning}').splitlines():
        paths = git(root, 'diff-tree', '--no-commit-id', '-r', '--name-only',
                    introduced + '^1', introduced).splitlines()
        if implementation_paths(paths):
            raise ValueError('source implementation occurred before reviewed planning')
    return planning

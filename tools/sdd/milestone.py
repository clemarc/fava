"""Shared read-only milestone resolution. Branch creation is a separate guarded step."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '.github/checks'))
from sdd import FEATURE, ROADMAP_ID, git, status, task_rows
from signatures import owner_merge


def normalize(value):
    value = value.strip().upper()
    if not re.fullmatch(ROADMAP_ID, value):
        raise ValueError('expected milestone Rn or Rn.n; case/outer whitespace normalize, digits do not')
    return value


def resolve(identifier, roadmaps):
    ident = normalize(identifier)
    matches = []
    for path, text in roadmaps.items():
        for line in text.splitlines():
            if re.match(r'^\|\s*R', line):
                cells = [x.strip() for x in line.strip('|').split('|')]
                if len(cells) != 7 or not re.fullmatch(ROADMAP_ID, cells[0]):
                    raise ValueError(f'{path}: malformed roadmap row')
                if cells[0] == ident:
                    if not re.fullmatch('specs/' + FEATURE, cells[6]):
                        raise ValueError(f'{ident}: invalid canonical directory')
                    matches.append(dict(id=ident, roadmap=path, feature=cells[6],
                                        scope=cells[3], deferred=cells[4],
                                        dependencies=[] if cells[5] == 'none' else re.findall(ROADMAP_ID, cells[5])))
    if len(matches) != 1:
        raise ValueError(f'{ident}: ' + ('unknown milestone' if not matches else 'ambiguous milestone across roadmap rows'))
    result = matches[0]
    lower = ident.lower()
    result.update(milestone_branch='milestone/' + lower,
                  preparation_branch='prepare/' + lower,
                  task_branch_prefix='task/' + lower + '/',
                  checkpoint_branch_prefix='checkpoint/' + lower + '/',
                  ledger=result['feature'] + '/execution.json')
    return result


def read(root, ref, path):
    return git(root, 'show', f'{ref}:{path}')


def ancestor(root, earlier, later):
    try:
        git(root, 'merge-base', '--is-ancestor', earlier, later)
        return True
    except subprocess.CalledProcessError:
        return False


def approval_merge(root, ref, path):
    """Find actual signed owner first-parent merge carrying the current artifact."""
    current = read(root, ref, path)
    for sha in git(root, 'log', '--first-parent', '--format=%H', ref, '--', path).splitlines():
        if owner_merge(root, sha, git) and read(root, sha, path) == current:
            return sha
    raise ValueError(f'{path}: no signed owner merge for this baseline; draft/status text is not approval')


def github(*args):
    if not os.environ.get('FAVA_GITHUB_API_TOKEN'):
        raise ValueError('missing configured FAVA_GITHUB_API_TOKEN')
    env = dict(os.environ, GH_TOKEN=os.environ['FAVA_GITHUB_API_TOKEN'], GH_DEBUG='')
    result = subprocess.run(['gh', *args], env=env, capture_output=True, text=True)
    if result.returncode:
        # Do not echo command environment, HTTP headers or credential-bearing output.
        raise ValueError('GitHub inspection failed; inspect safe CLI/runtime diagnostics before retrying')
    return json.loads(result.stdout)


def merged_pr(repository, sha, target):
    prs = github('api', f'repos/{repository}/commits/{sha}/pulls')
    matches = [p for p in prs if p.get('merged_at') and p['merge_commit_sha'] == sha
               and p['base']['ref'] == target]
    if len(matches) != 1:
        raise ValueError(f'{sha}: expected one merged PR into {target}')
    pr = github('api', f'repos/{repository}/pulls/{matches[0]["number"]}')
    if not pr.get('merged_by') or pr['merged_by']['login'] != 'clemarc':
        raise ValueError(f'{sha}: missing owner merge evidence')
    return pr['html_url']


def latest_preparation(result):
    merged = [p for p in result['prs'] if p['head'] == result['preparation_branch'] and p['merged']]
    if not merged:
        raise ValueError('owner-reviewed preparation PR must merge into milestone before implementation')
    # REST lists newest first by creation, which is not merge order. Explicit
    # merge chronology selects an amendment regardless of API response order.
    latest = max(merged, key=lambda p: (p['merged'], p['number']))
    if any(p['merged'] == latest['merged'] and p['merge_sha'] != latest['merge_sha'] for p in merged):
        raise ValueError('ambiguous preparation merge chronology; inspect ancestry/owner decision')
    return latest


def inspect(root, identifier, phase):
    repository = 'clemarc/fava'
    main = github('api', f'repos/{repository}/git/ref/heads/main')['object']['sha']
    # Fetch explicitly; snapshots from a previous conversation are never inputs.
    subprocess.run(['git', '-C', str(root), 'fetch', '--prune', 'origin',
                    '+refs/heads/*:refs/remotes/origin/*'], check=True, capture_output=True)
    if git(root, 'rev-parse', 'origin/main').strip() != main:
        raise ValueError('main moved during inspection; repeat before selecting a branch')
    paths = git(root, 'ls-tree', '-r', '--name-only', main).splitlines()
    result = resolve(identifier, {p: read(root, main, p) for p in paths if p.endswith('/roadmap.md')})
    feature = result['feature']
    try:
        spec = read(root, main, feature + '/spec.md')
    except subprocess.CalledProcessError:
        raise ValueError(f'{result["id"]}: specification absent from main; owner specification merge is prerequisite')
    if status(spec) == 'completed':
        raise ValueError(f'{result["id"]}: completed milestone is frozen')
    expected = f'Parent roadmap: {result["roadmap"]} → entry {result["id"]}'
    if expected not in spec:
        raise ValueError('canonical roadmap/spec identity mismatch')
    result['main_sha'] = main
    result['approvals'] = {}
    for label, path in [('roadmap', result['roadmap']), ('specification', feature + '/spec.md'),
                        ('governance', 'docs/process/sdd-v2.md')]:
        try:
            sha = approval_merge(root, main, path)
        except subprocess.CalledProcessError:
            raise ValueError(f'{path}: owner SDD v2 governance merge into main is prerequisite')
        result['approvals'][label] = {'sha': sha, 'pr': merged_pr(repository, sha, 'main')}
    result['dependency_evidence'] = {}
    roadmaps = {p: read(root, main, p) for p in paths if p.endswith('/roadmap.md')}
    for dep in result['dependencies']:
        directory = resolve(dep, roadmaps)['feature']
        try:
            rows = task_rows(read(root, main, directory + '/tasks.md'))
            read(root, main, directory + '/verification.md')
            sha = approval_merge(root, main, directory + '/tasks.md')
        except subprocess.CalledProcessError:
            raise ValueError(f'{dep}: integrated tasks/verification missing')
        if not rows or not all(row[1] for row in rows):
            raise ValueError(f'{dep}: implementation dependencies not integrated')
        result['dependency_evidence'][dep] = {'sha': sha, 'pr': merged_pr(repository, sha, 'main'),
                                             'verification': directory + '/verification.md'}
    result['branches'] = {line.split()[1]: line.split()[0] for line in
                          git(root, 'for-each-ref', '--format=%(objectname) %(refname)',
                              'refs/heads', 'refs/remotes/origin').splitlines()}
    # All pages, including closed/merged PRs: do not reopen retired preparations.
    result['prs'] = github('api', '--paginate', '--slurp', f'repos/{repository}/pulls?state=all&per_page=100')
    result['prs'] = [dict(number=p['number'], url=p['html_url'], state=p['state'],
                          merged=p['merged_at'], head=p['head']['ref'], base=p['base']['ref'],
                          sha=p['head']['sha'], merge_sha=p.get('merge_commit_sha')) for page in result['prs'] for p in page
                     if p['head']['ref'] in {result['milestone_branch'], result['preparation_branch']}
                     or p['head']['ref'].startswith((result['task_branch_prefix'], result['checkpoint_branch_prefix']))]
    target_ref = 'refs/remotes/origin/' + result['milestone_branch']
    target = result['branches'].get(target_ref)
    result['target_sha'] = target or main
    result['execution'] = None
    if target:
        if not ancestor(root, result['approvals']['specification']['sha'], target):
            raise ValueError('milestone branch does not contain approved specification baseline')
        if read(root, target, feature + '/spec.md') != spec:
            raise ValueError('milestone branch contract differs from approved main specification')
        try:
            result['execution'] = json.loads(read(root, target, result['ledger']))
        except subprocess.CalledProcessError:
            pass
    prep_ref = 'refs/remotes/origin/' + result['preparation_branch']
    if not result['execution'] and prep_ref in result['branches']:
        try:
            result['execution'] = json.loads(read(root, prep_ref, result['ledger']))
        except subprocess.CalledProcessError:
            pass
    reconcile(result, phase)
    if phase == 'implement':
        preparation = latest_preparation(result)
        merge = preparation['merge_sha']
        if not target or not ancestor(root, merge, target) or not owner_merge(root, merge, git):
            raise ValueError('reviewed preparation merge is absent from target or lacks signed owner proof')
        result['preparation_approval'] = {'sha': merge, 'pr': merged_pr(repository, merge, result['milestone_branch'])}
    if result['execution']:
        from ledger import validate as validate_ledger
        execution_ref = target
        try:
            read(root, execution_ref, result['ledger'])
        except subprocess.CalledProcessError:
            execution_ref = result['branches'].get(prep_ref)
        problems = validate_ledger(result['execution'], feature, read(root, execution_ref, feature + '/tasks.md'))
        if problems:
            raise ValueError('inconsistent execution state: ' + '; '.join(problems))
        for ident, record in result['execution']['tasks'].items():
            if record['state'] == 'integrated':
                if not ancestor(root, record['merge_sha'], target):
                    raise ValueError(f'{ident}: recorded integration is not in current target')
                actual_pr = merged_pr(repository, record['merge_sha'], result['milestone_branch'])
                if record['pr'] != actual_pr:
                    raise ValueError(f'{ident}: ledger PR does not match actual merged integration')
    return result


def reconcile(result, phase):
    ledger = result.get('execution')
    if ledger:
        if ledger.get('milestone') != result['id'] or ledger.get('feature') != result['feature'] or ledger.get('milestone_branch') != result['milestone_branch']:
            raise ValueError('ledger identity/branch contradicts canonical roadmap')
        if ledger.get('state') == 'completed':
            raise ValueError('completed execution cannot be reopened')
    for pr in result.get('prs', []):
        expected = 'main' if pr['head'] == result['milestone_branch'] else result['milestone_branch']
        if pr['base'] != expected:
            raise ValueError(f'PR #{pr["number"]}: wrong target {pr["base"]}, expected {expected}')
    prep = [p for p in result.get('prs', []) if p['head'] == result['preparation_branch']]
    if len([p for p in prep if p['state'] == 'open']) > 1:
        raise ValueError('duplicate preparation PRs')
    if phase == 'prepare' and any(p['merged'] for p in prep):
        raise ValueError('preparation already merged; use implementation, or owner-reviewed planning amendment')
    if phase == 'prepare' and prep and not any(p['state'] == 'open' for p in prep):
        raise ValueError('preparation PR retired/closed; owner decision required before reopening')
    if phase == 'implement' and not any(p['merged'] for p in prep):
        raise ValueError('owner-reviewed preparation PR must merge into milestone before implementation')


def checkout(root, result, branch):
    """Only called after live inspect. Never reset, force-switch or overwrite."""
    if git(root, 'status', '--porcelain').strip():
        raise ValueError('dirty checkout; preserve edits and use an isolated clean checkout')
    if branch not in {result['milestone_branch'], result['preparation_branch']}:
        raise ValueError('checkout helper permits only resolved integration/preparation branches')
    local = result['branches'].get('refs/heads/' + branch)
    remote = result['branches'].get('refs/remotes/origin/' + branch)
    parent = remote or result['target_sha']
    if branch == result['milestone_branch'] and not remote:
        parent = result['main_sha']
    if local and local != parent:
        raise ValueError('local/remote branch divergence; inspect unpublished work instead of resetting')
    if local:
        subprocess.run(['git', '-C', str(root), 'switch', branch], check=True)
    else:
        subprocess.run(['git', '-C', str(root), 'switch', '-c', branch, parent], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('identifier')
    parser.add_argument('--phase', choices=['prepare', 'implement'], required=True)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--checkout', choices=['milestone', 'preparation'])
    args = parser.parse_args()
    try:
        result = inspect(args.root, args.identifier, args.phase)
        if args.checkout:
            checkout(args.root, result, result[args.checkout + '_branch'])
        result['SPECIFY_FEATURE_DIRECTORY'] = str(args.root.resolve() / result['feature'])
        print(json.dumps(result, indent=2))
    except (ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        parser.exit(1, f'STOP: {error}\n')


if __name__ == '__main__':
    main()

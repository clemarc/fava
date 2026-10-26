"""Shared read-only milestone resolution. Branch creation is a separate guarded step."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '.github/checks'))
from sdd import FEATURE, ROADMAP_ID, git, status, task_rows
from signatures import owner_merge


# This is an immutable reconciliation record, not a second destination policy.
# PR #41 was the one automatic merge used to import C015 into the already-open
# T005 branch. Its reverse destination is otherwise forbidden. Keeping every
# identifying field here makes any later reverse-target PR fail closed.
TARGET_IMPORT_PR_RECONCILIATIONS = {
    'R3.5': {
        41: {
            'url': 'https://github.com/clemarc/fava/pull/41',
            'head': 'milestone/r3.5',
            'sha': '195631baf6deb20fcfce595fb43287cbde6a6206',
            'base': 'task/r3.5/t005',
            'merge_sha': '611f56ebac503c206c8c310161a6f3d6bcbceb36',
        },
    },
}


def reconciled_target_import_pr(result, pr):
    """Accept the one owner-authorized historical reverse target import only."""
    expected = TARGET_IMPORT_PR_RECONCILIATIONS.get(result['id'], {}).get(pr['number'])
    if not expected:
        return False
    return (pr.get('state') == 'closed' and bool(pr.get('merged'))
            and all(pr.get(key) == value for key, value in expected.items()))


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
    def matches_merge(pr):
        return (pr.get('merged_at') and pr.get('merge_commit_sha') == sha
                and pr.get('base', {}).get('ref') == target)

    prs = github('api', f'repos/{repository}/commits/{sha}/pulls')
    matches = [pr for pr in prs if matches_merge(pr)]
    if not matches:
        # Commit association can omit merges into non-default branches.
        # Inspect all closed PR pages; titles and ledger claims are not proof.
        pages = github('api', '--paginate', '--slurp',
                       f'repos/{repository}/pulls?state=closed&per_page=100')
        matches = [pr for page in pages for pr in page if matches_merge(pr)]
    if len(matches) != 1:
        raise ValueError(f'{sha}: expected one merged PR into {target}')
    pr = github('api', f'repos/{repository}/pulls/{matches[0]["number"]}')
    if not matches_merge(pr) or pr.get('merged') is not True:
        raise ValueError(f'{sha}: merged PR identity changed during inspection')
    if not pr.get('merged_by') or pr['merged_by']['login'] != 'clemarc':
        raise ValueError(f'{sha}: missing owner merge evidence')
    return pr['html_url']


def integrated_task_errors(root, feature, branch, ident, record, target, verified=None):
    """Bind a completed record to this task's source PR, merge and report."""
    from ledger import task_merge_errors
    verified = verified if verified is not None else set()
    key = (feature, branch, ident, json.dumps(record, sort_keys=True), target)
    if key in verified:
        return []
    errors = task_merge_errors(root, feature, ident, record, target, git)
    if errors:
        return errors
    sha = record['merge_sha']
    actual_url = merged_pr('clemarc/fava', sha, branch)
    if record.get('pr') != actual_url:
        return [ident + ': ledger PR does not match actual merged integration']
    number = actual_url.rsplit('/', 1)[-1]
    pr = github('api', f'repos/clemarc/fava/pulls/{number}')
    parents = git(root, 'show', '-s', '--format=%P', sha).split()
    signature = github('api', f'repos/clemarc/fava/commits/{sha}')['commit']['verification']
    if (pr['head']['sha'] != parents[1] or not signature.get('verified')
            or signature.get('reason') != 'valid'):
        return [ident + ': task PR head/verified merge mismatch']
    comment_id = record.get('integration_comment')
    if not isinstance(comment_id, int) or isinstance(comment_id, bool):
        return [ident + ': exact task PR evidence comment required']
    try:
        from integration import assess_revision, immutable_comment, timestamp
        comment = github('api', f'repos/clemarc/fava/issues/comments/{comment_id}')
        evidence = json.loads(comment['body'])
        cutoff = timestamp(pr['merged_at'])
        valid = (immutable_comment(comment, int(number), cutoff,
                                   timestamp(git(root, 'show', '-s', '--format=%cI', parents[1]).strip()))
                 and comment.get('html_url') in record.get('evidence', [])
                 and evidence.get('validated_head') == parents[1]
                 and evidence.get('validated_target') == parents[0]
                 and ident in evidence.get('tasks', [])
                 and pr['merge_commit_sha'] == sha and pr['base']['ref'] == branch)
        if not valid:
            return [ident + ': evidence is not bound to this task and merged PR head/target before integration']
        canonical = json.loads(read(root, parents[0], feature + '/execution.json'))
        context = dict(id=canonical['milestone'], feature=feature, ledger=feature + '/execution.json',
                       milestone_branch=branch, task_branch_prefix='task/' + canonical['milestone'].lower() + '/',
                       checkpoint_branch_prefix='checkpoint/' + canonical['milestone'].lower() + '/',
                       target_sha=parents[0], main_sha=canonical['specification_base'], execution=canonical,
                       preparation_approval={'sha': canonical['planning_revision']})
        retained = dict(number=int(number), state='MERGED', isDraft=False, headRefName=pr['head']['ref'],
                        headRefOid=parents[1], baseRefName=branch, baseRefOid=parents[0])
        _, errors = assess_revision(root, context, retained, comment_id, pr['merged_at'], verified)
        if not errors:
            verified.add(key)
        return [ident + ': ' + error for error in errors]
    except (ValueError, TypeError, KeyError, AttributeError, subprocess.CalledProcessError) as error:
        return [ident + ': incomplete retained integration proof (' + str(error) + ')']


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


def preparation_limit(record, number, milestone, before):
    """Verify a preparation grant as it existed at the relevant publication."""
    from ledger import AUTOMATIC_CORRECTION_LIMIT
    from integration import timestamp
    authorization = record.get('owner_extra_cycles')
    if not isinstance(authorization, dict) or type(authorization.get('comment_id')) is not int:
        return AUTOMATIC_CORRECTION_LIMIT
    comment = github('api', f'repos/clemarc/fava/issues/comments/{authorization["comment_id"]}')
    try:
        approval = json.loads(comment['body'])
        limit = approval.get('max_cycles')
        if (comment.get('issue_url') == f'https://api.github.com/repos/clemarc/fava/issues/{number}'
                and comment.get('user', {}).get('login') == 'clemarc'
                and comment.get('created_at') == comment.get('updated_at')
                and timestamp(comment['created_at']) < before
                and approval.get('type') == 'fava-correction-authorization'
                and approval.get('phase') == 'prepare' and approval.get('milestone') == milestone
                and type(limit) is int and limit > AUTOMATIC_CORRECTION_LIMIT):
            return limit
    except (ValueError, TypeError, AttributeError, KeyError):
        pass
    return AUTOMATIC_CORRECTION_LIMIT


def preparation_progress(root, result):
    """Resume budget from protected signed prep history, never prior chat."""
    pending = [p for p in result['prs'] if p['head'] == result['preparation_branch'] and p['state'] == 'open']
    if not pending:
        return None
    if len(pending) != 1:
        raise ValueError('ambiguous open preparation PRs')
    pr = pending[0]
    record = (result.get('execution') or {}).get('preparation_prs', {}).get(str(pr['number']))
    return preparation_revision_progress(root, result, pr, record)


def preparation_revision_progress(root, result, pr, record, cutoff=None, verification_base=None):
    """Verify one explicit preparation revision, whether open or already merged."""
    from ledger import AUTOMATIC_CORRECTION_LIMIT, transition_errors, preparation_round_errors
    if not record or record.get('branch') != result['preparation_branch']:
        raise ValueError('preparation PR correction history is missing; reconcile actual history with owner before assigning a count')
    count = record.get('correction_cycles')
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise ValueError('invalid preparation correction count')
    if (not record.get('heads') or len(record['heads']) != count + 1
            or any(not ancestor(root, h, pr['sha']) for h in record['heads'])):
        raise ValueError('preparation PR discarded registered history')
    from integration import timestamp
    task_history_protection(result['preparation_branch'], timestamp(git(root, 'show', '-s', '--format=%cI', record['heads'][0]).strip()), github)
    details = github('api', f'repos/clemarc/fava/pulls/{pr["number"]}')
    opened_at = details['created_at']
    proof_base = verification_base or result['main_sha']
    commits = set(git(root, 'rev-list', f'{proof_base}..{pr["sha"]}').splitlines()) | {record['heads'][0]}
    for sha in commits:
        signature = github('api', f'repos/clemarc/fava/commits/{sha}')['commit']['verification']
        if signature.get('verified') is not True or signature.get('reason') != 'valid':
            raise ValueError('preparation resume history contains an unverified signature')
        if transition_errors(root, sha, result['ledger'], git):
            raise ValueError('invalid intermediate preparation ledger transition')
    for sha in git(root, 'rev-list', '--first-parent', f'{result["main_sha"]}..{pr["sha"]}').splitlines():
        errors = preparation_round_errors(root, sha, result['ledger'], pr['number'], opened_at,
                                          result.get('target_sha', result['main_sha']), git)
        if errors:
            raise ValueError('; '.join(errors))
        try:
            retained = json.loads(read(root, sha, result['ledger'])).get('preparation_prs', {}).get(str(pr['number']), {})
        except subprocess.CalledProcessError:
            retained = {}
        if retained.get('correction_cycles', 0) > AUTOMATIC_CORRECTION_LIMIT:
            before = timestamp(git(root, 'show', '-s', '--format=%cI', sha).strip())
            if retained['correction_cycles'] > preparation_limit(retained, pr['number'], result['id'], before):
                raise ValueError('preparation correction limit exhausted at retained publication without timely authorization')
    cap = preparation_limit(record, pr['number'], result['id'], cutoff or datetime.now(timezone.utc))
    if count > cap:
        raise ValueError('preparation correction limit exhausted without verified owner authorization')
    return dict(pr=pr['number'], head=pr['sha'], correction_cycles=count, maximum_cycles=cap,
                next_round_authorized=count < cap, blocked=record.get('state') == 'blocked')


def preparation_trailers(root, result):
    """An amendment cannot hide a missing trailer on earlier retained planning."""
    from reconciliation import commit_message, adoption_merge
    from sdd import validate_commit
    reconciliations = []
    for pr in result['prs']:
        if pr['head'] != result['preparation_branch'] or not pr.get('merged'):
            continue
        merge = pr['merge_sha']
        actual_message = git(root, 'show', '-s', '--format=%B', merge)
        message = commit_message(root, result['main_sha'], result['target_sha'], merge, git)
        paths = git(root, 'diff', '--name-only', merge + '^1', merge).splitlines()
        issues = validate_commit(message, paths, lambda p: read(root, merge, p))
        if issues:
            raise ValueError(f'retained preparation PR #{pr["number"]} merge trailer validation failed: '
                             + '; '.join(issues)
                             + '; owner-reviewed reconciliation must be adopted on main and imported into milestone before implementation')
        if message != actual_message:
            adoption = adoption_merge(root, result['main_sha'], result['target_sha'], git)
            reconciliations.append({
                'sha': adoption, 'pr': merged_pr('clemarc/fava', adoption, 'main'), 'historical_merge': merge})
    return reconciliations


def retained_preparation_progress(root, result):
    """Revalidate every merged preparation and freeze its budget record at source."""
    from integration import timestamp
    merged = [p for p in result['prs'] if p['head'] == result['preparation_branch'] and p.get('merged')]
    records = result['execution'].get('preparation_prs', {})
    if not merged or set(records) != {str(p['number']) for p in merged}:
        raise ValueError('retained preparation records do not match merged preparation PRs')
    verified = {}
    for pr in merged:
        sha = pr['merge_sha']
        actual = github('api', f'repos/clemarc/fava/pulls/{pr["number"]}')
        parents = git(root, 'show', '-s', '--format=%P', sha).split()
        if (len(parents) != 2 or not ancestor(root, sha, result['target_sha'])
                or not owner_merge(root, sha, git)
                or actual.get('merge_commit_sha') != sha or actual.get('merged_at') != pr['merged']
                or actual.get('merged_by', {}).get('login') != 'clemarc'
                or actual['head']['sha'] != parents[1] or pr['sha'] != parents[1]
                or actual['head']['ref'] != result['preparation_branch']
                or actual['base']['ref'] != result['milestone_branch']):
            raise ValueError('retained preparation PR/source/owner merge mismatch')
        source = json.loads(read(root, parents[1], result['ledger']))
        at_merge = json.loads(read(root, sha, result['ledger']))
        record = source.get('preparation_prs', {}).get(str(pr['number']))
        if (not record or record != records[str(pr['number'])]
                or record != at_merge.get('preparation_prs', {}).get(str(pr['number']))):
            raise ValueError('merged preparation history record was altered or omitted')
        # The retained initial boundary must be on the actual publication chain.
        # Neither today's main nor a mutable ledger baseline may exclude rounds.
        initial = record['heads'][0]
        if initial not in git(root, 'rev-list', '--first-parent', parents[1]).splitlines():
            raise ValueError('initial preparation boundary is outside retained publication chain')
        baseline = git(root, 'rev-parse', initial + '^1').strip()
        context = dict(result, main_sha=baseline, target_sha=parents[0])
        verified[str(pr['number'])] = preparation_revision_progress(
            root, context, dict(pr, sha=parents[1]), record, timestamp(pr['merged']), verification_base=parents[0])
    return verified


def task_history_protection(branch, initial_time, api):
    """Conservative proof that effective immutable-history rules predate work.

    Current rule presence alone cannot establish past enforcement. Any changed,
    bypassed, missing or unsupported provenance requires owner reconciliation.
    """
    from integration import timestamp
    from urllib.parse import quote
    rules = api('api', 'repos/clemarc/fava/rules/branches/' + quote(branch, safe=''))
    required = {'required_signatures', 'non_fast_forward', 'deletion'}
    proven = set()
    snapshots = {}
    for rule in rules:
        if (rule['type'] not in required or rule.get('ruleset_source_type') != 'Repository'
                or rule.get('ruleset_source') != 'clemarc/fava' or type(rule.get('ruleset_id')) is not int):
            continue
        ident = rule['ruleset_id']
        if ident not in snapshots:
            snapshots[ident] = api('api', f'repos/clemarc/fava/rulesets/{ident}')
        state = snapshots[ident]
        try:
            valid = (state.get('enforcement') == 'active' and state.get('bypass_actors') == []
                     and timestamp(state['created_at']) <= timestamp(state['updated_at']) < initial_time
                     and rule['type'] in {r['type'] for r in state['rules']})
        except (KeyError, ValueError, TypeError, AttributeError):
            valid = False
        if valid:
            proven.add(rule['type'])
    if not required <= proven:
        raise ValueError('branch publication protection history is unprovable; owner reconciliation required before registration/resume')


def task_progress(root, result):
    """Fresh-context resume state from real PRs and retained canonical history."""
    from ledger import task_publication_progress
    from urllib.parse import quote
    progress = {}
    for pr in result['prs']:
        if pr['state'] != 'open' or not pr['head'].startswith(result['task_branch_prefix']):
            continue
        key = str(pr['number'])
        record = (result.get('execution') or {}).get('task_prs', {}).get(key)
        details = github('api', f'repos/clemarc/fava/pulls/{key}')
        if details['head']['sha'] != pr['sha'] or details['head']['ref'] != pr['head'] or details['base']['ref'] != result['milestone_branch']:
            raise ValueError('task PR moved during resume inspection')
        from integration import timestamp
        initial = record['heads'][0] if record else pr['sha']
        initial_time = timestamp(git(root, 'show', '-s', '--format=%cI', initial).strip())
        task_history_protection(pr['head'], initial_time, github)
        if not record:
            if initial_time >= timestamp(details['created_at']):
                raise ValueError('unregistered task already changed after PR opening; owner reconciliation required')
            commits = set(git(root, 'rev-list', f'{result["target_sha"]}..{pr["sha"]}').splitlines()) | {initial}
            for sha in commits:
                signature = github('api', f'repos/clemarc/fava/commits/{sha}')['commit']['verification']
                if signature.get('verified') is not True or signature.get('reason') != 'valid':
                    raise ValueError('unregistered task history contains an unverified signature')
            progress[key] = dict(state='registration-required', head=pr['sha'], opened_at=details['created_at'])
            continue  # Verified initial publication only; never permission to publish again.
        if record['branch'] != pr['head']:
            raise ValueError('registered task branch identity differs from actual PR')
        current = task_publication_progress(root, result['target_sha'], pr['sha'], result['ledger'],
                                            pr['number'], details['created_at'], git)
        for sha in set(current['reservations'].values()) | set(git(root, 'rev-list', f'{result["target_sha"]}..{pr["sha"]}').splitlines()):
            signature = github('api', f'repos/clemarc/fava/commits/{sha}')['commit']['verification']
            if signature.get('verified') is not True or signature.get('reason') != 'valid':
                raise ValueError('task resume history contains an unverified signature')
        from integration import verified_owner_limits, reservation_authorization_errors
        from ledger import AUTOMATIC_CORRECTION_LIMIT
        errors = reservation_authorization_errors(root, result['ledger'], current['reservations'],
                                                  set(record['tasks']), pr['number'], result['id'])
        if errors:
            raise ValueError('task correction budget exhausted: ' + '; '.join(errors))
        limits = verified_owner_limits(result['execution'], set(record['tasks']), pr['number'], result['id'], datetime.now(timezone.utc))
        cap = min(limits.get(t, AUTOMATIC_CORRECTION_LIMIT) for t in record['tasks'])
        count = current['correction_cycles']
        if count > cap:
            raise ValueError('task correction budget exhausted without timely verified owner authorization')
        blocked = record.get('state') == 'blocked' or any(result['execution']['tasks'][t].get('state') == 'blocked' for t in record['tasks'])
        progress[key] = dict(current, head=pr['sha'], maximum_cycles=cap,
                             next_round_authorized=count < cap and not blocked and not current['pending_reservation'],
                             state='blocked' if blocked else 'resume-reserved-fix' if current['pending_reservation'] else 'published')
    return progress


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
        result['preparation_reconciliations'] = preparation_trailers(root, result)

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
                problems = integrated_task_errors(root, feature, result['milestone_branch'], ident, record, target)
                if problems:
                    raise ValueError('; '.join(problems))
    if phase == 'implement':
        result['retained_preparation_progress'] = retained_preparation_progress(root, result)
        result['task_progress'] = task_progress(root, result)
    if phase == 'prepare':
        result['preparation_progress'] = preparation_progress(root, result)
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
        if pr['base'] != expected and not reconciled_target_import_pr(result, pr):
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
    parser.add_argument('--session-pr', type=int, help='actual task/checkpoint PR for compact coordinator recovery')
    parser.add_argument('--session-report', type=int, help='actual immutable integration report comment ID')
    parser.add_argument('--handoff', action='store_true', help='write coordinator observation under ignored artifacts/sdd-session')
    parser.add_argument('--recover', type=Path, help='reconcile a prior observation against fresh resolution and GitHub')
    parser.add_argument('--ambiguous-mutation', type=Path, help='exact pending publication/merge identity JSON; never credentials')
    args = parser.parse_args()
    try:
        if (args.handoff or args.recover or args.ambiguous_mutation) and args.phase != 'implement':
            raise ValueError('compact session recovery currently supports implementation only')
        if args.checkout and (args.handoff or args.recover or args.session_pr):
            raise ValueError('recovery is read-only; choose an isolated checkout separately')
        if args.recover and args.ambiguous_mutation:
            raise ValueError('recovery must reconcile its retained mutation before replacing it')
        if args.ambiguous_mutation and not args.handoff:
            raise ValueError('retain an ambiguous mutation only through an explicit handoff')
        result = inspect(args.root, args.identifier, args.phase)
        if args.handoff or args.recover or args.session_pr:
            from recovery import live_observation, snapshot, recover, save
            previous = json.loads(args.recover.read_text()) if args.recover else None
            if args.recover and not isinstance(previous, dict):
                raise ValueError('handoff must be a JSON object')
            number = args.session_pr or (previous or {}).get('pr')
            if type(number) is not int or number < 1:
                raise ValueError('compact recovery requires an actual positive session PR')
            observation = live_observation(args.root, result, number)
            outcome = recover(args.root, result, previous, observation) if previous is not None else None
            ambiguous = json.loads(args.ambiguous_mutation.read_text()) if args.ambiguous_mutation else None
            if previous and previous.get('ambiguous_mutation') and not (outcome or {}).get('mutation_resolved'):
                ambiguous = previous['ambiguous_mutation']
            report = args.session_report or (previous or {}).get('evidence_comment')
            verified = (outcome or {}).get('verified_evidence', [])
            if verified:
                verified_report = verified[0]['evidence_comment']
                if args.session_report and args.session_report != verified_report:
                    raise ValueError('requested report differs from verified merge evidence')
                report = verified_report
            current = snapshot(result, observation, args.phase, ambiguous, report)
            if outcome:
                current['pending_transition'] = outcome.get('next_action') or 'blocked'
                current['last_verified_checkpoint'] = outcome.get('last_verified_checkpoint')
            output = dict(current_state=current, recovery=outcome,
                          next_action=(outcome or {}).get('next_action', current['pending_transition']))
            if args.handoff:
                output['snapshot'] = save(args.root, current, outcome)
            print(json.dumps(output, separators=(',', ':'), sort_keys=True))
            raise SystemExit(1 if outcome and outcome.get('state') == 'blocked' else 0)
        if args.checkout:
            checkout(args.root, result, result[args.checkout + '_branch'])
        result['SPECIFY_FEATURE_DIRECTORY'] = str(args.root.resolve() / result['feature'])
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        parser.exit(1, f'STOP: {error}\n')


if __name__ == '__main__':
    main()

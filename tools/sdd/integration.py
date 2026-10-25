"""Read-only integration gate assessment; never merges or enables auto-merge."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '.github/checks'))
import sdd
from milestone import github, inspect, read, ancestor, integrated_task_errors
from lifecycle import planning_ref
from ledger import AUTOMATIC_CORRECTION_LIMIT, target_import, task_delta_errors
from review_policy import CODEX_ONLY, LEGACY, policy_for


def represented_task_ids(root, commits, target, git=None):
    """Pure target imports carry history trailers, not new worker task scope."""
    git = git or sdd.git
    ids, errors = set(), []
    for sha in commits:
        imported, findings = target_import(root, sha, target, git)
        if imported:
            errors += findings
            continue
        ids.update(re.findall(sdd.TASK, ' '.join(sdd.trailers(git(root, 'show', '-s', '--format=%B', sha)).get('Task', []))))
    return ids, errors


def registered_pr_errors(root, target, head_ledger, number, branch, task_ids, head):
    """Canonical PR-keyed checkpoints survive branch rewrites and ID changes."""
    record = target.get('task_prs', {}).get(str(number))
    if not record or record.get('branch') != branch or set(record.get('tasks', [])) != task_ids:
        return ['task PR identity/budget must be registered on the milestone target']
    errors = []
    count = record.get('correction_cycles')
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return ['invalid registered task PR correction count']
    if not record.get('heads') or any(not ancestor(root, prior, head) for prior in record['heads']):
        errors.append('task PR rewrote or discarded registered prior heads')
    for ident in task_ids:
        cycles = head_ledger.get('tasks', {}).get(ident, {}).get('correction_cycles', -1)
        if not isinstance(cycles, int) or isinstance(cycles, bool) or cycles != count:
            errors.append(ident + ': head counter must equal registered PR budget')
    return errors


def check_results(checks):
    results = {c['name']: c.get('conclusion') for c in checks if c.get('name')}
    # The repository's reusable workflow emits one named check per device family.
    # Do not mistake an absent aggregate name for missing native execution, or
    # accept just one successful matrix leg as both-family validation.
    families = ['ios-build-test / ios-build-test (iPhone)', 'ios-build-test / ios-build-test (iPad)']
    results['ios-build-test'] = 'SUCCESS' if all(results.get(name) == 'SUCCESS' for name in families) else 'INCOMPLETE'
    return results


def verified_owner_limits(ledger, task_ids, number, milestone, before=None):
    """A ledger marker alone never grants additional correction cycles."""
    limits = {}
    for ident in sorted(task_ids):
        authorization = ledger.get('tasks', {}).get(ident, {}).get('owner_extra_cycles')
        if not isinstance(authorization, dict) or not isinstance(authorization.get('comment_id'), int):
            continue
        comment = github('api', f'repos/clemarc/fava/issues/comments/{authorization["comment_id"]}')
        try:
            if (comment.get('created_at') != comment.get('updated_at')
                    or (before is not None and not timestamp(comment['created_at']) < before)):
                continue
            approval = json.loads(comment['body'])
        except (ValueError, TypeError, KeyError, AttributeError):
            continue
        if not isinstance(approval, dict) or not isinstance(approval.get('tasks'), list):
            continue
        cap = approval.get('max_cycles')
        if (comment.get('issue_url') == f'https://api.github.com/repos/clemarc/fava/issues/{number}'
                and comment.get('user', {}).get('login') == 'clemarc'
                and approval.get('type') == 'fava-correction-authorization'
                and approval.get('milestone') == milestone and ident in approval.get('tasks', [])
                and isinstance(cap, int) and not isinstance(cap, bool) and cap > AUTOMATIC_CORRECTION_LIMIT):
            limits[ident] = cap
    return limits


def reservation_authorization_errors(root, path, reservations, task_ids, number, milestone):
    """Each extra round retains its own prior authorization; later grants cannot repair it."""
    errors = []
    for cycle, sha in reservations.items():
        if cycle <= AUTOMATIC_CORRECTION_LIMIT:
            continue
        snapshot = json.loads(read(root, sha, path))
        before = timestamp(sdd.git(root, 'show', '-s', '--format=%cI', sha).strip())
        limits = verified_owner_limits(snapshot, task_ids, number, milestone, before)
        errors += [t + ': reservation lacks timely owner authorization for round ' + str(cycle)
                   for t in sorted(task_ids) if limits.get(t, AUTOMATIC_CORRECTION_LIMIT) < cycle]
    return errors


def durable_task_limits(target, head, task_ids, owner_limits=None):
    """Reports cannot override durable task blockers or correction budgets."""
    blockers = []
    owner_limits = owner_limits or {}
    for ident in sorted(task_ids):
        counts = []
        for label, ledger in [('target', target), ('head', head)]:
            record = (ledger or {}).get('tasks', {}).get(ident)
            if record is None:
                blockers.append(ident + ': missing ' + label + ' task record')
                continue
            cycles = record.get('correction_cycles', 0)
            if not isinstance(cycles, int) or isinstance(cycles, bool) or cycles < 0:
                blockers.append(ident + ': invalid ' + label + ' correction count')
            else:
                counts.append(cycles)
                if cycles > owner_limits.get(ident, AUTOMATIC_CORRECTION_LIMIT):
                    blockers.append(ident + ': three automatic correction cycles exhausted in ' + label)
            if record.get('state') in {'blocked', 'integrated'}:
                blockers.append(ident + ': ' + label + ' task is ' + record['state'])
        if len(counts) == 2 and counts[1] < counts[0]:
            blockers.append(ident + ': correction history cannot decrease')
    return blockers


def fresh_bot_reaction(request, reactions, head, number):
    """Only a new, unedited, single-SHA request on this PR can prove review."""
    if (request.get('issue_url') != f'https://api.github.com/repos/clemarc/fava/issues/{number}'
            or request.get('created_at') != request.get('updated_at')
            or re.findall(r'\b[0-9a-f]{40}\b', request.get('body', '')) != [head]):
        return False
    try:
        requested = datetime.fromisoformat(request['created_at'].replace('Z', '+00:00'))
        return any(r.get('content') == '+1' and r.get('user', {}).get('login') == 'chatgpt-codex-connector[bot]'
                   and datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')) >= requested
                   for r in reactions)
    except (KeyError, ValueError, TypeError):
        return False


def fresh_bot_receipt(root, request, receipt, head, number, head_time, report_time):
    """Recognize only the immutable v1 completed-review receipt for this head.

    An abbreviated reviewed SHA must resolve uniquely among local Git objects.
    The caller has fetched the actual PR head; a copied prefix, stale receipt,
    mutable summary or reaction on the PR root cannot supply this proof.
    """
    try:
        if (not re.fullmatch(r'[0-9a-f]{40}', head)
                or not immutable_comment(request, number, report_time, head_time)
                or not re.search(r'(?m)^@codex review(?:\s|$)', request.get('body', ''))
                or re.findall(r'\b[0-9a-f]{40}\b', request.get('body', '')) != [head]
                or not immutable_comment(receipt, number, report_time, timestamp(request['created_at']),
                                         actor='chatgpt-codex-connector[bot]')
                or receipt.get('user', {}).get('type') != 'Bot'
                or receipt.get('performed_via_github_app', {}).get('slug') != 'chatgpt-codex-connector'
                or receipt.get('performed_via_github_app', {}).get('id') != 1144995
                or type(receipt.get('id')) is not int or receipt['id'] <= 0
                or receipt.get('html_url') != f'https://github.com/clemarc/fava/pull/{number}#issuecomment-{receipt["id"]}'):
            return False
        body = receipt.get('body', '')
        # The exact stable verdict proves completion, not absence of findings.
        # Same-line closing content remains part of the independently reviewed
        # receipt; the finding-disposition gate still covers the whole body.
        match = re.fullmatch(
            r"<!-- codex-review-receipt:v1 -->\n\n"
            r"Codex Review: Didn't find any major issues\.(?: [^\r\n]*)?\n\n"
            r'\*\*Reviewed commit:\*\* `([0-9a-f]{10,40})`'
            r'(?:\n\n<details> <summary>ℹ️ About Codex in GitHub</summary>\n.*\n</details>)?\s*',
            body, re.S)
        if not match or body.count('codex-review-receipt:') != 1 or body.count('**Reviewed commit:**') != 1:
            return False
        prefix = match[1]
        return (head.startswith(prefix)
                and sdd.git(root, 'rev-parse', '--disambiguate=' + prefix).splitlines() == [head])
    except (KeyError, ValueError, TypeError, AttributeError, subprocess.CalledProcessError):
        return False


def evaluate(evidence):
    errors = []
    head, target = evidence.get('head'), evidence.get('target')
    if not head or not target or evidence.get('validated_head') != head or evidence.get('validated_target') != target:
        errors.append('validation is missing or stale for current head/target')
    fields = ['scope', 'dependencies', 'trailers', 'signatures', 'protected_target', 'structural_drift',
              'semantic_drift', 'findings_disposed']
    if evidence.get('review_policy', LEGACY) != CODEX_ONLY:
        fields.append('independent_review')
    for field in fields:
        if evidence.get(field) is not True:
            errors.append(field + ': verified evidence required')
    if evidence.get('base') != evidence.get('milestone_branch') or not str(evidence.get('base', '')).startswith('milestone/'):
        errors.append('task PR must target the registered milestone branch')
    if evidence.get('state') != 'OPEN' or evidence.get('draft') is not False:
        errors.append('task PR must be open and ready for review')
    if evidence.get('blocked_findings'):
        errors.append('unresolved critical correctness/security/scope/consistency findings')
    errors += evidence.get('task_limit_blockers', [])
    checks = evidence.get('checks', {})
    for name in ['sdd-quality', 'tooling-validation', 'ci-applicability', 'ci-required']:
        if checks.get(name) != 'SUCCESS':
            errors.append(name + ': current passing deterministic check required')
    if evidence.get('native_required'):
        if checks.get('ios-build-test') != 'SUCCESS' or not evidence.get('simulator_tests', 0) > 0 or not evidence.get('macos_build'):
            errors.append('actual macOS compilation and nonzero simulator tests required')
    if evidence.get('review_policy') == CODEX_ONLY:
        if (evidence.get('codex_configured') is not True or evidence.get('codex_available') is not True
                or evidence.get('codex_review_head') != head or evidence.get('codex_review_complete') is not True):
            errors.append('Codex bot review pending/stale/unavailable; retry cannot waive review')
    elif evidence.get('codex_configured') and evidence.get('codex_available'):
        if evidence.get('codex_review_head') != head or evidence.get('codex_review_complete') is not True:
            errors.append('Codex bot review pending/stale')
    elif evidence.get('codex_configured') and not evidence.get('codex_unavailability_evidence'):
        errors.append('record actual Codex unavailability; do not infer it from silence')
    if evidence.get('correction_cycles', 0) > AUTOMATIC_CORRECTION_LIMIT and not evidence.get('owner_extra_cycles'):
        errors.append('three automatic correction cycles exhausted')
    return errors


def assess(root, identifier, number, evidence_comment=None):
    context = inspect(root, identifier, 'implement')
    pr = github('pr', 'view', str(number), '--repo', 'clemarc/fava', '--json',
                'number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,commits,statusCheckRollup,reviews,url')
    return assess_revision(root, context, pr, evidence_comment)


def timestamp(value):
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('ambiguous timestamp without timezone')
    return stamp


def immutable_comment(comment, number, cutoff, head_time, actor='clemarc'):
    return (comment.get('issue_url') == f'https://api.github.com/repos/clemarc/fava/issues/{number}'
            and comment.get('user', {}).get('login') == actor
            and comment.get('created_at') == comment.get('updated_at')
            and head_time < timestamp(comment['created_at']) < cutoff)


def retained_checks(head, report, cutoff):
    """Use all retained attempts as of the cutoff, never today's latest rollup.

    A later rerun cannot authorize an earlier merge or erase valid historical
    proof. Pin IDs, exact SHA and Actions identity; pending/failed attempts that
    started before the cutoff invalidate an older success of the same name.
    """
    pages = github('api', '--paginate', '--slurp',
                   f'repos/clemarc/fava/commits/{head}/check-runs?filter=all&per_page=100')
    runs = [r for page in pages for r in page['check_runs']]
    latest = {}
    for run in runs:
        if run.get('app', {}).get('slug') != 'github-actions' or run.get('head_sha') != head:
            continue
        started = timestamp(run['started_at'])
        if started >= cutoff:
            continue
        name = run['name']
        if name in latest and timestamp(latest[name]['started_at']) == started:
            raise ValueError('ambiguous check-run chronology')
        if name not in latest or timestamp(latest[name]['started_at']) < started:
            latest[name] = run
    ids = report.get('check_run_ids')
    if not isinstance(ids, list) or not ids or any(type(i) is not int for i in ids) or len(ids) != len(set(ids)):
        raise ValueError('retained check_run_ids required')
    selected = [r for r in latest.values() if r['id'] in ids]
    if {r['id'] for r in selected} != set(ids):
        raise ValueError('checks are missing, stale or not bound to retained attempts')
    results = []
    report_time = timestamp(report['_created_at'])
    for run in selected:
        success = (run.get('status') == 'completed' and run.get('conclusion') == 'success'
                   and timestamp(run['started_at']) < timestamp(run['completed_at']) < report_time)
        results.append(dict(name=run['name'], conclusion='SUCCESS' if success else 'INCOMPLETE'))
    return check_results(results), {r['name']: r['details_url'] for r in selected}


def assess_revision(root, context, pr, evidence_comment, cutoff=None, verified=None):
    """Full gates at explicit retained parents; never calls the resolver.

    Historical dependency verification descends strictly through target ancestry.
    A per-assessment cache prevents repeated verification of shared dependencies.
    """
    number = pr['number']
    historical = cutoff is not None
    cutoff = timestamp(cutoff) if historical else datetime.now(timezone.utc)
    verified = verified if verified is not None else set()
    checkpoint = pr['headRefName'].startswith(context['checkpoint_branch_prefix'])
    if pr['baseRefName'] != context['milestone_branch'] or not pr['headRefName'].startswith((context['task_branch_prefix'], context['checkpoint_branch_prefix'])):
        raise ValueError('PR head/base does not match resolved task/integration branch')
    if not historical:
        subprocess.run(['git', '-C', str(root), 'fetch', 'origin', pr['headRefOid']], check=True, capture_output=True)
    head, target = pr['headRefOid'], context['target_sha']
    from urllib.parse import quote
    rules = github('api', 'repos/clemarc/fava/rules/branches/' + quote(context['milestone_branch'], safe=''))
    types = {r['type'] for r in rules}
    protected = {'pull_request', 'required_signatures', 'required_status_checks', 'deletion', 'non_fast_forward'} <= types
    protected = protected and any(r['type'] == 'required_status_checks'
                                  and r.get('parameters', {}).get('strict_required_status_checks_policy')
                                  and any(c['context'] == 'ci-required' for c in r.get('parameters', {}).get('required_status_checks', [])) for r in rules)
    protected = protected and any(r['type'] == 'pull_request' and r.get('parameters', {}).get('required_review_thread_resolution') for r in rules)
    feature = context['feature']
    ledger = json.loads(read(root, head, context['ledger']))
    if ledger.get('preparation_prs', {}) != (context.get('execution') or {}).get('preparation_prs', {}):
        raise ValueError('task/checkpoint cannot alter retained preparation history')
    # Durable report is necessary, never sufficient: compare live evidence below.
    # Validation occurs after publication. A commit cannot contain its own SHA;
    # put the SHA-bound report in a coordinator PR comment, not a self-referential
    # ledger commit. The ledger preserves its URL after integration/checkpoint.
    if not evidence_comment and not checkpoint:
        evidence_comment = ledger['tasks'][pr['headRefName'].split('/')[-1].upper()].get('integration_comment')
    if not evidence_comment:
        raise ValueError('current-head coordinator evidence comment is required')
    report = github('api', f'repos/clemarc/fava/issues/comments/{evidence_comment}')
    if report['issue_url'] != f'https://api.github.com/repos/clemarc/fava/issues/{number}' or report['user']['login'] != 'clemarc':
        raise ValueError('integration report must be an owner-identity coordinator comment on this PR')
    head_time = timestamp(sdd.git(root, 'show', '-s', '--format=%cI', head).strip())
    if not immutable_comment(report, number, cutoff, head_time):
        raise ValueError('integration report edited, unauthorized, missing or late/ambiguous')
    evidence = json.loads(report['body'])
    if not isinstance(evidence, dict):
        raise ValueError('integration report must be complete JSON object')
    declared_policy = evidence.get('review_policy')
    selected_policy = policy_for(root, target, head, sdd.git)
    if declared_policy not in (None, selected_policy) or (selected_policy == CODEX_ONLY and declared_policy != CODEX_ONLY):
        raise ValueError('integration report review_policy must match adopted target policy')
    evidence['review_policy'] = selected_policy
    evidence['_created_at'] = report['created_at']
    evidence.update(head=head, target=target, base=pr['baseRefName'],
                    milestone_branch=context['milestone_branch'], state='OPEN' if historical else pr['state'], draft=pr['isDraft'], protected_target=protected)
    if pr['baseRefOid'] != target:
        raise ValueError('GitHub target moved during assessment')
    commits = sdd.git(root, 'rev-list', f'{target}..{head}').splitlines()
    evidence['signatures'] = bool(commits) and all((lambda v: v.get('verified') is True and v.get('reason') == 'valid')(github('api', f'repos/clemarc/fava/commits/{sha}')['commit']['verification']) for sha in commits)
    paths = sdd.git(root, 'diff', '--name-only', target, head).splitlines()
    ids, import_errors = represented_task_ids(root, commits, target)
    # The coordinator comment is descriptive; execution.json owns cycle counts
    # and owner authorization. Assess every represented task, including batches.
    canonical = context.get('execution') or {}
    authorization_deadline = timestamp(report['created_at'])
    evidence['task_limit_blockers'] = []
    if not checkpoint:
        evidence['task_limit_blockers'] += registered_pr_errors(root, canonical, ledger, number, pr['headRefName'], ids, head)
        from ledger import task_publication_progress
        metadata = github('api', f'repos/clemarc/fava/pulls/{number}')
        if (metadata['head']['sha'] != head or metadata['head']['ref'] != pr['headRefName']
                or metadata['base']['ref'] != context['milestone_branch']):
            raise ValueError('actual task PR metadata differs from retained assessment')
        progress = task_publication_progress(root, target, head, context['ledger'], number, metadata['created_at'], sdd.git)
        for cycle, sha in progress['reservations'].items():
            signature = github('api', f'repos/clemarc/fava/commits/{sha}')['commit']['verification']
            if signature.get('verified') is not True or signature.get('reason') != 'valid':
                evidence['task_limit_blockers'].append('canonical registration/reservation is not verified signed')
        evidence['task_limit_blockers'] += reservation_authorization_errors(root, context['ledger'], progress['reservations'], ids, number, context['id'])
        if progress['pending_reservation']:
            evidence['task_limit_blockers'].append('reserved correction is still unpublished; resume it without a new round')
        from milestone import task_history_protection
        initial = canonical['task_prs'][str(number)]['heads'][0]
        task_history_protection(pr['headRefName'], timestamp(sdd.git(root, 'show', '-s', '--format=%cI', initial).strip()), github)
    owner_limits = verified_owner_limits(canonical, ids, number, context['id'], authorization_deadline)
    evidence['task_limit_blockers'] += durable_task_limits(canonical, ledger, ids, owner_limits)
    # Checkpoints have no Task trailers. Verify integrated records themselves,
    # rather than letting an empty represented-ID set bypass completion proof.
    for ident, record in ledger.get('tasks', {}).items():
        if record.get('state') == 'integrated':
            evidence['task_limit_blockers'] += integrated_task_errors(root, feature, context['milestone_branch'], ident, record, target, verified)
    evidence['task_correction_records'] = {ident: ledger['tasks'].get(ident) for ident in sorted(ids)}
    evidence['target_task_correction_records'] = {ident: canonical.get('tasks', {}).get(ident) for ident in sorted(ids)}
    reviewed_revision = ledger.get('planning_revision') or context['preparation_approval']['sha']
    rows = {r[0]: r for r in sdd.task_rows(read(root, reviewed_revision, feature + '/tasks.md'))}
    if not checkpoint:
        evidence['task_limit_blockers'] += task_delta_errors(root, feature, ids, commits, target, rows, sdd.git, head)
    allowed = set().union(*(sdd.task_paths(rows[t][2]) for t in ids if t in rows))
    shared = {feature + '/' + p for p in ['execution.json', 'tasks.md', 'decision-log.md']}
    evidence['scope'] = bool(ids) and ids <= set(rows) and set(paths) <= allowed | shared
    if checkpoint:
        evidence['scope'] = bool(paths) and set(paths) <= {feature + '/' + p for p in ['execution.json', 'tasks.md', 'decision-log.md']}
    evidence['dependencies'] = all(ledger['tasks'].get(dep, {}).get('state') == 'integrated'
                                   and ancestor(root, ledger['tasks'][dep]['merge_sha'], target)
                                   for t in ids if t in rows for dep in re.findall(sdd.TASK, rows[t][2]))
    errors = list(import_errors)
    for sha in commits:
        from ledger import transition_errors
        errors += transition_errors(root, sha, context['ledger'], sdd.git)
        changed = sdd.git(root, 'diff-tree', '--no-commit-id', '-r', '--name-only', sha + '^1', sha).splitlines()
        errors += sdd.validate_commit(sdd.git(root, 'show', '-s', '--format=%B', sha), changed, lambda p: read(root, sha, p))
        if sdd.implementation_paths(changed) or (not checkpoint and not target_import(root, sha, target, sdd.git)[0]):
            planning_ref(root, context['main_sha'], sha, feature, sdd.git)
    evidence['trailers'] = not errors
    if not checkpoint and set(evidence.get('tasks', [])) != ids:
        evidence['scope'] = False
    evidence['checks'], check_urls = retained_checks(head, evidence, cutoff)
    from native import classify
    evidence['native_required'] = classify(paths, sdd.git(root, 'ls-tree', '-r', '--name-only', head).splitlines(),
                                          sdd.git(root, 'ls-tree', '-r', '--name-only', target).splitlines()) == 'required'
    # Reviews may be COMMENTED by a separate Cloud subagent, with its report URL;
    # an implementation worker's own ledger assertion cannot supply that report.
    review = evidence.get('independent_review_url')
    threads = github('api', '--paginate', '--slurp', f'repos/clemarc/fava/pulls/{number}/comments?per_page=100')
    comments = [c for page in threads for c in page]
    reviews = github('api', '--paginate', '--slurp', f'repos/clemarc/fava/pulls/{number}/reviews?per_page=100')
    reviews = [r for page in reviews for r in page]
    # Bot findings also use issue comments. Enumerate them independently of the
    # chosen completion proof; omitting a receipt key cannot hide actual findings.
    # Mutable summaries remain review content, never completion proof.
    issue_pages = github('api', '--paginate', '--slurp',
                         f'repos/clemarc/fava/issues/{number}/comments?per_page=100')
    comments += [c for page in issue_pages for c in page
                 if c.get('user', {}).get('login') == 'chatgpt-codex-connector[bot]']
    evidence['codex_configured'] = True  # Current repository configuration; do not silently bypass.
    report_time = timestamp(report['created_at'])
    bot = [r for r in reviews if r['user']['login'] == 'chatgpt-codex-connector[bot]' and r['commit_id'] == head
           and r.get('state') not in {'PENDING', 'DISMISSED'}
           and head_time < timestamp(r['submitted_at']) < report_time]
    evidence['codex_available'] = True  # Silence or a report boolean cannot bypass actual review.
    evidence['codex_review_head'] = head if bot else None
    evidence['codex_review_complete'] = bool(bot)
    # Bot thumbs-up reports may be on the explicit SHA-scoped review request;
    # coordinator records that URL and checks the reaction's actor and timestamp.
    request_id = evidence.get('codex_request_comment')
    if request_id and not bot:
        request = github('api', f'repos/clemarc/fava/issues/comments/{request_id}')
        reactions = github('api', f'repos/clemarc/fava/issues/comments/{request_id}/reactions')
        reactions = [r for r in reactions if head_time < timestamp(r['created_at']) < report_time]
        if immutable_comment(request, number, report_time, head_time) and fresh_bot_reaction(request, reactions, head, number):
            evidence['codex_review_head'], evidence['codex_review_complete'] = head, True
    # New bot completions can be immutable issue-comment receipts rather than
    # Review objects or request reactions. Retain their numeric comment key;
    # validate actual API identity, exact head binding and fresh chronology.
    receipt_id = evidence.get('codex_receipt_comment')
    if type(receipt_id) is int and receipt_id > 0:
        receipt = github('api', f'repos/clemarc/fava/issues/comments/{receipt_id}')
        # A selected receipt is also actual review content. Existing independent
        # finding dispositions still cover it, even when it cannot prove review.
        if receipt.get('id') == receipt_id:
            comments.append(receipt)
        if request_id and receipt.get('id') == receipt_id:
            request = github('api', f'repos/clemarc/fava/issues/comments/{request_id}')
            if fresh_bot_receipt(root, request, receipt, head, number, head_time, report_time):
                evidence['codex_review_head'], evidence['codex_review_complete'] = head, True
    # Include findings at the integration cutoff too: same-second ordering is
    # ambiguous. Strictly later findings do not change a historical checkpoint.
    comments = [c for c in comments if timestamp(c['created_at']) <= cutoff]
    evidence['review_comments'] = [{'url': c['html_url'], 'body': c['body']} for c in comments]
    reviewed = {}
    reviewed_at = None
    evidence['independent_review'] = False
    if selected_policy == CODEX_ONLY:
        # The immutable coordinator report now owns semantic/native interpretation
        # and every finding disposition, after actual CI and bot evidence.
        reviewed = evidence
        reviewed_at = report_time
    elif evidence.get('independent_review_comment'):
        independent = github('api', f'repos/clemarc/fava/issues/comments/{evidence["independent_review_comment"]}')
        if immutable_comment(independent, number, report_time, head_time) and independent['html_url'] == review:
            reviewed = json.loads(independent['body'])
            reviewed_at = timestamp(independent['created_at'])
    elif evidence.get('independent_review_id'):
        independent = github('api', f'repos/clemarc/fava/pulls/{number}/reviews/{evidence["independent_review_id"]}')
        # GitHub review bodies are editable without an exposed edit timestamp.
        # Retain an immutable coordinator copy in a separate comment instead.
        raise ValueError('retain independent review as an unedited SHA-bound JSON comment with its original review URL')
    if not isinstance(reviewed, dict):
        raise ValueError('independent review report must be an object')
    evidence['independent_review'] = bool(reviewed.get('reviewer') and reviewed.get('worker')
                                         and reviewed['reviewer'] != reviewed['worker']
                                         and reviewed.get('head') == head and reviewed.get('target') == target)
    evidence['semantic_drift'] = evidence.get('semantic_drift') is True and reviewed.get('semantic_drift') is True
    dispositions = reviewed.get('findings')
    actual_findings = [(c['html_url'], timestamp(c['created_at'])) for c in comments]
    actual_findings += [(r['html_url'], timestamp(r['submitted_at'])) for r in reviews if r.get('body', '').strip()
                        and r.get('state') not in {'PENDING'} and timestamp(r['submitted_at']) <= cutoff]
    known = {url for url, _ in actual_findings}
    # Covering a predictable URL does not prove its content was inspected.
    # Use the same complete finding set for coverage and strict chronology,
    # including selected receipts and findings under every completion route.
    findings_precede_review = reviewed_at is not None and all(created < reviewed_at for _, created in actual_findings)
    valid_dispositions = isinstance(dispositions, list)
    covered = set()
    for finding in dispositions if valid_dispositions else []:
        if (not isinstance(finding, dict) or not finding.get('url') or not finding.get('rationale')
                or not finding.get('evidence') or finding.get('head') != head or finding.get('target') != target
                or finding.get('disposition') not in {'fixed', 'not-actionable'}):
            valid_dispositions = False
            continue
        covered.add(finding['url'])
    evidence['findings_disposed'] = (evidence.get('findings_disposed') is True
                                     and reviewed.get('findings_disposed') is True
                                     and valid_dispositions and known <= covered and findings_precede_review)
    if evidence['native_required']:
        native = reviewed.get('native', {})
        families = ['ios-build-test / ios-build-test (iPhone)', 'ios-build-test / ios-build-test (iPad)']
        evidence['macos_build'] = all(native.get(name, {}).get('build_succeeded') is True
                                     and native[name].get('job_url') == check_urls.get(name) for name in families)
        counts = [native.get(name, {}).get('tests') for name in families]
        evidence['simulator_tests'] = min(counts) if all(type(n) is int and n > 0 for n in counts) else 0
    # Semantic review, findings dispositions and native artifact interpretation
    # require coordinator inspection. Their linked reports are not AI CI gates.
    evidence['structural_drift'] = not errors
    if not ancestor(root, target, head):
        evidence['validated_target'] = None  # Required up-to-date integration policy.
    return evidence, evaluate(evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('identifier')
    parser.add_argument('--pr', type=int, required=True)
    parser.add_argument('--evidence-comment', type=int, help='SHA-bound coordinator JSON PR comment, written after publication')
    args = parser.parse_args()
    try:
        evidence, errors = assess(Path.cwd(), args.identifier, args.pr, args.evidence_comment)
        print(json.dumps({'evidence': evidence, 'blockers': errors}, indent=2))
        raise SystemExit(bool(errors))
    except (ValueError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'STOP: {error}\n')


if __name__ == '__main__':
    main()

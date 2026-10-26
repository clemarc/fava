"""Compact coordinator observations reconciled through existing live SDD gates."""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

import milestone

REPOSITORY = 'clemarc/fava'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def pending_mutation(value):
    if value is None:
        return None
    common = {'kind', 'branch', 'parent', 'tree', 'message_sha256'}
    merge = {'kind', 'pr', 'head', 'target', 'evidence_comment'}
    if not isinstance(value, dict) or value.get('kind') not in {'publication', 'merge'}:
        raise ValueError('unsupported ambiguous mutation')
    fields = common if value['kind'] == 'publication' else merge
    if set(value) != fields:
        raise ValueError('ambiguous mutation must contain only its exact identity fields')
    for key in (fields & {'parent', 'tree', 'head', 'target'}):
        if not isinstance(value[key], str) or not re.fullmatch('[0-9a-f]{40}', value[key]):
            raise ValueError('ambiguous mutation requires full Git object IDs')
    if value['kind'] == 'publication':
        if (not isinstance(value['message_sha256'], str)
                or not re.fullmatch('[0-9a-f]{64}', value['message_sha256'])
                or not isinstance(value['branch'], str)
                or not re.fullmatch('[A-Za-z0-9._/-]+', value['branch'])):
            raise ValueError('invalid publication identity')
    elif any(type(value[k]) is not int or value[k] < 1 for k in ('pr', 'evidence_comment')):
        raise ValueError('merge requires actual PR and report identifiers')
    return dict(value)


def live_observation(root, context, number, api=milestone.github):
    """Read current evidence references; bodies are hashed, never saved as logs."""
    matches = [p for p in context['prs'] if p['number'] == number]
    if len(matches) != 1:
        raise ValueError('selected PR absent or ambiguous in live resolved milestone')
    candidate = matches[0]
    pr = api('api', f'repos/{REPOSITORY}/pulls/{number}')
    if (pr['head']['sha'] != candidate['sha'] or pr['head']['ref'] != candidate['head']
            or pr['base']['ref'] != context['milestone_branch']):
        raise ValueError('selected PR moved during recovery inspection')
    checks = api('api', '--paginate', '--slurp',
                 f'repos/{REPOSITORY}/commits/{pr["head"]["sha"]}/check-runs?filter=all&per_page=100')
    reviews = api('api', '--paginate', '--slurp', f'repos/{REPOSITORY}/pulls/{number}/reviews?per_page=100')
    comments = api('api', '--paginate', '--slurp', f'repos/{REPOSITORY}/issues/{number}/comments?per_page=100')
    inline = api('api', '--paginate', '--slurp', f'repos/{REPOSITORY}/pulls/{number}/comments?per_page=100')
    # Digests include current content/edit/state so a favorable stale report
    # cannot hide a later finding, dismissal or rerun. Digests grant no approval.
    check_rows = [r for page in checks for r in page['check_runs']]
    native = [dict(id=c['id'], name=c['name'], status=c.get('status'), conclusion=c.get('conclusion'))
              for c in check_rows if c.get('name', '').startswith('ios-build-test')]
    final = api('api', f'repos/{REPOSITORY}/pulls/{number}')
    target = api('api', 'repos/' + REPOSITORY + '/git/ref/heads/' + context['milestone_branch'])
    if (final['head']['sha'] != pr['head']['sha'] or final.get('merge_commit_sha') != pr.get('merge_commit_sha')
            or final['state'] != pr['state'] or target['object']['sha'] != context['target_sha']):
        raise ValueError('head/target/integration changed during recovery inspection')
    task_ids = (context.get('execution') or {}).get('task_prs', {}).get(str(number), {}).get('tasks', [])
    if not task_ids and pr['head']['ref'].startswith(context['task_branch_prefix']):
        from integration import represented_task_ids
        commits = milestone.git(root, 'rev-list', context['target_sha'] + '..' + pr['head']['sha']).splitlines()
        ids, errors = represented_task_ids(root, commits, context['target_sha'])
        if errors:
            raise ValueError('task identity cannot be verified from actual source history')
        task_ids = sorted(ids)
    return dict(pr=pr, check_digest=digest(checks), review_digest=digest([reviews, comments, inline]),
                native=dict(state='checks_only_acceptance_not_verified', jobs=native),
                review_references=[dict(id=r.get('id'), commit=r.get('commit_id'),
                                        state=r.get('state'), url=r.get('html_url'))
                                   for page in reviews for r in page],
                task_ids=task_ids, checkout_head=milestone.git(root, 'rev-parse', 'HEAD').strip())


def verify_merged(root, context, pr, report, api=milestone.github):
    """Run the existing retained assessor at actual merge parents and cutoff."""
    from integration import assess_revision
    from signatures import verify
    if (not pr.get('merged') or pr['base']['ref'] != context['milestone_branch']
            or type(report) is not int or report < 1):
        raise ValueError('actual milestone merge and independent evidence required')
    sha = pr.get('merge_commit_sha')
    parents = milestone.git(root, 'show', '-s', '--format=%P', sha).split()
    signature = api('api', f'repos/{REPOSITORY}/commits/{sha}')['commit']['verification']
    if (len(parents) != 2 or parents[1] != pr['head']['sha']
            or not milestone.ancestor(root, sha, context['target_sha'])
            or not signature.get('verified') or signature.get('reason') != 'valid'
            or not verify(root, sha)):
        raise ValueError('actual signed retained merge ancestry is not verified')
    canonical = json.loads(milestone.read(root, parents[0], context['ledger']))
    retained_context = dict(context, target_sha=parents[0], execution=canonical,
                            main_sha=canonical['specification_base'],
                            preparation_approval={'sha': canonical['planning_revision']})
    retained_pr = dict(number=pr['number'], state='MERGED', isDraft=False,
                       headRefName=pr['head']['ref'], headRefOid=parents[1],
                       baseRefName=pr['base']['ref'], baseRefOid=parents[0])
    _, errors = assess_revision(root, retained_context, retained_pr, report, pr['merged_at'])
    if errors:
        raise ValueError('retained merge gates failed: ' + '; '.join(errors))
    return dict(pr=pr['number'], merge_sha=sha, head=parents[1], target=parents[0], evidence_comment=report)


def reconcile_publication(root, context, mutation, api=milestone.github):
    from signatures import verify
    branch = mutation['branch']
    if not branch.startswith((context['task_branch_prefix'], context['checkpoint_branch_prefix'])):
        raise ValueError('ambiguous publication branch outside resolved milestone')
    sha = api('api', f'repos/{REPOSITORY}/git/ref/heads/{branch}')['object']['sha']
    if sha != context['branches'].get('refs/remotes/origin/' + branch):
        raise ValueError('publication branch changed after resolver inspection')
    if sha == mutation['parent']:
        return dict(state='not_observed', action='reassess_before_expected_head_publication')
    if not sha:
        raise ValueError('ambiguous publication branch absent')
    actual = api('api', f'repos/{REPOSITORY}/commits/{sha}')
    verified = actual['commit']['verification']
    message = milestone.git(root, 'show', '-s', '--format=%B', sha).strip()
    if (milestone.git(root, 'show', '-s', '--format=%P', sha).strip() != mutation['parent']
            or milestone.git(root, 'show', '-s', '--format=%T', sha).strip() != mutation['tree']
            or hashlib.sha256(message.encode()).hexdigest() != mutation['message_sha256']
            or actual.get('author', {}).get('login') != 'clemarc'
            or verified.get('verified') is not True or verified.get('reason') != 'valid'
            or not verify(root, sha)):
        raise ValueError('publication outcome differs from intended signed tree/parent/message')
    if api('api', f'repos/{REPOSITORY}/git/ref/heads/{branch}')['object']['sha'] != sha:
        raise ValueError('publication branch moved during reconciliation')
    return dict(state='verified_applied', action='refresh_current_evidence', commit=sha)


def snapshot(context, observation, phase, ambiguous=None, report=None):
    pr = observation['pr']
    key = str(pr['number'])
    ledger = context.get('execution') or {}
    record = ledger.get('task_prs', {}).get(key, {})
    progress = context.get('task_progress', {}).get(key, {})
    reservations = progress.get('reservations', {})
    count = progress.get('correction_cycles', record.get('correction_cycles', 0))
    tasks = record.get('tasks', observation.get('task_ids', []))
    action = {'registration-required': 'register_existing_pr',
              'resume-reserved-fix': 'resume_existing_reserved_round',
              'blocked': 'blocked'}.get(progress.get('state'), 'refresh_current_evidence')
    integrated = [dict(task=t, pr=r.get('pr'), merge_sha=r.get('merge_sha'),
                       evidence_comment=r.get('integration_comment'))
                  for t, r in ledger.get('tasks', {}).items() if r.get('state') == 'integrated']
    return dict(schema_version=1, observed_at=datetime.now(timezone.utc).isoformat(),
                milestone=context['id'], feature=context['feature'], phase=phase,
                execution_phase=progress.get('state', ledger.get('state', 'unknown')),
                task_ids=tasks, pr=pr['number'], branch=pr['head']['ref'],
                head=pr['head']['sha'], target=context['target_sha'],
                checkout_head=observation['checkout_head'],
                correction_count=count, reservation=reservations.get(count, reservations.get(str(count))),
                native=observation['native'], check_digest=observation['check_digest'],
                review_digest=observation['review_digest'], evidence_comment=report,
                review_references=observation.get('review_references', []),
                report_references=[dict(task=t, evidence_comment=ledger.get('tasks', {}).get(t, {}).get('integration_comment'))
                                   for t in tasks],
                pending_transition='reconcile_ambiguous_mutation' if ambiguous else action,
                ambiguous_mutation=pending_mutation(ambiguous),
                last_verified_integrations=integrated, last_verified_checkpoint=None)


def recover(root, context, old, observation, gate=verify_merged, publication=reconcile_publication):
    """Return advisory next action only; never perform publication or integration."""
    if (not isinstance(old, dict) or old.get('schema_version') != 1 or
            any(old.get(k) != context[v] for k, v in [('milestone', 'id'), ('feature', 'feature')])):
        raise ValueError('handoff identity/schema differs from live resolution')
    pr = observation['pr']
    if old.get('pr') != pr['number'] or old.get('branch') != pr['head']['ref']:
        raise ValueError('handoff PR/branch differs from live selected identity')
    if type(old.get('correction_count')) is not int or old['correction_count'] < 0:
        raise ValueError('invalid handoff correction count')
    stale = [k for k, value in dict(head=pr['head']['sha'], target=context['target_sha'],
              checkout_head=observation['checkout_head'], check_digest=observation['check_digest'],
              review_digest=observation['review_digest']).items() if old.get(k) != value]
    result = dict(state='reconciled', stale_fields=stale, verified_evidence=[],
                  missing_requirements=[], next_action='refresh_current_evidence', blocking_reason=None,
                  mutation_resolved=False)
    if pr['state'] != 'open' and not pr.get('merged'):
        raise ValueError('closed unmerged PR requires owner reconciliation')
    progress = context.get('task_progress', {}).get(str(pr['number']), {})
    count = progress.get('correction_cycles', 0)
    if pr['state'] == 'open' and pr['head']['ref'].startswith(context['task_branch_prefix']):
        if count < old['correction_count']:
            raise ValueError('correction count decreased since handoff')
        if progress.get('pending_reservation'):
            reservations = progress.get('reservations', {})
            if not reservations.get(count, reservations.get(str(count))):
                raise ValueError('pending correction lacks verified canonical reservation')
    mutation = pending_mutation(old.get('ambiguous_mutation'))
    if mutation and mutation['kind'] == 'publication':
        if mutation['branch'] != pr['head']['ref']:
            raise ValueError('ambiguous publication belongs to another PR branch')
        outcome = publication(root, context, mutation)
        result.update(next_action=outcome['action'], publication=outcome,
                      mutation_resolved=outcome['state'] == 'verified_applied')
        if pr.get('merged'):
            if result['mutation_resolved'] and outcome['commit'] != pr['head']['sha']:
                raise ValueError('reconciled publication differs from merged PR head')
        else:
            if progress.get('state') == 'blocked':
                result.update(state='blocked', next_action=None, blocking_reason='canonical_task_blocked')
            elif outcome['state'] == 'not_observed':
                result['missing_requirements'] = ['fresh_publication_budget_and_verified_pure_import_checks']
            return result
    if mutation and mutation['kind'] == 'merge':
        if mutation['pr'] != pr['number']:
            raise ValueError('ambiguous merge belongs to another PR')
        if not pr.get('merged'):
            if pr['state'] != 'open' or mutation['head'] != pr['head']['sha'] or mutation['target'] != context['target_sha']:
                raise ValueError('unacknowledged merge has stale or retired inputs')
            result.update(next_action='reassess_before_guarded_merge', missing_requirements=['fresh_integration_assessment'])
            if progress.get('state') == 'blocked':
                result.update(state='blocked', next_action=None, blocking_reason='canonical_task_blocked')
            return result
    if pr.get('merged'):
        merge_intent = mutation if mutation and mutation['kind'] == 'merge' else None
        report = merge_intent['evidence_comment'] if merge_intent else old.get('evidence_comment')
        proof = gate(root, context, pr, report)
        if merge_intent and (proof['head'] != merge_intent['head'] or proof['target'] != merge_intent['target']):
            raise ValueError('actual merge differs from ambiguous mutation intent')
        result['verified_evidence'].append(proof)
        if merge_intent:
            result['mutation_resolved'] = True
        if mutation and not result['mutation_resolved']:
            return dict(result, state='blocked', next_action=None,
                        blocking_reason='unresolved_publication_on_merged_pr')
        if pr['head']['ref'].startswith(context['checkpoint_branch_prefix']):
            result.update(next_action='refresh_canonical_state', last_verified_checkpoint=proof)
        else:
            ledger = context.get('execution') or {}
            tasks = observation.get('task_ids') or ledger.get('task_prs', {}).get(str(pr['number']), {}).get('tasks', [])
            if not tasks:
                raise ValueError('merged task identity is unavailable')
            recorded = all(ledger.get('tasks', {}).get(t, {}).get('merge_sha') == pr['merge_commit_sha']
                           and ledger['tasks'][t].get('state') == 'integrated' for t in tasks)
            result.update(next_action='refresh_canonical_state' if recorded else 'prepare_standalone_completion_checkpoint')
        return result
    if pr['state'] != 'open':
        raise ValueError('closed unmerged PR requires owner reconciliation')
    if progress.get('state') == 'blocked':
        return dict(result, state='blocked', next_action=None, blocking_reason='canonical_task_blocked')
    if progress.get('pending_reservation'):
        reservations = progress.get('reservations', {})
        reservation = reservations.get(count, reservations.get(str(count)))
        if not reservation:
            raise ValueError('pending correction lacks verified canonical reservation')
        return dict(result, next_action='resume_existing_reserved_round',
                    reservation=reservation, correction_count=count,
                    missing_requirements=['verified_pure_target_import_before_source_publication'])
    if progress.get('state') == 'registration-required':
        result['next_action'] = 'register_existing_pr'
    elif not stale:
        result['next_action'] = 'assess_current_head'
    return result


def save(root, value, outcome=None):
    """Coordinator-only local output; canonical Git records are never modified."""
    directory = root / 'artifacts/sdd-session' / milestone.normalize(value['milestone']).lower()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = directory / '.writer-lock'
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        # Kernel releases this lock on interruption. The retained lock file is
        # harmless; deleting it could let two writers lock different inodes.
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        archive = directory / 'archive'
        archive.mkdir(exist_ok=True, mode=0o700)
        for name in ('snapshot.json', 'CURRENT.md'):
            path = directory / name
            if path.exists():
                content = path.read_bytes()
                destination = archive / (hashlib.sha256(content).hexdigest() + '-' + name)
                if not destination.exists():
                    with destination.open('xb') as stream:
                        os.chmod(destination, 0o600)
                        stream.write(content)
        body = dict(value, recovery=outcome) if outcome else value
        action = (outcome or {}).get('next_action', value['pending_transition'])
        current = (f'# {value["milestone"]}: PR #{value["pr"]}\n\n'
                   f'Phase: {value["phase"]}. Head: {value["head"]}.\n'
                   f'Target: {value["target"]}. Correction count: {value["correction_count"]}.\n'
                   f'Next: {action}.\nCanonical state: Git and live GitHub; snapshot is an observation.\n')
        for name, text in [('snapshot.json', json.dumps(body, sort_keys=True, indent=2)+'\n'), ('CURRENT.md', current)]:
            fd, temporary = tempfile.mkstemp(prefix='.handoff-', dir=directory)
            try:
                with os.fdopen(fd, 'w') as stream:
                    stream.write(text); stream.flush(); os.fsync(stream.fileno())
                os.replace(temporary, directory / name)
            finally:
                if os.path.exists(temporary): os.unlink(temporary)
    finally:
        os.close(descriptor)
    return str(directory / 'snapshot.json')

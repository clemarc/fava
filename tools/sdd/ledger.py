"""Execution schema and retained-history checks, independent of GitHub credentials."""
import re
import json
import subprocess
import hashlib
from datetime import datetime

AUTOMATIC_CORRECTION_LIMIT = 3


def composite_candidate(root, context, before, after, tasks_before, tasks_after,
                        completed, successor_number, *, git=None, api=None,
                        completion_verifier=None, signed=None, history_protection=None):
    """Inactive preview of one atomic complete+register delta, never authorization.

    Production transition dispatch deliberately does not call this function.
    Owner sequencing approval and a separate activation change are required.
    Providers can be injected by synthetic tests; defaults use existing proof.
    """
    import milestone
    import sdd
    from signatures import verify
    git, api = git or sdd.git, api or milestone.github
    completion_verifier = completion_verifier or milestone.integrated_task_errors
    signed = signed or verify
    history_protection = history_protection or milestone.task_history_protection
    result = dict(activation_enabled=False, accepted=False, valid_for_review=False,
                  intermediate_state='INTEGRATED_PENDING_COMPLETION', errors=[],
                  next_action='owner_policy_approval_and_separate_activation_required')
    if successor_number is None:
        return dict(result, next_action='assess_standalone_completion',
                    reason='successor_absent_or_delayed')
    errors = result['errors']
    try:
        target, feature = context['target_sha'], context['feature']
        result['expected_target'] = target
        result['base_digest'] = hashlib.sha256(json.dumps(
            [before, tasks_before], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        branch, path = context['milestone_branch'], context['ledger']
        if api('api', f'repos/clemarc/fava/git/ref/heads/{branch}')['object']['sha'] != target:
            raise ValueError('stale_target')
        if json.loads(git(root, 'show', target + ':' + path)) != before:
            raise ValueError('candidate_parent_is_not_canonical_ledger')
        if git(root, 'show', target + ':' + feature + '/tasks.md') != tasks_before:
            raise ValueError('candidate_tasks_are_not_canonical')
        if type(successor_number) is not int or successor_number < 1:
            raise ValueError('actual_successor_pr_required')
        if not completed or len(completed) != len(set(completed)):
            raise ValueError('unique_predecessor_tasks_required')
        completed = set(completed)
        errors += validate(before, feature, tasks_before)
        errors += validate(after, feature, tasks_after)
        errors += history_errors(before, after)
        old_rows, new_rows = sdd.task_rows(tasks_before), sdd.task_rows(tasks_after)
        approved_rows = sdd.task_rows(git(root, 'show', before['planning_revision'] + ':' + feature + '/tasks.md'))
        if [(r[0], r[2:]) for r in old_rows] != [(r[0], r[2:]) for r in approved_rows]:
            errors.append('target_task_definitions_differ_from_reviewed_planning')
        if [(r[0], r[2:]) for r in old_rows] != [(r[0], r[2:]) for r in new_rows]:
            errors.append('composite_cannot_change_task_definitions')
        changed_checks = {old[0] for old, new in zip(old_rows, new_rows) if old[1] != new[1]}
        if changed_checks != completed:
            errors.append('only_predecessor_completion_checkboxes_may_change')
        if any(before.get(k) != after.get(k) for k in set(before) | set(after)
               if k not in {'tasks', 'task_prs', 'checkpoints'}):
            errors.append('unrelated_execution_fields_changed')
        key = str(successor_number)
        previous_prs, current_prs = before.get('task_prs', {}), after.get('task_prs', {})
        if key in previous_prs:
            errors.append('duplicate_successor_registration')
        if set(current_prs) != set(previous_prs) | {key} or any(
                current_prs.get(k) != v for k, v in previous_prs.items()):
            errors.append('correction_reservations_or_retained_heads_changed')
        record = current_prs.get(key, {})
        successors = set(record.get('tasks', []))
        if not successors or successors & completed:
            errors.append('distinct_successor_tasks_required')
        for ident, old in before['tasks'].items():
            new = after['tasks'].get(ident, {})
            if old.get('correction_cycles', 0) != new.get('correction_cycles', 0):
                errors.append('task_correction_count_changed')
            if ident not in completed | successors and old != new:
                errors.append('unrelated_task_changed')
        for ident in completed:
            if before['tasks'].get(ident, {}).get('state') == 'integrated':
                errors.append('duplicate_predecessor_completion')
            candidate = after['tasks'].get(ident, {})
            if candidate.get('state') != 'integrated':
                errors.append('predecessor_completion_missing')
            errors += completion_verifier(root, feature, branch, ident, candidate, target)
        rows = {r[0]:r for r in approved_rows}
        dependencies = set()
        for ident in successors:
            if ident not in rows:
                errors.append('successor_not_in_approved_tasks')
                continue
            deps = set(re.findall(sdd.TASK, rows[ident][2]))
            dependencies |= deps
            for dep in deps - completed:
                old = before['tasks'].get(dep, {})
                if old.get('state') != 'integrated':
                    errors.append('other_dependency_not_canonical')
                else:
                    errors += completion_verifier(root, feature, branch, dep, old, target)
        if not completed <= dependencies:
            errors.append('dependency_relationship_not_approved')
        pr = api('api', f'repos/clemarc/fava/pulls/{successor_number}')
        head = pr['head']['sha']
        if (pr.get('state') != 'open' or pr.get('merged_at') or pr['base']['ref'] != branch
                or pr['head']['ref'] != record.get('branch')
                or record.get('heads') != [head] or record.get('correction_cycles') != 0):
            errors.append('successor_exact_initial_head_or_pr_invalid')
        commit = api('api', f'repos/clemarc/fava/commits/{head}')
        verification = commit['commit']['verification']
        opened = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
        published = datetime.fromisoformat(commit['commit']['committer']['date'].replace('Z', '+00:00'))
        if (published.tzinfo is None or opened.tzinfo is None or published >= opened
                or verification.get('verified') is not True or verification.get('reason') != 'valid'
                or not signed(root, head)):
            errors.append('successor_initial_publication_not_verified')
        history_protection(record.get('branch'), published, api)
        for ident in completed:
            git(root, 'merge-base', '--is-ancestor', after['tasks'][ident]['merge_sha'], head)
        from integration import represented_task_ids
        commits = git(root, 'rev-list', target + '..' + head).splitlines()
        for introduced in set(commits) | {head}:
            proof = verification if introduced == head else api(
                'api', f'repos/clemarc/fava/commits/{introduced}')['commit']['verification']
            if proof.get('verified') is not True or proof.get('reason') != 'valid' or not signed(root, introduced):
                errors.append('successor_introduced_history_not_verified')
        ids, scope_errors = represented_task_ids(root, commits, target, git)
        errors += scope_errors
        if ids != successors:
            errors.append('successor_source_task_identity_mismatch')
        errors += task_delta_errors(root, feature, successors, commits, target, rows, git, head)
        checkpoints = before.get('checkpoints', [])
        proposed = after.get('checkpoints', [])
        if len(proposed) != len(checkpoints) + 1 or proposed[:-1] != checkpoints:
            errors.append('one_atomic_checkpoint_required')
        else:
            checkpoint = proposed[-1]
            ident = checkpoint.get('id', '')
            if (not re.fullmatch(r'C[0-9]{3}', ident) or any(c.get('id') == ident for c in checkpoints)
                    or checkpoint.get('branch') != context['checkpoint_branch_prefix'] + ident.lower()
                    or checkpoint.get('kind') != 'task-completion-registration'
                    or set(checkpoint.get('completion', {}).get('tasks', [])) != completed
                    or set(checkpoint.get('registration', {}).get('tasks', [])) != successors
                    or checkpoint.get('registration', {}).get('task_pr') != pr['html_url']
                    or checkpoint.get('registration', {}).get('initial_head') != head):
                errors.append('atomic_checkpoint_identity_invalid')
        if api('api', f'repos/clemarc/fava/git/ref/heads/{branch}')['object']['sha'] != target:
            errors.append('target_moved_during_candidate_validation')
        final_pr = api('api', f'repos/clemarc/fava/pulls/{successor_number}')
        if (final_pr['head']['sha'] != head or final_pr['head']['ref'] != pr['head']['ref']
                or final_pr['base']['ref'] != branch or final_pr.get('state') != 'open' or final_pr.get('merged_at')):
            errors.append('successor_moved_during_candidate_validation')
        if not errors:
            result['valid_for_review'] = True
            result['candidate_digest'] = hashlib.sha256(json.dumps(
                [after, tasks_after], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    except (ValueError, KeyError, TypeError, AttributeError, OSError, subprocess.SubprocessError):
        errors.append('incomplete_or_inconsistent_composite_candidate')
    return result


def composite_recovery_preview(candidate, observation):
    """Synthetic interrupted-operation model, not an executable transition.

    Digests identify whole ledger+tasks candidates, never one half. A future
    activation must obtain observations through existing signed-publication and
    retained-merge verification; this preview cannot establish that proof.
    """
    if not isinstance(candidate, dict) or not isinstance(observation, dict):
        return dict(activation_enabled=False, accepted=False, next_action='blocked_invalid_observation')
    action = 'await_owner_policy_approval'
    expected = candidate.get('candidate_digest')
    canonical, published = observation.get('canonical_digest'), observation.get('published_digest')
    status = observation.get('checkpoint_result')
    if status is not None and not isinstance(status, str):
        return dict(activation_enabled=False, accepted=False, next_action='blocked_invalid_observation')
    if candidate.get('valid_for_review') is not True or not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
        action = 'blocked_invalid_candidate'
    elif canonical is not None and canonical not in (expected, candidate.get('base_digest')):
        action = 'blocked_partial_or_conflicting_canonical_state'
    elif canonical == expected:
        action = 'verify_existing_composite_merge'
    elif status in {'failure', 'cancelled', 'timed_out'}:
        action = 'reconcile_failed_checkpoint_before_standalone_fallback'
    elif published is not None and published != expected:
        action = 'blocked_conflicting_publication'
    elif observation.get('target') != candidate.get('expected_target'):
        action = 'rebuild_against_fresh_target'
    elif published == expected:
        action = 'reuse_existing_candidate_and_refresh_gates'
    elif observation.get('mutation_pending'):
        action = 'reconcile_publication_before_retry'
    return dict(activation_enabled=False, accepted=False, next_action=action)


def validate(ledger, feature, tasks):
    from milestone import normalize
    from sdd import task_rows
    errors = []
    ident = normalize(ledger['milestone'])
    if ledger.get('schema') != 1 or ledger.get('feature') != feature or ledger.get('milestone_branch') != 'milestone/' + ident.lower():
        errors.append('schema/feature/milestone branch mismatch')
    if not re.fullmatch(r'[0-9a-f]{40}', ledger.get('specification_base', '')):
        errors.append('specification_base must be inspected main SHA')
    if ledger.get('state') not in {'preparing', 'implementing', 'ready-for-owner', 'completed', 'blocked'}:
        errors.append('unknown milestone state')
    if ledger.get('planning_revision') is not None and not re.fullmatch(r'[0-9a-f]{40}', ledger.get('planning_revision', '')):
        errors.append('planning_revision must be actual owner preparation merge SHA or null')
    if ledger.get('state') != 'preparing' and not ledger.get('planning_revision'):
        errors.append('reviewed preparation revision required after preparation')
    rows = {r[0]: r for r in task_rows(tasks or '')}
    records = ledger.get('tasks', {})
    retired = ledger.get('retired_task_ids', [])
    if set(rows) != set(records) or set(rows) & set(retired) or len(retired) != len(set(retired)):
        errors.append('task records must exactly match retained tasks; retired IDs cannot be reused')
    for ident, record in records.items():
        if record.get('state') not in {'pending', 'working', 'review', 'blocked', 'integrated'}:
            errors.append(ident + ': invalid task state')
        if record.get('correction_cycles', 0) > AUTOMATIC_CORRECTION_LIMIT and not record.get('owner_extra_cycles'):
            if record.get('state') != 'blocked': errors.append(ident + ': correction limit requires blocker')
        if record.get('state') == 'integrated':
            if not rows.get(ident, ('', False))[1] or not record.get('pr') or not re.fullmatch(r'[0-9a-f]{40}', record.get('merge_sha', '')) or not record.get('evidence'):
                errors.append(ident + ': integration needs task checkbox, merge SHA, PR and evidence')
        elif rows.get(ident, ('', False))[1]:
            errors.append(ident + ': checked task lacks verified integration state')
    for number, record in ledger.get('task_prs', {}).items():
        if (not re.fullmatch(r'[1-9][0-9]*', number) or not isinstance(record, dict)
                or not isinstance(record.get('correction_cycles'), int)
                or isinstance(record.get('correction_cycles'), bool) or record['correction_cycles'] < 0
                or not record.get('tasks') or not set(record['tasks']) <= set(records)
                or not record.get('branch', '').startswith('task/' + ledger['milestone'].lower() + '/')
                or not record.get('heads') or len(record['heads']) != record['correction_cycles'] + 1
                or any(not re.fullmatch(r'[0-9a-f]{40}', h) for h in record['heads'])):
            errors.append(str(number) + ': invalid task PR history')
    for number, record in ledger.get('preparation_prs', {}).items():
        if (not re.fullmatch(r'[1-9][0-9]*', number) or not isinstance(record, dict)
                or record.get('branch') != 'prepare/' + ledger['milestone'].lower()
                or not isinstance(record.get('correction_cycles'), int)
                or isinstance(record.get('correction_cycles'), bool) or record['correction_cycles'] < 0
                or not record.get('heads') or len(record['heads']) != record['correction_cycles'] + 1
                or any(not re.fullmatch(r'[0-9a-f]{40}', h) for h in record['heads'])):
            errors.append(str(number) + ': invalid preparation PR history')
    if ledger.get('state') == 'completed' and not all(ledger.get('physical_acceptance', {}).get(family) for family in ['iPhone', 'iPad']):
        errors.append('completion requires separate iPhone and iPad acceptance evidence')
    if ledger.get('state') in {'ready-for-owner', 'completed'} and (not records or any(record.get('state') != 'integrated' for record in records.values())):
        errors.append('automated readiness/completion requires every retained task verified integrated')
    return errors


def history_errors(old, new, *, publication=True):
    errors = []
    for key in ['milestone', 'feature', 'milestone_branch', 'specification_base']:
        if old.get(key) != new.get(key): errors.append(key + ': immutable execution baseline')
    if not set(old.get('retired_task_ids', [])) <= set(new.get('retired_task_ids', [])):
        errors.append('retired task IDs are append-only')
    for ident, record in old.get('tasks', {}).items():
        current = new.get('tasks', {}).get(ident)
        if current is None and ident not in new.get('retired_task_ids', []):
            errors.append(ident + ': removed task must retire its ID')
        if record.get('state') == 'integrated' and current != record:
            errors.append(ident + ': integrated task history must remain frozen; new fixes need new IDs')
        if current is not None:
            old_cycles, new_cycles = record.get('correction_cycles', 0), current.get('correction_cycles', 0)
            if (not isinstance(old_cycles, int) or not isinstance(new_cycles, int)
                    or isinstance(new_cycles, bool) or new_cycles < old_cycles):
                errors.append(ident + ': correction count cannot decrease or become invalid')
    for number, current in new.get('task_prs', {}).items():
        record = old.get('task_prs', {}).get(number)
        count, heads = current.get('correction_cycles'), current.get('heads')
        if (type(count) is not int or count < 0 or not isinstance(heads, list) or len(heads) != count + 1):
            errors.append(number + ': task count must match retained publication boundaries')
        if record is None:
            if publication and (count != 0 or isinstance(count, bool) or not isinstance(heads, list) or len(heads) != 1):
                errors.append(number + ': initial task registration requires zero and one published head')
        else:
            retained = (isinstance(count, int) and not isinstance(count, bool)
                        and isinstance(heads, list) and count >= record['correction_cycles']
                        and heads[:len(record['heads'])] == record['heads'])
            single_round = ((count == record['correction_cycles'] and heads == record['heads'])
                            or (count == record['correction_cycles'] + 1
                                and isinstance(heads, list) and len(heads) == len(record['heads']) + 1
                                and heads[:-1] == record['heads']))
            if (any(current.get(k) != record.get(k) for k in ['tasks', 'branch'])
                    or not retained or (publication and not single_round)):
                errors.append(number + ': task reservation must increment once and retain one prior-head boundary')
    if not set(old.get('task_prs', {})) <= set(new.get('task_prs', {})):
        errors.append('task PR history cannot be deleted')
    for number, record in old.get('preparation_prs', {}).items():
        current = new.get('preparation_prs', {}).get(number)
        if (not current or current.get('branch') != record.get('branch')
                or not isinstance(current.get('correction_cycles'), int)
                or isinstance(current.get('correction_cycles'), bool)
                or current['correction_cycles'] < record['correction_cycles']
                or current.get('heads', [])[:len(record['heads'])] != record['heads']):
            errors.append(str(number) + ': preparation PR history is immutable/append-only; counters cannot decrease')
    return errors


def transition_errors(root, sha, path, git):
    """Check every parent edge, including intermediate heads and merge parents."""
    def snapshot(ref):
        try:
            return json.loads(git(root, 'show', f'{ref}:{path}'))
        except subprocess.CalledProcessError:
            return None
    try:
        current = snapshot(sha)
        errors = []
        parents = git(root, 'show', '-s', '--format=%P', sha).split()
        # A pure merge can import several already-retained reservations at once.
        # Validate its retention here; callers validate every introduced commit,
        # so the original registration/reservation publications remain strict.
        imported = len(parents) == 2 and target_import(root, sha, parents[1], git) == (True, [])
        for parent in parents:
            previous = snapshot(parent)
            if previous is not None:
                errors += history_errors(previous, current, publication=not imported) if current is not None else ['execution history cannot be deleted']
            elif current is not None and not imported:
                errors += history_errors(dict(current, task_prs={}), current)
        if imported and current is not None:
            snapshots = [snapshot(parent) or {} for parent in parents]
            for number, record in current.get('task_prs', {}).items():
                if not any(record == state.get('task_prs', {}).get(number) for state in snapshots):
                    # Automatic text merges can synthesize a record from edits
                    # on both sides. Such a record is a new publication, not an
                    # inherited reservation, and still needs single-step proof.
                    for state in snapshots:
                        old = state.get('task_prs', {})
                        errors += history_errors({'task_prs': {number: old[number]} if number in old else {}},
                                                 {'task_prs': {number: record}})
        return errors
    except (ValueError, TypeError, KeyError):
        return ['invalid execution history transition']


def target_import(root, sha, target, git):
    """Recognize target ancestry; only an exact automatic tree is a pure import."""
    parents = git(root, 'show', '-s', '--format=%P', sha).split()
    if len(parents) != 2:
        return False, []
    try:
        git(root, 'merge-base', '--is-ancestor', parents[1], target)
    except subprocess.CalledProcessError:
        return False, []
    try:
        automatic = git(root, 'merge-tree', '--write-tree', *parents).splitlines()[0]
        if automatic != git(root, 'rev-parse', sha + '^{tree}').strip():
            return True, ['target import contains unscoped merge-resolution changes']
    except subprocess.CalledProcessError:
        return True, ['target import is conflicted; resolve through scoped task commits before import']
    return True, []


def preparation_round_errors(root, sha, path, number, opened_at, target, git):
    """Every post-registration prep publication binds one round to its parent."""
    try:
        try:
            current = json.loads(git(root, 'show', f'{sha}:{path}'))
        except subprocess.CalledProcessError:
            return []  # Before the initial artifacts exist.
        parents = git(root, 'show', '-s', '--format=%P', sha).split()
        if not parents:
            return ['preparation publication lacks a parent']
        parent = parents[0]
        try:
            previous = json.loads(git(root, 'show', f'{parent}:{path}'))
        except subprocess.CalledProcessError:
            previous = {}
        key = str(number)
        old = previous.get('preparation_prs', {}).get(key)
        new = current.get('preparation_prs', {}).get(key)
        if new is None:
            return [] if old is None else ['preparation registration cannot be removed']
        if not isinstance(new.get('correction_cycles'), int) or isinstance(new.get('correction_cycles'), bool):
            return ['preparation correction count must be an integer']
        imported, errors = target_import(root, sha, target, git)
        if imported:
            return errors if new == old else errors + ['target import changed preparation round records']
        changed = set(git(root, 'diff-tree', '--no-commit-id', '-r', '--name-only', parent, sha).splitlines())
        if old is not None and changed == {path}:
            differences = {k for k in set(previous) | set(current) if previous.get(k) != current.get(k)}
            # Projection-only records and blocked-finding checkpoints make no
            # artifact progress and cannot reset counters, heads or approvals.
            projection = differences <= {'linear'} and new == old
            blocked = (differences <= {'preparation_prs', 'findings'}
                       and new == dict(old, state='blocked')
                       and current.get('findings', [])[:len(previous.get('findings', []))] == previous.get('findings', [])
                       and current.get('preparation_prs') == dict(previous.get('preparation_prs', {}), **{key: new}))
            if projection or blocked:
                return []
        if old is None:
            stamp = datetime.fromisoformat(git(root, 'show', '-s', '--format=%cI', parent).strip())
            opened = datetime.fromisoformat(opened_at.replace('Z', '+00:00'))
            allowed = {'preparation_pr', 'preparation_prs', 'linear'}
            other = {k for k in set(previous) | set(current) if previous.get(k) != current.get(k)} - allowed
            if (new.get('correction_cycles') != 0 or new.get('heads') != [parent]
                    or stamp >= opened or changed != {path} or other):
                return ['initial preparation registration must be zero, metadata-only and bound to the pre-opening head; late/ambiguous registration needs owner reconciliation']
        elif (new.get('correction_cycles') != old.get('correction_cycles', 0) + 1
              or new.get('heads') != old.get('heads', []) + [parent]):
            return ['preparation publication must increment once and append its immediately preceding head']
        return []
    except (ValueError, TypeError, KeyError, subprocess.CalledProcessError):
        return ['invalid preparation round/head evidence']


def task_delta_errors(root, feature, task_ids, commits, target, rows, git, head=None):
    """Imported work, empty commits and borrowed paths are not task evidence."""
    import sdd
    proven = set()
    touched = {}
    if head is None:
        # rev-list returns the source tip first; callers also pass it explicitly.
        head = commits[0] if commits else target
    surviving = set(git(root, 'diff', '--name-only', target, head).splitlines())
    candidates = {}
    for introduced in commits:
        imported, _ = target_import(root, introduced, target, git)
        if imported:
            continue
        paths = set(git(root, 'diff-tree', '--no-commit-id', '-r', '--name-only', introduced + '^1', introduced).splitlines())
        mapped = sdd.trailers(git(root, 'show', '-s', '--format=%B', introduced))
        ids = set(re.findall(sdd.TASK, ' '.join(mapped.get('Task', []))))
        for path in paths:
            touched.setdefault(path, []).append(ids)
        allowed = set().union(*(sdd.task_paths(rows[t][2]) for t in ids if t in rows))
        expected_fr = set().union(*(set(re.findall(sdd.FR, rows[t][2])) for t in ids if t in rows))
        shared = {feature + '/' + p for p in ['execution.json', 'tasks.md', 'decision-log.md']}
        if (feature in mapped.get('Spec', []) and ids <= set(rows) and paths <= allowed | shared
                and set(re.findall(sdd.FR, ' '.join(mapped.get('Implements', [])))) == expected_fr):
            for t in ids & set(task_ids):
                candidates.setdefault(t, set()).update(paths & sdd.task_paths(rows[t][2]))
    for t, paths in candidates.items():
        # Conservatively reject mixed ownership on a shared path. A prior touch
        # plus another task's surviving edit is not evidence for this task.
        if any(all(t in owners for owners in touched[path]) for path in paths & surviving):
            proven.add(t)
    return [t + ': no task-owned approved changes outside target imports' for t in sorted(set(task_ids) - proven)]


def task_merge_errors(root, feature, ident, record, target, git):
    """Credential-free task identity proof; live PR/report checks supplement it."""
    import sdd
    sha = record.get('merge_sha', '')
    try:
        git(root, 'merge-base', '--is-ancestor', sha, target)
        parents = git(root, 'show', '-s', '--format=%P', sha).split()
        mapped = sdd.trailers(git(root, 'show', '-s', '--format=%B', sha))
        if len(parents) != 2 or feature not in mapped.get('Spec', []) or ident not in re.findall(sdd.TASK, ' '.join(mapped.get('Task', []))):
            return [ident + ': cited merge lacks exact Spec/Task identity']
        if git(root, 'rev-parse', sha + '^{tree}').strip() != git(root, 'rev-parse', parents[1] + '^{tree}').strip():
            return [ident + ': integration tree differs from reviewed task source']
        rows = {r[0]: r for r in sdd.task_rows(git(root, 'show', f'{parents[0]}:{feature}/tasks.md'))}
        if ident not in rows:
            return [ident + ': task is absent from reviewed target mappings']
        merge_ids = set(re.findall(sdd.TASK, ' '.join(mapped.get('Task', []))))
        merge_fr = set().union(*(set(re.findall(sdd.FR, rows[t][2])) for t in merge_ids if t in rows))
        if not merge_ids <= set(rows) or set(re.findall(sdd.FR, ' '.join(mapped.get('Implements', [])))) != merge_fr:
            return [ident + ': merge requirement mappings do not match reviewed tasks']
        commits = git(root, 'rev-list', f'{parents[0]}..{parents[1]}').splitlines()
        return task_delta_errors(root, feature, {ident}, commits, parents[0], rows, git, parents[1])
    except (ValueError, subprocess.CalledProcessError):
        return [ident + ': cited task merge is absent from target or invalid']


def task_publication_progress(root, target, head, path, number, opened_at, git):
    """Reconcile signed first-parent publications with canonical reservations.

    The initial publication may contain multiple commits before PR creation.
    Thereafter every non-import commit is one publication/correction. A reserved
    but unpublished correction returns pending, so resume never reserves twice.
    """
    record = json.loads(git(root, 'show', f'{target}:{path}'))['task_prs'][str(number)]
    count, heads = record['correction_cycles'], record['heads']
    if (not isinstance(count, int) or isinstance(count, bool) or count < 0
            or len(heads) != count + 1):
        raise ValueError('task count must match retained publication boundaries')
    chain = git(root, 'rev-list', '--first-parent', '--reverse', head).splitlines()
    if heads[0] not in chain:
        raise ValueError('task initial publication was rewritten')
    initial = heads[0]
    opened = datetime.fromisoformat(opened_at.replace('Z', '+00:00'))
    stamp = datetime.fromisoformat(git(root, 'show', '-s', '--format=%cI', initial).strip())
    if stamp >= opened or stamp.tzinfo is None or opened.tzinfo is None:
        raise ValueError('initial task publication must strictly predate real PR opening')
    completed = 0
    segment = [initial]
    for sha in chain[chain.index(initial) + 1:]:
        imported, errors = target_import(root, sha, target, git)
        if errors:
            raise ValueError('; '.join(errors))
        if imported:
            segment.append(sha)
            continue
        if completed >= count or heads[completed + 1] not in segment:
            raise ValueError('unreserved/skipped task publication or invalid prior-head boundary')
        parent = git(root, 'rev-parse', sha + '^1').strip()
        before = json.loads(git(root, 'show', f'{parent}:{path}'))
        reserved = before.get('task_prs', {}).get(str(number), {})
        expected_heads = heads[:completed + 2]
        if (reserved.get('correction_cycles') != completed + 1 or reserved.get('heads') != expected_heads
                or reserved.get('branch') != record['branch'] or reserved.get('tasks') != record['tasks']):
            raise ValueError('task correction must import its canonical reservation before publication')
        completed += 1
        segment = [sha]
    if count - completed not in (0, 1) or (count > completed and heads[-1] not in segment):
        raise ValueError('skipped task publication or duplicate interrupted reservation')
    # Bind the initial registration and each reservation to the target history,
    # including metadata checkpoints that claim future or arbitrary heads.
    previous = None
    reservations = {}
    for sha in git(root, 'rev-list', '--first-parent', '--reverse', target).splitlines():
        try:
            snapshot = json.loads(git(root, 'show', f'{sha}:{path}'))
        except subprocess.CalledProcessError:
            continue
        current = snapshot.get('task_prs', {}).get(str(number))
        if current is None:
            if previous is not None: raise ValueError('task registration deleted')
            continue
        if previous is None:
            if current.get('correction_cycles') != 0 or current.get('heads') != [initial]:
                raise ValueError('initial task registration must be zero with the initial head')
        elif history_errors({'task_prs': {str(number): previous}}, {'task_prs': {str(number): current}}):
            raise ValueError('invalid canonical task reservation transition')
        if previous is None or current['correction_cycles'] != previous['correction_cycles'] or current['heads'] != previous['heads']:
            reservations[current['correction_cycles']] = sha
            boundary = current['heads'][-1]
            boundary_time = datetime.fromisoformat(git(root, 'show', '-s', '--format=%cI', boundary).strip())
            registered_time = datetime.fromisoformat(git(root, 'show', '-s', '--format=%cI', sha).strip())
            if boundary_time >= registered_time or opened >= registered_time:
                raise ValueError('ambiguous task registration/reservation chronology')
            # Canonical checkpoint must precede the correction, proven by ancestry
            # through its pure import, not just a worker-authored copied record.
            round_number = current['correction_cycles']
            if round_number and round_number <= completed:
                fixes = [h for h in chain[chain.index(initial) + 1:] if not target_import(root, h, target, git)[0]]
                try:
                    git(root, 'merge-base', '--is-ancestor', sha, fixes[round_number - 1] + '^1')
                except subprocess.CalledProcessError:
                    raise ValueError('canonical reservation did not precede its task correction')
        previous = current
    if previous != record:
        raise ValueError('missing retained canonical task registration')
    return dict(correction_cycles=count, completed_corrections=completed, pending_reservation=count > completed, reservations=reservations)

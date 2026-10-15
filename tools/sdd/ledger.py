"""Execution schema and retained-history checks, independent of GitHub credentials."""
import re
import json
import subprocess
from datetime import datetime

AUTOMATIC_CORRECTION_LIMIT = 3


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
                or not record.get('heads') or any(not re.fullmatch(r'[0-9a-f]{40}', h) for h in record['heads'])):
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

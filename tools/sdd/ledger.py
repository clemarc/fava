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
                or not record.get('heads') or any(not re.fullmatch(r'[0-9a-f]{40}', h) for h in record['heads'])):
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


def history_errors(old, new):
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
    for number, record in old.get('task_prs', {}).items():
        current = new.get('task_prs', {}).get(number)
        if (not current or any(current.get(k) != record.get(k) for k in ['tasks', 'branch'])
                or not isinstance(current.get('correction_cycles'), int)
                or isinstance(current.get('correction_cycles'), bool)
                or current['correction_cycles'] < record['correction_cycles']
                or current.get('heads', [])[:len(record['heads'])] != record['heads']):
            errors.append(str(number) + ': task PR history is immutable/append-only; counters cannot decrease')
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
        for parent in git(root, 'show', '-s', '--format=%P', sha).split():
            previous = snapshot(parent)
            if previous is not None:
                errors += history_errors(previous, current) if current is not None else ['execution history cannot be deleted']
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


def task_delta_errors(root, feature, task_ids, commits, target, rows, git):
    """Imported work, empty commits and borrowed paths are not task evidence."""
    import sdd
    proven = set()
    for introduced in commits:
        imported, _ = target_import(root, introduced, target, git)
        if imported:
            continue
        paths = set(git(root, 'diff-tree', '--no-commit-id', '-r', '--name-only', introduced + '^1', introduced).splitlines())
        mapped = sdd.trailers(git(root, 'show', '-s', '--format=%B', introduced))
        ids = set(re.findall(sdd.TASK, ' '.join(mapped.get('Task', []))))
        allowed = set().union(*(sdd.task_paths(rows[t][2]) for t in ids if t in rows))
        expected_fr = set().union(*(set(re.findall(sdd.FR, rows[t][2])) for t in ids if t in rows))
        shared = {feature + '/' + p for p in ['execution.json', 'tasks.md', 'decision-log.md']}
        if (feature in mapped.get('Spec', []) and ids <= set(rows) and paths <= allowed | shared
                and set(re.findall(sdd.FR, ' '.join(mapped.get('Implements', [])))) == expected_fr):
            proven |= {t for t in ids & set(task_ids) if paths & sdd.task_paths(rows[t][2])}
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
        rows = {r[0]: r for r in sdd.task_rows(git(root, 'show', f'{parents[0]}:{feature}/tasks.md'))}
        if ident not in rows:
            return [ident + ': task is absent from reviewed target mappings']
        merge_ids = set(re.findall(sdd.TASK, ' '.join(mapped.get('Task', []))))
        merge_fr = set().union(*(set(re.findall(sdd.FR, rows[t][2])) for t in merge_ids if t in rows))
        if not merge_ids <= set(rows) or set(re.findall(sdd.FR, ' '.join(mapped.get('Implements', [])))) != merge_fr:
            return [ident + ': merge requirement mappings do not match reviewed tasks']
        commits = git(root, 'rev-list', f'{parents[0]}..{parents[1]}').splitlines()
        return task_delta_errors(root, feature, {ident}, commits, parents[0], rows, git)
    except (ValueError, subprocess.CalledProcessError):
        return [ident + ': cited task merge is absent from target or invalid']

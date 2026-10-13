"""Execution schema and retained-history checks, independent of GitHub credentials."""
import re


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
        if record.get('correction_cycles', 0) > 2 and not record.get('owner_extra_cycles'):
            if record.get('state') != 'blocked': errors.append(ident + ': correction limit requires blocker')
        if record.get('state') == 'integrated':
            if not rows.get(ident, ('', False))[1] or not record.get('pr') or not re.fullmatch(r'[0-9a-f]{40}', record.get('merge_sha', '')) or not record.get('evidence'):
                errors.append(ident + ': integration needs task checkbox, merge SHA, PR and evidence')
        elif rows.get(ident, ('', False))[1]:
            errors.append(ident + ': checked task lacks verified integration state')
    if ledger.get('state') == 'completed' and not all(ledger.get('physical_acceptance', {}).get(family) for family in ['iPhone', 'iPad']):
        errors.append('completion requires separate iPhone and iPad acceptance evidence')
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
    return errors

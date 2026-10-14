"""Offline Fava SDD gates. Validation never rewrites repository artifacts."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/sdd'))

FEATURE = r'(?:[0-9]{3}-[a-z0-9]+(?:-[a-z0-9]+)*|[0-9]{8}-[0-9]{6}-[a-z0-9]+(?:-[a-z0-9]+)*|[a-z][a-z0-9]*(?:-[a-z0-9]+)*-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*)'
FR = r'FR-[0-9]{3}'
TASK = r'T[0-9]{3}'
STORY = r'US[1-9][0-9]*'
ROADMAP_ID = r'R[1-9][0-9]*(?:\.[1-9][0-9]*)?'
EXCEPTIONS = {'bootstrap', 'process', 'roadmap', 'specification', 'planning', 'tooling', 'reconciliation'}
PILOT_APPROVAL = 'd6a2f4be72f51f5f734b4c22de362fae07341572'
# Fixed, already published delivery boundary; never use a moving branch/ref here.
PILOT_DELIVERY_HEAD = '7ad912fc97c94aa87cd45de30e51b6588b2b49d8'
PILOT_FEATURES = {
    'specs/healthkit-run-library-01-app-foundation-and-authorization',
    'specs/healthkit-run-library-02-run-ingestion',
    'specs/healthkit-run-library-03-run-library',
}


def pilot_planning_ref(root, base, sha, feature, message):
    """Apply the one-time exception only to the recorded delivery's history."""
    if (base != PILOT_APPROVAL or sha == PILOT_APPROVAL
            or feature not in PILOT_FEATURES
            or trailers(message).get('Delivery-Pilot') != ['healthkit-r1-r3']):
        return base
    try:
        git(root, 'merge-base', '--is-ancestor', PILOT_APPROVAL, sha)
        git(root, 'merge-base', '--is-ancestor', sha, PILOT_DELIVERY_HEAD)
        git(root, 'cat-file', '-e', f'{base}:{feature}/spec.md')
        parent = git(root, 'rev-parse', sha + '^').strip()
        for artifact in ['plan.md', 'tasks.md']:
            git(root, 'cat-file', '-e', f'{parent}:{feature}/{artifact}')
        return parent
    except subprocess.CalledProcessError:
        return base


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL).decode('utf-8')


def clean(text):
    return re.sub(r'<!--.*?-->', '', text, flags=re.S)


def status(text):
    match = re.search(r'^\*{0,2}Status\*{0,2}:\s*([^\n]+)', text, re.M | re.I)
    return match.group(1).strip().lower() if match else ''


def definitions(spec):
    return re.findall(r'^\s*-\s+\*{0,2}(FR-\S+?)\*{0,2}:', clean(spec), re.M)


def stories(spec):
    parts = re.split(r'^###\s+(?:User Story\s+([0-9]+)|\[?(US[0-9]+)\]?)\b', clean(spec), flags=re.M)
    return {(named or 'US' + number): re.split(r'^#{1,3}\s', body, maxsplit=1, flags=re.M)[0]
            for number, named, body in zip(parts[1::3], parts[2::3], parts[3::3])}


def task_rows(text):
    phase = ''
    rows = []
    for line in clean(text).splitlines():
        if line.startswith('## '):
            phase = line
        if re.match(r'^- \[[ xX]\] ', line):
            m = re.match(r'^- \[([ xX])\] (T\S+)\s+(.+)$', line)
            if not m:
                raise ValueError(f'malformed task: {line}')
            rows.append((m[2], m[1].lower() == 'x', m[3], phase))
    return rows


def task_paths(text):
    return set(re.findall(r'(?<![\w/])(?:[\w.-]+/)*[\w.-]+\.[A-Za-z0-9]+(?![\w/])', text))


def governance_path(path):
    return (path.startswith(('.github/', '.agents/', '.specify/', 'tools/', 'docs/'))
            or path in {'AGENTS.md', 'README.md', 'LICENSE', '.gitignore', '.linear.toml',
                        'package.json', 'package-lock.json', 'skills-lock.json', '.codex/config.toml'})


def implementation_paths(paths):
    return [p for p in paths if not governance_path(p) and not p.startswith('specs/')]


def validate_feature(name, spec, tasks=None, plan=False):
    errors = []
    def fail(msg): errors.append(f'specs/{name}: {msg}')
    if not re.fullmatch(FEATURE, name): fail('feature name must be NNN-slug, timestamp-slug or epic-NN-slug')
    ids = definitions(spec)
    if not ids: fail('define requirements as - **FR-NNN**: ...')
    if any(not re.fullmatch(FR, x) or x == 'FR-000' for x in ids): fail('invalid FR identifier; use FR-001 and higher')
    if len(ids) != len(set(ids)): fail('duplicate requirement definitions within feature')
    for token in re.findall(r'\bFR-[A-Za-z0-9-]+', clean(spec)):
        if token not in ids: fail(f'unknown or malformed requirement {token}')
    story_map = stories(spec)
    headings = re.findall(r'^###\s+(?:User Story\s+([0-9]+)|\[?(US[0-9]+)\]?)\b', clean(spec), re.M)
    if len(headings) != len(story_map): fail('duplicate user-story identifiers')
    if not story_map: fail('at least one User Story N or USN heading is required')
    for story, body in story_map.items():
        if not re.fullmatch(STORY, story): fail(f'invalid story {story}')
        refs = set(re.findall(FR, body))
        if not refs: fail(f'{story} must reference applicable FR identifiers')
        if not refs <= set(ids): fail(f'{story} references unknown requirements')
    if tasks is None:
        if status(spec) == 'completed': fail('completed features require plan.md and tasks.md')
        return errors
    if not plan: fail('tasks.md requires plan.md; specification PRs may omit both')
    try: rows = task_rows(tasks)
    except ValueError as e:
        fail(str(e)); return errors
    task_ids = [r[0] for r in rows]
    if not rows: fail('tasks.md contains no executable tasks')
    if len(task_ids) != len(set(task_ids)): fail('duplicate task IDs')
    covered = set()
    for ident, done, body, phase in rows:
        if not re.fullmatch(TASK, ident) or ident == 'T000': fail(f'invalid task ID {ident}')
        refs = set(re.findall(r'\bFR-[A-Za-z0-9-]+', body)) - {'FR-exempt'}
        covered |= refs
        exempt = bool(re.search(r'\b(Setup|Foundational)\b', phase, re.I)) and 'FR-exempt:' in body
        if not refs and not exempt: fail(f'{ident} needs FR identifiers or a reasoned Setup/Foundational FR-exempt:')
        if exempt and not body.split('FR-exempt:', 1)[1].strip(): fail(f'{ident} FR exemption needs a reason')
        if not refs <= set(ids): fail(f'{ident} references unknown requirements: {sorted(refs - set(ids))}')
        us = set(re.findall(r'\[(US[^\]]+)\]', body))
        if not re.search(r'\b(Setup|Foundational)\b', phase, re.I) and not us: fail(f'{ident} needs a [USN] marker outside Setup/Foundational')
        if not us <= set(story_map): fail(f'{ident} references unknown user stories')
        for story in us & set(story_map):
            if refs and not refs & set(re.findall(FR, story_map[story])): fail(f'{ident} has no requirement in common with {story}')
        paths = task_paths(body)
        if not paths: fail(f'{ident} must name exact file paths (future files need not exist yet)')
        if any('..' in PurePosixPath(p).parts for p in paths): fail(f'{ident} path escapes repository')
        deps = set(re.findall(TASK, body))
        if ident in deps or not deps <= set(task_ids): fail(f'{ident} has self/unknown task dependencies')
        if '[P]' in body and not done:
            if any(not r[1] and r[0] in deps for r in rows): fail(f'{ident} [P] has unmet dependencies')
            if any(not r[1] and r[0] != ident and paths & task_paths(r[2]) for r in rows): fail(f'{ident} [P] shares a file with another open task')
    missing = set(ids) - covered
    if missing: fail(f'requirements missing from tasks.md: {sorted(missing)}')
    graph = {r[0]: set(re.findall(TASK, r[2])) for r in rows}
    def visit(node, trail):
        if node in trail: return True
        return any(visit(dep, trail | {node}) for dep in graph.get(node, set()))
    if any(visit(node, set()) for node in graph): fail('task dependency cycle')
    if status(spec) == 'completed' and any(not r[1] for r in rows): fail('completed feature has incomplete tasks')
    return errors


def trailers(message):
    block = message.rstrip().split('\n\n')[-1]
    parsed = {}
    for line in block.splitlines():
        m = re.fullmatch(r'([A-Za-z-]+):\s*(.+)', line)
        if not m: return {}
        parsed.setdefault(m[1], []).append(m[2])
    return parsed


def validate_commit(message, paths, read):
    errors = []
    t = trailers(message)
    native = implementation_paths(paths)
    kind = t.get('SDD-Type', [])
    if not native:
        if len(kind) != 1 or kind[0] not in EXCEPTIONS:
            errors.append('non-implementation commit needs one SDD-Type: ' + ', '.join(sorted(EXCEPTIONS)))
        elif any(p.startswith('specs/') for p in paths) and kind[0] not in {'roadmap', 'specification', 'planning', 'reconciliation'}:
            errors.append('spec artifacts require roadmap, specification, planning or reconciliation SDD-Type')
        elif kind[0] == 'reconciliation' and any(not (p.startswith('specs/_system/') or governance_path(p)) for p in paths):
            errors.append('reconciliation exception only permits current-state specs and governance paths')
        if not t.get('Task'):
            return errors
    if native and kind: errors.append('SDD-Type exception cannot cover application source/tests or unknown paths')
    specs = t.get('Spec', [])
    if len(specs) != 1 or not re.fullmatch('specs/' + FEATURE, specs[0]):
        return errors + ['implementation commit needs one Spec: specs/<feature-directory> trailer; split cross-feature commits']
    feature = specs[0]
    try:
        spec = read(feature + '/spec.md')
        tasks = read(feature + '/tasks.md')
        rows = task_rows(tasks)
    except (ValueError, FileNotFoundError, subprocess.CalledProcessError):
        return errors + [f'{feature} spec.md/tasks.md must exist in this commit']
    split_ids = lambda key: set(re.split(r'[,\s]+', ' '.join(t.get(key, [])))) - {''}
    task_ids, fr_ids = split_ids('Task'), split_ids('Implements')
    known = {r[0]: r for r in rows}
    if not task_ids or not task_ids <= set(known): errors.append('Task: must resolve to TNNN identifiers in the cited feature')
    mapped = set().union(*(set(re.findall(FR, known[x][2])) for x in task_ids & set(known)))
    if not fr_ids and mapped: errors.append('Implements: must cite applicable FR-NNN identifiers')
    if not fr_ids <= set(definitions(spec)) or fr_ids != mapped:
        errors.append('Implements: identifiers must match requirements of all cited tasks')
    if not mapped and task_ids and not all('FR-exempt:' in known[x][2] and re.search(r'Setup|Foundational', known[x][3], re.I) for x in task_ids & set(known)):
        errors.append('FR exemption is allowed only for explicit Setup/Foundational tasks')
    return errors


def validate_repo(root, base=None, head='HEAD', message=None, preparation_pr=None, preparation_opened_at=None):
    errors = []
    if not (root / 'specs').is_dir(): return ['missing specs/ directory']
    if not (root / '.specify/memory/constitution.md').is_file(): errors.append('missing .specify/memory/constitution.md')
    roadmap_entries = {}
    for path in sorted((root / 'specs').glob('*/roadmap.md')):
        text = clean(path.read_text())
        prefix = path.relative_to(root).as_posix()
        if status(text) not in {'draft', 'agreed', 'superseded'}: errors.append(f'{prefix}: invalid roadmap Status')
        for field in ['# Roadmap:', 'Tracker epic:', 'Intent:', '| ID | Sub-feature | Intent | In scope | Deferred to | Depends on | Directory |']:
            if field not in text: errors.append(f'{prefix}: missing {field}')
        rows = []
        for line in text.splitlines():
            if re.match(r'^\|\s*R', line):
                cells = [c.strip() for c in line.strip('|').split('|')]
                if len(cells) != 7 or not re.fullmatch(ROADMAP_ID, cells[0]):
                    errors.append(f'{prefix}: malformed roadmap entry {line}'); continue
                rows.append(cells)
        if base:
            try: prior_roadmap = git(root, 'show', f'{base}:{prefix}')
            except subprocess.CalledProcessError: prior_roadmap = ''
            if status(prior_roadmap) in {'agreed', 'superseded'}:
                current_rows = {r[0]: r for r in rows}
                for line in prior_roadmap.splitlines():
                    if re.match(r'^\|\s*R[1-9]', line):
                        old = [c.strip() for c in line.strip('|').split('|')]
                        if current_rows.get(old[0]) != old: errors.append(f'{prefix} {old[0]}: agreed roadmap entries cannot be rewritten or removed; add a superseding slice')
        ids = [r[0] for r in rows]
        if not rows or len(ids) != len(set(ids)): errors.append(f'{prefix}: missing/duplicate roadmap entry IDs')
        graph = {}
        for row in rows:
            ident, _, _, _, _, depends, directory = row
            if not all(row): errors.append(f'{prefix} {ident}: all scope/dependency cells must be explicit')
            if not re.fullmatch('specs/' + FEATURE, directory): errors.append(f'{prefix} {ident}: invalid feature directory {directory}')
            if directory in roadmap_entries: errors.append(f'{prefix}: directory {directory} has multiple roadmap entries')
            roadmap_entries[directory] = (prefix, ident)
            deps = set() if depends == 'none' else set(re.split(r'[,\s]+', depends)) - {''}
            if (depends != 'none' and (not deps or any(not re.fullmatch(ROADMAP_ID, d) for d in deps))) or not deps <= set(ids) or ident in deps: errors.append(f'{prefix} {ident}: invalid Depends on')
            graph[ident] = deps
        def cyclic(node, trail):
            return node in trail or any(cyclic(x, trail | {node}) for x in graph.get(node, set()))
        if any(cyclic(x, set()) for x in graph): errors.append(f'{prefix}: roadmap dependency cycle')
    for directory in sorted((root / 'specs').iterdir()):
        if not directory.is_dir() or directory.name == '_system' or (directory / 'roadmap.md').exists(): continue
        path = directory / 'spec.md'
        if not path.is_file(): errors.append(f'{directory.relative_to(root)}: feature requires spec.md'); continue
        spec = path.read_text()
        tasks = (directory / 'tasks.md').read_text() if (directory / 'tasks.md').exists() else None
        errors += validate_feature(directory.name, spec, tasks, (directory / 'plan.md').is_file())
        key = directory.relative_to(root).as_posix()
        plan_path = directory / 'plan.md'
        if plan_path.exists():
            unknown = set(re.findall(r'\bFR-[A-Za-z0-9-]+', clean(plan_path.read_text()))) - set(definitions(spec))
            if unknown: errors.append(f'{key}/plan.md: unknown requirements {sorted(unknown)}')
        log_path = directory / 'decision-log.md'
        if log_path.exists():
            decisions = re.findall(r'^#{1,3}\s+(DEC-\S+)', log_path.read_text(), re.M)
            if len(decisions) != len(set(decisions)) or any(not re.fullmatch(r'DEC-[0-9]{3}', d) for d in decisions):
                errors.append(f'{key}/decision-log.md: use unique DEC-NNN headings')
        ledger_path = directory / 'execution.json'
        if ledger_path.exists():
            from ledger import validate as validate_ledger
            try:
                errors += [f'{key}/execution.json: {e}' for e in validate_ledger(
                    json.loads(ledger_path.read_text()), key, tasks)]
            except (ValueError, TypeError, KeyError) as error:
                errors.append(f'{key}/execution.json: invalid ledger: {error}')
            if base:
                try:
                    old_ledger = json.loads(git(root, 'show', f'{base}:{key}/execution.json'))
                    new_ledger = json.loads(ledger_path.read_text())
                    from ledger import history_errors
                    errors += [f'{key}/execution.json: {e}' for e in history_errors(old_ledger, new_ledger)]
                except subprocess.CalledProcessError:
                    pass
                except (ValueError, TypeError, KeyError):
                    errors.append(f'{key}/execution.json: invalid history')
        parent = re.search(r'Parent roadmap:\s*(specs/[^\s]+/roadmap.md)\s*→\s*entry\s+(' + ROADMAP_ID + r')(?![\w.])', spec)
        if key in roadmap_entries and (not parent or parent.groups() != roadmap_entries[key]): errors.append(f'{key}: Parent roadmap must match {roadmap_entries[key]}')
        if parent and roadmap_entries.get(key) != parent.groups(): errors.append(f'{key}: parent roadmap entry does not resolve back to this directory')
        if not re.search(r'^\s*(?:##\s+Scope|Scope boundary:)', spec, re.M): errors.append(f'{key}: explicit Scope boundary: or ## Scope required')
        sup = re.search(r'^Supersedes:\s*(\S+)', spec, re.M)
        if sup and sup[1] != 'none':
            predecessor = sup[1].removeprefix('specs/')
            if predecessor == directory.name or not (root / 'specs' / predecessor / 'spec.md').is_file(): errors.append(f'{key}: Supersedes predecessor must exist and differ')
        if base:
            try: previous = git(root, 'show', f'{base}:{key}/spec.md')
            except subprocess.CalledProcessError: previous = None
            if previous is None and ((directory / 'plan.md').exists() or tasks is not None): errors.append(f'{key}: merge specification PR before adding derived planning artifacts')
            if previous is not None:
                normalized = lambda s: re.sub(r'^\*{0,2}Status\*{0,2}:.*$', '', s, flags=re.M)
                if normalized(previous) != normalized(spec): errors.append(f'{key}: approved requirements are immutable; create a new feature with Supersedes:')
                if status(previous) != status(spec) and status(spec) != 'completed': errors.append(f'{key}: only verified transition to Status: completed is allowed after approval')
                if status(previous) == 'completed' and git(root, 'diff', '--name-only', base, head, '--', key): errors.append(f'{key}: completed feature history is frozen')
                try: old_log = git(root, 'show', f'{base}:{key}/decision-log.md')
                except subprocess.CalledProcessError: old_log = ''
                if old_log and (not (directory / 'decision-log.md').exists() or not (directory / 'decision-log.md').read_text().startswith(old_log)): errors.append(f'{key}: decision-log.md must remain append-only')
    if base:
        if preparation_pr:
            from ledger import preparation_round_errors
            ledgers = [p for p in git(root, 'ls-tree', '-r', '--name-only', head).splitlines()
                       if p.startswith('specs/') and p.endswith('/execution.json')]
            registered = [p for p in ledgers if str(preparation_pr) in json.loads(git(root, 'show', f'{head}:{p}')).get('preparation_prs', {})]
            if len(registered) != 1 or not preparation_opened_at:
                errors.append('preparation PR requires exactly one registered ledger and actual opening timestamp')
            for sha in git(root, 'rev-list', '--first-parent', f'{base}..{head}').splitlines():
                for path in registered:
                    errors += [f'commit {sha[:12]}: {e}' for e in preparation_round_errors(
                        root, sha, path, preparation_pr, preparation_opened_at, base, git)]
        # Deleted contracts/completed directories cannot evade the current-tree walk.
        for path in git(root, 'diff', '--name-only', '--diff-filter=D', base, head, '--', 'specs').splitlines():
            if path.endswith('/roadmap.md'): errors.append(f'{path}: historical roadmaps cannot be deleted')
            if path.endswith('/spec.md'): errors.append(f'{path}: historical requirements cannot be deleted')
        paths = git(root, 'diff', '--name-only', base, head).splitlines()
        if any(p.startswith('specs/_system/') for p in paths):
            current = '\n'.join(p.read_text() for p in (root / 'specs/_system').glob('*.md'))
            for feature in (root / 'specs').glob('*/spec.md'):
                if status(feature.read_text()) != 'completed': continue
                for ident in definitions(feature.read_text()):
                    if not re.search(re.escape(ident) + r'\s+\(' + re.escape(feature.parent.name) + r'\)', current):
                        errors.append(f'specs/_system/: account for {ident} ({feature.parent.name}) as current or explicitly superseded')
        if implementation_paths(paths):
            for p in paths:
                if p.endswith('/spec.md') and not p.startswith('specs/_system/'):
                    try: git(root, 'cat-file', '-e', f'{base}:{p}')
                    except subprocess.CalledProcessError: errors.append(f'{p}: implementation must follow a merged specification and planning PR')
        # Source work requires an already approved breakdown in the base.
        for sha in git(root, 'rev-list', '--reverse', f'{base}..{head}').splitlines():
            # A merge records integration relative to its first parent; comparing
            # every parent incorrectly attributes target-only changes to the task.
            parents = git(root, 'show', '-s', '--format=%P', sha).split()
            paths = (git(root, 'diff-tree', '--no-commit-id', '-r', '--name-only', parents[0], sha)
                     if parents else git(root, 'diff-tree', '--root', '--no-commit-id', '-r', '--name-only', sha)).splitlines()
            if preparation_pr and implementation_paths(paths):
                from ledger import target_import
                imported, issues = target_import(root, sha, base, git)
                if not imported or issues:
                    errors.append(f'commit {sha[:12]}: preparation cannot introduce application implementation')
            from ledger import transition_errors, task_merge_errors
            for path in paths:
                if path.startswith('specs/') and path.endswith('/execution.json'):
                    errors += [f'commit {sha[:12]}: {e}' for e in transition_errors(root, sha, path, git)]
                    try:
                        execution = json.loads(git(root, 'show', f'{sha}:{path}'))
                        for ident, record in execution.get('tasks', {}).items():
                            if record.get('state') == 'integrated':
                                errors += task_merge_errors(root, path.rsplit('/', 1)[0], ident, record, sha, git)
                    except (ValueError, TypeError, KeyError, subprocess.CalledProcessError):
                        errors.append(f'commit {sha[:12]}: invalid execution history')
            if implementation_paths(paths) or trailers(git(root, 'show', '-s', '--format=%B', sha)).get('Task'):
                cited = trailers(git(root, 'show', '-s', '--format=%B', sha)).get('Spec', [])
                for feature in cited:
                    planning_ref = pilot_planning_ref(root, base, sha, feature, git(root, 'show', '-s', '--format=%B', sha))
                    if planning_ref == base:
                        from lifecycle import planning_ref as milestone_planning_ref
                        try:
                            planning_ref = milestone_planning_ref(root, base, sha, feature, git)
                        except (ValueError, subprocess.CalledProcessError) as error:
                            errors.append(f'{feature}: invalid reviewed planning proof: {error}')
                    for artifact in ['plan.md', 'tasks.md']:
                        try: git(root, 'cat-file', '-e', f'{planning_ref}:{feature}/{artifact}')
                        except subprocess.CalledProcessError: errors.append(f'{feature}/{artifact}: merge planning PR before implementation')
            read = lambda p: git(root, 'show', f'{sha}:{p}')
            errors += [f'commit {sha[:12]}: {e}' for e in validate_commit(git(root, 'show', '-s', '--format=%B', sha), paths, read)]
    if message:
        paths = git(root, 'diff', '--cached', '--name-only').splitlines()
        errors += validate_commit(message.read_text(), paths, lambda p: git(root, 'show', ':' + p))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--base', help='merge base for lifecycle and every new commit')
    parser.add_argument('--head', default='HEAD')
    parser.add_argument('--message-file', type=Path, help='validate pending message against staged paths')
    parser.add_argument('--preparation-pr', type=int, help='actual PR number from trusted Actions context')
    parser.add_argument('--preparation-opened-at', help='actual PR created_at from trusted Actions context')
    args = parser.parse_args()
    errors = validate_repo(args.root, args.base, args.head, args.message_file, args.preparation_pr, args.preparation_opened_at)
    for error in errors: print('ERROR:', error)
    if not errors: print('SDD quality passed (roadmap slices may precede feature specifications).')
    raise SystemExit(bool(errors))


if __name__ == '__main__': main()

"""Small pinned-CLI projection: dry-run by default; never an independent API client."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from milestone import inspect, read
from sdd import stories, task_rows

PROJECT = 'f823cc39-b818-460f-8682-bb4ec831885a'


def cli(root, *args, structured=True):
    if not os.environ.get('LINEAR_API_KEY'):
        raise ValueError('LINEAR_API_KEY binding missing; projection pending')
    env = dict(os.environ, LINEAR_IGNORE_ENV_FILE='1', LINEAR_DEBUG='0')
    result = subprocess.run([str(root / 'node_modules/.bin/linear'), '--no-input', *args],
                            env=env, capture_output=True, text=True, cwd=root)
    if result.returncode:
        raise ValueError(f'Linear CLI exit {result.returncode}; inspect current keyed items before retrying any write')
    return json.loads(result.stdout) if structured else result.stdout


def index(items):
    indexed = {}
    for item in items:
        keys = re.findall(r'^Repository key:\s*(\S+)\s*$', item.get('description') or '', re.M)
        if len(keys) > 1:
            raise ValueError('ambiguous repository keys in ' + item['identifier'])
        if keys:
            if keys[0] in indexed:
                raise ValueError('duplicate repository key ' + keys[0])
            indexed[keys[0]] = item
    return indexed


def desired(context, revision, spec, tasks, execution):
    feature, ident = context['feature'], context['id']
    results = []
    rows = task_rows(tasks)
    for story, body in stories(spec).items():
        related = [r for r in rows if '[' + story + ']' in r[2]]
        # Physical acceptance remains separate. Stories stay in review after
        # automated tasks integrate until the owner accepts the milestone.
        state = 'In Review' if related and all(r[1] for r in related) else 'Todo'
        if execution.get('state') == 'completed': state = 'Done'
        results.append(dict(key=feature + '/' + story, title=f'{ident} {story}',
                            body=body.strip(), file='spec.md', state=state, parent=None))
    for task, done, body, _ in rows:
        related = re.findall(r'\[(US[0-9]+)\]', body)
        record = execution.get('tasks', {}).get(task, {})
        if done and (record.get('state') != 'integrated' or not record.get('evidence')):
            raise ValueError(task + ': checked task has no verified integration evidence')
        state = 'Done' if done else {'review': 'In Review', 'working': 'In Progress'}.get(record.get('state'), 'Todo')
        results.append(dict(key=feature + '/' + task, title=(f'{ident} {task} — ' + body)[:200],
                            body=body, file='tasks.md', state=state,
                            parent=feature + '/' + related[0] if related else None))
    for item in results:
        source = f'https://github.com/clemarc/fava/blob/{revision}/{feature}/{item["file"]}'
        item['description'] = f'Repository key: {item["key"]}\n\nSource: {source}\n\nGit owns definitions and verified completion.\n\n{item.pop("body")}\n'
    return results


def differences(item, existing, parent):
    if not existing: return ['create']
    fields = [field for field in ['title', 'description'] if existing.get(field) != item[field]]
    if existing.get('state', {}).get('name') != item['state']: fields.append('state')
    actual_parent = (existing.get('parent') or {}).get('identifier')
    if actual_parent != parent: fields.append('parent')
    return fields


def scan(root):
    # CLI query omits descriptions; inspect every item, including archived keys,
    # rather than treating title search or a cached issue ID as stable identity.
    items = cli(root, 'issue', 'query', '--team', 'FAV', '--limit', 'all', '--include-archived', '--json')
    detailed = []
    for item in items:
        detail = cli(root, 'issue', 'view', item['identifier'], '--json', '--no-comments', '--no-download')
        detail['_project'] = (item.get('project') or {}).get('id')
        detail['_milestone'] = (item.get('projectMilestone') or {}).get('id')
        detailed.append(detail)
    return index(detailed)


def project(root, identifier, phase, apply=False):
    context = inspect(root, identifier, phase)
    revision = context['branches'].get('refs/remotes/origin/' + context['preparation_branch']) if phase == 'prepare' else context['target_sha']
    if not revision:
        raise ValueError('publish signed preparation artifacts before projection; do not project unreviewable local state')
    spec = read(root, revision, context['feature'] + '/spec.md')
    tasks = read(root, revision, context['feature'] + '/tasks.md')
    execution = json.loads(read(root, revision, context['ledger']))
    milestones = cli(root, 'milestone', 'list', '--project', PROJECT, '--limit', 'all', '--json')
    matches = [m for m in milestones if re.match(re.escape(context['id']) + r'(?:\s|$)', m['name'])]
    if len(matches) != 1:
        raise ValueError('missing/ambiguous Linear milestone; owner establishes the matching roadmap projection first')
    milestone = matches[0]['id']
    wanted = desired(context, revision, spec, tasks, execution)
    existing = scan(root)
    report = dict(revision=revision, apply=apply, verified=[], pending=[], retired=execution.get('retired_task_ids', []), changes=[])
    for item in wanted:
        current = existing.get(item['key'])
        if current and current['_project'] != PROJECT:
            raise ValueError('stable key exists in wrong project; stop rather than migrate silently')
        parent = existing[item['parent']]['identifier'] if item['parent'] in existing else None
        changed = differences(item, current, parent)
        if current and current['_milestone'] != milestone: changed.append('milestone')
        report['changes'].append(dict(key=item['key'], fields=changed, parent_key=item['parent']))
        if not apply:
            report['pending'].append(item['key']); continue
        if item['parent'] and not parent:
            raise ValueError('parent story projection missing before task upsert')
        if changed:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md') as description:
                description.write(item['description']); description.flush()
                args = ['issue', 'update', current['identifier']] if current else ['issue', 'create', '--team', 'FAV', '--no-use-default-template']
                args += ['--title', item['title'], '--description-file', description.name,
                         '--project', PROJECT, '--milestone', milestone, '--state', item['state']]
                if parent: args += ['--parent', parent]
                elif current and current.get('parent'): args += ['--clear-parent']
                cli(root, *args, structured=False)
            # Re-read after every mutation, including create responses which have
            # no JSON output in 3.0.0. Fail before a duplicate on ambiguous writes.
            existing = scan(root)
            current = existing.get(item['key'])
        if not current or differences(item, current, parent) or current['_project'] != PROJECT or current['_milestone'] != milestone:
            raise ValueError('projection verification failed for ' + item['key'])
        report['verified'].append(dict(key=item['key'], url=current['url'], identifier=current['identifier']))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('identifier')
    parser.add_argument('--phase', required=True, choices=['prepare', 'implement'])
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(project(Path.cwd(), args.identifier, args.phase, args.apply), indent=2))
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'PROJECTION PENDING: {error}\nReconstruct actual keyed items; do not claim synchronization.\n')


if __name__ == '__main__': main()

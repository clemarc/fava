"""Pinned-CLI projection fixtures; no network credentials or tracker mutations."""
from pathlib import Path
import copy
import json
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/sdd'))
import linear_projection as projection
from test_checks import SPEC, TASKS


class ProjectionTests(unittest.TestCase):
    def context(self):
        return dict(id='R3.5', feature='specs/demo-01-read', ledger='specs/demo-01-read/execution.json',
                    preparation_branch='prepare/r3.5', target_sha='head',
                    branches={'refs/remotes/origin/prepare/r3.5': 'head'})

    def test_stable_keys_parents_and_acceptance_states(self):
        items = projection.desired(self.context(), 'head', SPEC, TASKS, {})
        self.assertEqual([i['key'] for i in items], ['specs/demo-01-read/US1', 'specs/demo-01-read/T001',
                                                 'specs/demo-01-read/T002', 'specs/demo-01-read/T003'])
        self.assertIsNone(items[1]['parent'])
        self.assertEqual(items[2]['parent'], items[0]['key'])
        records = {'tasks': {t: {'state': 'integrated', 'evidence': ['CI']} for t in ['T001', 'T002', 'T003']}}
        items = projection.desired(self.context(), 'head', SPEC, TASKS.replace('[ ]', '[X]'), records)
        self.assertEqual(items[0]['state'], 'In Review')
        self.assertEqual(items[-1]['state'], 'Done')
        with self.assertRaisesRegex(ValueError, 'no verified integration'):
            projection.desired(self.context(), 'head', SPEC, TASKS.replace('[ ]', '[X]'), {})

    def test_duplicate_or_ambiguous_keys_fail_and_titles_are_not_identity(self):
        item = dict(identifier='FAV-1', description='Repository key: specs/demo-01-read/T001\n', title='Any title')
        self.assertEqual(projection.index([item])["specs/demo-01-read/T001"], item)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            projection.index([item, dict(item, identifier='FAV-2')])
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            projection.index([dict(item, description=item['description'] * 2)])
        self.assertEqual(projection.index([dict(item, description='no stable key')]), {})

    def test_dry_run_is_read_only_and_upsert_rechecks_state(self):
        context = self.context()
        items = projection.desired(context, 'head', SPEC, TASKS, {})
        state = {}
        calls = []
        def cli(root, *args, structured=True):
            calls.append(args)
            if args[:2] == ('milestone', 'list'):
                return [dict(name='R3.5 — fixture', id='milestone')]
            if args[:2] == ('issue', 'create'):
                description = Path(args[args.index('--description-file') + 1]).read_text()
                key = description.splitlines()[0].split(': ', 1)[1]
                state[key] = dict(identifier=f'FAV-{len(state)+1}', url='https://linear.app/fixture',
                                  title=args[args.index('--title') + 1], description=description,
                                  state={'name': args[args.index('--state') + 1]},
                                  parent={'identifier': args[args.index('--parent') + 1]} if '--parent' in args else None,
                                  _project=projection.PROJECT, _milestone='milestone')
                return ''
            raise AssertionError(args)
        def read(root, ref, path):
            return SPEC if path.endswith('spec.md') else TASKS if path.endswith('tasks.md') else '{}'
        with patch.object(projection, 'inspect', return_value=context), patch.object(projection, 'read', side_effect=read), \
             patch.object(projection, 'cli', side_effect=cli), patch.object(projection, 'scan', side_effect=lambda root: copy.deepcopy(state)):
            dry = projection.project(Path('/fixture'), 'R3.5', 'prepare')
            self.assertEqual(len(dry['pending']), 4)
            self.assertFalse(any(c[:2] == ('issue', 'create') for c in calls))
            actual = projection.project(Path('/fixture'), 'R3.5', 'prepare', True)
            self.assertEqual(len(actual['verified']), 4)
            before = len([c for c in calls if c[:2] == ('issue', 'create')])
            again = projection.project(Path('/fixture'), 'R3.5', 'prepare', True)
            self.assertEqual(len(again['verified']), 4)
            self.assertEqual(before, len([c for c in calls if c[:2] == ('issue', 'create')]))
            self.assertTrue(all(not c['fields'] for c in again['changes']))


if __name__ == '__main__': unittest.main()

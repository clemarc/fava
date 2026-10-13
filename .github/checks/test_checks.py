from pathlib import Path
import subprocess
import tempfile
import unittest

import aggregate
import native
import sdd

SPEC = '''# Feature: Fixture
Status: approved
Input: Parent roadmap: specs/demo/roadmap.md → entry R1
Supersedes: none
Scope boundary: synthetic fixture only
### User Story 1 - Read a workout (Priority: P1)
Requirements: FR-001, FR-002
## Requirements
- **FR-001**: Read synthetic workouts.
- **FR-002**: Handle empty results.
'''
TASKS = '''## Phase 1: Setup
- [ ] T001 Prepare settings in Fava/Config.swift (FR-exempt: shared setup only)
## Phase 2: User Story 1
- [ ] T002 [P] [US1] Test in FavaTests/ReadTests.swift (FR-001, FR-002)
- [ ] T003 [US1] Implement in Fava/Reader.swift (FR-001, FR-002) (depends on T002)
'''
ROADMAP = '''# Roadmap: Demo
Tracker epic: fixture
Intent: Test
Status: agreed
| ID | Sub-feature | Intent | In scope | Deferred to | Depends on | Directory |
|----|-------------|--------|----------|-------------|------------|-----------|
| R1 | Demo | Test | Reading | none | none | specs/demo-01-read |
'''


class FeatureTests(unittest.TestCase):
    def check(self, spec=SPEC, tasks=TASKS, plan=True):
        return sdd.validate_feature('demo-01-read', spec, tasks, plan)

    def test_specification_and_planning_stages(self):
        self.assertEqual(self.check(tasks=None, plan=False), [])
        self.assertEqual(self.check(tasks=None), [])
        self.assertEqual(self.check(), [])
        self.assertTrue(self.check(plan=False))

    def test_invalid_ids_duplicates_and_story_links(self):
        for spec in [SPEC + '- **FR-001**: duplicate\n', SPEC.replace('FR-002', 'FR-02'), SPEC.replace('Requirements: FR-001, FR-002', 'Requirements: none'), SPEC + '### User Story 1 - Duplicate\nFR-001\n']:
            self.assertTrue(self.check(spec=spec))
        for task in [TASKS.replace('T003', 'T002'), TASKS.replace('[US1]', '[US2]'), TASKS.replace('FR-002', 'FR-999'), TASKS.replace('Fava/Reader.swift', 'some directory'), TASKS.replace('FR-exempt: shared setup only', 'none')]:
            self.assertTrue(self.check(tasks=task))

    def test_coverage_and_dependency_safety(self):
        self.assertTrue(self.check(tasks=TASKS.replace(', FR-002', '')))
        self.assertTrue(self.check(tasks=TASKS.replace('[P] [US1]', '[P] [US1] (depends on T003)')))
        self.assertTrue(self.check(tasks=TASKS.replace('Fava/Reader.swift', 'FavaTests/ReadTests.swift')))
        self.assertTrue(self.check(tasks=TASKS.replace('depends on T002', 'depends on T003')))
        self.assertTrue(self.check(tasks=TASKS.replace('depends on T002', 'depends on T099')))

    def test_completed_requires_verified_tasks(self):
        self.assertTrue(self.check(spec=SPEC.replace('approved', 'completed')))
        self.assertEqual(self.check(spec=SPEC.replace('approved', 'completed'), tasks=TASKS.replace('[ ]', '[X]')), [])

    def test_scoped_ids_and_multiple_trailers(self):
        message = 'feat: reader\n\nSpec: specs/demo-01-read\nTask: T002, T003\nImplements: FR-001 FR-002\n'
        read = lambda p: SPEC if p.endswith('spec.md') else TASKS
        self.assertEqual(sdd.validate_commit(message, ['Fava/Reader.swift'], read), [])
        for wrong in [message.replace('T003', 'T099'), message.replace('FR-002', 'FR-999'), message.replace('Implements:', 'Not-Implements:'), 'feat: reader']:
            self.assertTrue(sdd.validate_commit(wrong, ['Fava/Reader.swift'], read))
        self.assertEqual(sdd.validate_commit('chore: workflow\n\nSDD-Type: tooling', ['.github/workflows/a.yml'], read), [])
        self.assertTrue(sdd.validate_commit('chore: workflow\n\nSDD-Type: tooling', ['Fava/Reader.swift'], read))
        self.assertTrue(sdd.validate_commit('chore: spec\n\nSDD-Type: tooling', ['specs/demo-01-read/spec.md'], read))
        self.assertTrue(sdd.validate_commit('chore: workflow\n\nSDD-Type: imaginary', ['README.md'], read))


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.put('.specify/memory/constitution.md', 'fixture')
        self.put('specs/demo/roadmap.md', ROADMAP)
        self.commit('roadmap')

    def tearDown(self): self.temp.cleanup()
    def git(self, *args): return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.DEVNULL, text=True).strip()
    def put(self, path, text):
        p = self.root / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
    def commit(self, kind):
        self.git('add', '.')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture\n\nSDD-Type: ' + kind)
        return self.git('rev-parse', 'HEAD')
    def validate(self, base=None): return sdd.validate_repo(self.root, base)

    def test_future_directories_and_parent_validation(self):
        self.assertEqual(self.validate(), [])
        self.put('specs/demo-01-read/spec.md', SPEC)
        self.assertEqual(self.validate(), [])
        self.put('specs/demo-01-read/spec.md', SPEC.replace('entry R1', 'entry R9'))
        self.assertTrue(self.validate())

    def test_staged_lifecycle_and_frozen_requirements(self):
        self.put('specs/demo-01-read/spec.md', SPEC)
        approved = self.commit('specification')
        self.put('specs/demo-01-read/tasks.md', TASKS)
        self.put('specs/demo-01-read/plan.md', 'derived')
        self.commit('planning')
        self.assertEqual(self.validate(approved), [])
        self.put('specs/demo-01-read/spec.md', SPEC.replace('Read synthetic', 'Write synthetic'))
        self.commit('specification')
        self.assertTrue(any('immutable' in e for e in self.validate(approved)))

    def test_premature_planning_and_contract_deletion(self):
        base = self.git('rev-parse', 'HEAD')
        self.put('specs/demo-01-read/spec.md', SPEC)
        self.put('specs/demo-01-read/plan.md', 'premature')
        self.commit('planning')
        self.assertTrue(any('merge specification' in e for e in self.validate(base)))
        approved = self.git('rev-parse', 'HEAD')
        (self.root / 'specs/demo-01-read/spec.md').unlink()
        self.commit('specification')
        self.assertTrue(any('cannot be deleted' in e for e in self.validate(approved)))

    def test_agreed_roadmap_freeze(self):
        base = self.git('rev-parse', 'HEAD')
        self.put('specs/demo/roadmap.md', ROADMAP.replace('| Reading |', '| Writing |'))
        self.commit('roadmap')
        self.assertTrue(any('cannot be rewritten' in e for e in self.validate(base)))

    def test_inserted_slice_links_dependencies_and_freeze(self):
        base = self.git('rev-parse', 'HEAD')
        inserted = '| R3.5 | Retention | Test | Saved history | R4 detail | R1 | specs/demo-05-retention |\n'
        detail = '| R4 | Detail | Test | Summary | none | R3.5 | specs/demo-04-detail |\n'
        amended = ROADMAP + inserted + detail
        self.put('specs/demo/roadmap.md', amended)
        self.commit('roadmap')
        self.assertEqual(self.validate(base), [])
        self.assertFalse((self.root / 'specs/demo-05-retention').exists())
        self.put('specs/demo-05-retention/spec.md', SPEC.replace('entry R1', 'entry R3.5'))
        self.commit('specification')
        self.assertEqual(self.validate(base), [])
        for wrong in ['R3', 'R3.50', 'R3.05', 'R3.5.1', 'R3.5x']:
            with self.subTest(parent=wrong):
                self.put('specs/demo-05-retention/spec.md', SPEC.replace('entry R1', 'entry ' + wrong))
                self.assertTrue(self.validate())
        self.put('specs/demo-05-retention/spec.md', SPEC.replace('entry R1', 'entry R3.5'))
        approved = self.git('rev-parse', 'HEAD')
        self.put('specs/demo/roadmap.md', amended.replace('| Saved history |', '| Changed history |'))
        self.commit('roadmap')
        self.assertTrue(any('R3.5: agreed roadmap entries cannot be rewritten' in e for e in self.validate(approved)))

    def test_inserted_slice_invalid_ids_dependencies_duplicates_and_cycles(self):
        inserted = '| R3.5 | Retention | Test | Saved history | none | R1 | specs/demo-05-retention |\n'
        amended = ROADMAP + inserted
        for wrong in ['R0.5', 'R03.5', 'R3.0', 'R3.05', 'R3.5.1', 'R3.5x']:
            with self.subTest(identifier=wrong):
                self.put('specs/demo/roadmap.md', ROADMAP + inserted.replace('R3.5', wrong))
                self.assertTrue(any('malformed roadmap entry' in e for e in self.validate()))
        for depends in ['R3.5', 'R3.50', 'R3.05', 'R1.5', 'R1.5.1', 'R1x']:
            with self.subTest(dependency=depends):
                self.put('specs/demo/roadmap.md', ROADMAP + inserted.replace('| R1 | specs/', '| ' + depends + ' | specs/'))
                self.assertTrue(any('invalid Depends on' in e for e in self.validate()))
        self.put('specs/demo/roadmap.md', amended + inserted)
        self.assertTrue(any('duplicate roadmap entry IDs' in e for e in self.validate()))
        self.put('specs/demo/roadmap.md', amended.replace('| none | none | specs/', '| none | R3.5 | specs/'))
        self.assertTrue(any('roadmap dependency cycle' in e for e in self.validate()))

    def test_reconciliation_coverage(self):
        self.put('specs/demo-01-read/spec.md', SPEC.replace('approved', 'completed'))
        self.put('specs/demo-01-read/plan.md', 'derived')
        self.put('specs/demo-01-read/tasks.md', TASKS.replace('[ ]', '[X]'))
        base = self.commit('planning')
        self.put('specs/_system/demo.md', 'FR-001 (demo-01-read): current\n')
        self.commit('reconciliation')
        self.assertTrue(any('account for FR-002' in e for e in self.validate(base)))
        self.put('specs/_system/demo.md', 'FR-001 (demo-01-read): current\nFR-002 (demo-01-read): current\n')
        self.commit('reconciliation')
        self.assertEqual(self.validate(base), [])

    def test_completed_freeze(self):
        self.put('specs/demo-01-read/spec.md', SPEC.replace('approved', 'completed'))
        self.put('specs/demo-01-read/plan.md', 'derived')
        self.put('specs/demo-01-read/tasks.md', TASKS.replace('[ ]', '[X]'))
        base = self.commit('planning')
        self.put('specs/demo-01-read/plan.md', 'rewrite')
        self.commit('planning')
        self.assertTrue(any('history is frozen' in e for e in self.validate(base)))

    def test_roadmap_invalid_dependency_and_supersession(self):
        self.put('specs/demo/roadmap.md', ROADMAP.replace('| none | specs/', '| R9 | specs/'))
        self.assertTrue(self.validate())
        self.put('specs/demo/roadmap.md', ROADMAP)
        self.put('specs/demo-01-read/spec.md', SPEC.replace('Supersedes: none', 'Supersedes: missing-01-feature'))
        self.assertTrue(self.validate())


class NativeAndAggregateTests(unittest.TestCase):
    def test_applicability(self):
        project = ['Fava.xcodeproj/project.pbxproj']
        self.assertEqual(native.classify(['README.md'], []), 'onboarding')
        self.assertEqual(native.classify(['docs/a.md'], project), 'documentation')
        for path in ['Fava/App.swift', '.github/checks/native.py', 'Fava/Info.plist', 'Fava/Assets.xcassets/a.json']:
            self.assertEqual(native.classify([path], project), 'required')
        with self.assertRaises(ValueError): native.classify(['Fava/App.swift'], [])
        with self.assertRaises(ValueError): native.classify(['Fava/Info.plist'], [])
        with self.assertRaises(ValueError): native.classify(['README.md'], [], project)

    def test_device_discovery(self):
        data = {'devices': {'com.apple.CoreSimulator.SimRuntime.iOS-18-5': [
            {'name': 'iPhone A', 'udid': 'A', 'isAvailable': True},
            {'name': 'iPhone B', 'udid': 'B', 'isAvailable': False},
            {'name': 'iPad A', 'udid': 'C', 'isAvailable': True}]}}
        self.assertEqual(native.select_device(data, 'id=A'), 'A')
        self.assertEqual(native.select_device(data, 'id=C', 'iPad'), 'C')
        with self.assertRaises(ValueError): native.select_device(data, 'id=B')

    def test_specs_and_sdd_tooling_skip_only_native_jobs(self):
        project = ['Fava.xcodeproj/project.pbxproj']
        specs = ['specs/demo/roadmap.md', 'specs/demo-01-read/spec.md',
                 'specs/demo-01-read/contracts/read.json', 'specs/demo-01-read/fixtures/empty.json']
        self.assertEqual(native.classify(specs, project), 'documentation')
        sdd_changes = specs + sorted(native.SDD_ONLY_PATHS)
        self.assertEqual(native.classify(sdd_changes, project), 'sdd-only')
        for path in ['Fava/App.swift', 'FavaTests/ReadTests.swift', 'Fava/Info.plist',
                     'Fava/Assets.xcassets/a.json', 'Fava.xcodeproj/project.pbxproj',
                     'Package.resolved', '.github/ios.json', '.github/checks/native.py',
                     '.github/checks/aggregate.py', '.github/workflows/ios-ci.yml',
                     '.github/workflows/sdd-quality.yml', 'unknown/config.json',
                     'specs/demo-01-read/fixtures/Reader.swift']:
            with self.subTest(path=path):
                self.assertEqual(native.classify(sdd_changes + [path], project), 'required')
        self.assertEqual(native.classify([], project), 'required')
        with self.assertRaises(ValueError): native.classify(specs, [], project)

    def test_fail_closed_aggregate(self):
        self.assertTrue(aggregate.validate('success', 'success', 'success', 'success', 'required'))
        for state in ['onboarding', 'documentation', 'sdd-only']:
            self.assertTrue(aggregate.validate('success', 'success', 'success', 'skipped', state))
            self.assertFalse(aggregate.validate('success', 'success', 'success', 'success', state))
            for gate in range(3):
                results = ['success', 'success', 'success']
                results[gate] = 'failure'
                self.assertFalse(aggregate.validate(*results, 'skipped', state))
        for bad in ['failure', 'cancelled', 'skipped', '', 'missing']:
            self.assertFalse(aggregate.validate(bad, 'success', 'success', 'success', 'required'))
            self.assertFalse(aggregate.validate('success', bad, 'success', 'success', 'required'))
            self.assertFalse(aggregate.validate('success', 'success', bad, 'success', 'required'))
            self.assertFalse(aggregate.validate('success', 'success', 'success', bad, 'required'))
        self.assertFalse(aggregate.validate('success', 'success', 'success', 'skipped', ''))


if __name__ == '__main__': unittest.main()

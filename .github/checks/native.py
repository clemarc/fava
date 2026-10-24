"""Classify native applicability and run real Xcode simulator validation on macOS."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from sdd import implementation_paths

SDD_ONLY_PATHS = {
    '.github/checks/sdd.py',
    '.github/checks/test_checks.py',
    '.github/checks/test_pilot.py',
    '.github/checks/tooling.py',
    '.github/checks/test_tooling.py',
}


def tracked(ref=None):
    args = ['git', 'ls-tree', '-r', '--name-only', ref] if ref else ['git', 'ls-files']
    return subprocess.check_output(args, text=True).splitlines()


def project_exists(paths):
    return any(p.endswith(('.xcodeproj/project.pbxproj', '.xcworkspace/contents.xcworkspacedata')) for p in paths)


def classify(paths, files, base_files=()):
    native = any(p.endswith(('.swift', '.pbxproj', '.xcscheme', '.xctestplan', '.xcworkspacedata', '.entitlements', '.storyboard', '.xib')) or '.xcassets/' in p or p == 'Package.resolved' for p in paths)
    has_project = project_exists(files)
    if project_exists(base_files) and not has_project:
        raise ValueError('Xcode project was removed; native onboarding cannot be re-enabled')
    if not has_project:
        if native or implementation_paths(paths) or 'Package.swift' in files:
            raise ValueError('Native changes require a real Xcode project, shared test scheme and .github/ios.json; onboarding only permits pre-app tooling/docs')
        return 'onboarding'
    documentation = lambda p: (p.startswith('specs/')
        or p.endswith('.md') and p.startswith(('docs/', '.agents/'))
        or p in {'README.md', 'AGENTS.md', '.specify/memory/constitution.md'})
    if paths and not native and all(documentation(p) or p in SDD_ONLY_PATHS for p in paths):
        return 'sdd-only' if any(p in SDD_ONLY_PATHS for p in paths) else 'documentation'
    return 'required'


class Timings:
    """Write best-effort, monotonic phase measurements without changing failures."""

    def __init__(self, family):
        self.family = family
        self.started = time.monotonic()
        self.events = []

    def phase(self, name):
        return _TimedPhase(self, name)

    def unknown(self, name, reason):
        self.events.append({'name': name, 'status': 'unknown', 'reason': reason})

    def write(self, path):
        completed = time.monotonic()
        payload = {
            'schema_version': 1,
            'family': self.family,
            'recorded_at': datetime.now(timezone.utc).isoformat(),
            'whole_job_seconds': round(completed - self.started, 6),
            'events': self.events,
        }
        try:
            destination = Path(path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
            print(f'Native timing evidence: {destination}')
        except OSError as error:
            # A timing write failure must not convert a successful native test to failure.
            print(f'WARNING: could not write native timing evidence: {error}', file=sys.stderr)


class _TimedPhase:
    def __init__(self, timings, name):
        self.timings, self.name = timings, name

    def __enter__(self):
        self.started = time.monotonic()
        return self

    def __exit__(self, exc_type, exc, _traceback):
        event = {'name': self.name, 'seconds': round(time.monotonic() - self.started, 6),
                 'status': 'failed' if exc_type else 'completed'}
        if exc:
            event['error'] = str(exc)
        self.timings.events.append(event)


def run(command, name, capture=False):
    print('+', ' '.join(command), flush=True)
    log = Path('artifacts') / (name + '.log')
    with log.open('w') as stream:
        if capture:
            process = subprocess.run(command, stdout=subprocess.PIPE, stderr=stream, text=True)
            stream.write(process.stdout)
            print(process.stdout, end='', flush=True)
            if process.returncode: raise ValueError(f'{name} failed; inspect {log}')
            return process.stdout
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output = []
        for line in process.stdout:
            stream.write(line)
            print(line, end='', flush=True)
            if capture: output.append(line)
        if process.wait(): raise ValueError(f'{name} failed; inspect {log}')
    return ''.join(output)


def validate_config(config, files):
    if set(config) != {'container', 'scheme'}: raise ValueError('.github/ios.json needs exactly container and scheme keys')
    container, scheme = config['container'], config['scheme']
    if not isinstance(container, str) or not isinstance(scheme, str) or not scheme or scheme.startswith('-'): raise ValueError('container and scheme must be nonempty strings')
    if '..' in Path(container).parts or Path(container).is_absolute() or not container.endswith(('.xcodeproj', '.xcworkspace')): raise ValueError('container must be a repository-relative .xcodeproj or .xcworkspace')
    marker = '/project.pbxproj' if container.endswith('.xcodeproj') else '/contents.xcworkspacedata'
    if container + marker not in files: raise ValueError('configured Xcode container is not tracked')
    shared = [p for p in files if p.endswith('/xcshareddata/xcschemes/' + scheme + '.xcscheme')]
    if not shared: raise ValueError('configured scheme must be shared and tracked')
    testables = any(ET.parse(p).findall('.//TestableReference') or ET.parse(p).findall('.//TestPlanReference') for p in shared)
    if not testables: raise ValueError('shared scheme must include test targets or a test plan; mandatory tests cannot silently disappear')
    for p in files:
        if p.endswith('/project.pbxproj') and 'XCRemoteSwiftPackageReference' in Path(p).read_text():
            if not any(x.endswith('Package.resolved') for x in files): raise ValueError('commit Package.resolved before resolving remote Swift packages')
    return ['-project' if container.endswith('.xcodeproj') else '-workspace', container, '-scheme', scheme]


def select_device(devices, destinations, family='iPhone'):
    eligible = []
    for runtime, entries in devices['devices'].items():
        if '.iOS-' not in runtime: continue
        version = tuple(int(x) for x in runtime.split('.iOS-')[-1].split('-'))
        for device in entries:
            if device.get('isAvailable') and device['name'].startswith(family) and device['udid'] in destinations:
                eligible.append((version, device['name'], device['udid']))
    if not eligible: raise ValueError(f'no available {family} iOS simulator compatible with the scheme; inspect devices/destinations logs')
    return sorted(eligible)[-1][2]


def native_test(family, timings):
    if sys.platform != 'darwin': raise ValueError('Xcode validation requires macOS; no native success can be reported on Linux')
    Path('artifacts').mkdir(exist_ok=True)
    with timings.phase('environment_and_dependency_preparation'):
        config = json.loads(Path('.github/ios.json').read_text())
        args = validate_config(config, tracked())
        run(['xcodebuild', '-version'], 'xcode-version')
        listing = json.loads(run(['xcodebuild', *args[:2], '-list', '-json'], 'schemes', True))
        schemes = next(iter(listing.values())).get('schemes', [])
        if config['scheme'] not in schemes: raise ValueError('configured shared scheme is absent from xcodebuild -list')
        common = ['xcodebuild', *args, '-configuration', 'Debug', '-derivedDataPath', 'artifacts/DerivedData', '-clonedSourcePackagesDirPath', 'artifacts/SourcePackages', '-disableAutomaticPackageResolution', '-onlyUsePackageVersionsFromResolvedFile', '-skipPackageUpdates', 'CODE_SIGNING_ALLOWED=NO', 'CODE_SIGNING_REQUIRED=NO']
        run([*common, '-resolvePackageDependencies'], 'dependencies')
    with timings.phase('simulator_discovery_and_selection'):
        devices = json.loads(run(['xcrun', 'simctl', 'list', 'devices', 'available', '-j'], 'devices', True))
        run(['xcrun', 'simctl', 'list', 'runtimes', '-j'], 'runtimes')
        destinations = run([*common, '-showdestinations'], 'destinations', True)
        udid = select_device(devices, destinations, family)
    destination = 'platform=iOS Simulator,id=' + udid
    # Current production behavior lets xcodebuild boot the destination. Its separate
    # readiness duration is therefore unknowable without changing the test sequence.
    timings.unknown('simulator_boot_and_readiness', 'owned by xcodebuild test in the current pipeline')
    with timings.phase('build_execution'):
        run([*common, '-destination', destination, 'build'], 'build')
    with timings.phase('test_execution'):
        run([*common, '-destination', destination, '-destination-timeout', '120', '-resultBundlePath', 'artifacts/FavaTests.xcresult', 'test'], 'tests')
    # A misconfigured test plan can exit zero while selecting no tests.
    with timings.phase('result_bundle_processing'):
        result = json.loads(run(['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', 'artifacts/FavaTests.xcresult'], 'test-summary', True))
        if result.get('totalTestCount', 0) < 1: raise ValueError('test result contains no tests; select unit/integration/UI targets in the shared scheme')
    timings.unknown('artifact_packaging_and_upload', 'performed by a subsequent GitHub Actions step')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['classify', 'test'])
    parser.add_argument('--base')
    parser.add_argument('--family', choices=['iPhone', 'iPad'], default='iPhone')
    parser.add_argument('--timing-path', default='artifacts/native-timing.json')
    args = parser.parse_args()
    timings = Timings(args.family) if args.mode == 'test' else None
    try:
        if args.mode == 'test': native_test(args.family, timings)
        else:
            paths = subprocess.check_output(['git', 'diff', '--name-only', args.base, 'HEAD'], text=True).splitlines() if args.base else tracked()
            state = classify(paths, tracked(), tracked(args.base) if args.base else [])
            print('Native applicability:', state)
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as stream: stream.write(f'native={str(state == "required").lower()}\nstate={state}\n')
            if os.environ.get('GITHUB_STEP_SUMMARY'):
                with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
                    stream.write(f'Native validation: **{state}**. ' + ('Xcode build/tests required.' if state == 'required' else 'Native build/tests did not run; this is not native test evidence.') + '\n')
    except (ValueError, FileNotFoundError, json.JSONDecodeError, ET.ParseError, subprocess.CalledProcessError) as error:
        print('ERROR:', error, file=sys.stderr); raise SystemExit(1)
    finally:
        if timings:
            timings.write(args.timing_path)


if __name__ == '__main__': main()

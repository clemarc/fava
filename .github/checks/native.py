"""Classify native applicability and run real Xcode simulator validation on macOS."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
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


def native_test(family):
    if sys.platform != 'darwin': raise ValueError('Xcode validation requires macOS; no native success can be reported on Linux')
    Path('artifacts').mkdir(exist_ok=True)
    config = json.loads(Path('.github/ios.json').read_text())
    args = validate_config(config, tracked())
    run(['xcodebuild', '-version'], 'xcode-version')
    listing = json.loads(run(['xcodebuild', *args[:2], '-list', '-json'], 'schemes', True))
    schemes = next(iter(listing.values())).get('schemes', [])
    if config['scheme'] not in schemes: raise ValueError('configured shared scheme is absent from xcodebuild -list')
    common = ['xcodebuild', *args, '-configuration', 'Debug', '-derivedDataPath', 'artifacts/DerivedData', '-clonedSourcePackagesDirPath', 'artifacts/SourcePackages', '-disableAutomaticPackageResolution', '-onlyUsePackageVersionsFromResolvedFile', '-skipPackageUpdates', 'CODE_SIGNING_ALLOWED=NO', 'CODE_SIGNING_REQUIRED=NO']
    run([*common, '-resolvePackageDependencies'], 'dependencies')
    devices = json.loads(run(['xcrun', 'simctl', 'list', 'devices', 'available', '-j'], 'devices', True))
    run(['xcrun', 'simctl', 'list', 'runtimes', '-j'], 'runtimes')
    destinations = run([*common, '-showdestinations'], 'destinations', True)
    udid = select_device(devices, destinations, family)
    destination = 'platform=iOS Simulator,id=' + udid
    run([*common, '-destination', destination, 'build'], 'build')
    run([*common, '-destination', destination, '-destination-timeout', '120', '-resultBundlePath', 'artifacts/FavaTests.xcresult', 'test'], 'tests')
    # A misconfigured test plan can exit zero while selecting no tests.
    result = json.loads(run(['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', 'artifacts/FavaTests.xcresult'], 'test-summary', True))
    if result.get('totalTestCount', 0) < 1: raise ValueError('test result contains no tests; select unit/integration/UI targets in the shared scheme')


def evidence_summary(result, family):
    """Validate the actual xcresulttool summary, including executed test counts."""
    keys = ('totalTestCount', 'passedTests', 'failedTests', 'skippedTests', 'expectedFailures')
    if not isinstance(result, dict) or any(type(result.get(k)) is not int or result[k] < 0 for k in keys):
        raise ValueError('missing_or_invalid_test_counts')
    if result['totalTestCount'] != sum(result[k] for k in keys[1:]):
        raise ValueError('inconsistent_test_counts')
    devices = result.get('devicesAndConfigurations')
    if not isinstance(devices, list) or not devices:
        raise ValueError('missing_device_results')
    for entry in devices:
        device = entry.get('device', {}) if isinstance(entry, dict) else {}
        if (not str(device.get('deviceName', '')).startswith(family)
                or device.get('platform') != 'iOS Simulator'):
            raise ValueError('wrong_simulator_family')
        if any(type(entry.get(k)) is not int or entry[k] < 0 for k in keys[1:]):
            raise ValueError('incomplete_device_counts')
    if any(sum(entry[k] for entry in devices) != result[k] for k in keys[1:]):
        raise ValueError('inconsistent_device_counts')
    if result.get('result') not in {'Passed', 'Failed'}:
        raise ValueError('unknown_test_result')
    if (result['result'] == 'Passed') != (result['failedTests'] == 0):
        raise ValueError('inconsistent_test_result')
    return dict(tests=result['passedTests'] + result['failedTests'] + result['expectedFailures'],
                passed=result['passedTests'], failed=result['failedTests'],
                skipped=result['skippedTests'], expected_failures=result['expectedFailures'],
                result=result['result'])


def evidence_log_text(log, head):
    """Normalize job logs and establish checkout and terminal-log identity."""
    # Both gh's decorated output and connector logs carry ISO timestamps.
    text = '\n'.join(re.sub(r'^.*?\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+Z ?', '', line)
                     for line in re.sub(r'\x1b\[[0-9;]*m', '', log).splitlines())
    checkout = re.findall(r'^\[command\].*git checkout --progress --force ([0-9a-f]{40})$', text, re.M)
    if checkout != [head]:
        raise ValueError('checkout_identity_missing_or_inconsistent')
    if 'Cleaning up orphan processes' not in text:
        raise ValueError('incomplete_job_log')
    return text


def log_evidence(log, head, family):
    """Parse full approved-route job logs without retaining their raw content."""
    text = evidence_log_text(log, head)
    command = '+ xcrun xcresulttool get test-results summary --path artifacts/FavaTests.xcresult'
    if text.count(command) != 1:
        raise ValueError('missing_or_ambiguous_test_summary')
    tail = text.split(command, 1)[1].lstrip()
    try:
        summary, _ = json.JSONDecoder().raw_decode(tail)
    except (ValueError, TypeError):
        raise ValueError('incomplete_test_summary') from None
    parsed = evidence_summary(summary, family)
    build = len(re.findall(r'^\*\* BUILD SUCCEEDED \*\*$', text, re.M)) == 1
    test = len(re.findall(r'^\*\* TEST SUCCEEDED \*\*$', text, re.M)) == 1
    if any(marker in text for marker in ('** BUILD FAILED **', '** TEST FAILED **')):
        raise ValueError('contradictory_native_result')
    return dict(parsed, build_succeeded=build, test_succeeded=test)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['classify', 'test'])
    parser.add_argument('--base')
    parser.add_argument('--family', choices=['iPhone', 'iPad'], default='iPhone')
    args = parser.parse_args()
    try:
        if args.mode == 'test': native_test(args.family)
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


if __name__ == '__main__': main()

"""Experimental shared-build native CI support; not used by production acceptance."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import native

REQUIRED_SUITES = ('FavaTests', 'FavaUITests')


class Timings:
    def __init__(self):
        self.started = time.monotonic()
        self.events = []

    @contextmanager
    def phase(self, name):
        started = time.monotonic()
        try:
            yield
        except Exception as error:
            self.events.append({'name': name, 'seconds': round(time.monotonic() - started, 6),
                                'status': 'failed', 'error': str(error)})
            raise
        else:
            self.events.append({'name': name, 'seconds': round(time.monotonic() - started, 6),
                                'status': 'completed'})

    def write(self, path):
        payload = {'schema_version': 1, 'whole_job_seconds': round(time.monotonic() - self.started, 6),
                   'events': self.events, 'recorded_at': datetime.now(timezone.utc).isoformat()}
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')


def run(command, name, artifacts=Path('artifacts'), capture=False):
    artifacts.mkdir(parents=True, exist_ok=True)
    print('+', ' '.join(command), flush=True)
    log = artifacts / f'{name}.log'
    with log.open('w') as stream:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output = []
        for line in process.stdout:
            stream.write(line)
            print(line, end='', flush=True)
            output.append(line)
        if process.wait():
            raise ValueError(f'{name} failed; inspect {log}')
    return ''.join(output) if capture else ''


def require_macos():
    if sys.platform != 'darwin':
        raise ValueError('shared native spike requires macOS; no portable-product success can be reported on Linux')


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def tree_manifest(root):
    root = Path(root)
    records = []
    for path in sorted(root.rglob('*')):
        details = path.lstat()
        record = {'path': str(path.relative_to(root)), 'mode': stat.S_IMODE(details.st_mode)}
        if path.is_symlink():
            record['type'], record['target'] = 'symlink', os.readlink(path)
        elif path.is_dir():
            record['type'] = 'directory'
        elif path.is_file():
            record['type'], record['size'] = 'file', details.st_size
        else:
            raise ValueError(f'unsupported product entry: {path}')
        records.append(record)
    return records


def verify_tree_manifest(root, expected):
    actual = tree_manifest(root)
    if actual != expected:
        raise ValueError('extracted test products changed modes, symbolic links, or contents')


def environment_details(artifacts):
    xcode = run(['xcodebuild', '-version'], 'xcode-version', artifacts, True).strip()
    sdk = run(['xcrun', '--sdk', 'iphonesimulator', '--show-sdk-version'], 'sdk-version', artifacts, True).strip()
    return {'xcode_version': xcode, 'simulator_sdk': sdk}


def common_build_arguments(artifacts):
    config = json.loads(Path('.github/ios.json').read_text())
    args = native.validate_config(config, native.tracked())
    listing = json.loads(run(['xcodebuild', *args[:2], '-list', '-json'], 'schemes', artifacts, True))
    schemes = next(iter(listing.values())).get('schemes', [])
    if config['scheme'] not in schemes:
        raise ValueError('configured shared scheme is absent from xcodebuild -list')
    common = ['xcodebuild', *args, '-configuration', 'Debug',
              '-derivedDataPath', str(artifacts / 'DerivedData'),
              '-clonedSourcePackagesDirPath', str(artifacts / 'SourcePackages'),
              '-disableAutomaticPackageResolution', '-onlyUsePackageVersionsFromResolvedFile',
              '-skipPackageUpdates', 'CODE_SIGNING_ALLOWED=NO', 'CODE_SIGNING_REQUIRED=NO']
    return config, common


def prepare(args):
    require_macos()
    artifacts, products = Path(args.artifacts), Path(args.products)
    timings = Timings()
    try:
        with timings.phase('environment_and_dependency_preparation'):
            details = environment_details(artifacts)
            config, common = common_build_arguments(artifacts)
            run([*common, '-resolvePackageDependencies'], 'dependencies', artifacts)
        with timings.phase('build_for_testing'):
            run([*common, '-destination', 'generic/platform=iOS Simulator',
                 '-testProductsPath', str(products), 'build-for-testing'], 'build-for-testing', artifacts)
        if not products.is_dir() or not any(products.rglob('*')):
            raise ValueError('build-for-testing did not produce portable test products')
        metadata = {**details, 'schema_version': 1, 'source_sha': args.source_sha,
                    'workflow_run_id': args.workflow_run_id, 'workflow_run_attempt': args.workflow_run_attempt,
                    'container': config['container'], 'scheme': config['scheme'],
                    'product_path': products.name, 'product_manifest': tree_manifest(products)}
        Path(args.metadata).parent.mkdir(parents=True, exist_ok=True)
        Path(args.metadata).write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
    finally:
        timings.write(args.timing_path)


def package(args):
    products, metadata, archive, provenance = map(Path, (args.products, args.metadata, args.archive, args.provenance))
    if not products.is_dir() or not metadata.is_file():
        raise ValueError('cannot package missing test products or build metadata')
    archive.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(products), str(archive)],
        'package-test-products', archive.parent)
    payload = json.loads(metadata.read_text())
    payload.update({'artifact_name': args.artifact_name, 'compressed_size_bytes': archive.stat().st_size,
                    'uncompressed_size_bytes': sum(item.get('size', 0) for item in payload['product_manifest']),
                    'archive_sha256': sha256(archive), 'retention_days': args.retention_days,
                    'package_seconds': round(time.monotonic() - started, 6)})
    provenance.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'archive_sha256': payload['archive_sha256'],
                      'compressed_size_bytes': payload['compressed_size_bytes'],
                      'uncompressed_size_bytes': payload['uncompressed_size_bytes']}))


def extract_and_verify(args):
    archive, provenance, extract_root = map(Path, (args.archive, args.provenance, args.extract_root))
    if not archive.is_file() or not provenance.is_file():
        raise ValueError('missing build artifact or provenance evidence')
    payload = json.loads(provenance.read_text())
    expected = {'source_sha': args.source_sha, 'workflow_run_id': args.workflow_run_id,
                'workflow_run_attempt': args.workflow_run_attempt, 'artifact_name': args.artifact_name,
                'archive_sha256': args.archive_sha256}
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f'artifact provenance mismatch for {key}')
    if sha256(archive) != args.archive_sha256:
        raise ValueError('artifact integrity digest mismatch')
    if extract_root.exists():
        raise ValueError('extraction destination already exists')
    extract_root.mkdir(parents=True)
    run(['ditto', '-x', '-k', str(archive), str(extract_root)], 'extract-test-products', extract_root)
    products = extract_root / payload['product_path']
    if not products.is_dir():
        raise ValueError('artifact does not contain expected test-products path')
    verify_tree_manifest(products, payload['product_manifest'])
    (extract_root / 'verified-provenance.json').write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')


def strings(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)
    elif isinstance(value, str):
        yield value


def test_products(args):
    require_macos()
    artifacts, products = Path(args.artifacts), Path(args.products)
    metadata = json.loads(Path(args.provenance).read_text())
    timings = Timings()
    try:
        with timings.phase('environment_and_configuration'):
            details = environment_details(artifacts)
            if details['xcode_version'] != metadata.get('xcode_version') or details['simulator_sdk'] != metadata.get('simulator_sdk'):
                raise ValueError('Xcode or simulator SDK differs from the build-product provenance')
            _config, common = common_build_arguments(artifacts)
        with timings.phase('simulator_discovery_and_selection'):
            devices = json.loads(run(['xcrun', 'simctl', 'list', 'devices', 'available', '-j'], 'devices', artifacts, True))
            destinations = run([*common, '-showdestinations'], 'destinations', artifacts, True)
            udid = native.select_device(devices, destinations, args.family)
        with timings.phase('simulator_boot_and_readiness'):
            run(['xcrun', 'simctl', 'bootstatus', udid, '-b'], 'bootstatus', artifacts)
        result = artifacts / f'FavaTests-{args.family}.xcresult'
        with timings.phase('test_without_building'):
            run([*common, '-destination', 'platform=iOS Simulator,id=' + udid,
                 '-destination-timeout', '120', '-testProductsPath', str(products),
                 '-resultBundlePath', str(result), 'test-without-building'], 'tests', artifacts)
        with timings.phase('result_bundle_processing'):
            summary = json.loads(run(['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', str(result)],
                                     'test-summary', artifacts, True))
            count = summary.get('totalTestCount', 0)
            suite_text = list(strings(summary))
            suites = {suite: any(suite in item for item in suite_text) for suite in REQUIRED_SUITES}
            if not isinstance(count, int) or count < 1:
                raise ValueError('test result contains no tests')
            if not all(suites.values()):
                raise ValueError('mandatory test suite missing from result evidence')
        report = {**metadata, 'family': args.family, 'test_count': count, 'mandatory_suites': suites,
                  'result_bundle': str(result), 'result_bundle_present': result.is_dir(),
                  'xcode_version': details['xcode_version'], 'simulator_sdk': details['simulator_sdk']}
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    finally:
        timings.write(args.timing_path)


def assess(args):
    reports = [json.loads(Path(path).read_text()) for path in (args.iphone_report, args.ipad_report)]
    expected_families = {'iPhone', 'iPad'}
    families = {report.get('family') for report in reports}
    if families != expected_families or len(reports) != len(families):
        raise ValueError('unexpected, missing, or duplicate device-family evidence')
    for report in reports:
        if report.get('source_sha') != args.source_sha or report.get('workflow_run_id') != args.workflow_run_id or report.get('workflow_run_attempt') != args.workflow_run_attempt:
            raise ValueError('test evidence belongs to another commit, run, or attempt')
        if report.get('artifact_name') != args.artifact_name or report.get('archive_sha256') != args.archive_sha256:
            raise ValueError('test evidence artifact identity mismatch')
        if not report.get('result_bundle_present') or not isinstance(report.get('test_count'), int) or report['test_count'] < 1:
            raise ValueError('missing result evidence or zero executed tests')
        if not all(report.get('mandatory_suites', {}).get(suite) is True for suite in REQUIRED_SUITES):
            raise ValueError('mandatory test-suite evidence is incomplete')
    print(json.dumps({'status': 'accepted', 'families': sorted(families),
                      'test_counts': {report['family']: report['test_count'] for report in reports}}, sort_keys=True))


def parser():
    main = argparse.ArgumentParser(description=__doc__)
    subparsers = main.add_subparsers(dest='mode', required=True)
    prep = subparsers.add_parser('prepare')
    prep.add_argument('--artifacts', default='artifacts')
    prep.add_argument('--products', required=True)
    prep.add_argument('--metadata', required=True)
    prep.add_argument('--source-sha', required=True)
    prep.add_argument('--workflow-run-id', required=True)
    prep.add_argument('--workflow-run-attempt', required=True)
    prep.add_argument('--timing-path', required=True)
    pack = subparsers.add_parser('package')
    for item in ('products', 'metadata', 'archive', 'provenance', 'artifact-name', 'retention-days'):
        pack.add_argument('--' + item, required=True)
    verify = subparsers.add_parser('extract-and-verify')
    for item in ('archive', 'provenance', 'extract-root', 'source-sha', 'workflow-run-id', 'workflow-run-attempt', 'artifact-name', 'archive-sha256'):
        verify.add_argument('--' + item, required=True)
    test = subparsers.add_parser('test-products')
    for item in ('products', 'provenance', 'report', 'timing-path'):
        test.add_argument('--' + item, required=True)
    test.add_argument('--artifacts', default='artifacts')
    test.add_argument('--family', choices=('iPhone', 'iPad'), required=True)
    gate = subparsers.add_parser('assess')
    for item in ('iphone-report', 'ipad-report', 'source-sha', 'workflow-run-id', 'workflow-run-attempt', 'artifact-name', 'archive-sha256'):
        gate.add_argument('--' + item, required=True)
    return main


def main():
    args = parser().parse_args()
    try:
        {'prepare': prepare, 'package': package, 'extract-and-verify': extract_and_verify,
         'test-products': test_products, 'assess': assess}[args.mode](args)
    except (ValueError, FileNotFoundError, json.JSONDecodeError, subprocess.CalledProcessError, ET.ParseError) as error:
        print('ERROR:', error, file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()

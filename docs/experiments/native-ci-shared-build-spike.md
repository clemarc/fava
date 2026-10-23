# Native CI shared-build spike

Status: experimental. The workflow in `.github/workflows/native-ci-shared-build-spike.yml` is manually dispatched and is not an input to `ci-required` or the milestone integration assessor.

## Baseline inspected at 7b2b072

`sdd-quality.yml` calls `ios-ci.yml` only when native validation is required. `ios-ci.yml` creates concurrent `iPhone` and `iPad` jobs on `macos-26`, pins `DEVELOPER_DIR` to Xcode 26.6, and gives each job 30 minutes.

Each matrix job runs `.github/checks/native.py test --family …`. The helper validates `.github/ios.json`, checks the shared `Fava` scheme with `xcodebuild -list`, resolves packages with automatic resolution disabled, intersects `simctl` available iOS devices with `xcodebuild -showdestinations`, builds the selected destination, runs `xcodebuild test`, and rejects an `.xcresult` summary with zero tests. It retains logs and result bundles for five days.

The repository has no `Package.swift` or `Package.resolved`, and `Fava.xcodeproj` has no `XCRemoteSwiftPackageReference`. `Fava.xcscheme` includes both `FavaTests` and `FavaUITests`. `tools/sdd/integration.py` currently maps the two matrix check names to one native result and requires both successful jobs plus coordinator-recorded nonzero counts. This spike does not change that mapping.

The baseline’s simulator boot interval is unknown because `xcodebuild test` owns it. The timing JSON records that explicitly. GitHub’s job timestamps remain the source for queue and runner-allocation time; subprocess timing cannot measure queueing.

## Experimental path

`prepare-native` uses the same Xcode image/configuration and runs `build-for-testing` for `generic/platform=iOS Simulator` with `-testProductsPath`. It packages the resulting `.xctestproducts` using `ditto`, preserving permissions and symbolic links. The artifact has one-day retention and includes only the archive and JSON provenance.

The provenance binds the archive to the source SHA, workflow run and attempt, artifact name, Xcode and SDK strings, archive SHA-256, compressed/uncompressed sizes, retention, and a product-tree manifest. Each test job downloads only that artifact, verifies every binding and digest, extracts it with `ditto`, verifies the manifest, boots an independently selected family-specific simulator, then runs `test-without-building -testProductsPath`. It records a separate result bundle, count, suite evidence, diagnostics, and timing JSON.

`spike-evidence-gate` is fail-closed for a missing/cancelled prepare or matrix job, mismatched source/run/attempt/artifact/digest, missing result bundle, zero tests, and either missing `FavaTests` or `FavaUITests`. Unit fixtures cover those rejection paths. It is intentionally not a required check.

## Benchmark protocol

Use a PR-triggered `ios-build-test` run on the spike SHA as the current-pipeline baseline, then manually dispatch the spike with `mode=shared` for that exact SHA. Do not use an artifact from another run or attempt. Download retained timing/result/provenance artifacts before the one-day expiry and record the following without inferring queue time from subprocess timing.

| Metric | Current | Shared build | Single runner |
| --- | --- | --- | --- |
| Compilation duration | pending | pending | not implemented |
| Simulator setup duration | pending; boot unknown | pending | not evaluated |
| iPhone/iPad test duration | pending | pending | not evaluated |
| Artifact upload/download | n/a | pending | n/a |
| Native job count | 2 | 3 | not evaluated |
| Total runner-minutes | pending | pending | not evaluated |
| End-to-end elapsed time | pending | pending | not evaluated |
| Test counts/evidence completeness | pending | pending | not evaluated |

Treat product portability as unproven until the shared run’s two `test-without-building` jobs and evidence gate pass. The architecture only merits production migration if it saves runner time without worsening critical-path time or reducing the two-family evidence.

## Production migration and rollback

If the experiment succeeds, production work would require a reviewed change to the reusable native workflow, a new isolated evidence parser that recognizes prepare/iPhone/iPad/provenance jobs, fixture coverage for every reject case above, a required-check migration only after live success, and an updated coordinator evidence format. Keep the current matrix workflow available until a protected PR validates the new aggregate. Roll back by restoring the present reusable matrix workflow and `integration.py` mapping; artifacts remain diagnostic only and expire automatically.

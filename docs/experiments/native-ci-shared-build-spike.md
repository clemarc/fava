# Native CI shared-build spike

Status: experimental. The workflow in `.github/workflows/native-ci-shared-build-spike.yml` runs on a PR only when its own spike files change, and is manually dispatchable after it reaches the default branch. It is not an input to `ci-required` or the milestone integration assessor.

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

Use the PR-triggered `ios-build-test` run on the spike SHA as the current-pipeline baseline and the spike’s PR-triggered shared run for that exact SHA. After this workflow is on the default branch, manual dispatch with `mode=shared` is also available. Do not use an artifact from another run or attempt. Download retained timing/result/provenance artifacts before the one-day expiry and record the following without inferring queue time from subprocess timing.

| Metric | Current | Shared build | Single runner |
| --- | --- | --- | --- |
| Compilation duration | iPhone 25.0s; iPad 16.2s | one generic build-for-testing: 54.0s | not implemented |
| Simulator setup duration | selection: 21.8s / 2.1s; boot unknown (owned by `xcodebuild test`) | selection: 37.3s / 2.1s; boot: 307.4s / 230.8s | not evaluated |
| iPhone/iPad test duration | 1,027.1s / 817.6s | 705.6s / 729.9s | not evaluated |
| Artifact upload/download | n/a | upload 3s; download 1s / 4s | n/a |
| Native job count | 2 | 3 (prepare, iPhone, iPad) | not evaluated |
| Total macOS runner-minutes | 32.8 | 36.9 | not evaluated |
| End-to-end elapsed time | 18m42s | 20m05s | not evaluated |
| Test counts/evidence completeness | 41 per family; passing conventional gate | 41 per family; both required suites, `.xcresult`, provenance, and isolated gate accepted | not evaluated |

### Recorded comparison

The controlled comparison used source `29a3c1c1bc4e0e824205f15c519356f0d1d4da8b`, Xcode 26.6 (17F113), and iOS Simulator SDK 26.5 on `macos-26`. The conventional run was [40177650811](https://github.com/clemarc/fava/actions/runs/40177650811); the shared run was [40177650776](https://github.com/clemarc/fava/actions/runs/40177650776), attempt 1. Both started at `2026-10-25T08:41:56Z`, so no material queue delay confounds this observation.

The portable artifact was `native-test-products-40177650776-1-29a3c1c1bc4e0e824205f15c519356f0d1d4da8b` (artifact ID `12593261828`): 15,659,445 bytes compressed, 51,525,462 bytes uncompressed, internal archive SHA-256 `c438e35c6d68c291e1c627c86fd7afed131f342750f2bc21eb54279bce7e8bf1`, and GitHub artifact digest `sha256:3be9a431d8269d2a2d478085b9bb6fb4a7d35fd531af2c5d00808e3fb0d7e10b`. It expires after one day. `ditto` packaging plus manifest verification preserved executable modes and symbolic links. Independent evidence artifacts were `12593625231` (iPhone) and `12593049671` (iPad), also one-day retention.

This is one verified paired observation, not a three-sample performance claim. Although shared compilation eliminated one 16--25 second per-family build and shortened raw test execution, the additional generic build, serial dependency, simulator startup, and artifact workflow raised both measured macOS runner use (+4.2 minutes) and critical path (+1m23s). Retain the current parallel architecture for production; first optimize simulator startup/UI-test variance and collect more paired samples before reconsidering shared build. A single-runner variant was intentionally not implemented because it would serialize the two device-family acceptance paths and make independent evidence weaker.

The prototype also observed two earlier iPad UI-test failures in different `FoundationUITests` methods while the matching conventional iPad job passed. A final independent shared run passed both families and the evidence gate, so this is recorded as UI-test variance rather than a product-portability defect. The gate rejects incomplete evidence; it was corrected to check out the tested source before loading the isolated parser.

Product portability is proven for the recorded run: both `test-without-building` jobs and the evidence gate passed. A production migration still requires repeated paired samples that save runner time without worsening critical-path time or reducing two-family evidence.

## Production migration and rollback

If the experiment succeeds, production work would require a reviewed change to the reusable native workflow, a new isolated evidence parser that recognizes prepare/iPhone/iPad/provenance jobs, fixture coverage for every reject case above, a required-check migration only after live success, and an updated coordinator evidence format. Keep the current matrix workflow available until a protected PR validates the new aggregate. Roll back by restoring the present reusable matrix workflow and `integration.py` mapping; artifacts remain diagnostic only and expire automatically.

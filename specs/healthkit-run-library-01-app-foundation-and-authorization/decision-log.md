# R1 decisions

## DEC-001 Native universal application and platform baseline
Use SwiftUI and iOS/iPadOS 17+, standard Apple frameworks, one app and two test
targets. iPad HealthKit is available from this platform baseline. Keep the Xcode
project in Git; no app package or build-generation dependency is necessary.

## DEC-002 Observable request, not permission
Use a main-actor HealthAccessModel and injectable store adapter. The adapter
requests workout records only with no writes. Completion is neutral; only a
reported HKError.errorUserCanceled maps to cancellation. No persisted request
state or authorization inference; R1 retrieves no workouts.

## DEC-003 Pilot delivery and Linear projection
The owner explicitly authorized one R1–R3 PR and autonomous checkpoint progression.
The validator's exception is restricted to the three exact features descended
from approved PR #3 and requires plans/tasks in the preceding commit plus a
Delivery-Pilot trailer. Preserve all other gates and governance files. Project
Linear through installed CLI commands with stable keys and duplicate detection;
no custom sync service. Physical acceptance keeps specification status unchanged.

## DEC-004 Adopt reviewed Xcode build recommendations
After opening the project in Xcode 27, the owner selected the recommended compiler
diagnostics, script sandboxing, Debug active-architecture builds, Release
whole-module compilation and asset/string symbol generation. Retain these shared
settings for diagnostics, build efficiency and generated resource access. There
are currently no custom build scripts or asset/string catalogs. Keep Swift 5 mode,
iOS/iPadOS 17 minimum and CI's Xcode 26.6 pin. Preserve the existing shared-scheme
launcher identifiers and explicit serial unit/UI tests; Xcode's upgrade-version
metadata records the editor version without changing the CI toolchain. Verify
Debug simulator tests and a Release simulator build before declaring readiness.

# Implementation Plan: R1 App Foundation and HealthKit Authorization

Input: approved spec.md, merged in PR #3. Parent roadmap entry R1.
Delivery: feat/healthkit-run-library-r1-r3; owner-authorized single draft PR pilot.

## Summary
Create a native SwiftUI app and explicit workout-only HealthKit authorization flow,
with injected system dependencies, deterministic tests and real macOS simulator CI.
Do not read workouts in R1. Preserve the approved requirements unchanged.

## Technical Context
Swift 5 language mode on Xcode 26.6; iOS/iPadOS 17.0 minimum (HealthKit on iPad).
Apple SwiftUI, Foundation, HealthKit, UIKit and XCTest only. No app dependencies.
One Xcode project, application target, hosted unit target and simulator UI target.
Shared Fava scheme; .github/ios.json activates existing native CI. Debug synthetic
launch fixtures only; release production always uses HKHealthStore.

## Constitution Check
Native Swift/SwiftUI and both device families: satisfied by universal target.
Local-first, no writes/services/accounts: satisfied by workout read-only request.
Mandatory tests: unit request state-machine, adapter request-scope tests, launch,
navigation, mocked outcome and accessibility/reachability UI tests on both families.
Flow-Forward: merged spec immutable; append-only DEC log; no completed status until
physical-device acceptance. Git owns tasks; Linear projects stable keys through CLI.
Signed API commits with scoped trailers, latest-SHA CI, human merge only.
Single-PR planning exception is documented in docs/process/r1-r3-delivery-pilot.md;
preceding published planning commit required, other lifecycle gates unchanged.
Post-design review: all checks satisfied; no unresolved technical clarifications.

## Architecture and Files
Fava/FavaApp.swift owns one HealthAccessModel for the process lifetime.
Fava/HealthAccess.swift defines availability, request outcomes and observable state;
main-actor model rejects overlapping requests synchronously, before launching work.
Fava/HealthKitAccess.swift adapts HKHealthStore via an injectable workout-request
store. No authorizationStatus inference. Report HKError.errorUserCanceled only as
cancellation; an error otherwise fails, a true success completes neutrally.
Fava/RootView.swift uses a stack with scrollable purpose, request controls and
neutral library destination; VoiceOver announces request-state messages.
FavaTests/HealthAccessTests.swift and FavaUITests/FoundationUITests.swift cover
acceptance behavior. Fava.xcodeproj/project.pbxproj and shared scheme build/test.

## Delivery Phases
Setup project → request-state tests → app/adapter → simulator UI coverage → signed
implementation commit → CI → evidence/task updates → signed checkpoint → latest
CI. R2 starts only after actual compilation and simulator tests pass.

## Verification
Every R1 FR maps to tasks.md. Linux runs deterministic SDD, tooling and fixtures;
Xcode build and simulator tests run in Actions (iPhone and iPad). SC-001 measured
launch timing, SC-004/005 device installation/comprehension and SC-006 actual
VoiceOver/system permission experience remain manual; no invented results.

## Complexity Tracking
No application dependencies or extra services. Single narrow process exception
implements the explicit user instruction without changing governance contracts.

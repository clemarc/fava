# Tasks: R1 App Foundation and HealthKit Authorization

Input: approved spec.md and plan.md. Stable keys: feature directory/T-ID.
Tests mandatory; completion requires recorded evidence in verification.md.

## Phase 1: Setup
- [X] T001 Create universal application and unit/UI test targets in Fava.xcodeproj/project.pbxproj and Fava.xcodeproj/xcshareddata/xcschemes/Fava.xcscheme (FR-exempt: shared native build foundation). Verify real Xcode build/test discovery in CI.

## Phase 2: User Story 1 — Launch and navigate
- [X] T002 [US1] Implement launch, scrollable initial purpose and neutral library navigation in Fava/FavaApp.swift and Fava/RootView.swift (FR-001, FR-002, FR-003, FR-012) (depends on T001). Verify FoundationUITests launch/back/relaunch and large text reachability on both families.
- [X] T003 [US1] Automate launch, navigation and accessible control checks in FavaUITests/FoundationUITests.swift (FR-001, FR-002, FR-003, FR-012) (depends on T002). Preserve manual launch timing/device walkthrough in quickstart.md.

## Phase 3: User Story 2 — Deliberate access
- [X] T004 [US2] Test explicit initiation, neutral completion, repeat/concurrency guard and fresh session in FavaTests/HealthAccessTests.swift (FR-002, FR-004, FR-006, FR-007, FR-009, FR-011, FR-012) (depends on T001). Run on simulator, synthetic callbacks only.
- [X] T005 [US2] Implement request state controller and workout-only HealthKit adapter in Fava/HealthAccess.swift and Fava/HealthKitAccess.swift and Fava/Info.plist and Fava/Fava.entitlements (FR-002, FR-004, FR-006, FR-007, FR-009, FR-011, FR-012) (depends on T004). Verify scope through injected store and state tests.

## Phase 4: User Story 3 — Recover
- [X] T006 [US3] Test and implement unavailable, failure, reported cancellation, retry and background-safe state in FavaTests/HealthAccessTests.swift and Fava/HealthAccess.swift (FR-005, FR-006, FR-008, FR-009, FR-010, FR-012, FR-013) (depends on T005). Assert no request for unavailable source and no fabricated permission state.
- [X] T007 [US2] [US3] Add deterministic synthetic outcome UI tests and VoiceOver state announcements in FavaUITests/FoundationUITests.swift and Fava/RootView.swift (FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013) (depends on T006). Verify controls, progress, neutral messages, retry, navigation and large text.

## Phase 5: Verification
- [X] T008 [US1] [US2] [US3] Activate mandatory native CI via .github/ios.json and .github/workflows/ios-ci.yml and record verified build, simulator counts, convergence and device obligations in specs/healthkit-run-library-01-app-foundation-and-authorization/verification.md (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013) (depends on T003, T007). R1 exit requires latest-SHA native and deterministic CI success.

## Dependencies and implementation strategy
T001 → T002 → T003; T001 → T004 → T005 → T006 → T007; both → T008.
Write request tests before implementation. Test-file tasks are deliberately
sequential to avoid conflicting edits. Unit/UI test execution may be independent
once implemented; no open task is marked parallel with unmet dependencies.
US1 is the navigation MVP; US2 and US3 complete R1 before the native checkpoint.
No R2 implementation begins until R1 native CI actually passes.

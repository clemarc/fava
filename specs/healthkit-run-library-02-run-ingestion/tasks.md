# Tasks: R2 Run Ingestion

Input: approved spec.md, plan.md; R1 source checkpoint passed. Verification.md owns
completion evidence. Stable keys feature directory/T-ID; tests mandatory.

## Phase 1: User Story 1 — Accessible running history
- [X] T001 [US1] Author mixed-activity, all-history, identity and source-value adapter tests in FavaTests/RunIngestionTests.swift (FR-001, FR-002, FR-003, FR-004, FR-005, FR-012). Verify missing/zero distance and recorded duration differing from elapsed.
- [X] T002 [US1] Implement source observation and unlimited running query in Fava/RunRecord.swift and Fava/HealthKitWorkoutReader.swift and update Fava.xcodeproj/project.pbxproj (FR-001, FR-002, FR-003, FR-004, FR-005, FR-012) (depends on T001). Spy checks actual query parameters, no authorization/writes.

## Phase 2: User Story 2 — Repeatable saved observations
- [X] T003 [US2] Author ten-repeat, duplicate/tied identities, overlap, atomic snapshot replacement and relaunch/interruption tests in FavaTests/RunIngestionTests.swift (FR-003, FR-006, FR-007, FR-008, FR-009, FR-013) (depends on T002).
- [X] T004 [US2] Implement snapshot retention and guarded attempt state in Fava/RunSnapshotStore.swift and Fava/RunIngestion.swift and wire controller lifetime in Fava/FavaApp.swift (FR-003, FR-006, FR-007, FR-008, FR-009, FR-013) (depends on T003). Preserve saved empty/nonempty on failed/unavailable/interrupted attempts; complete successful replacement only.

## Phase 3: User Story 3 — Honest outcomes and recovery
- [X] T005 [US3] Test and implement not-requested/loading/nonempty/empty/failed/unavailable, cache errors, explicit retry and background/relaunch behavior in FavaTests/RunIngestionTests.swift and Fava/RunIngestion.swift (FR-007, FR-008, FR-010, FR-011, FR-012, FR-014) (depends on T004). Distinguish saved provenance and reject malformed/partial results; no automatic authorization.
- [X] T006 [US1] [US2] [US3] Verify R1 regression, R2 unit fixtures, native builds and latest-SHA CI; record convergence and manual obligations in specs/healthkit-run-library-02-run-ingestion/verification.md (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014) (depends on T005). No completion without actual evidence.

## Dependencies and strategy
Sequential T001 → T002 → T003 → T004 → T005 → T006. Tests precede corresponding
implementation. Query and persistence tests share a file, so no misleading [P]
markers. Once complete, independent test methods can run in normal XCTest order.
R2 changes no library screen or permission flow. R3 entry/refresh triggers follow
only after this checkpoint passes.

# Tasks: R3 Run Library

Input approved spec.md and plan.md; R2 native checkpoint passed. Stable repository
keys feature/US-ID and feature/T-ID. Verification.md supports every completion.

## Phase 1: User Story 1 — Browse summaries
- [ ] T001 [US1] Author full-history chronological/tied identity, locale/time-zone, recorded duration and missing/zero/conversion formatting tests in FavaTests/RunLibraryTests.swift (FR-001, FR-002, FR-003, FR-004, FR-011, FR-012).
- [ ] T002 [US1] Implement row ordering/formatting and native accessible list in Fava/RunLibraryPresentation.swift and Fava/RunLibraryView.swift (FR-001, FR-002, FR-003, FR-004, FR-011, FR-012) (depends on T001). No cap or source mutation; vertical text wraps and native scrolling.

## Phase 2: User Story 2 — Honest attempts and saved provenance
- [ ] T003 [US2] Test all attempt/saved-empty/nonempty combinations, entry/refresh/overlap/retry, successful-empty replacement and relaunch in FavaTests/RunLibraryTests.swift and FavaUITests/RunLibraryUITests.swift (FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014) (depends on T002).
- [ ] T004 [US2] Integrate deliberate entry/read controls, notices, saved provenance and background return in Fava/RootView.swift and Fava/RunLibraryView.swift and Fava/FavaApp.swift (FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014) (depends on T003). Never auto-authorize or trigger reads on recomputation/settings dismissal.

## Phase 3: User Story 3 — Exact identity selection
- [ ] T005 [US3] Implement/test source-UUID selection handoff and accessible selected state in Fava/RunLibraryPresentation.swift and Fava/RunLibraryView.swift and FavaTests/RunLibraryTests.swift and FavaUITests/RunLibraryUITests.swift (FR-002, FR-011, FR-015) (depends on T004). Matching summaries select distinct identities; no detail screen.

## Phase 4: User Story 4 — Distance settings
- [ ] T006 [US4] Test device resolver/default/fixed overrides, local relaunch and zero read/source mutation on preference change in FavaTests/RunLibraryTests.swift (FR-004, FR-011, FR-016, FR-017) (depends on T005).
- [ ] T007 [US4] Implement retained modes, accessible settings sheet and one-action return in Fava/DistanceSettings.swift and Fava/RunLibraryView.swift and Fava/FavaApp.swift (FR-004, FR-011, FR-016, FR-017) (depends on T006).

## Phase 5: Verification
- [ ] T008 [US1] [US2] [US3] [US4] Add isolated DEBUG fixtures and both-family simulator UI coverage, including every Dynamic Type category and largest-size settings, in Fava/SyntheticLibraryFixtures.swift and FavaUITests/RunLibraryUITests.swift and Fava.xcodeproj/project.pbxproj (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017) (depends on T007). Real local storage in synthetic relaunch tests; no production fixtures.
- [ ] T009 [US1] [US2] [US3] [US4] Run complete R1–R3 regression, latest signed commit/native CI, convergence and final consistency review in specs/healthkit-run-library-03-run-library/verification.md (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017) (depends on T008). Update tasks/Linear only with evidence; document manual acceptance and PR review readiness, never merge.

## Dependencies and strategy
Sequential T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009.
Shared view/test files make parallel task edits inappropriate; tests can execute
independently after implementation. Start with list summaries, then state/entry
integration, selection, settings and synthetic end-to-end regression. Tests precede
related code. No R4 work or requirement changes. Physical walkthroughs remain
pending and are not falsely marked complete by automated implementation tasks.

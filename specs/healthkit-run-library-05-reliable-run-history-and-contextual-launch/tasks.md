# Tasks: R3.5 reliable run history and contextual launch

Input: approved spec.md, plan.md, research.md, data-model.md and
contracts/history-and-navigation.md in this directory. Tests are mandatory.
Write acceptance/failure assertions before their production changes within each
task, then integrate only a coherent passing task PR. All tasks remain pending.

## Phase 1: Setup

Reuse the existing app, shared scheme and iPhone/iPad matrix. No initialization
or new dependency task is needed. The implementation coordinator first registers
the actual owner preparation merge through a gated execution metadata checkpoint.
That checkpoint is process evidence, not application implementation or a task ID.

## Phase 2: Foundational storage and read model

- [x] T001 Implement schema-2 history validation and schema-1 read-only adoption in Fava/RunHistory.swift, Fava/RunRecord.swift and Fava/RunSnapshotStore.swift; register source/tests in Fava.xcodeproj/project.pbxproj and add FavaTests/RunSnapshotStoreTests.swift for absent versus unreadable, populated/empty legacy with capturedAt seeded as prior observation/per-row time, genuinely absent/null time remaining unknown, malformed present time recovery, first-save migration, atomic save/reset and injected failure preserving bytes. Introduce the typed store API additively and keep the existing RunSnapshotStoring caller/conformer contract working until its later coordinated activation; this task changes no production read behavior. Constraints: UUID unique; finite nonnegative duration/distance; missing and zero differ; every provenance/returned key belongs to history; only genuine not-found is absent. (FR-005 FR-009 FR-012 FR-018 FR-019)
- [x] T002 [US2] [US3] [US1] Implement retained UUID union, independent source/save attempt outcomes, injected clock, local recovery/reload and separate transport/generation guards in Fava/RunIngestion.swift; activate the additive typed store contract and migrate all affected callers/conformers in Fava/FavaApp.swift, Fava/RunSnapshotStore.swift, Fava/SyntheticLibraryFixtures.swift, Fava/RunLibraryView.swift, Fava/RunLibraryPresentation.swift and Fava/RootView.swift, with FavaTests/RunIngestionTests.swift, FavaTests/RunLibraryTests.swift and FavaUITests/RunLibraryUITests.swift updated in the same task. At activation, ship minimum truthful saved-history/latest-saved-observation notices, per-row returned/unobserved/unknown membership and known/unknown last-observed times, plus independent current source/save outcomes. Never label the whole retained union as returned by the latest read. Include minimum A/B→B/C, repeated-empty and save-failure (populated, absent and saved-empty history) controlled-clock fixture/app wiring and actual FavaUITests/RunLibraryUITests.swift assertions for these states in this same task. Expose actionable local-recovery error/local Retry before contextual routing, saved observation count versus retained count, accessible non-color row/outcome states, prior-session labels, and new-read Retry without successful-empty claims after saving failure. Assert exact unchanged saved rows/summaries/membership/times through failure and relaunch, including known legacy membership with unknown time. Preserve exhaustive state handling and replace superseded empty-deletion expectations immediately; remove any transitional API only after all consumers compile. Cover duplicate/partial/failure/unavailable/save-failure and relaunch without active work. Saved rows/provenance change only after whole-document persistence; local recovery blocks source overwrite; local Retry makes zero source calls. (FR-002 FR-004 FR-005 FR-006 FR-007 FR-008 FR-009 FR-010 FR-015 FR-016 FR-018) (depends on T001)

## Phase 3: US1 — Return directly to useful runs (P1)

Independent test: populated, absent, empty, legacy and unreadable launch contexts;
rows before held source completion; exact entry/request counts and navigation.

- [x] T003 [US1] Add explicit launch/entry coordination in Fava/LaunchContext.swift, Fava/RootView.swift and Fava/FavaApp.swift, adding minimum absent/empty/populated/corrupt/read-error/local-retry fixture controls in Fava/SyntheticLibraryFixtures.swift with FavaTests/LaunchContextTests.swift registered in Fava.xcodeproj/project.pbxproj; update raw-launch/deliberate-entry and back/access helpers in FavaUITests/RunLibraryUITests.swift and FavaUITests/FoundationUITests.swift in this same task, asserting recovery/error/local-retry UI and zero source overwrite as well as populated direct-launch behavior. Test populated→library, absent/empty→setup, unreadable→recovery, successful local retry routing, one initial/deliberate entry read, active reuse and no reads on foreground/layout/recomputation. Preserve a working deliberate-access return path until the Settings access task integrates (for example, keep setup beneath the initially displayed library); do not remove access assertions to accommodate direct launch. Ordinary empty or save failure must leave the entered library visible; restore zero active read/access requests. (FR-001 FR-002 FR-004 FR-016 FR-018 FR-019) (depends on T002)
- [ ] T004 [US1] Extract/expand Settings in Fava/SettingsView.swift and Fava/RunLibraryView.swift, wire the existing deliberate HealthAccessModel through Fava/RootView.swift, register the new source in Fava.xcodeproj/project.pbxproj, and extend FavaTests/LaunchContextTests.swift plus FavaUITests/FoundationUITests.swift and FavaUITests/RunLibraryUITests.swift for one-action Settings/Done, Device/Kilometres/Miles, access discoverability and zero automatic requests/reads. Keep workout-only non-overlap and distinct completion/failure/cancellation/unavailable guidance; preserve R1 setup fixtures. (FR-003 FR-004 FR-014 FR-015 FR-017) (depends on T003)

## Phase 4: US2 — Preserve changing source visibility (P1)

Independent test: A/B→B/C→empty twice→failure/unavailable→relaunch, exact durable
rows/metadata and fresh-read retry after saving failure, including no prior rows.

- [ ] T005 [US2] Expand FavaTests/RunIngestionTests.swift and FavaTests/RunSnapshotStoreTests.swift with the full retention/migration matrix beyond the passing T002 regression baseline; superseded replacement assertions were already updated at T002 activation. Assert A/B/C union with returned count two, complete B summary replacement including nil/zero, unobserved A preservation, duplicate delivery versus equal-looking distinct UUIDs, empty-only observation advance, partial failure rejection, exact prior view on saving failure with populated/absent/prior-empty storage, fresh-read Retry, preserved capturedAt-derived times and genuinely untimed legacy unknowns through migration/save failure/relaunch, and offline relaunch. (FR-005 FR-006 FR-007 FR-008 FR-009 FR-010 FR-016 FR-017 FR-018) (depends on T004)

## Phase 5: US3 — Explain freshness and recover deliberately (P2)

Independent test: saved/returned/unobserved/unknown row labels remain distinct
from loading, current empty, source failure, unavailable and local saving failure.

- [ ] T006 [US3] Expand the already truthful saved-history/observation/current-attempt/recovery presentation established with retention activation in Fava/RunLibraryPresentation.swift and Fava/RunLibraryView.swift, with FavaTests/RunLibraryTests.swift and same-task acceptance/failure assertions in FavaUITests/RunLibraryUITests.swift plus minimum subset/empty/save-failure/controlled-time fixture wiring in Fava/SyntheticLibraryFixtures.swift and Fava/FavaApp.swift for expanded layout/guidance/accessibility coverage of the passing prior-versus-current wording and latest saved returned count/time, per-run unknown/last-observed/unobserved labels, source-success/save-failure feedback, conditional Health/system Settings guidance and disabled controls while any transport drains. Preserve stable source ordering, exact UUID handoff and unit-only formatting; use text/accessibility values and outcome announcements without color dependence. (FR-002 FR-004 FR-007 FR-008 FR-009 FR-010 FR-014 FR-015 FR-016 FR-017) (depends on T005)

## Phase 6: US4 — Clear local history intentionally (P2)

Independent test: cancellation/failure preserve state; success survives relaunch
and no pre-clear callback restores data; later explicit entry may reimport.

- [ ] T007 [US4] Implement confirmed durable clear in Fava/RunIngestion.swift and Fava/RunSnapshotStore.swift with FavaTests/RunIngestionTests.swift and FavaTests/RunSnapshotStoreTests.swift; test empty tombstone removes all run/observation metadata, legacy/corrupt clearing, clear failure preserves generation/data, both read-save/clear orders and late success/empty/failure/duplicate callbacks. Keep this clear model unexposed to user actions until the following confirmation/navigation UI task integrates; no unconfirmed destructive entry point is introduced. Retain the physical in-flight guard until callback drain, allow no concurrent read or queued automatic reimport, and preserve units/system access. (FR-011 FR-012 FR-013 FR-017 FR-018 FR-019) (depends on T006)
- [ ] T008 [US4] Add Settings destructive confirmation/cancel/failure retry and success→setup navigation in Fava/SettingsView.swift, Fava/RootView.swift and Fava/LaunchContext.swift; reset transient selection in Fava/RunLibraryPresentation.swift only after durable clear and extend FavaTests/LaunchContextTests.swift for no navigation/read/request on cancel/failure, success dismissal/setup, unchanged units and later deliberate reimport. Add minimum clear failure/held-late-callback fixture controls in Fava/SyntheticLibraryFixtures.swift and Fava/FavaApp.swift and same-task FavaUITests/RunLibraryUITests.swift assertions for confirmation copy/roles/accessibility, cancellation, failed-clear retry with unchanged rows/route, successful dismissal/setup, relaunch, stale callback rejection and later reimport. Confirmation names all local data, unchanged HealthKit/permissions and possible reimport; all controls remain accessible. (FR-001 FR-003 FR-011 FR-012 FR-013 FR-014 FR-015 FR-017 FR-019) (depends on T007)

## Phase 7: Whole-flow acceptance and evidence

- [ ] T009 [US1] [US2] [US3] [US4] Expand the already integrated minimal isolated DEBUG-only fixtures in Fava/SyntheticLibraryFixtures.swift and Fava/FavaApp.swift for sequenced subset/empty, versioned legacy/corrupt/read-error files, local retry, save/clear failure, injected clock, held/late callbacks and 1,000 saved runs; keep R1 fixtures isolated and release providers unchanged; exercise fixture integration in FavaTests/RunIngestionTests.swift. (FR-001 FR-002 FR-004 FR-005 FR-006 FR-007 FR-008 FR-009 FR-011 FR-012 FR-013 FR-016 FR-018 FR-019) (depends on T008)
- [ ] T010 [US1] [US2] [US3] [US4] Extend FavaUITests/RunLibraryUITests.swift and FavaUITests/FoundationUITests.swift for contextual launch, saved rows during held/failed/unavailable reads, subset/empty/save-failure provenance with/without rows, recovery/retry, one-action Settings/access/Done, clear cancel/fail/success/late result/relaunch/reimport, exact selection and persisted units. Expand the already passing helpers/assertions maintained by T002–T008; cover all 12 Dynamic Type categories, scroll reachability and exposed selected/enabled/destructive/outcome states on both families. (FR-001 FR-002 FR-003 FR-004 FR-005 FR-006 FR-007 FR-008 FR-009 FR-010 FR-011 FR-012 FR-013 FR-014 FR-015 FR-016 FR-017 FR-018 FR-019) (depends on T009)
- [ ] T011 [US1] [US3] Add FavaUITests/HistoryPerformanceUITests.swift and register it in Fava.xcodeproj/project.pbxproj; measure synthetic 1,000-run offline launch with source held, assert usable rows/actions within 2 seconds, and preserve source/locale/timezone ordering and lazy rendering. If measurement requires it, cache ordering/formatters in Fava/RunLibraryPresentation.swift without changing source values. Record simulator timing as automated evidence distinct from physical SC-001/SC-006. (FR-001 FR-004 FR-015 FR-016 FR-017) (depends on T010)
- [ ] T012 [US1] [US2] [US3] [US4] Validate complete regression, semantic drift, deterministic gates and actual macOS builds/nonzero iPhone/iPad simulator results; record exact SHAs/jobs/counts, FR/scenario coverage, migration/save/clear/race results and sanitized pending device/accessibility/performance steps in specs/healthkit-run-library-05-reliable-run-history-and-contextual-launch/verification.md and specs/healthkit-run-library-05-reliable-run-history-and-contextual-launch/quickstart.md. Coordinator alone updates specs/healthkit-run-library-05-reliable-run-history-and-contextual-launch/execution.json and task evidence; obtain independent review and actual configured Codex findings before final owner handoff, with actual Linear status. No device result or completion is inferred from CI. (FR-001 FR-002 FR-003 FR-004 FR-005 FR-006 FR-007 FR-008 FR-009 FR-010 FR-011 FR-012 FR-013 FR-014 FR-015 FR-016 FR-017 FR-018 FR-019) (depends on T011)

## Dependencies, ownership and parallel work

The baseline implementation order is T001→T002→T003→T004→T005→T006→T007→T008→T009→T010→T011→T012.
Storage/read foundations precede the US1 navigation increment; it is the first
reviewable UI increment, not a reduced final milestone scope. All four stories
are required for delivery. No writable parallel group is approved at this baseline.
Within each story, tests and production updates share paths; execute serially. Each behavior/API/wording change owns its immediate regression maintenance; T005/T010 add coverage rather than defer fixes needed by earlier gates. Minimal synthetic fixture/app wiring and UI acceptance/failure assertions ship with each behavior change, including truthful provenance at retention activation, recovery and destructive confirmation. Later presentation tasks expand a correct baseline; they cannot defer truthful notices needed by earlier behavior.
Independent read-only review may run in parallel with unrelated research.

The coordinator serializes project.pbxproj registration and all shared files:
RunIngestion.swift, RunLibraryView.swift, RootView.swift, SettingsView.swift,
RunLibraryPresentation.swift, synthetic fixtures and unit/UI test files. Each
task's listed paths are its allowed write scope; obtain a reviewed amendment for
new paths. Only the coordinator writes ledger/tasks/append-only decisions.

## Acceptance and FR coverage

The specification supplies exact scenario text; ranges below include every scenario.

| Approved scenarios / success criteria | Tasks and validation |
| --- | --- |
| US1.1–2, .5, .7; SC-001 | T001–003, T009–011: launch, migration/recovery and pending-read usability |
| US1.3–4; SC-005 | T003–004, T010: entry/request counts and navigation |
| US1.6 | T005–006, T010: values/order/identity/units |
| US2.1–9; SC-002–003 | T001–002, T005–006, T009–010: retention, source/save outcomes, provenance |
| US3.1–5 | T002–006, T009–010: freshness/guidance/overlap/offline |
| US3.6; SC-006 | T004, T006, T008, T010–012: all type sizes plus pending physical VoiceOver/resized iPad |
| US4.1–6; SC-004 | T001, T007–010: confirmation, atomic clear, races, failure and restored/absent app data |
| SC-007 | T012 and quickstart.md: separate pending physical iPhone/iPad record |

| FR | Tasks |
| --- | --- |
| FR-001 | T003 T008 T009 T010 T011 T012 |
| FR-002 | T002 T003 T006 T009 T010 T012 |
| FR-003 | T004 T008 T010 T012 |
| FR-004 | T002 T003 T004 T006 T009 T010 T011 T012 |
| FR-005 | T001 T002 T005 T009 T010 T012 |
| FR-006 | T002 T005 T009 T010 T012 |
| FR-007 | T002 T005 T006 T009 T010 T012 |
| FR-008 | T002 T005 T006 T009 T010 T012 |
| FR-009 | T001 T002 T005 T006 T009 T010 T012 |
| FR-010 | T002 T005 T006 T010 T012 |
| FR-011 | T007 T008 T009 T010 T012 |
| FR-012 | T001 T007 T008 T009 T010 T012 |
| FR-013 | T007 T008 T009 T010 T012 |
| FR-014 | T004 T006 T008 T010 T012 |
| FR-015 | T002 T004 T006 T008 T010 T011 T012 |
| FR-016 | T002 T003 T005 T006 T009 T010 T011 T012 |
| FR-017 | T004 T005 T006 T007 T008 T010 T011 T012 |
| FR-018 | T001 T002 T003 T005 T007 T009 T010 T012 |
| FR-019 | T001 T003 T007 T008 T009 T010 T012 |

Retained IDs: T001–T012. Retired IDs: none. Completion checkboxes require actual
gated integration and verification; physical acceptance is tracked separately.

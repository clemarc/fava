# Implementation plan: R3.5 reliable run history and contextual launch

**Branch**: `prepare/r3.5` | **Date**: 2026-10-16 | **Spec**: [spec.md](spec.md)

## Milestone baseline and execution

Canonical directory: specs/healthkit-run-library-05-reliable-run-history-and-contextual-launch.
Approved main: 922b9c9ab0c25559bfd327fff1b74127e1952f31. Signed owner approvals:
roadmap PR #8 / 0f6b64a2041e015f63369b5ad7c4f871cc053063;
clarified spec PR #9 / a68b6db26ac54de0e83fb451868f54d32b078c34;
governance PR #10 / 70d9c74af0f8448603d7ec818dbbe383649661df.
Resolver inspected live GitHub merges, refs and PR states on 2026-10-16. No earlier
R3.5 prep/task PR or ledger existed. milestone/r3.5 and prepare/r3.5 begin at the
inspected main; preparation targets milestone/r3.5 and is owner-merged only.
execution.json records this baseline; planning_revision stays null until that merge.

R1/R2/R3 integration is PR #7 / ae763f34a17324ff4e51abe6881be479f8638782.
[Research](research.md) identifies source/test inspection and predecessor native
checkpoints; baseline main-push [38920312080](https://github.com/clemarc/fava/actions/runs/38920312080)
passed. Device acceptance remains pending separately. The merged spec's historical
Draft/Feature Branch text does not override approval or the resolved directory.

## Summary

Retain imported UUIDs across complete subset/empty reads, display committed
observation provenance separately from current attempts, launch from saved context,
and clear local history deliberately. Reuse the existing HealthKit reader, access
state machine, source formatting, units and identity selection. Add a content-versioned
history envelope, atomic whole-document commits, recovery state, clear generations
and explicit navigation events. [DEC-001–005](decision-log.md) govern these choices.

Scope is the 19 approved FRs and four stories. R4 detail, new permissions, background
reconciliation, per-run deletion, design overhaul, accounts/backend/iCloud and AI
remain deferred. No contract or predecessor feature file changes are proposed.

## Technical Context

- Language: Swift with the existing compiler settings; SwiftUI, Combine,
  Foundation, HealthKit and UIKit accessibility only.
- Platform: existing iOS/iPadOS deployment target and Xcode 26.6 on macos-26 CI;
  no deployment-target or build-setting change is needed.
- Storage: protected JSON at the existing runs-v1.json path, schema 1 adoption and
  schema 2 atomic commits; units remain separate UserDefaults.
- Tests: XCTest unit/integration and XCUITest through the shared Fava scheme,
  actual iPhone/iPad simulator jobs; deterministic Python/tooling gates on Linux.
- Performance: usable saved-history screen within 2 seconds for synthetic 1,000
  runs without network on supported physical iPhone and iPad (SC-001). Pending
  measurement, never an assertion of current performance.
- Constraints: offline/local-first, synthetic public data, no restored active
  work, one source query at a time, no rows/provenance before successful save.

## Constitution Check

Pre-research and post-design review: pass for preparation scope. Approved contract
and R1–R3 history remain unchanged; decisions are append-only; no third-party app
dependency; tasks map all FRs and stories with mandatory acceptance/failure tests.
Native evidence, independent task review, current CI/signatures and owner planning
merge precede implementation integration. Git owns completion; Linear is projected
only after signed publication. Physical acceptance precedes completion/freeze.
No exception or new product decision is required by this design.

## Project Structure

Existing app/test targets remain. New source: Fava/RunHistory.swift (pure retained
model/merge), Fava/LaunchContext.swift (route/entry coordinator),
Fava/SettingsView.swift (extracted units/access/clear). New tests:
FavaTests/RunSnapshotStoreTests.swift and FavaTests/LaunchContextTests.swift.
Existing RunRecord.swift retains the legacy decoder; RunSnapshotStore.swift,
RunIngestion.swift, RootView.swift, RunLibraryView.swift, RunLibraryPresentation.swift,
FavaApp.swift and synthetic/unit/UI fixtures receive scoped updates. New files
must be registered in Fava.xcodeproj/project.pbxproj by their owning serial task.
Shared scheme already includes unit/UI targets; verify membership rather than
adding unneeded workflow/configuration changes.

Design artifacts: research.md, data-model.md, contracts/history-and-navigation.md,
quickstart.md. tasks.md defines stable task identities and file ownership;
execution.json records pending implementation, not approval or scope.

## Test and migration strategy

Follow [data-model.md](data-model.md) and [contract](contracts/history-and-navigation.md).
Read storage directly: only genuine file-not-found is absent; do not use a
fileExists precheck that could mistake inaccessible storage for empty history.
Legacy populated/empty adoption must preserve original bytes, values and unknown
times; a next-save migration failure leaves the prior document/view intact.
Inject clock and file operations for repeatable tests, including privileged CI
where chmod alone cannot reliably force write failure.

Test A/B → B/C → repeated empty → failure/unavailable → relaunch; duplicate IDs,
equal summaries, nil/zero replacement, and failed source delivery after intermediate
samples. Assert exact saved membership, last-observed times, source returned count
and prior/current labels. Test local-save failure with populated, absent and prior
empty history: no unsaved row/provenance publication, new-read Retry. Recovery
tests preserve corrupt/unsupported/unreadable bytes and allow local retry/clear.

Clear tests cover cancellation, atomic failure, success/relaunch, unreadable and
legacy files, preserved units, both commit/clear orders, old callback success/empty/
failure, duplicate delivery, no overlapping query during stale callback drain and
later explicit reimport. Source success may commit before clear, then clear removes
it; after clear it can never commit. Keep visible library on ordinary empty/save
failure; only launch/explicit navigation/successful clear changes route.

UI tests cover every US acceptance scenario via the matrix in tasks.md, exact
entry/request counts, setup/direct/recovery launches, one-action Settings/Done,
conditional access guidance, selection, offline browsing and 1,000-row pending-read
launch. Preserve R1-only setup fixture isolation. Update only superseded replacement
assertions in R2/R3 tests; retain remaining regression coverage. Every Dynamic Type
category must expose notices/provenance/actions; VoiceOver and resized physical
iPad walkthroughs remain manual. Use lazy List rows and prepare ordering on history
change; reuse locale/timezone-aware formatting if measurement identifies a bottleneck.

## Execution order and ownership

Storage/model foundation → contextual launch/Settings → retained read integration
→ provenance → confirmed clearing → whole-flow UI/performance/regression evidence.
Each task includes its tests before implementation and publishes one coherent
reviewable change; no failing test-only PR is integrated. Shared source/project
files are serialized. Baseline parallel_groups is empty: no speculative [P] markers.
Read-only research/review may run concurrently in isolated roles. A later writable
parallel group needs reviewed disjoint paths and integrated dependencies.

Implementation must register the actual owner preparation merge in a gated metadata
checkpoint before any source commit. New task PRs follow the retained correction
budget and independent review process. Automated readiness is ready-for-owner;
physical iPhone/iPad, accessibility and performance results remain explicit pending
obligations until recorded. See quickstart.md for validation and device steps.

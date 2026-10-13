# R3 implementation and verification record

Initial publication phase: IMPLEMENT → TEST → COMMIT → CI. R3 tasks remained open pending native evidence; the verified checkpoint follows below.
R1 checkpoint: 7bcfec6 / run 38305400468, both families 13 passing tests.
R2 checkpoint: 5c65aa2 / run 38307744070, both families 25 passing tests.
R3 signed planning commit: b65f19645481227cfc9307dbc44fdcf7aa5e74d7.
R2 checkpoint/task/Linear evidence is persisted in that planning commit.

Local deterministic SDD and tooling passed; 22 validator/tooling fixtures and 7
commit-builder fixtures passed. Native execution awaits actual Actions results.
Nine RunLibraryTests authored: chronology/stable ties/2000 records, current locale
and timezone, recorded duration/zero, distance conversion rounding/nil/zero,
Device/fixed preference resolution and changes, persistence/no read/source mutation,
exact UUID selection, six neutral attempt messages, saved empty/nonempty provenance
through loading/failure/unavailability. Seven RunLibraryUITests authored: rows and
selection, saved pending/failed/unavailable rows, empty/failure/retry, saved empty and
relaunch, settings persistence/no spurious read/entry replacement, refresh/active
reentry and row/actions at all 12 Dynamic Type sizes. Existing R1/R2 tests retained.
Expected selected coverage is 41 tests/family; actual counts must be read from CI.

Production flow: explicit library navigation invokes one R2 read, no body/onAppear
read; modal settings leaves library mounted and changing preference does not read.
Rows use complete R2 snapshot, source UUID and stable source-time ordering. Saved
rows and saved-empty provenance remain alongside the current attempt notice.
Refresh/retry guards reuse R2, no authorization; native back stays available.
Settings-only presentation conversion preserves source values/units/IDs. Selection
marks/hands off exact UUID without R4 content. DEBUG fixtures use isolated synthetic
snapshot and preference sessions; release code excludes fixture providers.

Manual acceptance is pending: physical iPhone/iPad installation/HealthKit request
and actual readable workouts, launch measurements, offline end-to-end, VoiceOver
announcements/selected states and resized iPad/all-type-size walkthroughs. See all
three quickstart.md files; no manual-device success is claimed.

Resume: PR #7 / feat/healthkit-run-library-r1-r3. Inspect latest source SHA/native
run, compare successful counts and test logs. At most two scoped corrective cycles
if failing. After passing: convergence, evidence/task/Linear completion, final
consistency, signed evidence commit and latest-SHA CI. Mark PR ready only then;
never merge or enable auto-merge. Do not duplicate any recorded Linear key.

## Native corrective cycle 1

Source 49397491c47c90b1eea9398032e46bdc0478d9a2 was signed and branch-verified, but
GitHub PR head initially remained b65f196 and no source workflow appeared. Closed
and reopened the same draft PR (no merge); head then matched 4939749 and
https://github.com/clemarc/fava/actions/runs/38310496498 started against that SHA.
This publication/event reconciliation is recorded separately from native fixes.

Run 38310496498: SDD, tooling/actionlint and required applicability passed. Actual
Xcode 26.6 application builds succeeded on iPhone and iPad. Test compilation failed:
RunLibraryTests fixture helper run() collided with inherited XCTestCase.run(), so
no-argument fixture calls returned Void. Renamed to fixtureRun throughout that
file, preserving every test/assertion and all production behavior. No native test
success/count claimed from the failed run. Native corrective cycle 1 of 2.

## R3 verified source checkpoint

Latest tested source SHA: f112ed33ffeb6a31256f1ffb764aceda88ccd523, also PR head.
GraphQL VALID/isValid/signedByGitHub and REST verified/valid; branch, parent,
message and complete tree matched. All nine PR commits individually VALID in
final GraphQL review; autoMergeRequest null, PR draft. One native corrective cycle.
Run https://github.com/clemarc/fava/actions/runs/38310796493 completed successfully:
sdd-quality, tooling-validation/actionlint, ci-applicability required,
iPhone native job 115015799830, iPad native job 115015799837, ci-required all passed.
Both Xcode 26.6 builds succeeded. Each xcresult reports 41 tests passed, zero failed:
28 unit tests (7 R1 + 12 R2 + 9 R3) and 13 simulator UI tests (6 R1 + 7 R3).
No R1/R2 regression or skipped mandatory native job. Automated launch smoke passed.

T001/T002: chronology/stable ties/full history, current date/time formatting,
recorded duration/zero, exact distance conversion/rounding and nil/zero passed.
T003/T004: UI and unit tests passed for all attempt notices, saved empty/nonempty
provenance during pending/failure/unavailable, entry/refresh/retry/reentry guards,
empty replacement, relaunch and usable back navigation, with no automatic request.
T005: exact UUID consumer handoff and native accessible selected states passed.
T006/T007: Device/fixed mode behavior, persisted preferences, no read/source mutation,
settings selected controls and one-action return passed, including largest type size.
T008: seven UI tests passed on both families, with every Dynamic Type library/row
reachability category and isolated synthetic cache/defaults. Production uses R2.
T009: full regression, deterministic/native aggregate, signing and consistency review
passed at source checkpoint; final evidence publication must pass latest-head CI.
All nine implementation tasks verified. No physical-device work is marked complete.

Convergence: installed $speckit-converge prerequisite ran after implement/tasks;
reviewed 17 FRs, 4 stories, 9 tasks and DEC-001–004 against source and actual results.
No remaining unbuilt work, no unrequested R4, category permission, service or account.
No convergence tasks appended; tasks.md untouched by converge. Completion markers
updated separately from actual implementation verification. Requirements unchanged.

## Final consistency and resume record

R1, R2 and R3 source checkpoints passed in order. 44 FRs, 10 stories, 23 traced
implementation tasks; all have source/tests/evidence and no unexplained omission.
All three approved specs plus roadmap, constitution, playbook and AGENTS.md match
approved main d6a2f4be72f51f5f734b4c22de362fae07341572 byte-for-byte. Active spec
status wording remains unchanged until physical-device/owner acceptance. Architecture
stays native/local-first, HealthKit authoritative; JSON only a derived observation.
No R4 screen, background updates, search/filter/sort modes or unrelated backend/AI.

Manual acceptance remains pending: actual iPhone/iPad installation and entitlements,
HealthKit allow/decline/re-request/cancel and real readable history, offline flow,
20-launch timing per family and comprehension, VoiceOver outcomes/selected/enabled
states, compact/resized iPad layouts and all Dynamic Type sizes, current device
clock/time-zone/measurement preferences. Record sanitized device/OS/outcome only.

Main ruleset 24928891 is active and preserves PRs, signatures and no-force-push;
it still has no required_status_checks entry. Existing process assigns applying
ci-required in Settings to the owner (docs/process/ci-and-agent-verification.md,
Owner's main ruleset: "verify checks first and let the owner apply these exact
settings"). ci-required now aggregates actual native validation. No repository
ruleset or merge setting changed in this delivery; owner enforcement is an explicit
process follow-up, not a fabricated required-check setting.

Next action after this record is published: verify its signed branch/PR head and
all mandatory latest-SHA CI (including both 41-test native jobs), then update PR
with the exact final SHA/run and mark ready for owner review. Its SHA is discoverable
as branch HEAD; successful final run links are maintained in PR #7. If interrupted,
resume this step without recreating plans/issues, rewriting requirements, or merging.
R1/R2 checkpoint links remain above and in their separate verification.md files.

## Partial physical-iPhone observation, 2026-10-13

The owner reports the app launches, requests HealthKit permissions and displays a
real run on an iPhone 13 mini running iOS 27. Installed revision is unconfirmed.
See the sanitized [device report](../../docs/verification/2026-10-13-iphone-manual-acceptance.md)
for the exact evidence boundary and outstanding checklist. Populated-library
observation is recorded; full R3/device-family acceptance remains open. No story or
feature is marked complete and no source, test, requirement or task was changed.

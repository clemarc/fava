# R3 implementation evidence — native checkpoint pending

Phase IMPLEMENT → TEST → COMMIT → CI. No R3 tasks completed yet.
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

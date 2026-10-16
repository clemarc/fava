# R3.5 validation guide

This is a planned validation procedure, not implementation or passing evidence.
Use synthetic records only in public tests, logs and artifacts.

## Automated validation

After owner preparation merge and implementation, use the existing shared Fava
scheme on a Mac with the pinned Xcode 26.6 and available iOS simulators:

```sh
python3 .github/checks/sdd.py
python3 .github/checks/native.py test --family iPhone
python3 .github/checks/native.py test --family iPad
```

Run from repository root. Retain actual build result, nonzero unit/UI counts and
exact SHA/job URLs from both Actions jobs. Linux checks do not execute Swift.
Use tasks.md's acceptance matrix to account for every scenario and failure class.

Fixture harness extends --run-fixture and --test-session with isolated protected
files/defaults, injected clock and held callbacks. Required cases: absent; legacy
populated/empty; v2 populated/empty; corrupt/unsupported/read-error; local-load
retry; A/B→B/C; repeated empty; failure after intermediate data; unavailable;
save failure with and without prior rows; clear failure; held pre-clear callback;
1,000-run saved launch. Each behavior task defines its minimum fixture names;
T009 expands the combined matrix. Legacy fixtures separately cover valid capturedAt
(preserved prior/per-row times), absent/null time (unknown) and malformed time (recovery).

1. Launch populated with a held read: rows are immediately selectable, history is
   labelled saved, exactly one entry read and zero access requests occur.
2. Commit B/C over A/B: A/B/C remain, B updates completely, A is unobserved, latest
   returned count is two. Commit empty twice: rows/per-run times stay; latest
   observation advances. Fail/save-fail/unavailable: saved metadata stays exact.
3. Launch absent/legacy-empty/corrupt: setup/prior-empty/recovery differ. Local
   retry touches no source; failed retry preserves bytes. Relaunch restores no work.
4. Open Settings, change/relaunch units, open deliberate access, Done: no entry read
   or authorization until explicitly requested. Existing request outcomes remain.
5. Cancel clear, force clear failure, then clear while a held read is active:
   cancellation/failure preserve state; success routes setup and survives relaunch;
   old callback cannot restore rows or notices. No overlapping read during drain.
   A later explicit library entry can reimport the same UUIDs.
6. Exercise every Dynamic Type category, selected/enabled/destructive states,
   scrolling notices and exact UUID handoff on both simulator families.

## Physical acceptance — pending

Record sanitized model/OS, exact installed SHA and outcome per family; never upload
real workouts, screenshots/history or exports. Prior R1–R3 partial iPhone evidence
does not establish these outcomes, and iPad remains separately required.

- On supported compact iPhone and resized iPad, demonstrate saved-history launch,
  first/no-saved setup, deliberate workout-only access and conditional recovery
  guidance. Test completion/cancel/failure/unavailability where reproducible;
  never infer read permission from empty results.
- Demonstrate nonempty, empty/subset where reproducible, retained rows, Refresh,
  offline browsing, units/relaunch and confirmed clearing with source workouts
  and system permissions preserved. Automated synthetic tests cover outcomes
  that cannot be reliably forced with actual HealthKit.
- With synthetic 1,000-run storage and network disabled, record cold-launch usable
  saved-screen time for 20 launches per family (including rows and reachable
  actions), each against the 2-second SC-001 budget. Report device, OS, revision,
  raw timings and failures. Source completion must not be needed for usability.
- Walk all four journeys with VoiceOver and every supported Dynamic Type size;
  report names/roles/selected/disabled/outcome announcements, non-color provenance,
  one-action return, clipping and resized-iPad reachability (SC-006).
- Fresh absent app data shows setup; restored synthetic app data follows normal
  load rules. Make no promise of cloud restoration or permission reset on reinstall.

After automated readiness the milestone stays ready-for-owner. Record both-family
acceptance before proposing completion/freeze; owner main merge remains separate.

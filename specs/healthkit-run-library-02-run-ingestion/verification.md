# R2 implementation evidence — CI pending

Phase IMPLEMENT → TEST → COMMIT → CI. tasks remain open pending native tests.
R1 validated checkpoint: 7bcfec6f49e142f3dc85fa99f3227201f79b636e / run 38305400468.
R2 signed planning: 0182d3f842cf6b73e1dda3a13d5a216483e9a2cc; prerequisites,
analysis and deterministic SDD/tooling passed. 22 validator/tooling and 7 builder
fixtures passed locally. No Xcode or component-test success claimed on Linux.

RunIngestionTests authors 11 acceptance tests: mixed/indoor/outdoor/multi-year
HealthKit workouts and query parameters, exact source recorded values/nil/zero,
partial/error/malformed rejection, ten-repeat UUID dedup/tied summaries, 2000-record
no-cap result, overlap and saved/current separation, successful empty/full replacement,
unavailable/later retry, nonempty/empty relaunch after interruption, cache failures,
file snapshot round-trip/replacement/corruption and independent R1 request state.
No unit or simulator result is marked passed before actual Actions evidence.

Actual HealthKit store issues one running-workout query with no date predicate and
HKObjectQueryNoLimit, never authorization or writes. Failed samples are rejected.
Protected atomic local snapshot persists complete success only; failed or pending
attempt keeps previous records. No loading/permission state is persisted. No new UI
trigger/list, detail, backend, observer or reconciliation has been introduced.

Manual iPhone/iPad access/read demonstrations remain pending; see quickstart.md.
Resume on PR #7 current branch: inspect latest SHA/run, logs and xcresult; permit
at most two scoped corrections if failing. R3 begins only after R1/R2 full native
matrix and mandatory checks pass. Preserve stable Linear keys on any resume.

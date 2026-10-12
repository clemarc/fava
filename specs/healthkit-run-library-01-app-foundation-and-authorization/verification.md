# R1 implementation evidence — native checkpoint pending

Phase: IMPLEMENT → TEST → COMMIT → CI. No tasks marked complete yet.
Approved contract: PR #3, main d6a2f4be72f51f5f734b4c22de362fae07341572.
Preceding signed planning checkpoint: 898d6f67e75baf5bbb5fa6bf8ecd30c73c186648.
PR: https://github.com/clemarc/fava/pull/7 (draft).

Local checks: deterministic SDD and tooling passed; 22 validator/tooling fixtures
and 7 commit-builder fixtures passed. Plists and shared scheme XML parsed.
Linux has no Xcode/Swift: compilation and simulator assertions remain unverified.
No test result or device acceptance is claimed from source inspection.

Acceptance coverage authored: HealthAccessTests (7 tests) covers fresh launches,
explicit and repeated requests, overlap rejection, neutral completion, failure,
reported cancellation/retry, availability transitions and background-safe state;
adapter spy checks workout-only reads/no writes and exact cancellation mapping.
FoundationUITests (6 tests) covers launch/navigation/relaunch, completion/retry,
failure/cancellation, unavailable and active/background states plus action
reachability across all 12 Dynamic Type categories. Native CI matrix runs iPhone
and iPad with the shared scheme. Fixtures are DEBUG-only and synthetic.

Implementation review against plan/spec/tasks found no unrequested workout read,
R4 detail, permission inference, service or account. Current code matches planned
state and adapter contracts. Convergence completion awaits actual native tests.
Existing custom checklist markers preserved; merged spec satisfies their stated
requirements-quality criteria (see checklists/analysis.md).

Manual acceptance remains open: physical installation/HealthKit entitlement,
allow/decline/re-request/cancel/offline/background, actual VoiceOver announcements,
resized iPad layout and every Dynamic Type size; 20-launch timing and comprehension
walkthrough on both families. Record only sanitized device/OS/outcome information.
No physical device is attached to this task.

Resume: inspect latest PR SHA and CI logs. Correct at most two failed-checkpoint
cycles. Only after native build and simulator tests pass, record evidence, complete
verified tasks and project statuses; publish a signed checkpoint and validate latest
SHA. R2 remains pending until the R1 gate passes.

## Corrective cycle 1

Run https://github.com/clemarc/fava/actions/runs/38305185988 at signed
188e696ea10d6e2a7bff3f0c7278852cecff6cc0: SDD, tooling/actionlint and applicability
passed. Xcode 26.6 started on both families, but compilation failed at
HealthAccess.swift:36 (wrapped property accessed before initialization). No native
tests ran. Fixed initialization using a local provider availability value; the
existing fresh-session and unavailable-init tests cover the affected behavior.
No requirements, gates or test assertions were relaxed. Correction 1 of 2.

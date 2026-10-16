# Preparation review: R3.5

Specification baseline: main 922b9c9ab0c25559bfd327fff1b74127e1952f31.
Approved clarified contract: [PR #9](https://github.com/clemarc/fava/pull/9), owner
merge a68b6db26ac54de0e83fb451868f54d32b078c34. Roadmap approval is
[PR #8](https://github.com/clemarc/fava/pull/8); adopted governance is
[PR #10](https://github.com/clemarc/fava/pull/10). Live resolver verified them.

Integration branch: milestone/r3.5. Preparation branch: prepare/r3.5, targeting
that integration branch. The actual prep PR number is registered in execution.json
immediately after opening; its description retains exact tested head/target and
CI/review links. A commit cannot name its own future SHA. No prep merge is predicted.

## Scope and design

[Plan](plan.md), [research](research.md), [model](data-model.md) and
[contract](contracts/history-and-navigation.md) derive the approved 19 FRs/four
stories without changing spec.md, roadmap or predecessor history. Contextual
launch, retained local observations, independent current outcomes, honest freshness,
Settings access and confirmed clear are included. The spec's deferred scope stays
excluded. R1–R3 integrated source/tests and recorded native evidence were inspected;
their physical acceptance remains separate and pending.

## Migration, persistence and concurrency

[DEC-001–005](decision-log.md) choose one protected content-versioned file,
read-only legacy adoption, atomic save-before-publish and generation/transport
separation. Unknown legacy times remain unknown; legacy empty remains prior empty.
Source success/save failure keeps exactly the prior saved rows/provenance and
retries with a fresh source read. Local recovery preserves unreadable bytes until
successful local retry or confirmed clear. Clear writes an empty tombstone before
routing setup/invalidation, preserves units and prevents old callback resurrection
or overlapping queries. Failure preserves prior durable state and navigation.

## Coverage and ownership

[Tasks](tasks.md) contain T001–T012, exact paths, dependencies and FR/US/scenario
matrices. All checkboxes are pending; no retired IDs exist. The serial baseline
has no writable parallel group. Coordinator owns shared ledger/tasks/DEC records,
project membership changes and serialization of overlapping source/test paths.
Read-only research used separate storage and navigation agents; their source/test
findings informed the decisions. Later independent implementation review remains
mandatory. Tests cover storage/migration, outcome/merge, navigation, clear races,
UI accessibility, 1,000-row performance and preserved predecessor behaviors.

## Risks, decisions and review

Synchronous protected JSON commits can affect launch latency; T011 measures and
optimizes within the existing contract. An old noncancellable read can temporarily
disable Refresh after clear; text explains the transport drain, and no queued
automatic import occurs. Unknown/corrupt history cannot be silently overwritten.
Device accessibility/performance results and native implementation results do not
exist yet; quickstart.md specifies their collection. No unresolved product decision
or critical design ambiguity was identified in initial semantic analysis.

Reviewer-owned [preparation checklist](checklists/preparation.md) adds ten unchecked
requirements-quality items. Existing history/clarification/requirements artifacts
are preserved with their historical notes. Owner review of these checklists is
pending; generated markers do not claim approval or implementation completion.

## Initial Spec Kit analysis

Command: speckit-analyze with explicit SPECIFY_FEATURE_DIRECTORY and
SPECIFY_FEATURE_NO_PERSIST=1, after plan → tasks → checklist. All relevant before/
after Git commit hooks were inspected and disabled. Setup/prerequisite scripts
resolved this exact directory; no create-new-feature or stale feature.json was used.
The analysis itself was read-only; this report records its result.

| Detection | Result |
| --- | --- |
| Contract/constitution conflict | None; no scope or completed-history mutation |
| Missing FR/story/scenario coverage | None; tasks.md accounts for 19/19 FRs, four stories and SC-001–SC-007 |
| Dependency/ownership conflict | None; explicit acyclic serial chain, no [P] marker |
| Ambiguity/duplication affecting work | None; legacy, save failure, transport drain and routing are specified |
| Unmapped task or unresolved placeholder | None in generated planning; inherited constitution model/version TODOs are outside scope |

Metrics: 19 functional requirements, seven measurable success criteria, 12 tasks;
100% FR coverage; zero critical/high consistency findings; no remediation needed.
Automatic SDD passed locally. Required fixture/tooling/commit-builder results and
latest signed PR-head CI are retained in the PR description after publication.
These planning checks establish no native implementation or physical acceptance.

## Execution and tracker

execution.json is preparing, all 12 tasks pending, planning_revision null,
physical_acceptance.iPhone/iPad null. It records the actual prep PR immediately
after opening and preserves signed publication/correction history. Linear initially
has 16 pending stable keys (four stories, 12 tasks). Publish/registration precede
dry-run/upsert; actual verified URLs, failures and pending keys belong in its
linear record. The report never infers synchronization from installed tooling.

## Owner handoff

Review design, migration/failure/race coverage, task granularity, serial ownership
and reviewer-owned checklists, then merge the preparation PR into milestone/r3.5
using Create a merge commit. The PR description supplies validated copyable title/
body ending in SDD-Type: planning. Confirm the generated merge trailers in GitHub.
Post-merge verification inspects actual owner/destination/signature/parents/tree/
message and validates introduced history against its first parent; no main-push
run is expected for this destination. Start $fava-milestone-implement R3.5 only
after that owner merge. No application code is implemented by this preparation.

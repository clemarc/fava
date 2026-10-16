# R3.5 design decisions

## DEC-001 — One versioned atomic history document

Keep Application Support/Fava/runs-v1.json as the single authoritative local
observation document, dispatching schema 1 or 2 by content. Adopt valid schema-1
records in memory without rewriting on launch. Its capturedAt is retained only
as legacy capture evidence, never invented as per-run observation time. A legacy
empty snapshot carries a known-prior-empty marker with unknown observation time.
The next accepted source result writes schema 2 by atomic replacement with complete
file protection and backup exclusion. One filename avoids a stale fallback file
resurrecting history after clearing. HealthKit remains authoritative; this is a
derived observation cache. No additional dependency is needed.

## DEC-002 — Commit history and provenance together

Construct an immutable candidate by UUID union, replacing returned summaries
including nil distance, and preserving unreturned summaries. Atomically persist
the entire candidate, latest returned-ID set and observation time before publishing
any row/provenance change. A source success with saving failure is a separate
attempt outcome; it keeps exactly the prior saved view and offers a new source
read on Retry. Never publish an unsaved candidate.

## DEC-003 — Recovery preserves unreadable data

An unreadable/unsupported document enters local recovery, distinct from absent
history. Do not allow source commits to replace it. Deliberate local Retry reloads
the same document; confirmed clear may replace it with a durable empty tombstone.
Neither operation requests authorization. Preserve bytes on decode, validation,
protection and I/O errors; show actionable recovery rather than successful-empty.

## DEC-004 — Serialize clear and accepted reads

RunIngestionModel owns synchronous store commits on MainActor and an independent
transport-in-flight token plus history generation. Successful clear atomically
writes a schema-2 empty tombstone first, then increments generation and invalidates
old results, clears selection and routes to setup. An old HealthKit read remains
in flight until its callback drains; it cannot commit, alter notices or allow a
second overlapping query. Failed clear changes no generation, saved data or route.
Cancellation is best effort only; correctness relies on tokens. After drain,
only a new explicit library entry or Refresh may read. Serial synchronous local
commits avoid actor reentrancy between a candidate save and clear; measure their
cost with the specified 1,000-run launch fixture before changing that boundary.

## DEC-005 — Explicit routes define library entry

A root navigation coordinator selects setup, library or recovery once from local
load context. Initial populated launch displays saved rows independently of the
entry read; start that single read from a guarded initial-entry event after route
installation. Deliberate setup-to-library navigation is another entry. Settings,
access presentation, sheet dismissal, unit changes, scene activation, layout and
view recomputation do not create entries. Settings Done dismisses its whole flow
to the library in one action. Deliberate authorization remains HealthAccessModel's
existing workout-only, non-overlapping request flow.

## DEC-006 — Keep each intermediate task buildable and testable

Independent preparation review found that delaying existing test/helper updates
until T010 would break earlier retention/contextual-launch task PRs. T001 adds
typed storage APIs alongside the existing caller contract; T002 activates them
and migrates all consumers/conformers and immediate retention assertions together.
T003 owns launch/back helper changes; T004 and T006 maintain affected Settings/
notice expectations. T005/T010 expand coverage instead of postponing regression
maintenance. Preserve task IDs and serial ownership; every task still needs
passing current native/CI gates before integration.

# ADR-003: Reconcile the R3.5 preparation merge trailer

Date: 2026-10-17. Status: proposed; activation requires the owner's signed
governance merge into main.

PR [#14](https://github.com/clemarc/fava/pull/14) was owner-merged into
`milestone/r3.5`, with a valid GitHub signature and both expected parents. Its
merge tree matches the reviewed preparation head and introduces no application
code. Its actual message contains only the title and omits `SDD-Type: planning`.
The PR description's trailer does not repair that historical message.

Preserve that immutable merge. Accept only its missing planning trailer after
owner adoption of this decision. The [fixed record](003-r35-preparation-merge-reconciliation.json)
pins the merge SHA, ordered parents, reviewed source tree, original message,
approval PR and destination. Keep the record unchanged; it is not a registry
for future exceptions. R1–R3's separate pilot exception remains unchanged.

Offline validation requires the exact record at both the validation base and
head. It discovers one introducing two-parent merge in the base's full ancestry,
verifies the pinned public GitHub owner signature, requires the record absent
from its first parent and unchanged in its second parent and merge, and checks
a process/tooling trailer, no application delta and the reviewed source tree.
It also verifies the historical preparation identity and owner signature. Only
that historical commit receives an effective planning trailer for validation;
its actual message remains unchanged. Pending commit messages and all other
history use normal validation. Proposal-only, unsigned, changed or ambiguous
evidence cannot activate the exception.

The live resolver additionally verifies that adoption belongs to an actual
owner-merged PR targeting main, and rechecks every retained preparation merge
and its trailers, including #14 after a later planning amendment. When
GitHub's commit-to-PR association omits a milestone merge, the resolver searches
all closed PR pages for one exact merge SHA/destination match and rechecks the
selected PR's actual merged status, SHA, destination and owner. No title,
branch name, ledger assertion or draft marker grants approval.

After owner adoption, bring the approved governance into `milestone/r3.5`
through a separate signed, reviewed synchronization PR with an owner merge.
Ordinary coordinator checkpoints cannot change tooling/process paths. Preserve
`specification_base`, approved requirements, preparation history/correction
counts and all pending task state. Resume the implementation skill only after
that synchronization; it must still register the actual planning merge through
a gated checkpoint before source work.

This decision grants no application acceptance, task completion or main merge
authority. Review, signatures, CI, native tests, chronology, task integration and
physical iPhone/iPad acceptance remain required. Public signing evidence cannot
distinguish owner and agent operations sharing one credential; the existing
owner-review process boundary still applies.

# ADR-005 proposal: selective completion and registration checkpoints

Status: proposed; owner approval absent; activation disabled.

This document does not amend the current rule requiring canonical predecessor
completion before dependent implementation begins. No active milestone record,
checkpoint or signed history is migrated. C014/C015 are not recreated.

## Proposed narrow sequencing amendment

After a predecessor's actual signed integration into the registered milestone
has passed all retained integration gates, the coordinator MAY identify it as
`INTEGRATED_PENDING_COMPLETION` while its completion record is not canonical.
This is an intermediate execution phase, not product completion or a new owner
approval. The coordinator MAY then authorize only the approved immediate
successor's initial source preparation and one initial signed publication, on
an isolated task branch with an actual PR. Every other dependency MUST already
have verified canonical completion. The dependency relationship and exact task
scope MUST come from the approved Git plan/tasks.

The successor MUST NOT publish corrective source or integrate before its own
registration is canonical. After registration, every correction still requires
the existing durable reservation before corrective publication. Subsequent
source publication cannot be disguised as another initial head. Existing branch
protection, retained-head ancestry, three-round counters, independent review,
finding dispositions, qualifying bot review, native/current-target gates and
owner/main authority remain unchanged.

The coordinator MAY publish one atomic signed metadata checkpoint containing
both predecessor completion and successor registration only when both transitions
independently satisfy their invariants. The checkpoint MUST be gated, merged
only into the registered milestone, and post-merge verified. The successor MUST
import the canonical checkpoint through a verified signed pure automatic merge
before further source work. Conflict resolution belongs in separately scoped
source commits under the existing rules; it is not a pure import.

When no successor is ready, successor preparation is delayed, or either transition
cannot safely join, the coordinator MUST use standalone completion checkpointing.
Do not delay durable predecessor completion merely to obtain consolidation.
Reconcile any already-published or ambiguous composite before falling back.

## Atomic record and evidence

Keep the existing execution ledger, task checkbox file and checkpoint branches.
The proposed checkpoint kind is `task-completion-registration`, with one next
checkpoint ID and its matching branch. Its `completion.tasks` names completed
predecessors; their task records retain actual PR, merge, immutable report and
evidence references. Its `registration` contains exact successor task IDs, actual
PR URL and `initial_head`. The existing PR-keyed registration record is still
zero corrections with exactly that initial head. No correction reservation is
combined with completion or registration.

Both ledger and checkbox updates form one exact candidate. Definitions and
unrelated ledger fields remain unchanged. No new physical acceptance claim,
Linear projection, counter edit or erased retained head belongs in this delta.
The predecessor integration must be an actual signed milestone merge with
independently validated completion evidence. Successor source must match its
approved tasks, descend from the predecessor integration and be the actual
pre-opening initial head bound to its PR. Recheck the target before publication
and integration. The usual complete-tree/parent/message/signature verification
and actual post-merge checks remain mandatory.

GraphQL publication is one commit transaction: neither half may become canonical
alone. A digest of the entire ledger+tasks candidate helps synthetic comparison;
it is not a Git tree SHA, signature or approval token. An invalid or partially
valid delta must never authorize publication, integration or successor progress.

## Interrupted operations

Reuse the existing signed-publication and retained-integration recovery helpers.
Before publication, retain expected branch/parent/tree/message identity. A lost
acknowledgement requires authoritative branch inspection before retry; a matching
published candidate is reused. After a lost merge acknowledgement, verify the
actual destination, signed parents/tree and retained gates before recording
completion. A changed target requires refreshed assessment. A failed/cancelled/
timed-out checkpoint cannot establish either canonical transition. A partial or
conflicting canonical record blocks all successor progress and requires
reconciliation, never acceptance of the favorable half.

The inactive synthetic preview distinguishes unchanged canonical base from the
whole candidate using separate digests, and rejects partial/conflicting state.
It models unknown publication, matching existing
candidate, canonical merge, failed checkpoint and conflicting/partial state. It
returns only reconciliation guidance with `accepted: false` and
`activation_enabled: false`. It does not fetch live publication proof or execute
the proposed workflow. Such proof must come from the existing helpers when a
separately reviewed activation is implemented.

## Preparatory implementation and acceptance criteria

`ledger.composite_candidate` checks the complete proposed delta against canonical
Git and current target metadata. It reuses the existing ledger/history, actual
completion verifier and source task/scope helpers. Defaults require actual proof;
synthetic tests inject fixtures. Production transition dispatch does not invoke
it, and the active ledger enum still rejects `INTEGRATED_PENDING_COMPLETION`.
There is no owner-approved boolean or runtime switch that can activate it.

Before activation, the owner must explicitly approve this sequencing exception,
with signed owner adoption and target import under the normal governance process.
A separate reviewed activation change must wire actual scheduling, atomic
checkpoint dispatch and authoritative interrupted-operation recovery, retaining
all existing gates. A main merge of preparatory code does not activate the rule.

The synthetic acceptance suite must cover:

- Valid combined delta; invalid predecessor completion or missing independent
  evidence; invalid successor initial head/signature/chronology and stale target.
- Duplicate completion/registration; completion-only or registration-only partial
  deltas; one exact atomic checkpoint; approved successor dependency/scope.
- Interrupted publication, lost acknowledgement, matching existing candidate,
  failed checkpoint, conflicting/partial canonical state and target movement.
- Standalone completion fallback; unchanged correction reservations/counters;
  retained-head and predecessor/source ancestry; no live activation or new ledger
  state accepted by the current policy.

After approved activation, demonstrate a new synthetic/live pilot checkpoint,
its independent gates, signed publication/merge and successor pure automatic
import. Measure fewer completion-only integrations without changing correction
reservation counts. No active R3.5 replay, historical rewrite or promotion to main
is authorized by this proposal.

Rollback before activation: revert preparatory functions/tests/proposal. After
any future activation, disable new composite scheduling and use the unchanged
standalone flow; retain already signed records and counters without rewriting
history. The native scheduling pilot is independent and grants no sequencing
exception.

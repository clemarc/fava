# Owner-started milestone delivery

This policy is proposed until the owner reviews and merges the governance PR to
main. The prior prohibition on all agent merges remains effective until then.
After adoption, the owner starts two Cloud tasks per milestone:

```text
$fava-milestone-prepare R3.5
$fava-milestone-implement R3.5
```

Roadmap and specification/clarification PRs remain owner-reviewed and
human-merged to main. Preparation starts from main containing those approvals
and adopted governance. It ends with a planning PR targeting the milestone
branch. The owner reviews and merges preparation before starting implementation.
The implementation coordinator may integrate gated task/checkpoint PRs **only**
into the registered milestone branch. It ends with a milestone PR against main
for owner testing, review and human merge. Agents never enable auto-merge.

## Identity and shared resolution

Both skills use `python3 tools/sdd/milestone.py ID --phase prepare|implement`.
The pipe here describes alternatives, not a shell command. Actual examples:

```sh
python3 tools/sdd/milestone.py r3.5 --phase prepare
python3 tools/sdd/milestone.py R3.5 --phase implement
```

The resolver strips surrounding whitespace and uppercases `r`; digits and the
decimal remain exact. R3.50 is distinct from R3.5; R03.5, R3.05, R3.0 and multiple
decimal components are invalid. Search canonical roadmap rows in fetched main;
exactly one ID must match. Never turn R3.5 into directory 03/04/35. R3.5 maps to
`specs/healthkit-run-library-05-reliable-run-history-and-contextual-launch`.
Scope, deferred work and dependencies come from the row and approved contract.
Historical `Feature Branch` metadata does not override execution branches.

The resolver checks signed owner merge history and live GitHub merged PRs for
roadmap, specification and governance. A Draft heading, agreed marker, checklist
checkbox, ledger claim or branch name alone is not approval. The exact merged
contract controls requirements even if its original Draft heading remains.
Dependencies require integrated task/verification evidence on main and their
actual merged PRs; the coordinator inspects underlying tests/source and reports
any pending physical acceptance separately. Unknown/ambiguous IDs, completed
specs/ledgers, missing approvals or contradictory state stop with the artifact,
revision or PR causing the problem.

Read applicable AGENTS, constitution, playbook, signing/CI/Linear guidance, the
approved spec/clarifications, available plan/tasks/research/contracts/checklists,
decision logs and ledger. Set **SPECIFY_FEATURE_DIRECTORY** to the resolved
absolute directory for every Spec Kit invocation and every worker. No reliance
on a previous chat, feature.json, supplied feature path or manually chosen branch.

## Branches and interruption recovery

| Purpose | Deterministic branch | Start revision | PR destination |
| --- | --- | --- | --- |
| Integration | milestone/r3.5 | Inspected approved main | main, at final handoff |
| Preparation | prepare/r3.5 | Inspected milestone head | milestone/r3.5, owner merges |
| Task/batch | task/r3.5/tNNN | Inspected milestone head; lowest batch task ID | milestone/r3.5 |
| Serialized checkpoint | checkpoint/r3.5/cNNN | Inspected milestone head; next ledger checkpoint ID | milestone/r3.5 |

Before any checkout/ref creation, inspect `git status --porcelain`,
`git worktree list --porcelain`, local and freshly fetched remote refs, all PR
states and ledger. Do not reset files/branches, overwrite dirty user work, discard
unpublished commits or blindly regenerate planning. Matching local/remote work
resumes; divergence requires inspection/reconciliation. A dirty or occupied
checkout uses a separate explicitly created clean checkout/worktree. Subagents
do not automatically have worktrees. Never hand two workers the same write paths.

Create absent remote refs with the existing authorized branch API at the exact
inspected parent. Never publish unsigned local commits. The shared resolver's
`--checkout milestone` and `--checkout preparation` create only absent local refs
or switch clean matching ones; they never write remotely. Remote creation and
signed publication follow the existing GraphQL process. Reinspect missing-ref
errors, races and ambiguous API responses before retrying. A branch alone is not
registered approval: its feature, main baseline and reviewed prep must agree.

On restart, fetch again, inspect every matching PR including merged/closed,
check actual target/head, commits, reviews and checks, and reconcile ledger
evidence. A merged task is not repeated; an open matching PR is resumed; a
closed unmerged PR is not automatically reopened. A merged preparation cannot
restart preparation. Existing artifacts require baseline/identity comparison and
a named owner-reviewed planning amendment if regeneration changes approved work.
Retain task IDs for retained work, retire removed IDs permanently, never reuse
them. Integrated task records stay frozen; follow-up work gets new task IDs.

## Durable state and preparation

Git owns requirements, plans, tasks, decisions and completion evidence. The
feature-local execution.json ledger records schema, canonical milestone/feature,
specification_base (full inspected main SHA), milestone branch, prep PR,
planning_revision (actual owner prep merge SHA), state, retired IDs, tasks,
checkpoints, ownership, review findings and Linear projection results. It is not
a second specification. Store evidence URLs/SHAs, not credentials/health data.
Use the committed templates. The coordinator alone updates shared state and
DEC logs; workers return proposed entries. Preserve decisions before regeneration.

Lifecycle order is plan → tasks → checklist → analyze, invoking the installed
Spec Kit skills after their prerequisites exist. Prep performs no application
implementation. Its design includes test strategy, migration/persistence failure,
concurrency and late-result handling, accessibility/performance, exact files,
FR/US/acceptance coverage, dependencies, reviewed safe parallel groups and shared
file ownership. Mandatory tests override optional upstream examples. Generated
quality checklists remain reviewer-owned and unchecked until the reviewer acts;
implementation workers cannot use them as completion evidence. The report
separates decisions resolved in design from product questions requiring owner
approval/supersession. Stop affected work for unresolved critical findings.

Planning_revision is null in the prep PR because its future merge does not yet
exist. After owner merge, implementation verifies and records the actual merge
in a small checkpoint PR, with `SDD-Type: planning`; subsequent source commits
require that checkpoint in their first-parent history. Checkpoint PRs use the
same signing, current CI, independent review and findings gates; scope consists
only of execution metadata/task evidence/append-only decisions, never contracts.
Their native applicability follows the actual diff, not a name-based exemption.

Preparation PRs persist their budget in preparation_prs, keyed by actual PR
number with immutable branch, correction_cycles and append-only heads. Register
count zero after initial publication and before review; before each fix append
the prior head and increment the counter in the signed preparation ledger.
Protect prepare/* against force pushes/deletion and require signatures before
publication; the separate settings proposal describes these additional rules.
The resolver returns preparation_progress for fresh invocations, verifies all
history transitions and registered ancestry, and reports the next-round budget.
Missing records must be reconciled with actual history/owner, never assumed zero.
An extra round requires owner_extra_cycles.comment_id referring to an actual
owner-authored comment on that prep PR with type fava-correction-authorization,
phase prepare, the canonical milestone and a finite max_cycles greater than
three. A truthy marker, wrong actor/PR/phase or malformed comment is not approval.
Counts do not reset across invocation or regeneration. An exhausted/blocked
preparation uses the same concrete escalation template; no owner merge is made.

Initial registration must be metadata-only at zero and bind the immediately
preceding published head, committed before the actual PR opening. Late registration
or ambiguous same-second chronology fails closed for owner reconciliation.
Every artifact fix publication increments the counter and appends its immediate
parent in that same commit. Verified pure target imports, projection-only updates
and narrowly scoped append-only blocker checkpoints preserve the record without
consuming a round. Credential-free Actions supplies the actual PR number/opening
time and validates every first-parent publication, including unchanged ledgers.
Preparation branch context selects stricter checks; it is not approval evidence.

## Implementation and integration gates

Before any agent integration, verify the effective milestone rules require signed
PRs, ci-required/up-to-date targets and discussion resolution. Missing protections
block integration until the owner applies the settings proposal.

One coordinator reconciles state, selects ready tasks, delegates small batches,
publishes signed task PRs, monitors validation/review, fixes justified findings,
integrates serially, records evidence and projects actual Linear state. It
continues until approved work and whole-milestone automated validation pass or
no unrelated ready task remains. Sequential execution is reliable baseline.
Explicitly request subagents where supported. Independent review uses a reviewer
separate from the implementation worker; if unavailable, record blocked review
and obtain another supported reviewer/session or owner. Parallel workers require
isolated clean checkouts, reviewed disjoint write ownership and integrated
dependencies. Shared state has one writer and integrations always serialize.

Every integration requires evidence for **both current PR head and milestone
target**:

- Registered milestone destination, authorized task/batch scope, integrated
  dependency merge SHAs, resolvable Spec/Task/Implements trailers on all source
  and integration commits, and verified signatures on every introduced commit.
- Successful deterministic sdd-quality, tooling-validation, ci-applicability and
  fail-closed ci-required. Actual macOS compilation and nonzero simulator tests
  when native applies; inspect logs/xcresult summaries, exact SHA and run links.
- Independent review of current head/target, with reviewer and worker identity,
  report revision and findings. Configured available Codex bot review must
  complete for that head. Reaction-based completion requires a new unedited
  single-SHA request on this PR and a bot reaction after its creation. A pending request, older review or silence is not
  approval. If configured review cannot run, record the actual failure and block
  integration; do not silently bypass a timeout.
- Evidence-backed disposition of **every** finding: link, severity, assessment,
  rationale, attempted fix/test, disposition revision and required owner decision
  if unaddressable. Resolve a discussion only after verifying its disposition.
  No unresolved critical correctness/security/scope/consistency finding.
- Structural drift checks plus semantic comparison to the approved specification,
  reviewed plan/tasks and FR/US/acceptance mappings. CI cannot judge requirement
  meaning; the independent reviewer/coordinator must inspect the actual reports.
- Fresh tests, review and drift assessment after head edits or target movement.
  Recheck refs immediately before merge. Update a stale task branch with a signed
  merge from the current target, then rerun. Never treat an older green SHA as
  evidence. All target merges retain both parents and valid trailers.

`tools/sdd/integration.py ID --pr NUMBER` inspects live head/target, introduced
commit signatures/trailers, scope/dependencies, CI and bot review, and evaluates
the ledger's linked reports. It is read-only, and is an assessment aid, **not a
merge authorization token**. The coordinator verifies every linked report,
macOS result, review discussion and semantic finding before merging. Human/
agent identity cannot be inferred from a boolean or a shared GitHub login.

Publish the final task SHA first, then write a coordinator JSON PR comment with
tasks (exact represented task IDs), validated_head/validated_target, report URLs, worker/reviewer IDs, review head/
target, semantic and finding dispositions, native build/test counts and bot
request evidence. Supply its numeric ID with `--evidence-comment ID` (or preserve
integration_comment in the task record from an earlier checkpoint). A commit
cannot contain its own SHA: SHA-bound evidence belongs in the PR after publication,
then its URL is recorded in the serialized ledger checkpoint after integration.
Every integrated task retains integration_comment, its actual PR comment ID,
and that comment's URL in evidence. The resolver and checkpoint assessor fetch
the actual merged PR and comment, verify the merge signature/head/target, and
match the exact task to both source and merge Spec/Task trailers. Deterministic
CI also checks that the cited merge is an ancestor and its own source history
changes that task's approved paths; a union trailer alone cannot rename another
task's work. Documentation, tooling and other non-application tasks use the same
exact Spec/Task/FR identity and approved file mappings, without a source-path
requirement. No-source commits still need their applicable SDD-Type exception.
Pure target-import merges retain history mappings but are excluded from the
worker's represented task IDs only after their tree matches Git's automatic
merge. Conflict resolutions/extra edits require separate scoped task commits
before import; they cannot be hidden behind an already integrated task ID.
Use that same import classification when proving task-owned changes before both
integration and completion. An empty task claim followed by another task's
shared-file import cannot establish completion, even with relabeled trailers.
Independent review is retained in a separate reviewer JSON PR comment
(independent_review_comment plus URL), optionally linking its original GitHub review, containing head, target, reviewer and
worker runtime identities. The coordinator publishes a subagent's unedited
report, preserving its identity and findings; shared GitHub login does not create
another approving actor. The helper fetches both reports, checks their PR/author
and current live facts;
its subjective report fields still require coordinator/independent inspection.

Use three automatic correction cycles maximum per task PR, durable across restarts.
One cycle is a consolidated set of justified fixes followed by fresh validation
and review; the initial implementation/review is not a correction cycle. Record
the round before publication so an interruption cannot hide an attempt. A third
round that clears all gates may integrate; findings remaining after that round
require escalation. New findings, retries or resumed Cloud tasks do not reset
the count. An unchanged CI rerun is not another fix round; retain its failure and
retry evidence. The coordinator serializes the PR-level count across batch task
records; splitting or retiring task IDs cannot reset the same PR's budget.
Before task integration, register task_prs on the canonical milestone target
through a gated metadata checkpoint. Keys are actual PR numbers; each entry
contains immutable branch/tasks, correction_cycles and append-only heads of
published task revisions. Before each fix round, checkpoint the incremented
counter and prior head there, then synchronize the worker's signed history and
task counts. Initial registration uses count zero. Keep every registered head
as an ancestor of the current task head; no rewritten branch can discard the
checkpointed budget. New task PRs fail integration until registered. CI and the
assessor check each ledger parent transition, including intermediate commits
and merge parents, so a later commit cannot hide a reset. Never delete registry
entries or rebind their PR/task identity. Registration is execution evidence,
not approval, and all checkpoint gates still apply.
After exhaustion, record the blocker and continue unrelated ready tasks where
possible. More cycles require owner authorization. Never weaken scope, tests,
approval/signing/review or drift gates to continue. No-source checkpoints do not
evade signature/review/CI requirements. Record actual post-merge signature/parents
and destination; fail and stop further integration if verification disagrees.

Use [the escalation template](../../.specify/templates/escalation-template.md).
For every new/unresolved finding give its link, severity/impact, affected paths,
assessment/evidence and attempted fixes/results. Prepare a concrete reviewable
patch or exact proposed edits within authorized scope, with a validation plan,
risks and alternatives. Ask for the specific owner decision and, where needed,
an explicit number of extra rounds/absolute cap. Do not merely ask permission to
try again. Preserve blocked status and open discussions until the disposition
is verified; no extra publication or integration precedes the needed approval.

## Merge history and deterministic promotion proof

Keep two-parent merges; do not squash/rebase away reviewed planning/task history.
The SDD validator compares merge changes to the **first parent** and validates
each introduced commit, including merge messages. Source-bearing merges cite
the union of integrated Task IDs and their exact Implements mapping in one Spec.
Non-source prep/checkpoint merges use `SDD-Type: planning`. Add Milestone and
Integration-PR trailers for navigation; they never establish approval alone.
The owner should preserve these trailers on final main merge as well.

```text
feat: integrate R3.5 T004

Spec: specs/healthkit-run-library-05-reliable-run-history-and-contextual-launch
Task: T004
Implements: FR-001 FR-003
Milestone: R3.5
Integration-PR: https://github.com/clemarc/fava/pull/NUMBER
```

FRs above are illustrative: use the actual reviewed task mappings. Target-only
source brought into a worker branch also needs full applicable task/FR trailers.

Ordinary implementation still requires plan/tasks in its approved PR base. For
registered milestone promotion, the final main PR may introduce reviewed plans
and later source together. The validator follows the execution ledger's full
SHAs and proves: specification_base is an ancestor of the main base, its exact
contract/roadmap identity remains intact; planning_revision is a cryptographically
verified owner two-parent merge containing plan/tasks/ledger/prep report; that
merge and its registration precede every source commit; preparation history
contains no source work. The same checks run for source-bearing merges. This
does not extend the fixed R1–R3 pilot exception.

Verification uses standard Git/GnuPG and the committed **public** GitHub web-flow
key, fingerprint `968479A1AFF927E37D1A566BB5690EEEBB952194`, downloaded from
https://github.com/web-flow.gpg. Key rotations require owner-reviewed pin updates.
Only that signer and the recorded owner's email qualify for this new approval
proof. Other local signing methods remain valid for ordinary work with GitHub
Verified evidence, but cannot silently substitute milestone owner approval.
Live reconstruction additionally checks merged PR destination and merged_by.
Actions use no OpenAI/Linear/API secrets or headless AI gate. This proves signed
history/chronology, not that a shared owner credential was operated by a human;
stronger identity separation is a settings prerequisite below.

## Final owner handoff and completion

Use `.specify/templates/milestone-handoff-template.md`. Include exact tested
revision, CI/macOS/simulator evidence and counts, task/FR/acceptance coverage,
migration, saving failures and read/clear race evidence, manual physical iPhone
and iPad steps, accessibility/performance results or explicitly pending checks,
limitations/unresolved findings and actual Linear projection status.

Use state ready-for-owner after automated work, **not completed**. R3.5's physical
acceptance is mandatory and pending until the owner supplies sanitized outcomes.
After testing, authorized fixes use task PRs/new IDs and refreshed validation;
record both-family acceptance before proposing Status: completed and freeze.
Keep specification baseline metadata unchanged through the milestone PR so its
reviewed planning chronology remains verifiable. After owner acceptance, authorized
fixes and the owner's main promotion merge, propose a separate signed completion-only
PR to record completion/freeze metadata and acceptance evidence, without application
changes. The owner reviews and merges that PR too.
No rewrite of approved R3.5 clarifications/acceptance or R1–R3 history. Changed
requirements use the existing human-approved Supersedes process. Main merge is
always human; keep auto-merge disabled.

## Cloud capabilities and adoption

Inspected 2026-10-13: Linux Cloud, Git/Python/GnuPG/gh and signed GraphQL access
as clemarc work. Subagent tools are available in this task; separate checkouts
are not automatic. Runtime reports no advertised Goal capability; no Goal
command or unattended-duration guarantee is assumed. Every invocation must
recheck capabilities and actual API access. Available Goal completion criteria
are prep PR handoff / implementation ready-for-owner or explicit blockers,
never main merge or physical acceptance. Otherwise use supported long-running
instructions and signed durable checkpoints. Interruptions resume with the same
skill/ID; unavailable review/macOS/credentials are reported, not simulated.

PR #8's roadmap and #9's clarified specification are owner-merged as inspected
on 2026-10-13; #9 latest head 02a0cb0 passed applicable CI (native intentionally
skipped) and both initial Codex threads are resolved. The resolver rechecks this
evidence, not this paragraph. If #9 were open, its owner merge would be required.
No preparation or application implementation is performed by the governance PR.

Adoption order: owner reviews/merges governance; applies separately documented
[ruleset changes](sdd-v2-settings.md); starts preparation; reviews/merges prep;
starts implementation; tests physical devices and reviews final main PR. Linear
projection must use the pinned CLI and verified stable keys. Missing tracker
access is recorded pending and never blocks deterministic CI.

### Durable correction authorization and task identity

Integration compares each represented task against both the inspected milestone
ledger and PR-head ledger. A PR cannot erase a target blocker, decrease its
correction count or reuse an integrated task ID. Follow-up implementation uses
new owner-reviewed task IDs. Counter decreases also fail deterministic history
validation. Resolve a blocked task through a reviewed metadata checkpoint before
retrying integration; a worker's head-only state change is not resolution.

Extra cycles require owner evidence recorded on the milestone target. The task's
owner_extra_cycles record is an object containing comment_id, pointing to an
actual owner-authored JSON comment on that task PR. The assessor fetches the
comment and verifies its PR, actor, milestone, task and finite maximum:

```json
{"type":"fava-correction-authorization","milestone":"R3.5","tasks":["T003"],"max_cycles":4}
```

This is a format example, not approval. A boolean/string marker, an unmerged PR
record, another PR's comment, another actor or a comment for different tasks does
not grant authority. The owner supplies authorization; workers/coordinators must
not manufacture it. The shared-owner-identity limitation and stronger identity
separation in the settings proposal still apply. The default is three cycles.

## Retained task evidence and publication boundaries

Task registration is exactly zero with one initial published head. That initial
head must be committed strictly before the actual PR opening time; registration
follows opening. Each reservation appends exactly one
prior publication boundary and increments exactly once. Every subsequent
non-import first-parent commit consumes one reserved correction. Consolidate fixes
into that one signed publication; do not publish intermediate work. Its first
parent must contain the canonical signed reservation checkpoint. Pure automatic
target imports can occur before the fix and between its boundary and publication.
Head task counts must equal the canonical PR count. Skipped heads, arbitrary
ancestor boundaries, jumps, rewritten history and ambiguous timestamps block.

The resolver returns task_progress for open task PRs. `registration-required`
means inspect/register the existing initial publication, not start a duplicate
PR or assume a budget. `resume-reserved-fix` means finish the already reserved
correction without another increment; repeated imports do not consume it. A
pending reservation cannot integrate. Separate task branch protections are an
owner adoption prerequisite, as described in the settings proposal. Extra-cycle
authorization must be an unedited owner comment strictly before the applicable
reservation; later authorization cannot retroactively legalize it.

Live assessment and completed-task reconciliation use the same full verifier at
explicit source and target SHAs. Reconciliation descends through retained merge
parents, never calls the milestone resolver recursively, and requires the merge
tree to preserve the reviewed source tree. Task-owned paths must differ from the
exact target. Pure imports, replayed patches and reverted work cannot prove
completion. If several task IDs modify a shared path in different commits, that
path is conservatively excluded as ownership evidence unless every modifying
commit includes the task. Use separate serial task PRs or a reviewed coherent
batch with truthful joint Task/FR mappings; a historical touch is insufficient.

Coordinator JSON must include `check_run_ids` for the actual successful Actions
check runs, `validated_head`, `validated_target`, exact `tasks`, `semantic_drift`,
`findings_disposed`, `independent_review_comment` and its
`independent_review_url`. Publish a new comment after evidence is available; do
not edit earlier evidence. Retained check IDs are fetched with all attempts and
verified against the SHA, Actions identity, actual conclusion and timestamps.
The newest attempt started before integration must succeed before the report;
a pending/failed attempt cannot be hidden by citing an older success. Later
reruns neither invalidate valid historical proof nor authorize an earlier merge.
Missing, edited, unauthorized or same-second ambiguous evidence fails closed.

The independent JSON comment is an unedited coordinator-published copy of the
separate review, with `head`, `target`, distinct `worker`/`reviewer` runtime IDs,
`semantic_drift: true`, `findings_disposed: true`, and `findings: []` when none
exist. Each actual PR review/comment finding needs a `url`, `rationale`,
`evidence`, exact `head`/`target`, and `disposition` of `fixed` or `not-actionable`.
Preserve original report wording/identity and actual inspection; booleans do not
replace review. For native work, `native` maps each configured full iPhone/iPad
check name to `build_succeeded`, positive integer `tests`, and `job_url` matching
the retained check's details URL. The reviewer must inspect those job logs and
artifacts. This is interpreted native evidence backed by actual successful
family checks, not an automated semantic/log-content oracle.

GitHub review bodies have no exposed immutable edit timestamp. Preserve an
independent GitHub review's original URL and unedited content in the SHA-bound
JSON comment rather than using `independent_review_id` alone. Configured Codex
review must be actual exact-head review or a timely reaction to a fresh request;
a report's availability boolean cannot bypass it. All review/CI evidence must
precede the coordinator report, which must precede integration. Complete finding
dispositions are rechecked using actual GitHub reviews/comments. Current rules
are checked at resume; GitHub does not supply a historical rules snapshot here.
Shared owner login still cannot technically distinguish human and agent actions.

### Protection provenance and aggregate history

Before returning registration-required, task resume verifies signatures and
proves that active no-bypass repository rules for signatures/no-force/no-deletion
predate the candidate initial head. That head must strictly predate PR opening;
a later head or unknown protection history stops for owner reconciliation.
Registered task/preparation history uses its retained first head for this proof,
never the current head. A later ruleset update conservatively invalidates this
simple provenance proof, even if benign; see the settings proposal. Do not
recreate a branch/PR or reset its count to evade reconciliation.

Extra-cycle authorization is an unedited owner comment strictly before the
publication or reservation it authorizes. Each retained boundary uses its own
ledger snapshot: a later grant may extend the budget for subsequent rounds but
cannot repair an unauthorized earlier round. Subsequent metadata or projection
updates cannot move those deadlines. Preparation resume verifies actual commit
signatures as well as retained ledger transitions and owner authorization.

Exact zero/one-step reservation checks apply at original publications. Cumulative
base-to-head comparisons and pure automatic imports instead preserve identities,
counters and all boundaries: they may inherit several previously validated
reservations for another PR. Every introduced original commit is still checked.
A merged record synthesized from both parents retains strict origin checks;
automatically combining invalid counter/head edits cannot manufacture a valid
budget. No signature, scope, review or CI gate is waived for imports.

Implementation startup also revalidates every retained merged preparation PR.
Its budget record must match the actual source, owner merge and current ledger;
each publication and grant is checked at its original boundary, with final
authorization bounded by merge time. A later amendment cannot hide an invalid
earlier preparation. Missing/corrupted records, mismatched count/head cardinality
or unprovable history stop implementation for owner reconciliation.

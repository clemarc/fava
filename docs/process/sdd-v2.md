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
  complete for that head. A pending request, older review or silence is not
  approval. Prove actual service/configuration unavailability if review cannot
  run, record it and retain independent review; do not silently bypass a timeout.
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
validated_head/validated_target, report URLs, worker/reviewer IDs, review head/
target, semantic and finding dispositions, native build/test counts and bot
request evidence. Supply its numeric ID with `--evidence-comment ID` (or preserve
integration_comment in the task record from an earlier checkpoint). A commit
cannot contain its own SHA: SHA-bound evidence belongs in the PR after publication,
then its URL is recorded in the serialized ledger checkpoint after integration.
Independent review is either a real GitHub review (independent_review_id plus
its URL and target SHA) or a separate reviewer JSON PR comment
(independent_review_comment plus URL), containing head, target, reviewer and
worker runtime identities. The coordinator publishes a subagent's unedited
report, preserving its identity and findings; shared GitHub login does not create
another approving actor. The helper fetches both reports, checks their PR/author
and current live facts;
its subjective report fields still require coordinator/independent inspection.

Use two automatic correction cycles maximum per task PR, durable across restarts.
After exhaustion, record the blocker and continue unrelated ready tasks where
possible. More cycles require owner authorization. Never weaken scope, tests,
approval/signing/review or drift gates to continue. No-source checkpoints do not
evade signature/review/CI requirements. Record actual post-merge signature/parents
and destination; fail and stop further integration if verification disagrees.

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

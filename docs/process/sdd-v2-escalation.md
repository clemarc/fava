# PR #10: owner-authorized fifth correction round

Scope: SDD governance/tooling only; no application/specification/R3.5 work.
Published head: 86dcb96d260428aeac9fec00b53a02cb04613e4c.
Target main: a68b6db26ac54de0e83fb451868f54d32b078c34.
Four correction publications used, including explicitly owner-authorized rounds.
The new default of three rounds is proposed and does not reset this count.

## Findings and proposed fixes

1. P1 [preserve counts across prior heads](https://github.com/clemarc/fava/pull/10#discussion_r4268553948). An intermediate third-round ledger can reset to zero when only target/current snapshots are checked. Earlier target/head fixes prevented head-only resets relative to target but missed intervening transitions. Proposed patch: tools/sdd/ledger.py checks every parent transition; .github/checks/sdd.py invokes it for each ledger-changing commit. Canonical task_prs checkpoints retain numeric PR identity, branch/task IDs, monotonic counter and prior heads. tools/sdd/integration.py rejects unregistered PRs, counter rollback and rewritten head ancestry. Implementation instructions checkpoint this history before each fix round. Regressions reproduce the actual 0 → 3 → 0 signed history and reject registry deletion/rebinding/reset/rewrites.
2. P1 [verify checkpoint completion identity](https://github.com/clemarc/fava/pull/10#discussion_r4268553959). A metadata checkpoint could complete T003 using T002's merged PR because it has no Task trailers and field-shape checks do not bind task identity. Proposed patch: deterministic task_merge_errors verifies ancestor/two-parent merge and the exact task in both merge and source history; even a forged union merge trailer fails. Resolver and assessor fetch the actual merged PR and evidence comment, verify signed merge/head/target and exact task membership. All integrated records are checked on checkpoints regardless of represented trailer IDs. Regressions accept exact T003 evidence and reject another task, old head/target and another PR's report.

## Validation and risks

59 workflow fixtures and seven commit-builder fixtures pass locally, plus
SDD/tooling/whitespace checks. Tests use synthetic data and ephemeral signing
keys. Published head 86dcb96 passed all six checks in
[run 38535796922](https://github.com/clemarc/fava/actions/runs/38535796922):
actual Xcode build and 41 tests, zero failures, per simulator family. These
results cannot validate this changed patch. The owner authorized this additional
round on 2026-10-14. Publish through verified GraphQL signing,
run fresh deterministic CI plus both simulator families, request independent
Codex review for the exact head, assess new findings and refresh evidence.

The stronger registration contract adds gated metadata checkpoints before task
fix rounds. Unregistered/new-schema work fails closed; no active R3.5 ledger
exists to migrate. Shared owner credentials still cannot technically distinguish
agent versus human comments/merges; identity separation remains a separate
owner settings decision. No signing, CI, approval or product gate is weakened.

## Owner authorization

On 2026-10-14, the owner answered “Authorize one additional round” to the
request for one governance-only publication/validation/review round for PR #10
(absolute maximum five correction publications), containing these two fixes
and their fixtures/guidance. No PR merge, auto-merge, settings changes or
R3.5 work. New findings beyond that round require a fresh concrete escalation.
This authorization is limited to publication/validation/review; it does not
approve governance adoption or assert verified completion. Keep
unresolved discussions open until their published dispositions are verified.

## Further findings: owner-authorized rounds six/seven

Current published head: 26eb4db135f6dd177f3fa8b06c185016d862993d; main remains
a68b6db26ac54de0e83fb451868f54d32b078c34. The authorized fifth publication is
complete. On 2026-10-14 the owner answered “Authorize two rounds (max seven)”
to the bounded additional-round request. These fixes form round six; round
seven remains available for justified workflow follow-up findings.

1. P1 [preparation counter resume](https://github.com/clemarc/fava/pull/10#discussion_r4268988652). Implementation task counters did not cover preparation. Proposed: preparation_prs records, append-only history validation, preparation_progress returned by the resolver, and actual owner phase/PR/milestone authorization. New prepare/* signature/no-force-push/no-deletion protections are an explicit owner prerequisite; no settings are changed here. Synthetic tests cover resume at three, unauthorized fourth, wrong phase/milestone/PR, missing registration and missing protections.
2. P2 [hard-coded milestone examples](https://github.com/clemarc/fava/pull/10#discussion_r4268988659). Command/branch examples could steer a generic invocation to R3.5. Proposed: use the supplied FAVA_MILESTONE and returned branch fields throughout both skills; fixture resolves R4 independently. Preserve R3.5-specific approved directory notes.
3. P1 independent / P2 [non-application completion](https://github.com/clemarc/fava/pull/10#discussion_r4268988666). The fifth-round source-path predicate blocked valid documentation/tooling tasks. Proposed: exact reviewed task path and FR mappings, still tied to real signed merge/PR/report evidence. Require full Spec/Task/Implements validation for non-source Task commits and reviewed planning chronology. Signed fixtures accept docs/tools tasks and reject another task's evidence.
4. P1 independent review: target synchronization included historical integrated IDs in worker scope. Proposed: exclude a target import's trailers from represented worker IDs only when its tree exactly matches Git's automatic merge. Check signatures/trailers/history for all commits; reject injected edits/conflicts. A signed fixture preserves the worker's scope after another task integrates and rejects an altered import tree. Resolve conflicts in separately scoped commits before import.

The independent reviewer /root/fifth_round_review reproduced both integration
regressions and rechecked the prepared fixes, finding no further concrete
regression in this focused scope. 64 workflow and seven publication fixtures
pass, along with tooling/SDD/whitespace checks. Fresh native CI and Codex review
would be required after any new signed publication. Published-head native CI
failed unchanged iPad background-return (FoundationUITests.swift:78) and
iPhone accessibility-size navigation assertions (RunLibraryUITests.swift:16,
141–143). Both actual logs were inspected; ci-required failed closed. Attempt
2 reran failed jobs unchanged on that SHA and was cancelled by round six. No
application/test or workflow gate is changed. [Independent review and prepared
re-review](https://github.com/clemarc/fava/pull/10#issuecomment-6165447406) are recorded.

Authorized scope: two additional governance correction rounds (maximum seven
total) to publish these four fixes and address justified workflow findings from
their refreshed review, with fresh signing/CI/review each round. Additional rounds
beyond the selected maximum
require another concrete escalation. Default three rounds for future milestone
PRs, all approval/testing gates, and no main/prep merges remain unchanged.
No R3.5 work, settings changes or credentials are authorized by this proposal.

## Seventh round: preparation publications and borrowed completion evidence

Round six published signed head 1f3a0b6b60f4b8daf0ec762ffa11bc8e840d26f0.
All six checks passed in [run 38545381256](https://github.com/clemarc/fava/actions/runs/38545381256),
including actual Xcode compilation and 41 tests with zero failures per simulator
family; both native logs were inspected. That evidence applies only to round six.

1. P1 [bind preparation rounds to publications](https://github.com/clemarc/fava/pull/10#discussion_r4269323141). Require initial metadata-only zero registration against the immediately preceding pre-opening head. Check every subsequent first-parent artifact publication for exactly one increment and that publication's parent, even when the ledger is unchanged. Use actual PR number/opening time from the Actions event and resolver API. Narrow exemptions preserve history for projection, blocker records and verified pure target imports; late or ambiguous registration fails closed.
2. P1 [exclude target imports from completion evidence](https://github.com/clemarc/fava/pull/10#discussion_r4269323152). Share verified import classification across scope and completion proof. Require actual task-owned path changes outside imported target history before integration and again when recording completion. An empty task commit followed by another task's shared-file import cannot complete the task. Preserve signature/trailer checks and reject edited/conflicted imports.

66 workflow fixtures and seven publication fixtures pass locally. The independent
reviewer /root/fifth_round_review rechecked both prepared fixes and found no
further concrete defect in that focused scope. Same-second initial registration
chronology deliberately requires reconciliation rather than an inferred approval.
Round seven consumes the second additional round authorized above: publication,
fresh CI and exact-head Codex review only. Any further correction publication
requires a new concrete escalation and owner authorization. No governance
adoption, merge, settings change, tracker write or R3.5 work is authorized here.

## Bounded restart authorization: rounds eight and nine

On 2026-10-14 the owner explicitly authorized up to two additional scoped
correction publications for PR #10: rounds eight and nine, maximum nine total.
Authorization covers workflow fixes, signed publication, CI and review only.
It excludes merges, auto-merge, settings/credential changes, R3.5 preparation
and application changes. Reuse chore/sdd-v2 and PR #10 without rewriting history.

The consolidated eighth-round patch addresses the three findings linked in the
[pause/restart report](https://github.com/clemarc/fava/pull/10#issuecomment-6167080631).
The [review record](sdd-v2-review.md) describes implementation, adversarial/positive
fixtures and limitations. Publish only after assessing independent review, then
verify fresh exact-head signing, CI/native and Codex review. One ninth correction
publication remains available if justified. If exhausted, retain a tested concrete
follow-up patch and linked escalation with the exact owner decision; do not
silently publish again or claim readiness with critical findings outstanding.

## Ninth round finding: owner-authorized tenth correction

Published head: e8970e159f7eb19b5ed6fdfec89b032cff5cab4a; main remains
a68b6db26ac54de0e83fb451868f54d32b078c34. Rounds eight and nine were published
with verified GraphQL/REST signatures and exact tree/parent/message checks.
Nine correction publications are consumed. On 2026-10-15, after the concrete
patch, validation and bounded request were presented, the owner answered
“ok let's go”, authorizing round ten, absolute maximum ten, for this workflow
fix, signed publication, CI and review only.

Fresh exact-head Codex review found justified P1
[revalidate merged preparation history](https://github.com/clemarc/fava/pull/10#discussion_r4279729251).
The open-preparation resume fixes do not run when implementation starts after
owner merge. Generic validation also accepts a preparation correction count
without the corresponding number of retained heads. Consequently, an unauthorized
extra preparation round or later corrupted record can reach implementation.
Independent review reproduced the gap; an owner merge alone cannot waive it.

Proposed fix: share the explicit preparation-revision verifier between open
resume and implementation startup. Reconcile every retained merged preparation
PR against actual metadata, signed owner merge parents, source and current
records, protected signed history and each publication's immutable timely grant.
Anchor traversal to the retained initial publication's first parent, not a
later main/ledger baseline; bound the final grant by merge time. Require
heads = correction_cycles + 1. A later valid amendment cannot hide an invalid
older preparation. No new orchestration service or weaker gate is introduced.

Local validation: 98 workflow tests and seven publication tests pass, including
a real signed preparation/zero-registration/four-correction/owner-merge/checkpoint/
implementation-inspect walkthrough. Timely authorization and a later valid
amendment pass; missing, edited, late and post-merge grants, wrong source heads,
corrupted count/head or authorization records, and omitted older preparation
records stop implementation. Existing native-evidence, task budget, full
completion, replay and application/docs/tooling fixtures remain passing.
SDD/tooling/whitespace checks pass. These local results are not fresh published
CI/native or Codex validation of this proposal. Published-head CI/review links
and final independent assessment are recorded in the PR escalation comment.

Risk: conservative reconciliation can block legacy or edited preparation history;
there is no automatic migration or budget reset. GitHub owner/agent identity
separation and separately installed protections remain adoption prerequisites.
Git is authoritative; no Linear projection, R3.5 preparation, application/spec
change, merge, auto-merge or settings/credential change is part of this proposal.

Authorized scope: **one additional correction publication, round ten, absolute
maximum ten**, on this same PR/branch for the reviewed patch, verified signing,
fresh CI/native and independent/Codex review only. No merge, auto-merge, settings/
credential changes, application/spec changes or R3.5 work. The final closure
review covers lifecycle transitions before publication. Any new critical finding
after round ten requires a concrete owner decision about remediation or reduced
scope; no eleventh publication or weakening of gates is authorized.

## Round ten closure: two remaining P1s, no further publication authorized

Published head ec378950aaa7712451553a89ecff5c98a9b0fc61 consumed the tenth and
final authorized publication. Fresh independent published-head review reported
no actionable findings, but fresh Codex review 5533796314 identified two justified
remaining defects. Independent reassessment confirmed both; review completion
alone was not treated as approval.

- [Initial publication signature coverage](https://github.com/clemarc/fava/pull/10#discussion_r4283500133): the initial-head-parent boundary is appropriate for correction accounting but excludes older commits in the initial publication from signature/transition proof. The local follow-up passes the actual retained merge target separately as the complete introduced-history verification base. Round accounting retains its original boundary.
- [Freeze preparation records before integration](https://github.com/clemarc/fava/pull/10#discussion_r4283500144): task/checkpoint metadata can append to preparation records, then make startup fail its frozen-record equality check. The local follow-up rejects any difference between canonical and PR-head preparation records in shared assessment, before integration. Owner preparation amendments use their separate reviewed path.

A concrete **uncommitted, unpublished** patch changes only these helpers,
regression fixtures and this escalation. Local validation: 100 workflow tests,
seven publication tests, SDD/tooling/whitespace checks pass. New fixtures use real
signed and unsigned multi-commit preparation history, an invalid earlier ledger
transition, valid task/checkpoint assessments and preparation-record mutations.
The existing valid preparation amendment and full task lifecycle tests still pass.
Published-head CI/native evidence cannot validate this local patch.

The agreed bounded closure pass has ended with blockers; no round eleven is
authorized and the workflow is not ready for adoption. The next step is an owner
disposition of this concrete patch and the intended automation scope, rather than
another automatically requested correction round. Recommended: review the two
specific fixes and the lifecycle contract together before deciding whether to
permit a separately bounded publication. Alternatively, defer autonomous task
integration and redesign a smaller owner-mediated workflow under explicit scope
approval; that would change the original goal and is not applied here. Do not
merge this PR or weaken signature, review, test or authorization gates to end the
loop. No settings/credentials, application/specification, R3.5 or Linear changes.

## Owner authorization for final review: round eleven

On 2026-10-15, after the exact tested two-fix patch and remaining blockers were
presented, the owner instructed “go ahead so we can have a final review”. This
authorizes one additional scoped correction publication, round eleven, maximum
eleven total, for that patch, verified signing and fresh CI/native/independent/
Codex review. Earlier statements that round eleven was unauthorized describe the
prior pause; this explicit instruction supersedes that limit for this one round.
No merge, auto-merge, settings/credentials, application/specification, R3.5 or
tracker changes. No twelfth publication is authorized.

Round ten completed all six CI checks in run 38741304394. That evidence applies
only to its published head; round eleven requires new exact-head validation.

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
2 reruns failed jobs unchanged on the published SHA and is pending. No
application/test or workflow gate is changed. [Independent review and prepared
re-review](https://github.com/clemarc/fava/pull/10#issuecomment-6165447406) are recorded.

Authorized scope: two additional governance correction rounds (maximum seven
total) to publish these four fixes and address justified workflow findings from
their refreshed review, with fresh signing/CI/review each round. Additional rounds
beyond the selected maximum
require another concrete escalation. Default three rounds for future milestone
PRs, all approval/testing gates, and no main/prep merges remain unchanged.
No R3.5 work, settings changes or credentials are authorized by this proposal.

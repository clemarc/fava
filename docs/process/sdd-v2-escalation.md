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

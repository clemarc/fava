# SDD v2 governance review

This is a workflow/governance review, not R3.5 preparation or product acceptance.
Base: inspected main a68b6db26ac54de0e83fb451868f54d32b078c34 (#9 owner merge).
Roadmap approval: #8, 0f6b64a2041e015f63369b5ad7c4f871cc053063.

- R3.5's contract/clarifications/directory and all specs/history are untouched.
  No source, app assets, Xcode project, native applicability or workflow gates
  are changed. New unknown tooling paths correctly require existing native CI.
- Constitution 2.0.0 records major authority change/rationale/active-work impact;
  prior all-agent-merge prohibition stays until owner governance merge.
- Both skill inputs use shared canonical resolution and deterministic branches;
  local/remote/PR/ledger inspection precedes creation, with no resetting user work.
- Promotion checks use actual signed owner planning merges and ancestry, not
  markers/trailers alone; same proof handles final two-parent main promotion.
  Immutable reviewed plan/task mappings precede source; task checkbox transitions
  are execution evidence. Fixed R1–R3 pilot constants/logic are unchanged.
- Mandatory tests, actual macOS/nonzero simulator validation, physical iPhone/iPad
  acceptance, reviewer-owned checklists and human main/prep review remain.
- One coordinator serializes shared records and task integration, explicitly
  requests supported subagents and isolates parallel writes. Two correction
  cycles persist; current head/target, review, finding and drift evidence gate
  task merges. The read-only assessor is not a merge-authorization token.
- Projection uses existing pinned CLI and repository keys, checks duplicates,
  produces a dry-run and verifies hierarchy/status after mutations. Live CLI
  reads succeeded; no tracker mutations or R3.5 artifacts were created here.
- Actions remain deterministic/credential-free, using existing discovery of the
  new Python fixtures. No headless AI key gate or orchestration service.

Validation: 49 SDD/tooling/resolver/integration/projection fixtures and seven
commit-builder fixtures pass locally. Fixtures include real ephemeral signed
owner merge history, final main merge promotion, missing/wrong/late approval,
unreviewed task mapping changes, decimal/unknown/ambiguous IDs, existing and dirty/
divergent branches, interrupted/open/closed/completed execution, wrong targets,
stale validation/review, missing/partial iPhone+iPad matrix evidence, retired keys and idempotent
projection. Production key verification also resolved actual #8/#9 signed merges.
Tooling references/skill discovery, SDD repository checks and whitespace pass.
Latest remote CI, actual native results and Codex review belong in the PR report;
local Linux fixtures cannot claim Xcode/device execution.

Limitations/prerequisites: owner adoption and separate ruleset changes before
agent integration; shared owner GitHub identity remains a process-only human
boundary without separately provisioned app/owner restrictions. Goal mode is not
advertised. Native CI and independent review may block unattended execution.
Live projection mutation behavior is simulated with a CLI client; actual future
runs must verify results. No settings/credentials are changed by this PR.

## Codex finding dispositions (second correction cycle)

- P1 [reaction freshness](https://github.com/clemarc/fava/pull/10#discussion_r4263849455): justified. Require a new unedited single-SHA request on this PR and a bot reaction no earlier than its creation. Fixtures reject edited requests, old reactions, wrong PR/head and multiple SHA requests.
- P1 [unfinished completion](https://github.com/clemarc/fava/pull/10#discussion_r4263849465): justified. ready-for-owner/completed requires every retained task verified integrated; completed still also requires both physical acceptances. Fixtures reject each unfinished state even with device evidence and permit complete integrated evidence.
- P2 [planning amendment selection](https://github.com/clemarc/fava/pull/10#discussion_r4263849472): justified. Select by explicit merge chronology, reject ambiguous ties, then verify target ancestry/signature/merged PR; never depend on REST response order. Both response-order fixtures select the newer amendment.

These dispositions are backed by local regression fixtures. Resolve discussions
only after verified publication and latest-head CI; refreshed Codex review is
requested for the final revision. No requirement or gate is weakened.

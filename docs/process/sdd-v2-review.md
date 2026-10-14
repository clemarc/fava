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
  requests supported subagents and isolates parallel writes. Three correction
  cycles persist; current head/target, review, finding and drift evidence gate
  task merges. The read-only assessor is not a merge-authorization token.
- Projection uses existing pinned CLI and repository keys, checks duplicates,
  produces a dry-run and verifies hierarchy/status after mutations. Live CLI
  reads succeeded; no tracker mutations or R3.5 artifacts were created here.
- Actions remain deterministic/credential-free, using existing discovery of the
  new Python fixtures. No headless AI key gate or orchestration service.

Validation: 59 SDD/tooling/resolver/integration/projection fixtures and seven
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

## Additional review fixes (owner-authorized third correction cycle)

- P1 [aggregate-only native evidence](https://github.com/clemarc/fava/pull/10#discussion_r4263942064): justified. Always derive native aggregate success from both configured family jobs; reject empty and aggregate-only rollups, with fixtures.
- P1 [durable correction limits](https://github.com/clemarc/fava/pull/10#discussion_r4263942076): justified. Assess every represented task's durable correction count, authorization and blocked state; favorable/omitted report fields cannot suppress durable blockers. Fixtures cover batches, exhausted/blocked records, authorized extra cycles, missing records and invalid counters.

The published b6a91f4 revision passed all six CI checks in run 38466141867,
including actual Xcode 26.6 compilation and 41 simulator tests on each of iPhone
and iPad. These results are baseline evidence; changed code needs a fresh run.
The owner explicitly authorized one additional publication/validation cycle in
this task after the original two automatic cycles. This authorization applies
only to this governance PR. No default budget, requirement or integration gate
is changed by these fixes.

## Further review fixes and owner-requested escalation amendment

- P1 [canonical target correction records](https://github.com/clemarc/fava/pull/10#discussion_r4267662250): justified. Compare target and head records, prevent decreases, and fetch actual owner task-PR authorization rather than accept a truthy marker. Deterministic history checks prevent checkpoint counter resets. Regression fixtures cover forged head-only recovery/authorization and wrong actor/PR/milestone/task comments.
- P1 [integrated task ID reuse](https://github.com/clemarc/fava/pull/10#discussion_r4267662253): justified. Reject represented tasks integrated in either target or head; follow-up source work requires a new reviewed ID. Regression proves the previous frozen task cannot be reinterpreted as new implementation.

The owner explicitly requested publication of these fixes and one extra default
review/fix round on 2026-10-14. The proposed policy, all delivery skills and the
shared validator now allow three rounds, durable across resumptions; a fourth
requires verified owner authorization. Boundary fixtures accept a clean third
round and reject an unauthorized fourth or a still-blocked authorized task.
Escalation now requires linked findings, severity/impact, attempted fixes and
evidence, a concrete proposed patch with validation/risks, and the exact decision
needed, using the repository escalation template. The unadopted 2.0.0 amendment
records this rationale and active-work impact without resetting counters.

54 workflow fixtures and seven publication fixtures pass locally. The earlier
6b3e4af revision passed all six checks in run 38524365083 attempt 2, with 41 tests
on each simulator family. Attempt 1 failed an unchanged app UI navigation
assertion on iPhone; its unchanged retry passed. These are baseline results;
the new publication requires fresh CI/native validation and Codex review.
No R3.5/application work or main merge is authorized by these changes.

## Latest review: owner-authorized fifth correction round

- P1 [intermediate correction reset](https://github.com/clemarc/fava/pull/10#discussion_r4268553948): justified. Target/head comparison alone missed a 0 → 3 → 0 sequence. The prepared validator checks every ledger parent transition; canonical PR-keyed checkpoints retain immutable task/branch identity, monotonically increasing counters and append-only prior heads. The live assessor rejects missing registration, counter rollback and rewritten ancestry.
- P1 [cross-task checkpoint evidence](https://github.com/clemarc/fava/pull/10#discussion_r4268553959): justified. Metadata checkpoints have no Task trailers. Prepared checks inspect integrated records directly, require the exact task in source and merge trailers, and bind actual PR head/target and fetched task evidence. Another task's merge or a forged union trailer cannot complete this task.

59 workflow fixtures and seven publication fixtures pass locally, including
signed synthetic histories for intermediate reset rejection and exact task merge
identity. The owner authorized this fifth round on 2026-10-14. These changes need fresh
CI/native and Codex review after signed publication. [The escalation report](sdd-v2-escalation.md) records impacts,
attempts, proposed fixes, validation, risks and the specific additional-cycle
request and the subsequent explicit authorization. No main/preparation approval
is manufactured; governance remains proposed until the owner merges it.

## Subsequent review: owner-authorized sixth correction round

- P1 [preparation resume budget](https://github.com/clemarc/fava/pull/10#discussion_r4268988652): justified. Persist preparation_prs in signed preparation history, protect prepare branches from rewriting/deletion, validate append-only counters/heads, return verified preparation_progress and require actual owner phase-specific authorization for extra rounds. Missing history never means zero.
- P2 [generic milestone instructions](https://github.com/clemarc/fava/pull/10#discussion_r4268988659): justified ambiguity. Both skills now use the user argument and resolver-returned normalized ID/branches; R3.5 remains a labeled example/contract-specific note. Synthetic R4 resolves its own directory and prefixes.
- P1 independent review / P2 [non-application task completion](https://github.com/clemarc/fava/pull/10#discussion_r4268988666): justified. Exact reviewed path/FR mappings prove task-specific changes for documentation/tooling as well as application tasks. Non-source Task trailers now receive full mapping and planning-chronology validation while retaining SDD-Type requirements.
- P1 independent review target import attribution: justified. A verified automatic target import retains historical trailers without adding completed task IDs to worker scope; altered/conflicted merge trees block assessment. Synthetic signed histories exercise valid target movement and injected merge edits.

The separate reviewer /root/fifth_round_review confirmed the prepared fixes
address its scenarios and found no further concrete regression in focused
re-review. 64 workflow fixtures and seven publication fixtures pass locally.
The fifth published head remains 26eb4db; native CI exposed an unchanged app UI
assertion on iPad and accessibility-size navigation assertions on iPhone. Both
actual failure logs were inspected; unchanged failed-job attempt 2 is running. Neither app/tests nor CI gates are modified.
The owner authorized up to two additional scoped rounds (maximum seven total)
on 2026-10-14; this is round six. See [the escalation report](sdd-v2-escalation.md)
for the findings, patch rationale and exact authorization boundary.

## Consolidated completion and budget proof (authorized round eight)

The owner authorized rounds eight and nine only, maximum nine correction
publications, on 2026-10-14. The prior pause report is retained at
https://github.com/clemarc/fava/pull/10#issuecomment-6167080631.
This patch reconstructs its proposals from published code; no prior /tmp patch
was assumed. All three remaining P1s were independently reproduced:

- [Full completion gates](https://github.com/clemarc/fava/pull/10#discussion_r4268988627): live and historical assessment share explicit-parent verification without resolver recursion. Complete immutable authorized reports, signed history, planning/scope/dependencies, retained actual CI attempts, native job interpretation, independent/Codex review and finding dispositions must precede integration. Later reruns cannot authorize past merges or erase valid earlier proof. Integration must retain the reviewed source tree.
- [Task publication budget](https://github.com/clemarc/fava/pull/10#discussion_r4268988639): zero registration, one boundary/increment per reservation, real PR opening metadata and retained first-parent publications. Canonical signed reservations precede corrections; pure imports may intervene. Resume enforces the cap before publication and reuses pending reservations. Same-count metadata cannot replace a reservation timestamp. Extra-cycle authorization must be immutable and timely. Task-branch protections remain separate owner prerequisites.
- [Replayed target patches](https://github.com/clemarc/fava/pull/10#discussion_r4269846235): completion requires surviving task-owned changes against the exact target as well as reviewed Task/FR/path history. Replayed/reverted work and ambiguous mixed ownership cannot establish completion; documentation/tooling tasks retain support.

Independent read-only reviewer /root/independent_review identified additional
merge-tree, authorization-timing and resume-budget cases during this patch's
review; each received a targeted fix and regression fixture. Review completion
alone is not approval. The final independent conclusion and fresh Codex/CI
results are recorded on the PR after publication.

Local validation: 93 discovered workflow fixtures and seven publication fixtures
pass, including a signed registration/import/reservation/correction/integration/
checkpoint/resume walkthrough, valid application/docs/tooling tasks, interrupted
reservations, successive rounds, skipped work, false/late/edited reports, failed
and late checks/reviews, legitimate reruns and replay/revert/shared-path cases.
SDD/tooling/whitespace checks pass. Synthetic native evidence exercises gate
logic, not actual Xcode execution. Fresh macOS CI and exact-head Codex review
remain necessary after publication; no older run validates this patch.

Current limitations: Linux Cloud with supported subagents and no advertised
Goal capability; one coordinator controls writes. GitHub identity remains
clemarc for both agent and owner, so human intent is a process boundary. Only
main ruleset 24928891 exists; additional main/milestone/prepare/task protections
are proposed, not applied. Git is authoritative; Linear mutation behavior is
fixture-tested and no projection was performed in this task. Physical-device
acceptance remains separate. No application/specification change, R3.5
preparation, merge, auto-merge or settings/credential change was performed.

# SDD reliability rollout and coordinator handoff

All changes remain reviewable PRs; no agent main/milestone merge or activation
is authorized. Git definitions/completion, independent review, signed ancestry,
durable correction reservations/counters, current-head/target gates, guarded
integration and separate physical iPhone/iPad acceptance remain mandatory.
The initial `sdd-reliability-handoff.md` captured the first slice's historical
status; this document records the subsequent implementation and rollout gates.

## Focused changes

| PR | Change | Reviewed implementation head |
| --- | --- | --- |
| [43](https://github.com/clemarc/fava/pull/43) | Capability preflight and deterministic routes | `bf5a641639591efe0762dfb4dbe7cc989d38da8b` |
| [44](https://github.com/clemarc/fava/pull/44) | Native evidence retrieval, fallback and structured verification | `1694e708a11b6541b62cb4a0d11655c5ff493699` |
| [46](https://github.com/clemarc/fava/pull/46) | Compact observations and interrupted-session reconciliation | `a6ca98e3c5b1591185988cee0710c44e057f7cb3` |
| [47](https://github.com/clemarc/fava/pull/47) | Resolver/assessor timing and request/history counters | `403ba24d5ad7b6af28e44eb06f2fc52c20f42400` |
| [48](https://github.com/clemarc/fava/pull/48) | Default-off A1 scheduling and existing-phase timing | `b1eb274298718551a3e7c74385155a05091d3a13` |
| [49](https://github.com/clemarc/fava/pull/49) | Inactive atomic checkpoint validator and ADR-006 proposal | `6b9c446106cc4f594db604599ae4c5a2d594e5d6` |

Each PR records exact changed files, local tests, correctness/security effects,
compatibility, rollback and dependencies. Implementation changes received isolated
independent review; qualifying current-head GitHub Codex and latest Actions remain
separate delivery checks. Refresh them before owner integration, especially after
the signed corrections. Do not interpret this table as CI approval.

Main advanced to `f0047f1aaf8f00f2fabdea9286fe1596a346e313` through owner PR #45.
Preserve its exact historical PR #41 exception and future reverse-target rejection.
An unpublished broader import-classification draft was archived, not published.
ADR-006 avoids collision with the adopted ADR-005. Active R3.5 records, C014/C015,
the spike branch, tracker state and historical signed commits are untouched.

## Owner integration and compatibility

Review PRs in table order, refreshing actual main/head and checks before each
integration. No old successful SHA or earlier target proves the resulting merge.
The sources started from `7b2b072`; owner PR #45 is an intervening target change.
Branches need normal reviewed target refresh as required by protections. Preserve
signatures, both parents and applicable terminal trailers; never rewrite signed
history to conceal the old target.

A local, uncommitted compatibility tree on current main combines all six changes.
It creates no unsigned commit or external integration. Two shared-file resolutions
are required when applying the independent PRs:

- `tools/sdd/milestone.py`: retain the complete recovery CLI flags/body and its
  controlled errors. Add measurement flags and wrap that entire body in the
  measurement invocation. Preserve owner PR #45's exact reconciliation unchanged.
- `.github/checks/native.py`: retain the evidence-summary/log parsing functions
  and the separate compile-feedback function, schedule CLI and phase timing.
  Preserve original test commands and both-family architecture.

The final combined tree `24e6e82f2b3b8f8906858e2db52ae90060806c26`
passed 236 governance fixtures and 16 GitHub tooling tests, including the timing
update. SDD, tooling guardrails, whitespace and standalone pinned-signature
preflight checks passed. Independent compatibility review confirmed the owner
reconciliation is unchanged and the shared-file resolutions preserve both helpers.
These are local compatibility results, not new native or merge acceptance.

The combined tree is retained locally at
`/workspace/shared/fava-reliability-combined-20261025` for inspection. Individual
signed commits remain the publication authority; this local tree is test evidence,
not a new branch merge or acceptance token. Re-run fixtures and current-head CI
after the actual reviewed integration, including main-push verification after
owner merge. Roll back an individual slice with its PR's documented revert path;
keep signed history and correction records.

## Compact operating path after dependency adoption

1. Run the capability preflight. Read the exact operation's interface/access
   state; a report exit zero is not readiness. Use only its permitted fallback.
2. Resolve the owner-supplied milestone through the existing live resolver. For
   an actual task/checkpoint PR, generate `--session-pr NUMBER --handoff`; resume
   with `--recover PATH --handoff`. Respect missing requirements and blocking
   reasons. Never elevate the observation over canonical state.
3. Use structured native evidence for exact run/attempt/head. Invoke the connector
   only for an explicit fallback request, sanitize in memory before persistence,
   then let the parser extract counts and mandatory results. Inspect targeted
   failure diagnostics; do not manually reconstruct successful logs repeatedly.
4. Workers return narrow source/test changes and proposed decisions. The sole
   coordinator retains shared records and serializes transitions. Reviewers
   inspect exact diffs, approved requirements and actual test/evidence references.
5. Refresh the existing integration assessor, actual review dispositions, head
   and target before guarded integration. A `next_action` or successful native
   report is not merge permission. Use `--measure --purpose diagnostic` when
   investigating repeated verification; it never caches acceptance proof.

Read the canonical helper contracts in `github-cloud-commits.md`,
`ci-and-agent-verification.md`, `sdd-v2.md` and `sdd-measurements.md`. Do not
introduce another orchestration service or improvise credentials/API fallbacks.

## Native decision and remaining rollout evidence

Retain parallel iPhone/iPad build/test jobs. The completed paired spike used
32.8 runner-minutes and 18m42s for the current architecture versus 36.9 and
20m05s for shared build; both executed 41 tests per family. Shared run
`40177650776` verified portability but did not improve this paired observation.
There is no production shared-build migration, persistent DerivedData cache or
cross-commit native evidence reuse. Native performance remains separate from
checkpoint governance.

A1 is implemented but disabled in trusted target configuration. Prioritize a
controlled owner-reviewed rollout after signed adoption/import. Keep fast early
compilation, both-family current-head native acceptance, exact-head review and
unchanged-head retry rules. Deferred initial heads still fail ci-required.
Validate actual signed-import synchronize behavior before enabling a milestone.

For each pilot identity, report actual started-job runner consumption, end-to-end
elapsed and queue/overlap time, expected configured and executed test counts by
family, and skipped/cancelled/timed-out/superseded/infrastructure/unavailable
classifications. The phase logger observes existing commands; it does not split
out simulator boot hidden inside xcodebuild test. Compare time from initial source
publication to first actionable defect. Report unavailable latency honestly and
label failed-phase completion only as an upper bound. No A1 savings or change in
defect latency is claimed before an active pilot. See `native-scheduling-pilot.md`.

The consolidation proposal remains disabled. It needs explicit owner sequencing
approval and a separate reviewed activation change; merging preparatory code
does not approve the exception. Standalone completion and separate correction
reservations remain in force. See ADR-006's exact amendment and acceptance cases.

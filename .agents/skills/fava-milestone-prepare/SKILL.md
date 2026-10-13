---
name: fava-milestone-prepare
description: Prepare an approved Fava roadmap milestone in a fresh owner-started Codex Cloud task using only its ID, with signed planning PR and safe resume.
---

# Prepare a milestone

Input: one milestone ID, for example `$fava-milestone-prepare R3.5` or `r3.5`.
Use `tools/sdd/milestone.py` and `docs/process/sdd-v2.md`; do not infer a feature
path, use a prior conversation, or invoke specify/create-new-feature. Read
`AGENTS.md`, constitution, playbook, signing/CI/Linear guidance and applicable
nested instructions before writing. This skill prepares planning only.

1. Check the selected Cloud runtime's actual tools, credentials, network and
   checkout capabilities. Report Linux/macOS distinction and Goal/subagent
   availability. No skill invocation enables a runtime capability. Do not
   execute this workflow before the owner has merged SDD v2 governance to main.
2. Run `python3 tools/sdd/milestone.py R3.5 --phase prepare` using the supplied
   normalized ID. Inspect its complete result: canonical roadmap row, deferred
   scope, dependencies, signed owner roadmap/spec/governance merges and GitHub
   evidence, local/remote refs, all existing PR states, ledger and current SHAs.
   A Draft label is not approval and does not cancel a real owner merge. A
   missing/ambiguous/completed/inconsistent result is a stop with named evidence.
   For R3.5, retain directory `healthkit-run-library-05-reliable-run-history-and-contextual-launch`;
   `05` is unrelated to its decimal ID. PR #9 must be owner-merged; recheck live.
3. Read the exact approved spec and clarifications, all existing lifecycle
   artifacts, checklists, decisions, predecessor verification and execution
   ledger from the selected refs. Confirm integration dependencies using actual
   source/CI evidence, not only checked tasks. R1–R3 device checks remain separate
   acceptance obligations; do not relabel them completed to start R3.5.
4. Set `SPECIFY_FEATURE_DIRECTORY` explicitly to the resolver's absolute path
   for every Spec Kit command, in every worker. Ignore stale feature.json and
   historical Feature Branch metadata. Follow the shared branch/resume procedure
   in `docs/process/sdd-v2.md`: create missing `milestone/r3.5` at the inspected
   main SHA and `prepare/r3.5` at its inspected head; resume matching refs/PRs.
   Use `--checkout milestone` / `--checkout preparation` only on a clean checkout.
   Inspect local unpublished work, worktree occupancy and remote movement first.
   Never reset, stash/discard someone else's files, recreate retired work, force
   refs, or create duplicate PRs. Publish missing remote refs with the existing
   authorized GitHub branch API at the exact inspected SHA.
5. Reconstruct progress before running generators. If prep merged, return the
   existing handoff; do not reopen. If artifacts exist, compare baselines, task
   identities, retired IDs and approvals. Resume the first unfinished stage.
   Approved planning changes need an explicit owner-reviewed amendment PR; do
   not silently regenerate it or invalidate integrated tasks. Append durable
   DEC decisions before any necessary derived regeneration.
6. Run the installed `$speckit-plan`, `$speckit-tasks`, `$speckit-checklist`, then
   `$speckit-analyze` in that order after their prerequisites exist. Read each
   installed skill when using it; repository rules override optional tests and
   local auto-commit hooks. Scope research subagents if supported, otherwise work
   sequentially. Planning must design migration, atomic persistence and failure
   handling, clear/read races, recovery, accessibility, performance and tests
   against the approved FR/US/acceptance scenarios. Do not alter the contract.
7. Produce design, test strategy, exact file paths, stable TNNN/FR/US mappings,
   explicit dependencies, safe parallel groups and shared-file ownership. Use
   `.specify/templates/execution-template.json` for `execution.json` and
   `.specify/templates/preparation-review-template.md` for the report. Record
   inspected specification_base, branch, prep PR/evidence, pending tasks and
   retired IDs. planning_revision stays null until the actual owner prep merge
   exists; never predict a merge SHA. Ledger is execution evidence, not scope.
8. Publish the validated artifacts first as a signed draft prep PR (step 9's
   signing/validation rules apply), so projection source links are reviewable.
   Project tasks with the pinned Linear CLI workflow in
   `docs/process/linear-integration.md`. Inspect help/auth/project, generate a
   dry-run by stable repository key, then upsert only Git-derived definitions.
   Verify actual returned items/hierarchy/status and record successes, failures
   and pending keys. Never claim synchronization from CLI availability. Do not
   project this governance task as R3.5 preparation.
9. Validate SDD, fixtures, semantic analysis, scope and staged diff using
   `$fava-ci-verify`; publish verified GraphQL commits with `SDD-Type: planning`.
   Open/update the same preparation PR **against milestone/r3.5**. Monitor the
   current SHA, read actual failure logs, fix at most two cycles. Record scope,
   migration, risks, coverage and unresolved owner decisions in the report.
10. End with the prep PR, exact revision/evidence, actual Linear status and owner
    handoff: review design/tasks/parallel ownership and reviewer-owned checklists,
    then merge the prep PR into the milestone branch. Do not merge it, implement
    application code or start implementation. Owner starts the second Cloud task.

Goal mode, only if actually available: completion means a signed, validated,
reviewable prep PR and owner handoff, with unresolved decisions reported. Otherwise
use the supported long-running task loop and durable checkpoints; after an
interruption the same invocation resolves and resumes from Git/GitHub.

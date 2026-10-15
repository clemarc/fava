---
name: fava-milestone-implement
description: Coordinate implementation of an owner-prepared Fava milestone from its ID, resuming durable Git/GitHub state and gated task PR integration; leave main for the owner.
---

# Implement a milestone

Input: `$fava-milestone-implement R3.5` (case and surrounding whitespace normalize).
Read `AGENTS.md`, constitution, playbook, `docs/process/sdd-v2.md`, CI/signing/Linear
guidance, and installed skills before using them. Never require chat history, a
feature path or branch argument. Never merge or enable auto-merge into main.

1. Check actual Cloud capabilities. **Explicitly request subagents** using the
   selected runtime's supported delegation tools when available: one isolated
   implementation worker and a separate independent reviewer. If unavailable,
   implement sequentially and obtain independent review through an available
   separate reviewer/session or owner; do not self-certify independent review.
   Do not invent Goal, worktree, agent or resume commands. Runtime limits mean
   checkpoint and resume, not weaken gates. See the shared resource for isolation.
2. Set FAVA_MILESTONE to the user-supplied ID and run
   `python3 tools/sdd/milestone.py "$FAVA_MILESTONE" --phase implement`. Use the
   returned normalized id and branch fields for every subsequent operation.
   Resolve the actual
   canonical directory, dependencies, approved main baseline and all branch/PR
   state. Set `SPECIFY_FEATURE_DIRECTORY` to its returned absolute path. Read
   approved spec/clarifications, plan/tasks, append-only decisions, checklists,
   prep report, ledger and predecessor verification. Stop on unknown, ambiguous,
   completed or inconsistent work. Stop if reviewed preparation has not merged.
3. Verify the merged prep PR's actual destination, signed owner two-parent merge,
   unchanged approved contract and review evidence. Fetch the merge and preserve
   both parents. Register its actual SHA as planning_revision in a signed planning
   checkpoint on the milestone branch through a small registration PR. The owner
   already reviewed preparation; this metadata-only PR may use task integration
   gates with independent review, current CI/signatures and a planning exception.
   No new product approval is manufactured. Before source work use
   `tools/sdd/lifecycle.py` through SDD validation to verify chronology.
4. Use **one coordinator** as the only writer for execution.json, task checkbox
   state, decision-log.md, finding dispositions and Linear state. Reconcile each
   record with live PRs/branches/commits/checks/reviews before scheduling. Verify
   integrated merge SHAs are ancestors of the current milestone head. A worker
   crash, missing PR response, closed PR or stale lease requires inspection before
   retry. Existing open task PRs take precedence over new branches. Merged task
   evidence is reconciled, not implemented again; a closed unmerged task needs a
   recorded reason/owner decision before reopening. Preserve correction counts.
   Reconciliation verifies each integrated ID's actual source/merge trailers,
   PR head and SHA-bound task evidence; another task's merge is not completion.
5. Select a small task or coherent batch whose dependencies are integrated.
   Task branch is the returned task_branch_prefix plus the lowercase lowest
   stable task ID in a batch (e.g. t003); never infer a prefix from an example.
   Branch from the **inspected current milestone head**. Inspect local/remote
   refs, worktree list, matching PRs and ledger before creation. Use isolated
   clean checkouts; subagents share files unless isolation is explicitly created.
   Sequential execution is the baseline. Parallelism requires reviewed groups,
   disjoint write paths, satisfied dependencies and separate worktrees/checkouts.
   All integrations serialize through the coordinator; workers never update
   shared records. Append DEC rationale before regenerating derived artifacts.
6. Scope `$speckit-implement` to those task IDs. Mandatory automated acceptance
   and failure tests apply. Workers return code/test changes, proposed decisions
   and evidence; coordinator records them. Do not tick quality checklists or
   manufacture owner approval. Record local verification; Xcode awaits actual
   macOS CI when Cloud is Linux. Use only synthetic fixtures.
7. Publish signed GraphQL commits with Spec/Task/Implements trailers. The
   coordinator adds scoped durable progress/evidence in the task branch and
   opens/updates its signed PR against the milestone branch. Request independent
   review and configured Codex bot review for the full current head SHA using a
   new unedited SHA-scoped request comment; never reuse old reactions. Review
   requests/comments to GitHub are authorized by this owner-started skill.
   Before integration, register its numeric PR key, immutable branch/task IDs,
   zero counter and one initial published head in task_prs via a gated metadata checkpoint on
   the milestone. Before each fix round, checkpoint the incremented PR counter
   and prior head there; synchronize the worker's signed history/counters with
   that target. Preserve all registered heads as ancestors; never force rewrite
   them. Require task branch signatures/no-force-push/no-deletion protections.
   Read resolver task_progress: resume-reserved-fix finishes the existing round
   without another increment; registration-required reuses the existing PR.
   Every correction is one non-import publication following its canonical signed
   reservation; pure automatic imports may intervene. Initial registration must
   bind the real pre-opening head at zero. Checkpoint gating cannot
   manufacture task completion: exact merge/PR/task report proof is mandatory.
8. Monitor current-head CI, macOS build and **nonzero simulator tests** when
   native applies. Read real failed logs and Codex comments; assess each finding,
   fix justified issues and refresh tests/review after changes. Retain three
   automatic correction cycles per PR across invocations; then record blocked
   findings and continue unrelated ready tasks. Use
   `.specify/templates/escalation-template.md` to give the owner linked findings,
   severity/impact, attempted fixes and a concrete proposed patch with tests,
   risks and the precise decision/extra-cycle authorization needed. Prepare
   reviewable fixes within scope before escalating; do not publish another cycle
   without authorization. Never relax requirements/gates.
9. Apply every gate in `docs/process/sdd-v2.md`, using
   `python3 tools/sdd/integration.py "$FAVA_MILESTONE" --pr NUMBER --evidence-comment COMMENT_ID`
   with retained check_run_ids and the immutable independent JSON report described
   in the shared resource, after setting FAVA_MILESTONE to the resolver-returned normalized id
   with a coordinator JSON comment written after publication of the current
   SHA (see the shared resource) as a read-only structural
   assessment. Independently inspect its referenced semantic/review/native
   reports and all live review discussions; a successful assessment does not
   itself authorize integration. Verify report revision/author and evidence,
   every finding's disposition and current target SHA. No stale or pending bot
   review counts; prove actual unavailability if configured review cannot run.
10. Once authorized gates pass, **merge only this task PR into the registered
    milestone branch**, with a two-parent merge retaining source history and
    valid merge-message trailers. Reinspect the target immediately before the
    request and use the current PR-head guard. Target movement invalidates gates;
    update the task branch with a signed, trailered target merge, then rerun
    validation/review before integration. Target imports must match Git’s pure
    automatic merge tree; any conflict resolution or additional edits belong in
    separate scoped task commits before the import. Import trailers retain
    historical mappings but do not add completed IDs to the worker’s scope.
    Disable no protections; use no
    auto-merge. Verify the actual integration commit signature, parents, target,
    full tree and PR linkage. If post-merge signature verification fails, stop
    further integrations and record the blocker; never declare completion.
11. Record integrated task state, checkboxes, merge/evidence links and actual
    Linear results through a serialized signed checkpoint PR to the milestone.
    Before any retry inspect whether a prior merge/checkpoint already succeeded.
    Do not overwrite integrated records; follow-up fixes receive new task IDs.
    Repeat reconciliation and scheduling until all approved implementation and
    whole-milestone automated validation pass. No ready work plus blockers means
    a durable blocked handoff, not success or silent infinite retries.
12. Run `$speckit-analyze` and `$speckit-converge` on complete artifacts. Check
    additions against approved scope; owner-review any planning amendment before
    implementation. Run whole-milestone regression on the exact current head.
    Open/update **the returned milestone_branch → main** and follow the final
    handoff template.
    Report exact tested SHA, CI/simulator, task/FR/acceptance coverage, migration,
    persistence and race evidence, physical iPhone/iPad instructions, accessibility
    and performance results/pending checks, outstanding findings and actual
    Linear projection. Stop ready for owner testing/review, never main merge.

R3.5 remains active while approved physical iPhone/iPad acceptance is pending.
After owner testing, incorporate only authorized fixes through the same gates,
record sanitized acceptance evidence, then propose the verified completion/freeze
transition. Main merge remains the owner's action. Preserve specification baseline
metadata through the milestone PR; after acceptance, authorized fixes and the
owner's main promotion, propose completion/freeze in a separate signed metadata-only
PR for owner review and merge, with acceptance evidence and no application changes.
Goal completion, where available, is the ready-for-owner handoff (or an explicit blocker), not product
acceptance/main merge; otherwise run the supported long-running loop with durable
checkpoints and use this same invocation to resume interrupted work.

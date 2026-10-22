---
name: fava-independent-review
description: Independently review a Fava change against its approved scope, valid workflows, regression coverage and actual validation evidence; return findings bound to the inspected head and target through the invoking review system.
---

# Independently review a change

Input: PR number or explicit head and target revisions, lifecycle stage and task
IDs when applicable. Resolve full SHAs from actual Git/GitHub evidence; report
missing or contradictory inputs rather than infer approval from chat history.

Read `AGENTS.md`, `.specify/memory/constitution.md`,
`docs/process/sdd-playbook.md`, `docs/process/sdd-v2.md`,
`docs/process/ci-and-agent-verification.md` and `docs/process/writing.md`.
These are the canonical gates and evidence requirements; this skill supplies
the review procedure without changing merge authority or correction budgets.

## Independence and scope

The reviewer must be a separate runtime/session or owner from the implementation
worker. Record both identities. A worker may use this procedure for self-checks,
but must label the result as self-review, not independent evidence.

Review without editing tracked files, checklist markers or execution records.
Return findings through the invoking review system: a subagent returns its report
to the coordinator; GitHub Codex review emits its normal review output. The
coordinator retains the separate report's unedited wording and identity. Run
relevant checks in an isolated checkout or temporary workspace when they write
artifacts. Use synthetic data. Do not make additional external API writes,
publish commits or integration reports, resolve threads, merge or delegate
implementation through this skill.

## Review procedure

1. Bind the review to the actual full head and target SHAs. Read the complete
   target-to-head diff, affected callers and tests, and relevant prior history;
   do not limit review to the latest correction. Read the approved specification,
   available plan/tasks and append-only decisions. For governance or maintenance,
   use its stated scope and governing process rather than invent feature artifacts.
2. Check scope and traceability: task/FR/story mappings, reviewed paths,
   dependencies, preparation approval and preservation of approved requirements
   and completed history. Distinguish imported target history from worker-owned
   changes. Inspect the actual implementation rather than accept favorable
   report fields as proof.
3. Check every independently integrated task's intermediate behavior. API,
   caller, UI, fixture and test migrations must land when needed to compile and
   preserve truthful behavior. Activating a feature must include its minimum
   acceptance/failure coverage; later tasks may expand that baseline.
4. Follow the changed behavior through relevant success and failure paths:
   persistence/reload, migration, authorization, cancellation, concurrency,
   navigation, accessibility and recovery. Check invariants across components,
   including observation provenance and publication only after successful saving.
   Select paths relevant to the change rather than manufacture findings for
   unrelated features.
5. For workflow changes, examine lifecycle transitions and valid execution as
   well as rejection: preparation and amendments, owner merge, startup,
   registration, correction reservation, target import, integration, checkpoint,
   interruption/resume and completion. Look for valid docs/tooling tasks being
   rejected and invalid older history being hidden by later valid records.
   Check evidence identity, immutability and chronology at boundaries, including
   equal timestamps, using the canonical SDD rules.
6. Assess test quality. Assertions must verify the intended result and relevant
   failure cases. Preserve meaningful existing regression coverage; fallback
   navigation, weakened assertions or fixtures that bypass production behavior
   cannot establish correctness. Run focused available checks when useful and
   record their actual outcomes; distinguish synthetic gate fixtures from native
   execution.
7. Inspect actual current-head CI results and, when native applies, configured
   iPhone/iPad job logs and relevant artifacts. Verify checkout, build result,
   nonzero executed tests and failures. Distinguish skipped, cancelled, missing
   or inaccessible evidence from success. State access limitations explicitly;
   do not substitute a coordinator's summary for independent inspection.
8. Form an initial findings pass before reading prior reviewer conclusions when
   practical. Then inspect every actual Codex/other review finding and its proposed
   disposition. Confirm fixes against code and tests; identify first-discovered,
   duplicate and confirmed findings separately when provenance is available.
   A no-findings review is limited to the inspected scope and evidence.
9. Recheck head and target before returning the final report. Movement invalidates
   current integration evidence. After fixes, review the affected behavior and
   regressions, not merely whether a suggested patch was applied.

## Report

Lead with actionable findings, ordered by severity. For each, provide a precise
file/line reference, concrete trigger, observable consequence, requirement or
invariant violated, and reproduction/test evidence when available. Distinguish
demonstrated defects from unresolved questions and verification limitations.
Avoid speculative issues and preferences without a concrete consequence.

Record full head/target SHAs, worker/reviewer identities, scope, checks actually
run or inspected, and missing evidence. If no actionable findings remain, say so
explicitly without implying owner approval or physical-device acceptance.

When integration evidence is requested, use the independent JSON report contract
in `docs/process/sdd-v2.md`. Supply semantic/finding/native attestations only
after actual inspection. All included findings must precede the final immutable
independent report; a newly arriving finding requires refreshed assessment.
Report unresolved findings or unavailable evidence honestly instead of producing
a favorable integration report. The coordinator owns publication and disposition
records; this skill grants no additional external write authority.

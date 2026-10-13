# R3.5 Clarification Review Report

**Date**: 2026-10-13
**Feature**: [spec.md](../spec.md)
**Command**: `speckit-clarify r3.5`
**Stage**: Specification refinement in PR #9, before specification merge or planning.

## Accepted answers

Two questions asked and answered, one at a time:

1. No saved runs, including first installation and confirmed clearing: setup/access. Readable populated history: direct library launch.
2. Source read succeeds but local saving fails: display only previously saved runs and saved provenance, report saving failure and offer Retry when available. Do not show temporary unsaved rows/updates. With no saved history, show no rows and explicit saving-failure feedback.

Answers are recorded once each under `spec.md` §Clarifications and incorporated in the contract. Prior owner choices about retaining all identities and entry reads for new data remain in force.

## Sections updated

- Clarifications: two accepted answers.
- User Scenarios & Testing: US2's saving-failure/subset scenarios and US3's saved-observation provenance.
- Edge Cases: unsaved updates, unchanged saved metadata and a fresh-source-read Retry.
- Functional Requirements: FR-005 and FR-007–FR-009 distinguish source success, local saving and saved-history publication.
- Key Entities: latest saved read observation and saved row provenance.
- Success Criteria: SC-002/SC-003 cover saving failures with populated and absent history, unchanged saved times/membership and available Retry.
- Assumptions: launch choice is owner-confirmed rather than a draft default; saving-failure choice is recorded.

## Spec quality checklist

Built-in `requirements.md`: **16/16 → 16/16** passing.
Newly passing: none. Regressions: none. Still unchecked: none.
No marker or other content changes were needed; its original specification-review notes remain historical. This report records the current clarification result.

The reviewer-owned `history.md` remains untouched and unchecked; generated checklist markers are not implementation evidence or owner approval.

## Coverage summary

| Category | Status | Disposition |
| --- | --- | --- |
| Functional scope and behavior | Clear | Retention, entry reads and exclusions already defined; prior owner choices preserved. |
| Domain and data model | Resolved | Saved history/provenance advance together only after successful saving; unsaved source outcome stays separate. |
| Interaction and UX flow | Resolved | No-history launch selected; saving failure has exact rows, feedback and Retry. |
| Non-functional quality attributes | Clear | Performance budget, offline use, durable retention/clearing, privacy boundaries and accessibility are measurable. |
| Integration and external dependencies | Clear | Workout-only HealthKit access, neutral empty results and source/local failures are distinct. |
| Edge cases and failure handling | Resolved | Saving failure with no rows, older data, concurrent reads and clearing races have acceptance coverage. |
| Constraints and tradeoffs | Deferred | Migration/storage mechanics and exact formatting belong to planning; no product decision is deferred. |
| Terminology and consistency | Resolved | Saved observation, retained history and current attempt outcome have distinct meanings. |
| Completion signals | Clear | Automated synthetic acceptance and separate sanitized device evidence remain required after implementation. |
| Miscellaneous and placeholders | Clear | No unresolved clarification markers or unselected launch default remain. |

No critical unresolved ambiguity or remaining product question was found. Planning may follow owner review and merge of the specification. Suggested next command after merge: `speckit-plan r3.5`.

## Verification and lifecycle

- Deterministic SDD/roadmap/requirement checks, 29 validator/tooling fixtures, seven commit-builder fixtures and tooling validation passed locally.
- Existing roadmap and historical R1–R3 directories were compared with the main base and are unchanged. No plans, tasks, application code or Linear mutations are introduced.
- Before/after clarify hooks are disabled in `.specify/extensions.yml`; no hook execution or unsigned local commit is required. Verified GraphQL publication and latest-head Actions evidence are attached to PR #9.
- Analyze/converge prerequisites do not exist at this stage; they were not invoked. Native builds/device acceptance are future implementation obligations, not claimed by this specification refinement.

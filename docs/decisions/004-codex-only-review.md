# ADR-004: Use Codex as the required reviewer

Date: 2026-10-22. Status: proposed for owner adoption in PR #36.

The owner requested one review gate after comparing Codex and separate-reviewer
findings. Replace the mandatory additional reviewer runtime with Codex PR review.
This trades the extra reviewer's distinct defect detection for lower coordination
cost. Broader instructions improve coverage but do not prove that one review is
equivalent to two. Reassess using unique valid findings and review effort.

Codex follows `.agents/skills/fava-review/SKILL.md`. The coordinator still verifies
scope against approved requirements/tasks, interprets actual CI/native logs and
records evidence-backed dispositions of every actual finding. This inspection
may be performed by the implementation coordinator; it is not represented as
independent review. Owner main/preparation approval, signing, tests, physical
acceptance and the source correction budget remain unchanged. Codex failure or
timeout blocks integration; an unavailability note cannot waive this sole gate.

## Adoption and historical evidence

This supersedes ADR-002’s additional-reviewer obligation only for newly adopted
targets. It is a major governance amendment, proposed as constitution 3.0.0. The
[pinned policy record](004-codex-only-review-policy.json) activates only after
the actual signed owner governance merge into main is imported unchanged into
the milestone target. A record in the PR head alone cannot activate the policy.
The verifier checks the introducing owner merge and actual merged PR destination.
Malformed, edited or unadopted policy evidence blocks assessment.

For new integrations after activation, the immutable coordinator JSON contains
`review_policy: codex-only-v1`, exact validated head/target, successful check IDs,
semantic assessment, complete finding dispositions, interpreted native evidence
when applicable, and actual Codex completion proof. No independent-review comment
or second runtime identity is required. Actual findings must precede that report;
favorable booleans and predicted URLs cannot dispose future content.

When reconciling an earlier integration, select its policy from the retained
target parent. A target without the new record retains mandatory independent
review and its original evidence chronology. Do not migrate, rewrite or weaken
T001–T003 reports, completed checkpoints, preparation history or correction counts.
In-flight work uses the new policy only after target synchronization and fresh
head/target evidence. Main and preparation remain owner-merged.

## Review requests and recovery

The [timing evidence and retry procedure](../process/codex-review.md) distinguish
same-head request retries from source correction publications. Request state is
retained in immutable GitHub comments; restarting the coordinator cannot reset
the retry count or deadline. One request retry is allowed after failure or a
20-minute inactive timeout. Running reviews are polled without duplicate requests.
At 45 minutes overall or an exhausted retry budget, retain a blocked handoff;
never manufacture review completion. Recheck actual evidence before each write
and after ambiguous API responses. Only the coordinator writes request comments.

This decision does not authorize adopting itself, merging main, changing GitHub
settings, integrating blocked tasks or accepting the feature on physical devices.

# SDD reliability implementation handoff

This maintenance work targets main through an owner-reviewed PR. It does not
modify R3.5 execution records or activate governance changes.

## Slice 1: capability preflight

Changed files:

- `tools/github/preflight.py`: read-only session capability report and operation routes.
- `tools/github/test_preflight.py`: success, missing prerequisites, transport,
  authorization, malformed/partial response and safe-routing fixtures.
- `docs/process/github-cloud-commits.md`: report contract and reconciliation rules.
- `.agents/skills/fava-ci-verify/SKILL.md`: invoke the preflight before Cloud operations.
- This handoff: scope, remaining work and rollback.

The existing `tooling-validation` job already discovers these tests. No workflow
trigger, native acceptance, review, signing or correction policy changes. This is
observational tooling: it does not execute mutations or supply new credentials.
Rollback by reverting the slice and removing its skill invocation. Existing
publication and delivery helpers remain usable throughout.

Local validation: 16 GitHub tooling tests and 167 synthetic governance tests
passed; SDD quality, tooling guardrails and diff whitespace checks passed.
Governance fixtures required approved sandbox escalation for temporary GPG
signing sockets. An independent review found a missing-helper crash and an
unsupported-command classification gap; both were fixed and the reviewer
confirmed no remaining actionable findings. GitHub Codex review and current-head
Actions remain publication checks, not established by these local results.

At initial inspection on 2026-10-24, main was
`7b2b072b69b314ca6574153e45b047ac0d1068d3`; milestone/r3.5 was
`195631baf6deb20fcfce595fb43287cbde6a6206`. Task PR #39 targeted milestone/r3.5;
spike PR #42 targeted main. Treat these as navigation references only: refresh
live state before further work. Do not edit or check out the spike branch.
Direct read-only GraphQL required approved sandbox escalation and then succeeded;
connector branch inspection also succeeded. Neither proves mutation success.

## Remaining slices (not implemented)

1. Native evidence retrieval: extend `.github/checks/native.py` and the current
   CI verifier; bind workflow/run/attempt/job identity, process connector
   `structuredContent.content` and chunking without model log parsing; separate
   required evidence from optional artifacts; sanitize destinations and classify
   unsuccessful outcomes. Fail closed on unavailable mandatory evidence.
2. Recovery: generate compact snapshots through existing milestone/integration
   helpers; reconcile every interrupted transition with current Git/GitHub;
   never trust a snapshot over authoritative state. Add all interrupted-session
   cases from the assignment before reducing existing coordinator checks.
3. Measurements: instrument resolver/assessor and GitHub calls for duration,
   request/object counts, historical repeats and live refresh. No persistent
   proof cache without reviewed invalidation rules.
4. A1 pilot: inspect registration/import and current-head retry policy before
   scheduling changes. Preserve early compilation, full iPhone/iPad acceptance,
   exact-head review, correction runs, cancellation scope and required checks.
   Report runner-time separately from elapsed time against the supplied baseline.
   Keep the shared-build spike's architecture and files outside this work.
5. Consolidation preparation: draft the narrow
   `INTEGRATED_PENDING_COMPLETION` sequencing exception for owner approval;
   implement atomic synthetic validators and interrupted-operation tests.
   Keep activation disabled. No successor correction or integration before
   canonical registration. Preserve standalone completion fallback, reservation
   counters and retained-head ancestry; do not recreate C014/C015.
6. Simplify coordinator instructions only as deterministic helpers replace
   manual steps. Keep review tied to exact candidate diff and test evidence.

Sequence shared-file changes. Each slice needs focused negative tests, existing
synthetic governance fixtures, signed publication and independent Codex review.
No main or milestone merge is authorized by this handoff. The owner must approve
any governance-policy activation separately.

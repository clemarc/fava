# Spec-Driven Delivery Playbook

Fava uses Spec Kit 1.0.13 and Codex, with Git authoritative and Linear a one-way
projection. The constitution governs this playbook. SDD v2 is proposed until the
owner reviews and merges its governance PR; the earlier prohibition on agent
merges remains effective until that adoption.

## Sources and artifact ownership

| Artifact | Role | Ownership |
| --- | --- | --- |
| Constitution | Principles, gates, pins and authority | Owner-approved governance PR |
| Epic roadmap | Stable slices, scope and dependencies | Owner-reviewed/main-merged |
| Feature spec/clarifications | Requirements and acceptance contract | Owner-reviewed/main-merged |
| Decision log | Durable rationale with DEC-NNN IDs | Append-only, coordinator writes |
| Plan/research/data model/contracts | Derived implementation design | Preparation review; owner merge |
| Tasks | Stable TNNN, FR/US mappings, paths, dependencies | Git canonical; coordinator records verification |
| Reviewer quality checklists | Requirement quality, not implementation evidence | Reviewer marks; workers read only |
| Execution ledger | Reconciled branches, revisions, states and evidence | One coordinator; not a requirements source |
| Current-state specs | Qualified current/superseded FRs | Reviewed reconciliation PR |
| Linear | Stakeholder task/progress projection | Pinned CLI; verified repository keys |

An approved spec controls requirements. Active derived artifacts may grow with
review; record durable decisions before regeneration. Changed requirements use
human-approved supersession in a new directory. Explicit verified completion
freezes the entire feature directory. Do not rewrite R1–R3 history or change
R3.5's approved scope, clarifications and acceptance.

## Owner-started lifecycle

| Stage | Owner and operation | Exit gate |
| --- | --- | --- |
| Roadmap/specification | Owner reviews separate roadmap/spec/clarification PRs | Human merge to main |
| Preparation | Owner starts `$fava-milestone-prepare R3.5` | Signed validated prep PR to milestone branch, owner handoff |
| Preparation approval | Owner reviews plan/tasks/quality/parallel ownership | Human merge into milestone branch |
| Implementation | Owner starts `$fava-milestone-implement R3.5`; one coordinator | Gated task PRs serialized into milestone branch |
| Whole-milestone handoff | Coordinator validates and opens milestone → main | Exact tested revision ready for owner device testing/review |
| Acceptance/completion | Owner tests physical iPhone/iPad, authorizes fixes | Evidence recorded before proposed completion/freeze; human main merge |
| Reconciliation | Account for qualified FRs/current supersession | Reviewed PR to main |

Read [SDD v2 operations](sdd-v2.md) for executable resolution, branch/resume,
ledger, preparation, integration gates, correction limits and handoff. Skills take
only an ID, normalize case/outer whitespace, and reconstruct from Git/GitHub.
Decimal milestones retain their exact canonical directories; numbering is never
inferred. Set SPECIFY_FEATURE_DIRECTORY explicitly. Unknown, ambiguous, completed
or contradictory work stops precisely. A draft/agreed marker is not approval.

Preparation runs plan → tasks → checklist → analyze in lifecycle order. No source
implementation before the actual signed owner planning merge. Existing prep is
resumed, never blindly regenerated/reopened; planning amendments require owner
review. One coordinator owns shared task records/decisions/ledger and integration.
Explicitly request subagents where supported; independent review is separate
from the worker. Sequential work is the baseline. Parallel groups require reviewed
disjoint ownership, isolated checkouts and integrated dependencies.

## Task design and traceability

Each task is independently executable and verifiable, with exact paths, FR and
US references and dependencies. Setup/Foundational tasks may use a reasoned
FR-exempt clause. Preserve IDs for retained work; retire removed keys permanently.
A [P] marker alone does not establish safe parallelism.

```text
- [ ] T014 [US1] Implement and test behavior in Fava/Example.swift and FavaTests/ExampleTests.swift (FR-003) (depends on T013)
```

Source commits and source-bearing merge commits use Spec/Task/Implements trailers
resolving to actual approved task/FR mappings. Preserve both merge parents/task
history. Non-feature changes use documented SDD-Type exceptions without invented
FRs. Audit walk: source → signed commit → task → qualified FR/spec → roadmap →
approval PR, validation/review and tracker projection. Decision IDs are append-only;
reversals cite their predecessor. Completion records cite actual verified evidence.

## Quality and approval gates

Tests are mandatory, including appropriate automated acceptance/failure scenarios.
Native work requires actual macOS Xcode compilation and nonzero simulator tests;
HealthKit acceptance additionally needs separate physical iPhone/iPad evidence.
Simulator results cannot prove real device authorization/workout access. Public
source/logs/PRs/artifacts contain synthetic data only.

GitHub Actions enforce deterministic structure/lifecycle, trailers, tooling,
native applicability/build/tests and fail-closed ci-required on the current SHA.
No headless AI gate, OpenAI API key or tracker credential in Actions. Installed
checklist/analyze/converge supplement CI with semantic review. They cannot
replace deterministic tests, signing or human acceptance.

Task integration requires current head AND target evidence: authorized scope,
integrated dependencies, valid trailers and all introduced signatures, CI/native
success, separate independent review, completed configured available Codex review,
evidence-backed disposition of every finding and structural/semantic drift checks.
Head edits or target movement refresh validation/review. Unresolved critical
correctness/security/scope/consistency findings block integration. Two automatic
correction cycles per task PR; further cycles require owner authorization. Record
blockers and continue unrelated ready tasks rather than weakening gates.

Quality checklist markers belong to reviewers. Implementation workers cannot
mark them or manufacture owner approval. GitHub bot review is not an owner's
approval and pending/stale reviews are not completed review.

## Cloud publication, runtime and settings

Use the [verified GraphQL process](github-cloud-commits.md) and
[delivery skill](../../.agents/skills/fava-ci-verify/SKILL.md). Inspect the branch
head, stage only intended files, use expectedHeadOid, and verify GitHub signature,
identity, complete tree, parents/message and destination. Never silently publish
unsigned local/REST commits or commit directly to main. Monitor latest-head CI;
read actual failed logs and report limitations honestly.

Main and preparation remain human-merged. After owner governance adoption,
only the coordinator may integrate gated task/checkpoint PRs to the registered
milestone. Never main merge or auto-merge. Verify runtime capabilities per task;
no skill enables unavailable Goal/subagent/macOS features. Supported long-running
loops use durable checkpoints for interruption recovery.

[Observed/proposed GitHub settings](sdd-v2-settings.md) are separate from repository
changes. Shared owner credentials cannot distinguish agent versus human merges;
stronger enforcement needs explicitly provisioned identity separation and
owner-only main restrictions. No credentials/settings are provisioned silently.

## Linear projection and reconciliation

Use the [pinned project-local CLI/skill](linear-integration.md). Project maps to
epic, milestone to roadmap slice, story to parent issue, task to sub-issue (Setup/
Foundational may sit directly under the milestone). Stable keys include feature
path and US/T ID; titles are not identity. Dry-run, detect duplicates/drift,
upsert canonical fields, verify returned hierarchy/status and record actual
success/pending keys. No automatic deletion, bidirectional requirements sync or
CI tracker dependency. Coordinator alone writes projection state; disable
competing native status automation through owner settings.

After delivery, current-state reconciliation accounts for each completed qualified
FR as current or superseded. Preserve historical contracts/decisions. Do not label
R3.5 completed while its approved physical acceptance is pending.

## Project decisions

- [ADR-001](../decisions/001-ci-and-cloud-delivery.md): deterministic CI, staged
  contracts, signed Cloud delivery, mandatory native/device validation.
- [ADR-002](../decisions/002-owner-started-milestone-delivery.md): two repository
  skills, shared milestone resolution, owner preparation and limited integration.
- [R1–R3 pilot](r1-r3-delivery-pilot.md): fixed historical exception; not broadened.
- Spec Kit pins remain in init-options/integration; upgrades require a reviewed
  branch and active-artifact validation. No new orchestration service is introduced.

Sources: [GitHub Spec Kit](https://github.com/github/spec-kit),
[Linear GitHub integration](https://linear.app/docs/github). This Fava-specific
playbook replaces the generic Oct 5 reference assumptions about headless CI,
tracker services and approval authority; product contracts/history are unchanged.

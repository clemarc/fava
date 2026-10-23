# Fava Constitution

## Core Principles

### I. Flow-Forward

Requirements in a feature whose specification PR has merged MUST be controlled
contracts: changed requirements MUST create a new feature/change directory naming
the predecessor with `Supersedes:`. Active features MAY add or regenerate derived
planning/task artifacts in subsequent planning and implementation PRs. Decision logs
MUST remain append-only. After verified completion, mark `Status: completed` in
`spec.md`; the entire completed feature directory MUST then remain frozen.
Completion metadata does not permit rewriting historical requirements.
This preserves the requirements and decisions that governed delivered work.

### II. Living Spec

For an active feature, `spec.md` MUST be the human-edited requirements contract.
`plan.md` and `tasks.md` MUST be derived from that contract and MAY be regenerated.
Scope and acceptance changes MUST originate in `spec.md` before derived artifacts
are updated. Durable implementation rationale MUST be recorded in
`decision-log.md` so regeneration cannot erase it.

### III. Spec of Specs

Work framed as an epic MUST be decomposed first in a `roadmap.md`. Every sub-feature
MUST reference its parent roadmap entry and state an explicit scope boundary.
The roadmap MUST identify the slices and their dependencies; scope changes MUST
update the roadmap and affected specs before implementation proceeds.

### IV. Enforced Quality Gates

Tests MUST be mandatory. Every user-story implementation MUST be verifiable by
automated tests appropriate to its component, including acceptance behavior and
relevant failure cases. Automated tests and applicable deterministic checks MUST
pass before work is considered complete; applicable GitHub Actions deterministic PR checks MUST pass against the latest
commit before merge. Xcode compilation and simulator tests MUST run on macOS CI
for native changes. HealthKit authorization and real workout access on a physical
device MUST be verified separately before HealthKit feature acceptance. Spec Kit analysis MUST supplement deterministic checks and MUST NOT be
the sole blocking quality gate. Critical consistency findings MUST be resolved
before the affected work proceeds.

### V. Repository Canonical

Requirements, plans, decisions, and generated implementation tasks MUST be
canonical in Git. External trackers MUST be projections of repository state and
MUST NOT become competing requirements sources.

For this pilot, generated tasks MUST also be projected into Linear to provide
implementation-progress visibility; `tasks.md` remains canonical. Linear MUST be
treated as read-only for requirements and task definition. Changes to task scope,
wording, requirements, or acceptance criteria MUST originate in the repository
and be re-projected to Linear. Progress displayed in Linear MUST reflect repository
state.

Projected work MUST use stable repository keys, never Linear issue titles as
identifiers. A task key MUST include its feature directory and task ID, for example
`001-workout-summary/T014`. Regeneration MUST preserve keys for retained tasks;
retired keys MUST NOT be reused for different work.

## Technical Rules and Project Pins

- Fava MUST be a native personal iPhone and iPad application targeting iOS and iPadOS,
  written in Swift with SwiftUI.
- The application architecture MUST be local-first. HealthKit MUST be the authoritative
  source for health and workout data; local caches or derived views MUST NOT become
  competing sources of truth.
- Standard Apple frameworks MUST be preferred. Each additional dependency MUST have a
  documented reason in the feature's `decision-log.md`.
- Each new durable implementation decision MUST be recorded in `decision-log.md`
  with a stable DEC identifier, such as `DEC-001`, and its rationale. Reversals MUST
  be new entries referencing the decisions they supersede.
- **Spec Kit pin:** **1.0.13**, confirmed by `.specify/init-options.json` and
  `.specify/integration.json`.
- **Coding agent:** **Codex**.
- **Agent version:** TODO(CODEX_VERSION): no reliable Codex application/CLI version
  is recorded in the repository.
- **Model pin:** TODO(CODING_MODEL): no reliable coding-model identifier/version
  is recorded in the repository.

## Development Workflow and Quality Gates

- Each implementation task MUST cite at least one FR identifier. Explicitly defined
  Setup or Foundational tasks MAY omit an FR when no meaningful requirement mapping
  exists; the exemption MUST be stated in the task.
- Tasks MUST name exact file paths wherever known and MUST be small enough to execute
  and verify independently.
- Source-bearing merge commits MUST retain task history, verified signatures and
  the same resolvable trailers as source commits, using the union of task/FR
  mappings; non-source preparation/checkpoint merges use SDD-Type: planning.
- Commits implementing feature work MUST carry `Spec:`, `Task:`, and `Implements:`
  trailers resolving to the feature, task, and applicable FR identifiers. A Setup or
  Foundational FR exemption MUST be explicit rather than inventing a requirement.
- Before implementation, specs, plans, and tasks MUST agree on scope and references.
  Before completion, acceptance behavior MUST have automated test evidence, task
  status MUST reflect verified work, and durable decisions MUST be recorded.
- Review MUST verify constitution compliance, resolvable requirement/task references,
  passing applicable deterministic checks, and preservation of approved requirements and completed feature history.

Codex Cloud MUST prefer GitHub GraphQL `createCommitOnBranch` using existing
API authorization and MUST verify the actual GitHub signature, branch and intended
tree before claiming a signed delivery. The signing policy does not replace SDD
trailers; no unsigned local/REST fallback may be silently published. Non-feature
commits MUST use an explicit documented `SDD-Type:` exception without fabricated
FR/task references. Agent-driven Spec Kit checks supplement deterministic Actions
and MUST NOT require an OpenAI API key in CI.

Roadmap/specification/clarification and governance PRs MUST be owner-reviewed and
human-merged to main. Preparation PRs MUST be owner-reviewed and human-merged to
the registered milestone integration branch before source implementation. After
owner adoption of this amendment, one coordinator MAY merge Codex-reviewed
task/checkpoint PRs only into that registered branch after all current
head/target gates in `docs/process/sdd-v2.md` pass. Agents MUST NOT merge or enable
auto-merge to main; auto-merge MUST NOT be used. The prior prohibition on all agent
merges remains effective until the owner approves and merges this governance.
For this solo pilot no additional-person GitHub approval is required, but task
integration MUST have review separate from the implementation worker. In Codex Cloud,
Linear operations MUST use the pinned project-local CLI/skill, while local MCP
configuration remains supported. Linear connectivity MUST NOT gate CI.

Owner-started preparation and implementation MUST resolve a milestone from the
canonical roadmap and live Git/GitHub evidence without previous chat context.
Stable IDs/directories and approved requirements MUST remain intact. Durable
execution state MUST be reconciled to actual branches, commits, reviews and
checks; ledger claims MUST NOT substitute for approval. Reviewed planning MUST
precede source implementation, including final milestone promotion that introduces
planning and implementation together. CI MUST remain credential-free and deterministic.

One coordinator MUST serialize integration and shared execution/task/decision
records. Parallel workers require isolated checkouts, disjoint ownership and
satisfied dependencies. Every integration MUST verify destination/scope/dependencies,
trailers/signatures, current deterministic CI/ci-required, applicable actual macOS
compilation/nonzero simulator tests, completed exact-head Codex review, finding
dispositions and structural/semantic drift. Under the adopted codex-only policy,
the coordinator MUST interpret actual native logs and record complete findings
and semantic evidence; a second reviewer runtime is not required. Earlier
integrations MUST retain their original independent/Codex proof. The new policy
MUST activate only after signed owner main adoption and target import as specified
in `docs/decisions/004-codex-only-review.md`. Timeout or unavailable Codex MUST
block integration, never waive the sole review gate. Head/target movement
MUST refresh evidence. Three automatic correction cycles per task PR are the
limit unless the owner authorizes more; blocked tasks MUST NOT weaken gates.
Escalations MUST include linked findings with severity/impact, evidence and
attempted fixes, a concrete proposed fix with validation and risks, and the
precise owner decision required. New findings do not restart the cycle budget.

Final handoff MUST include task/FR/acceptance coverage, tested revision, automated
and device instructions, migration/persistence/race evidence, accessibility and
performance results or pending checks, unresolved findings and actual Linear
status. Physical iPhone AND iPad acceptance MUST precede feature completion/freeze;
automated readiness MUST NOT be labelled completed.

The detailed delivery-process references are `docs/process/sdd-playbook.md` and
`docs/process/sdd-v2.md`.
The Linear task-projection rule remains the Fava pilot policy; the playbook
mirrors it without granting the tracker requirements authority.

## Governance

These principles and technical rules MUST govern all feature specifications, plans,
tasks, implementation, and review. Plans MUST check compliance before implementation.
This constitution MUST take precedence where the detailed playbook or templates conflict
with the project's rules, including the Linear pilot exception.

Amendments MUST record their rationale, impact on active work, and any required migration,
and MUST be reviewed and approved by the project owner before adoption. Semantic versioning
MUST apply: MAJOR for incompatible principle changes or removals, MINOR for added principles
or materially expanded obligations, and PATCH for clarifications without changed obligations.
The original ratification date MUST be preserved; the amendment date MUST reflect the
latest content change. Remove the temporary Sync Impact Report before committing.

Amendment 1.1.0 (proposed for owner review in the CI setup PR): clarifies the
staged Flow-Forward lifecycle and adds latest-commit Actions, verified API signing,
solo human review and physical-device acceptance obligations. Existing product
requirements and roadmap are unchanged. No historical features exist to migrate;
R1 activates native CI using `docs/process/ci-and-agent-verification.md`.

Amendment 2.0.0 (proposed for owner review): introduces two owner-started milestone
skills and replaces the blanket agent-merge prohibition with narrowly gated task
integration to registered milestone branches. This is MAJOR because merge
authority changes incompatibly. Human preparation/main approval, signed history,
mandatory automated/native tests and physical acceptance remain. Git remains
canonical; Linear is a verified projection. R3.5 retains its ID, exact directory,
approved scope/clarifications/acceptance. R1–R3 history and the fixed pilot exception
are not migrated or rewritten. Active work must reconstruct approvals and create
reviewed preparation before implementation; no existing draft gains approval from
this amendment. No R3.5 preparation occurs in the governance PR. Adoption requires
owner governance merge, separately reviewed ruleset/capability prerequisites, and
then owner-started preparation; policy changes are not retroactive authorization.
At the owner's request on 2026-10-14, this unadopted amendment also increases
the automatic correction budget from two to three rounds and requires reviewable
fix proposals at escalation to reduce owner interruptions. Counts remain durable
and monotonic; active work gets no reset, approval or weaker integration gate.
The new policy takes effect only upon owner adoption of this governance PR.

Amendment 3.0.0 (proposed for owner review in PR #36): removes the mandatory
additional independent reviewer after signed owner adoption and milestone-target
import of ADR-004. This is MAJOR because new task/checkpoint review evidence
changes incompatibly. Codex remains required; the coordinator takes responsibility
for actual scope/native interpretation and finding dispositions. Owner main/prep
approval, signatures, CI, device acceptance and source correction limits remain.
Historical integrations are verified using their original target policy; no
records, counters, requirements or task history are migrated. Same-head request
retries are bounded separately and cannot establish completion. This amendment
is not active merely because its proposal exists in a PR head.

**Version**: 3.0.0 | **Ratified**: 2026-10-05 | **Last Amended**: 2026-10-22

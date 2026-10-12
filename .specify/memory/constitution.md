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

Human owner review MUST precede merge; agents MUST NOT merge or enable auto-merge.
For this solo pilot no additional-person approval is required. In Codex Cloud,
Linear operations MUST use the pinned project-local CLI/skill, while local MCP
configuration remains supported. Linear connectivity MUST NOT gate CI.

The detailed delivery-process reference is `docs/process/sdd-playbook.md`.
The Linear task-projection rule above is an explicit pilot exception to the playbook's
normal convention of keeping tasks out of trackers.

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

**Version**: 1.1.0 | **Ratified**: 2026-10-05 | **Last Amended**: 2026-10-12

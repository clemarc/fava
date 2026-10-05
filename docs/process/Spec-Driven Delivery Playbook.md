# Spec-Driven Delivery Playbook

Project kickstart for Spec Kit, epic decomposition and work-tracker sync

Oct 5, 2026 · @Clément

## Purpose and scope

This playbook sets up a new project so every change traces to a requirement and every epic breaks into tasks that a person or an agent can pick up alone. It uses GitHub Spec Kit as the spec-driven development (SDD) framework, keeps the repository as the source of truth, and projects progress one way into whichever work tracker the project uses: GitHub Projects, Linear, Azure Boards or Jira.

Copy it into the new repo as `docs/process/sdd-playbook.md`, fill the placeholders marked `{like this}`, and record the project-specific choices in the constitution and in the decisions table at the end.

| Fixed by this playbook | Decided per project |
| --- | --- |
| Artifact ownership and repo layout | Stack, testing approach, security baseline |
| Lifecycle steps and their exit gates | Coding agent and model |
| ID scheme, commit trailers, audit walk | Work tracker and its process template |
| Epic decomposition and task format | Code host (GitHub, GitLab, Azure Repos) |
| CI enforcement and gate set | Spec Kit presets and extensions to install |
| One-way tracker sync contract | Whether to keep the central spec after the pilot |
| Extension governance and upgrade path | What qualifies for the lightweight path |

## Principles

Five rules carry the method. The first four are Spec Kit conventions; the fifth governs the work tracker. Record all five in the constitution so agents load them on every run.

1. **Flow-Forward.** A merged feature directory is frozen. A new or changed requirement opens a new directory that names the one it supersedes, so history reads as a dated change log.
2. **Living Spec.** Inside an active feature, `spec.md` is the only human-edited contract. `plan.md` and `tasks.md` are regenerated from it; rationale worth keeping goes in `decision-log.md` first.
3. **Spec of Specs.** An epic too large for one cycle starts as a `roadmap.md` of sub-features. Each sub-spec links back to its roadmap entry.
4. **Enforced gates.** Spec Kit's checks report but never block, so CI blocks. Every PR touching `specs/` or source runs the agreed gate set, and spec changes need approved review.
5. **Repo canonical, tracker as projection.** Epics start in the tracker. From refinement onward the repo owns requirements, and the tracker receives a read-only projection plus state driven by CI events.

The method costs more tokens and review time per feature than lighter loops such as OpenSpec. The lightweight path (section Quality gates) keeps that cost off small fixes.

## Artifact model and repository layout

Four artifacts are human-edited sources: the constitution, the roadmap, `spec.md` and the decision log. The central spec is reconciled from them, the tracker holds none of them, and everything else may be regenerated.

```text
.specify/
  memory/constitution.md        # project principles + this playbook's rules
  templates/overrides/          # project-local template tweaks
  presets/  extensions/         # installed from the org catalog
  extension-catalogs.yml        # points at the approved catalog
specs/
  _system/<domain>.md           # central current-state spec (reconciled)
  <epic-slug>/roadmap.md        # epic decomposition; header holds tracker epic ID
  NNN-<slug>/                   # one directory per feature or change
    spec.md                     # WHAT and WHY: user stories, FR-IDs
    decision-log.md             # rationale that must survive regeneration
    plan.md  research.md        # HOW: technical approach
    data-model.md  contracts/  quickstart.md
    checklists/                 # requirement quality checks
    tasks.md                    # T-IDs, [P] markers, file paths
.github/ or .ci/
  sync/tracker-sync.{py|ts}     # one-way repo-to-tracker projection
  checks/                       # trailer, ID and path-rule scripts
CODEOWNERS
```

| Artifact | Role | Type | Edited by |
| --- | --- | --- | --- |
| `constitution.md` | Principles, quality gates, these rules, pinned versions | Source | Tech lead, via PR |
| `roadmap.md` | Epic split into sub-features with scope boundaries | Source | Engineer, scope agreed with product owner |
| `spec.md` | Requirements contract for one feature | Source | Engineer, reviewed by product owner |
| `decision-log.md` | Implementation decisions and their reasons | Source, append-only | Engineer or agent, reviewed in PR |
| `plan.md`, `research.md`, `data-model.md`, `contracts/` | Technical design derived from the spec | Derived | Agent, reviewed by engineer |
| `tasks.md` | Executable task list | Derived | Agent; engineer ticks and confirms `[P]` |
| `_system/<domain>.md` | Requirements in force today | Reconciled | Agent, reviewed by engineer |
| Tracker items | Read-only projection for stakeholders | Projection | Sync job only |

`decision-log.md` is an addition to Spec Kit core. Without it, regenerating `plan.md` or `tasks.md` discards the reasons behind implementation choices.

## Delivery lifecycle

Work enters from the tracker as an epic and leaves as merged code plus an updated central spec. If breakdown finds scope the epic never agreed to, work returns to step 1 and the spec changes before any task does.

&#91;embedded content: delivery lifecycle · 6 steps, 1 loop, tracker as projection\]

The tracker sends one thing into the repo, the epic ID; everything after flows back to it as projection from steps 2 and 5.

| Step | Owner | Spec Kit commands and artifacts | Exit gate |
| --- | --- | --- | --- |
| 1. Take the epic | Engineer, with product owner | Roadmap pass → `roadmap.md`; `/speckit.specify` and `/speckit.clarify` per sub-feature → `spec.md` | Scope agreed; roadmap and spec PRs merged with product owner and tech lead approval |
| 2. Specs and work breakdown | Engineer | `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.checklist` | Analyze has no critical findings; breakdown merged; tracker shows Features and Stories |
| 3. Implement a task | Engineer, agent-assisted in the IDE | Scoped `/speckit.implement` run; decision recorded in `decision-log.md` | Task ticked in `tasks.md`; commits carry trailers |
| 4. Pre-PR gates | CI | Deterministic checks plus headless `/speckit.analyze` | Agreed gate set green |
| 5. Human review and merge | Peer reviewer per CODEOWNERS | PR reviewed against `spec.md` and the task's FR-IDs | Required approvals; tracker state updated from the merge event |
| 6. Reconcile specs | Engineer, agent-assisted | Merged feature folded into `specs/_system/` | Reconciliation PR merged; every FR present or marked superseded |

## Work tracker sync

The tracker originates epics and shows progress; it never originates or edits requirements. Sync runs one way, repo to tracker, except for the epic itself, whose ID is copied into `roadmap.md`.

### Contract every adapter implements

- **Keyed, not ID-mapped.** Each synced item carries a repo key such as `012-payment-methods/US1`. The sync finds items by that key, so the repo never stores tracker IDs below the epic.
- **Idempotent upsert.** Running the sync twice changes nothing. Title, description and acceptance criteria are overwritten on every run; the description opens with a link to the source file at the merge commit.
- **One writer for state.** Either the sync job or the tool's native PR automation moves an item's state, never both. The default here is the sync job, driven by the CI events below; native integrations are kept for PR links only.
- **Service identity in CI.** The sync never runs from a developer's machine, so every tracker change traces to a pipeline run. Each run uploads a sync report as a build artifact and supports `--dry-run`.
- **Drift is reported, not merged.** Where the tool cannot lock fields, the sync overwrites edits and comments on the item that changes go through a spec PR.

### Hierarchy mapping

Tasks stay out of every tracker on purpose: `tasks.md` is regenerated while a feature is active, and mirroring that churn floods the board.

| Repo level | Repo source | GitHub Projects | Linear | Azure Boards | Jira |
| --- | --- | --- | --- | --- | --- |
| Epic | ID in `roadmap.md` header; created in the tracker by the product owner | Issue with type Epic, added to the project | Project (Initiative if the epic spans several projects) | Epic | Item at the level above Epic (needs a custom hierarchy level), else Epic |
| Feature | Roadmap entry (R2) and its feature directory | Sub-issue of the epic, type Feature | Parent issue in the project | Feature | Epic, or Story with a feature label when Epic is the top level |
| User story | US1 in `spec.md` | Sub-issue of the feature | Sub-issue of the feature issue | User Story | Story |
| Task | `tasks.md` | Not synced | Not synced | Not synced | Not synced |
| Repo key stored in |  | Project text field `Repo key` plus a body marker | Description marker plus an attachment linking the spec file (no custom fields) | Custom field | Custom text field |
| Field locking |  | None; overwrite and report drift | None; overwrite and report drift | Field rules by area path or group | Field and workflow permissions; overwrite as fallback |
| Native PR automation to disable or keep for links only |  | Built-in project workflows, closing keywords | Team PR and commit automation, closing magic words | `AB#` links and state transitions | Development panel and automation rules |

### State from CI events

| CI event | Tracker change | GitHub Projects Status | Linear status | Azure Boards (Agile) | Jira |
| --- | --- | --- | --- | --- | --- |
| Roadmap or spec PR for the epic opened | Epic starts | In progress | Started | Epic → Active | In Progress |
| Breakdown merged to main | Features and stories created | Todo | Backlog or Todo | New | To Do |
| First PR opened citing a task of the story | Story starts, PR linked | In progress | In Progress | Active | In Progress |
| PR merged that ticks the story's last task | Story done | Done (issue closed) | Done | Resolved | Done |
| All stories of a feature done | Feature done | Done | Done | Resolved | Done |
| Release pipeline deploys the change | Story and feature released | Released (custom option) | Released (custom status) | Closed | Released (custom status) |

State names follow each tool's default workflow; rename them in `.specify/tracker.yml` to match the project's process template.

### Implementation choice

Write one small sync script per project against the tracker's API (GitHub GraphQL for Projects, Linear GraphQL, Azure DevOps REST, Jira REST) behind a shared adapter interface: `upsert(key, fields, parentKey)`, `setState(key, state)`, `link(key, url)`. Evaluate a community Spec Kit extension for the chosen tracker first, subject to the catalog rules in Extensibility and governance.

## Traceability model

Every line of code traces to a requirement through a chain of stable IDs, each stored in plain text in the repository.

| ID | Format | Lives in | Rule |
| --- | --- | --- | --- |
| Tracker epic | Tool's native ID (`#1234`, `ENG-42`, `AB#1234`, `PROJ-7`) | Tracker; copied into the roadmap header | The only tracker ID the repo stores |
| Roadmap entry | R1, R2 … | `roadmap.md` | Immutable once merged; superseded entries stay, marked |
| Feature | `NNN-slug` | `specs/` directory name | Unique per repo; collision rule in Epic decomposition |
| User story | US1, US2 … | `spec.md`; the tracker story carries `NNN-slug/US1` | Scoped to its feature |
| Requirement | FR-001 … | `spec.md`, then the central spec | Never renumbered or reused |
| Task | T001 … | `tasks.md` | Each task cites at least one FR-ID |
| Decision | DEC-001 … | `decision-log.md` | Append-only; a reversal is a new entry citing the old one |

**Commit convention.** Every commit to source paths carries Git trailers:

```text
feat: add default payment method endpoint

Spec: specs/012-payment-methods
Task: T014
Implements: FR-003
```

**Audit walk.** From any line of code: `git blame` → commit → `Task:` trailer → `tasks.md` → FR-ID in `spec.md` → roadmap entry → tracker epic. The PR on that commit holds the approvals and CI evidence, and the sync links it from the tracker story. For a changed requirement, the superseded directory shows the old contract, the new directory shows who changed it and when, and the central spec shows what is in force today.

A CI check rejects commits to source paths without `Spec:` and `Task:` trailers, so the chain cannot silently break.

## Epic decomposition

An epic becomes a roadmap of independently specifiable sub-features; each then runs the normal lifecycle as its own feature directory.

**When to decompose.** Spec Kit's guidance escalates by overhead: limit tasks per implement run, then delegate to sub-agents, then combine both. Decompose only when one phase still won't fit one run. Work already framed as an epic across several people or sprints is decomposed up front.

**Roadmap pass.**

1. Take an epic from the tracker once its ready criteria are met; state it in one or two sentences and record its tracker ID in the roadmap header.
2. Have the agent propose slices that each deliver something demonstrable and testable on its own.
3. Write one line of intent and an explicit scope boundary per slice: what is in, what is deferred to a sibling.
4. Order by dependency; slices with no dependency between them run in parallel.
5. Agree the slicing with the product owner in the roadmap PR, and merge it before any sub-spec is written.

**Rules.**

- Each sub-spec's Input line names its parent: `Parent roadmap: specs/{epic-slug}/roadmap.md → entry R2`.
- Scope changes update the roadmap first, then the affected sub-specs.
- A slice still too big gets its own roadmap one level down; go no deeper than the context problem requires.
- Number features per epic or by timestamp (`{epic}-{NN}-slug` or `20261005-1432-slug`), not Spec Kit's global sequence, so engineers branching at the same time never collide. Enforce it with a CI check or a branch-convention extension.
- One git worktree per engineer, so each has isolated active-feature state.

**Parallel slicing by component.** In a monorepo with several building blocks, slice the epic one component per entry so one engineer per component works in parallel. Where a slice needs another component, its spec records the expected interface in the Assumptions section and builds against a stub. A final integration slice replaces the stubs and carries end-user acceptance.

| ID | Sub-feature | Depends on |
| --- | --- | --- |
| R1 | {Backend service} | none |
| R2 | {Second service} | none |
| R3 | {Frontend} | none |
| R4 | Integration: replace stubs, end-to-end acceptance | R1–R3 |

In R1–R3, user stories are written from the consuming component's point of view, for example "as the frontend, I can fetch a customer's open cases and get a typed result". End-user stories are accepted in R4. Once interfaces stop changing between epics, move to a contracts-first slice (R0) that every component depends on, with shared contracts changed only through PRs approved by producer and consumer.

## Task design and execution

A task is ready to hand off when someone holding only that task, the spec and the plan can finish and verify it.

**Structure of `tasks.md`** (generated by `/speckit.tasks`):

1. Setup: shared project initialization
2. Foundational: blocking prerequisites; no user story starts until this phase is done
3. One phase per user story, in priority order (P1, P2 …), each with its goal, independent test criteria and a checkpoint
4. Polish: cross-cutting work

**Task line format.** Spec Kit core is `- [ ] T014 [P] [US1] <action> in <exact file path>`. This playbook appends the requirement reference:

```text
- [ ] T014 [P] [US1] Add POST /payment-methods/default in src/billing/api/default.ts (FR-003)
```

**Definition of ready for a task.**

- Cites at least one FR-ID, and one US label outside Setup and Foundational.
- Names exact file paths; `[P]` only when it touches files no other open task touches and has no unmet dependency.
- Has a test task before it when the constitution requires TDD. Tests are optional in Spec Kit by default; set the constitution to make them mandatory.
- Fits one agent run: if it needs more than the task, its user story and plan excerpts, split it.

**Running implementation.** Never run `/speckit.implement` across a whole feature in one go; context exhaustion makes agents lose the plan mid-run.

| Situation | Invocation |
| --- | --- |
| Default | `/speckit.implement` scoped to one task ID or a short run of IDs |
| Phase at a time | `/speckit.implement` scoped to one phase, then review before the next |
| Parallel tasks, agent supports sub-agents | `/speckit.implement` delegating `[P]` tasks to sub-agents |
| Parallel people or features | One git worktree per feature, one engineer per worktree |
| Cloud agent authoring PRs | Off until the entry criteria in Quality gates hold |

Completed tasks are ticked `[X]` in `tasks.md`, so the next run resumes where the last stopped. The `[P]` marker is the agent's inference; an engineer confirms it before handing tasks out in parallel.

## Quality gates and CI

CI is the enforcer because Spec Kit's checks only report. The gate set is agreed in the constitution before the first feature; each gate starts as a PR checklist item and moves into CI once automated.

| Check | Type | Runs on | Blocks merge |
| --- | --- | --- | --- |
| Tests | Deterministic | Every PR | Yes |
| Human review: CODEOWNERS approval | Branch protection | Every PR | Yes |
| Commit trailers present (`Spec:`, `Task:`) on source paths | Deterministic script | Every PR | Yes |
| Frozen directories untouched: merged `specs/NNN-*/` edited only by supersession | Deterministic path rule | Every PR | Yes |
| ID cross-reference: every task's FR-IDs exist in `spec.md`; every FR has a task | Deterministic script | PRs touching `specs/` | Yes |
| Roadmap links resolve both ways (sub-spec → entry, entry → directory) | Deterministic script | PRs touching `roadmap.md` or a sub-spec | Yes |
| `/speckit.analyze` consistency report | Agent, headless | PRs touching `specs/` | Yes on critical findings |
| Feature completion check against `spec.md` | Agent | Before the final PR of a feature | Yes if it finds unmet FRs |
| Tracker sync succeeded for the merge | Pipeline status | Merges touching `specs/` | No; alerts the tech lead |
| Reconciliation complete: every merged FR in `_system/` or marked superseded | Deterministic script | Reconciliation PRs | Yes |

Agent checks are non-deterministic, so they are an extra gate, never the only one. Pin the agent model and prompt in CI, keep the analyze report as a build artifact for audit evidence, and log any human override of a finding with its reason in the PR.

**Lightweight path.** A fix that changes no requirement skips `plan.md` and `tasks.md` but still opens a PR whose commits carry `Spec:` and `Implements:` trailers pointing at an existing FR. The constitution states what qualifies: {a size threshold, a change type list, or tech lead discretion}.

**Review regime.** Every PR is engineer-authored. Engineers may use an agent in the IDE, but the engineer is the author and is accountable for the whole diff. Spec PRs need product owner and tech lead approval.

Cloud-agent-authored PRs are a later stage, enabled only when all three hold: every gate above is automated, pilot data shows low rework on agent-assisted tasks, and the client explicitly agrees. Agent PRs then need the assigning engineer plus one other reviewer, no auto-merge, and review against the task's FR-IDs rather than the tests alone.

## Spec reconciliation

Keep a central current-state spec at requirement level, produced by reconciliation after each merge rather than by hand, and confirm or drop it with pilot evidence.

History plus code show what was built, when and by whom. They fall short on four questions: intent (a bug and a requirement look the same in code), audit ("what must the system do today about refunds?" means replaying every directory and its supersessions), agent context (a new epic needs the current contract, and loading dozens of historical directories exhausts the context window) and impact analysis (step 1 needs to see which existing requirements a new epic changes).

| Option | What it is | Cost | Answers the four questions |
| --- | --- | --- | --- |
| A. No central spec | Feature directories plus code | None | Only by replaying history |
| B. Hand-maintained central spec | Engineers edit a system spec alongside features | High; drifts under pressure | While it is kept current |
| C. Reconciled current-state spec | Agent folds each merged feature into `_system/`, engineer reviews | One small PR per feature | Yes |

**How option C works.**

- One file per domain at `specs/_system/{domain}.md`, listing the requirements in force.
- Each requirement keeps its original FR-ID and cites its source, for example `FR-003 (012-payment-methods)`. A superseded requirement is replaced; its history stays in the frozen feature directory.
- Step 6 opens a reconciliation PR after merge; CI checks that every FR in merged features appears in the central spec or is marked superseded.
- Only requirements and acceptance scenarios go in. Plans, tasks and design detail stay in feature directories.

Feature directories are the immutable change log; the central spec is the current contract. Community extensions to evaluate for the fold step: Archive (archives merged features into project memory) and Canon (baseline-driven and spec-drift workflows).

## Extensibility and governance

Conventions ship as one versioned org preset plus a short list of approved extensions, so no project edits Spec Kit core. Spec Kit resolves templates top-down at runtime and uses the first match.

| Priority | Layer | Location | Used for |
| --- | --- | --- | --- |
| 1 | Project-local overrides | `.specify/templates/overrides/` | One-off client tweaks |
| 2 | Presets | `.specify/presets/templates/` | The org preset carrying this playbook |
| 3 | Extensions | `.specify/extensions/templates/` | New commands: tracker sync, roadmap, archive |
| 4 | Core | `.specify/templates/` | Spec Kit defaults |

Extension and preset commands are written into the agent's command directory at install time; when two provide the same command, the higher priority wins.

- Host an org catalog and point projects at it through `.specify/extension-catalogs.yml`, with the community catalog set to discovery only (`install_allowed: false`).
- Review extension source before approving it; the community catalog's maintainers check entries for format, not code.
- Record the Spec Kit version and org preset version in the constitution so an audit can reconstruct the rules in force.
- Upgrade Spec Kit on a branch through its upgrade workflow, re-run `/speckit.analyze` on active features, then merge.

## Roles and responsibilities

| Activity | Product owner | Tech lead | Engineer | Agent |
| --- | --- | --- | --- | --- |
| Epic in the tracker, ready criteria | Owns | Consulted | Informed | none |
| 1. Roadmap pass and specs | Agrees scope | Approves spec PR | Owns | Drafts slices and specs |
| 2. Plan, tasks, analyze | Informed | Approves breakdown | Owns; confirms `[P]` | Generates artifacts |
| 3. Implement tasks, decision log | Informed | Consulted | Owns every diff | Assists in the IDE |
| 4. Pre-PR gates | none | Owns the agreed gate set | Fixes findings | Runs headless analyze |
| 5. Review and merge | Accepts behaviour on request | Reviews | Authors the PR | none |
| 6. Reconcile central spec | Informed | Consulted | Owns the reconciliation PR | Drafts the fold |
| Constitution, org preset, extensions | Consulted | Owns | Contributes | none |
| Tracker sync job | Informed | Owns | Maintains | none |

## Kickstart checklist

Pilot on one real epic of 3 to 5 sub-features before any wider rollout, and let the pilot's evidence confirm or revise the conventions.

### Phase 1: foundations

- [ ] Create the repo and run `specify init` with the chosen agent; pin the Spec Kit version
- [ ] Point `.specify/extension-catalogs.yml` at the org catalog; install the org preset
- [ ] Write `constitution.md` from the template below; record Spec Kit and preset versions
- [ ] Add CODEOWNERS by component path and branch protection on the default branch
- [ ] Add CI checks: tests, commit trailers, frozen-directory path rule, ID cross-reference, roadmap links
- [ ] Add headless `/speckit.analyze` to CI with pinned model and prompt; store the report as an artifact
- [ ] Configure the tracker: hierarchy levels, `Repo key` field (or marker convention), state names, field locks where supported
- [ ] Create the CI service identity for the tracker with the narrowest scope that allows item writes
- [ ] Write `.specify/tracker.yml` and the sync script; disable native state automation for synced items
- [ ] Exit: a sample feature runs all six lifecycle steps and appears correctly in the tracker

### Phase 2: pilot

- [ ] Pick one tracker epic of 3 to 5 sub-features; run the roadmap pass and merge `roadmap.md`
- [ ] Run every sub-feature through steps 1 to 6, including reconciliation
- [ ] Log token spend, review time per PR and rework rate on agent-assisted tasks
- [ ] Exit: a mock audit traces 10 random lines of code to their requirement and tracker epic

### Phase 3: review

- [ ] Compare pilot measures against expectations; decide on the central spec and the lightweight path threshold
- [ ] Exit: decide to roll out, adjust conventions, or stop; record it as an ADR

### Phase 4: rollout

- [ ] Onboard remaining engineers; automate any gate still on the PR checklist
- [ ] Exit: all new work runs on the process; the sync report is green for two consecutive weeks

## Templates

Copy these into the org preset so every project starts from the same files.

**`constitution.md` additions** (append to the section Spec Kit generates):

```markdown
## Delivery conventions
Versions: Spec Kit {x.y.z}, org preset {x.y.z}, agent {name + model}

1. Flow-Forward: merged specs/NNN-*/ directories are frozen; changes open a new directory with `Supersedes: NNN-slug`.
2. Living Spec: spec.md is the only human-edited contract in an active feature; record rationale in decision-log.md before regenerating plan.md or tasks.md.
3. Spec of Specs: epics start with specs/{epic-slug}/roadmap.md; every sub-spec names its roadmap entry.
4. Enforced gates: the CI gate set in docs/process/sdd-playbook.md blocks merge.
5. The tracker is a read-only projection; requirement changes go through spec PRs.

## Testing
Tests are mandatory; every user-story phase starts with a failing test task.

## Lightweight path
Qualifies when: {threshold or change types}. Still requires Spec: and Implements: trailers.

## Component rules
### {component}: {language, framework, lint, test runner}
```

**`roadmap.md`**

```markdown
# Roadmap: {epic title}
Tracker epic: {native ID + link}
Intent: {one or two sentences}
Status: draft | agreed | superseded

| ID | Sub-feature | Intent | In scope | Deferred to | Depends on | Directory |
|----|-------------|--------|----------|-------------|------------|-----------|
| R1 | ... | ... | ... | R2 | none | specs/{NNN-slug} |
```

**`spec.md` header**

```markdown
# Feature: {title}
Input: Parent roadmap: specs/{epic-slug}/roadmap.md → entry R{n}
Component: {component}
Supersedes: {NNN-slug or none}
```

**`decision-log.md` entry**

```markdown
## DEC-{NNN}: {decision in one line}
Date: {YYYY-MM-DD} · Author: {name} · Tasks: T{nnn} · Requirements: FR-{nnn}
Context: {what forced the choice}
Decision: {what we chose}
Alternatives: {what we rejected and why}
Supersedes: {DEC-id or none}
```

**PR template**

```markdown
Spec: specs/{NNN-slug}
Tasks: T{nnn}, T{nnn}
Implements: FR-{nnn}

- [ ] Tasks ticked in tasks.md
- [ ] New decisions recorded in decision-log.md
- [ ] Analyze report attached; overrides justified below
```

**`.specify/tracker.yml`**

```yaml
tool: github-projects   # github-projects | linear | azure-boards | jira
project: "{org}/{project number | Linear team key | ADO project | Jira key}"
key_field: "Repo key"   # custom field name, or "marker" for description markers
levels:
  epic: { type: "Epic" }
  feature: { type: "Feature" }
  story: { type: "Story" }
states:
  todo: "Todo"
  in_progress: "In progress"
  done: "Done"
  released: "Released"
native_state_automation: disabled
identity: "{CI service identity name}"
```

## Decisions each project records

Record each answer as an ADR or in the constitution before Phase 1 exits.

| Decision | Options | Default in this playbook |
| --- | --- | --- |
| Code host | GitHub, GitLab, Azure Repos | Decides how PRs link to tracker items |
| Work tracker and process template | GitHub Projects, Linear, Azure Boards (Agile, Scrum, CMMI), Jira | State names set in `tracker.yml` |
| Who drives tracker state | Sync job from CI events, or native PR automation | Sync job; native integration for links only |
| Sync implementation | Own script on the tracker API, or a community extension | Own script until an extension passes source review |
| Coding agent and CI analyze model | Any Spec Kit-supported agent | Pinned in the constitution; API budget owner named |
| Feature numbering | Per epic, or timestamp | Per epic |
| Central spec | Keep option C, or history plus code only | Keep through the pilot, then decide |
| Lightweight path threshold | Size, change type, tech lead discretion | Change types listed in the constitution |
| Tasks in the tracker | Never, or summary per story for capacity planning | Never |
| Audit evidence | Git history, or a signed trace index per release | Git history plus analyze artifacts |

**Risks to watch.** Ceremony on small changes pushes people around the process; the lightweight path is the answer. Stakeholders editing synced items creates two versions of scope; field locks and overwrite-with-comment close it. Agent gates that flip between runs erode trust; deterministic scripts carry the blocking load. Spec Kit changes fast; the pinned version and branch upgrade keep the preset and CI from breaking.

## Sources

- [GitHub Spec Kit repository and docs](https://github.com/github/spec-kit): Spec Persistence Models, Spec of Specs, Handling Complex Features, Extensions reference, Templates
- [Linear: GitHub integration](https://linear.app/docs/github): magic words, per-team PR and commit automation
- [GitHub Docs: best practices for Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects): sub-issues, issue types, custom fields, built-in workflows
- Derived from ADR-001 (Adopt GitHub Spec Kit) and TDR-001 (Spec Kit methodology), 23 Sep 2026

---
description: "Create a draft SDD epic roadmap from a Linear project"
---

# Create Epic Roadmap

## Goal

Create the canonical `roadmap.md` for one epic using its existing Linear
Project as input.

The Linear Project originates the epic. From this command onward, detailed
scope is canonical in the repository.

This command creates a DRAFT roadmap only.

It MUST NOT:

- create feature specs
- create implementation plans
- create tasks
- create or modify Linear milestones or issues
- implement application code
- commit or push changes

## User Input

$ARGUMENTS

The input MUST identify exactly one existing Linear Project by URL or stable
project ID.

A project title MAY be supplied, but if more than one match exists, stop and
ask the user to provide the URL or stable ID.

## Required Project Context

Before doing any work, read:

1. `.specify/memory/constitution.md`
2. `docs/process/sdd-playbook.md`

The constitution is authoritative for project governance.

The playbook defines:

- roadmap decomposition rules
- roadmap artifact format
- scope-boundary expectations
- dependency rules
- feature-directory conventions

Use the project-configured Linear MCP server for Linear access.

Linear access during this command is READ-ONLY.

## Preconditions

Verify:

1. This is an initialized Spec Kit repository.
2. `.specify/memory/constitution.md` exists.
3. `docs/process/sdd-playbook.md` exists.
4. Git is available.
5. The Linear MCP server is available.
6. The working tree has no unrelated uncommitted changes.

If the working tree is dirty because of unrelated changes, STOP and report
the files preventing roadmap creation.

Do not stash, discard, rewrite, or commit unrelated user changes.

## Phase 1 — Resolve Epic

Using Linear MCP, retrieve the Linear Project identified by `$ARGUMENTS`.

Capture:

- stable project UUID or API-addressable identifier
- human-readable project identifier, if one exists
- exact project name
- project URL
- team
- project status
- summary
- description
- explicitly stated in-scope items
- explicitly stated deferred/out-of-scope items

Do not modify Linear.

If the project cannot be resolved uniquely, STOP.

When multiple identifiers exist, prefer the stable API-addressable project
UUID as the canonical tracker identifier in `roadmap.md`.

Human-readable identifiers may also be recorded as supplementary metadata.

## Phase 2 — Derive Epic Slug

Derive a lowercase kebab-case slug from the Linear Project name.

Example:

`HealthKit Run Library`

becomes:

`healthkit-run-library`

The canonical roadmap path is:

`specs/<epic-slug>/roadmap.md`

If that roadmap already exists:

- if its status is `draft`, update the existing draft rather than creating a
  second roadmap;
- if its status is `agreed` or `superseded`, STOP and report that the roadmap
  may not be silently rewritten.

Respect the Flow-Forward principle in the project constitution.

## Phase 3 — Create Roadmap Branch

If currently on the default branch, create:

`specs/<epic-slug>-roadmap`

If already on a non-default branch, continue on the current branch and report
the branch name.

Never overwrite or delete an existing branch.

Do not commit or push.

## Phase 4 — Propose Slices

Decompose the epic into independently specifiable product or user-capability
slices.

Prefer the SMALLEST number of coherent slices that makes each slice:

- independently specifiable;
- demonstrable or objectively verifiable;
- small enough for one Spec Kit feature lifecycle;
- clearly bounded from its siblings.

Three to five slices is a useful starting range, not a target that must be
filled.

Do not create an additional slice merely to represent infrastructure,
architecture, project setup, or a technical component.

### Slice design rules

Each slice MUST:

- describe a capability or observable outcome, not an implementation activity;
- have one clear intent;
- have an explicit in-scope boundary;
- state what is deliberately deferred;
- identify dependencies on other roadmap entries;
- avoid mixing unrelated product capabilities;
- avoid defining implementation tasks;
- avoid prescribing temporary diagnostics or intermediate implementation UI.

Prefer vertical/product slices over infrastructure-only slices.

A foundational slice is allowed only when it delivers a demonstrable,
testable capability required by later slices.

For example:

Prefer:

`Authorize HealthKit access`

over:

`Create app foundation and configure HealthKit`

Prefer:

`Load running workouts`

over:

`Build HealthKit repository layer`

### Avoid implementation-specific roadmap requirements

The roadmap SHOULD describe WHAT becomes possible, not HOW verification is
implemented.

Do not prescribe things such as:

- temporary counters;
- debug screens;
- exact file structures;
- exact UI widgets;
- storage mechanisms;
- architectural layers;
- implementation libraries;
- exact workout fields;
- caching strategy;
- refresh mechanics;

unless the Linear epic explicitly makes one of those part of the product
requirement.

For example:

Prefer:

`Provide a user-visible, verifiable indication that running workouts loaded`

over:

`Display a loaded-run count`

The later feature specification decides the exact acceptance experience.

### Consolidate artificial slices

If an initial decomposition produces an infrastructure-only slice followed
immediately by the user capability it exists to enable, consider combining
them.

Do not preserve an initial proposed decomposition merely because it was
suggested by the user or appeared in prior planning.

The purpose of the roadmap pass is to improve the decomposition.

Order slices by dependency.

Use IDs:

`R1`, `R2`, `R3`, ...

Once merged, roadmap IDs are immutable.

## Phase 5 — Determine Feature Directories

Use per-epic numbering:

`specs/<epic-slug>-01-<feature-slug>`
`specs/<epic-slug>-02-<feature-slug>`
...

Directory slugs SHOULD describe the capability rather than an implementation
component.

Do not create those directories yet.

Only record the intended directory in the roadmap.

## Phase 6 — Identify Open Questions

During decomposition, capture decisions that must be made later but are NOT
required to agree the roadmap boundary.

Examples include:

- exact data fields;
- ordering;
- refresh behavior;
- history limits;
- device-specific behavior;
- detailed authorization messaging;
- caching or persistence policy.

Record these under:

`## Open questions for feature specs`

Each question SHOULD indicate the roadmap entry that must resolve it where
that is obvious.

Do not resolve these questions unless the Linear epic or constitution already
contains the answer.

Do not hide unresolved scope decisions inside prose such as
"decomposition assumptions."

If an unresolved question would materially change the slice boundaries,
STOP and surface it for human roadmap review instead of guessing.

## Phase 7 — Write roadmap.md

Create the epic directory if needed:

`specs/<epic-slug>/`

Write:

`specs/<epic-slug>/roadmap.md`

using this structure:

# Roadmap: <Linear Project name>

Tracker epic: <stable Linear project UUID> · <Linear project URL>

Intent: <one or two sentence user/product outcome>

Status: draft

| ID | Sub-feature | Intent | In scope | Deferred to | Depends on | Directory |
|----|-------------|--------|----------|-------------|------------|-----------|
| R1 | ... | ... | ... | ... | none | specs/... |

## Epic boundaries

### In scope

- ...

### Deferred

- ...

## Decomposition rationale

Briefly explain any non-obvious decomposition decisions.

Focus on why slices were combined or separated.

Do not repeat the roadmap table.

## Open questions for feature specs

- R1: ...
- R2: ...

Omit this section if there are genuinely no unresolved questions.

## Source

- Linear project: <URL>
- Stable project UUID: <UUID>
- Human-readable project identifier: <identifier, if available>
- Team: <team>
- Project status at generation: <status>
- Project summary: <summary>
- Generated from project state on: <YYYY-MM-DD>

Do not copy the full Linear project description into the Source section unless
it contains information that is not already represented elsewhere in the
roadmap.

Do not include:

- user stories
- FR identifiers
- implementation design
- file-level implementation tasks
- architecture not required to define slice boundaries
- temporary verification

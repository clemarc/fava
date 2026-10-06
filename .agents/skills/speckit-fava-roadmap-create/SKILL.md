---
name: speckit-fava-roadmap-create
description: Create a draft SDD epic roadmap from a Linear project
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: Fava
  source: fava-roadmap:commands/create.md
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
ask the user to provide the URL or ID.

## Required Project Context

Before doing any work, read:

1. `.specify/memory/constitution.md`
2. `docs/process/sdd-playbook.md`

The constitution is authoritative for project governance.

The playbook defines:

- roadmap decomposition rules
- the roadmap artifact format
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
6. The working tree has no uncommitted changes.

If the working tree is dirty, STOP and report the files preventing roadmap
creation.

Do not stash, discard, or commit unrelated user changes.

## Phase 1 — Resolve Epic

Using Linear MCP, retrieve the Linear Project identified by `$ARGUMENTS`.

Capture:

- stable project ID
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

Decompose the epic into independently specifiable sub-features.

Prefer 3–5 slices unless the epic clearly requires another number.

Each slice MUST:

- deliver something demonstrable or objectively verifiable;
- have one clear intent;
- have an explicit in-scope boundary;
- state what is deliberately deferred;
- identify dependencies on other roadmap entries;
- be small enough to run through one Spec Kit feature lifecycle;
- avoid mixing unrelated product capabilities;
- avoid defining implementation tasks.

Prefer vertical/product slices over infrastructure-only slices.

A foundational slice is allowed only when it produces a demonstrable,
testable capability required by later slices.

Do not create a slice merely because a technical component exists.

Order slices by dependency.

Use IDs:

`R1`, `R2`, `R3`, ...

Once merged, roadmap IDs are immutable.

## Phase 5 — Determine Feature Directories

Use per-epic numbering:

`specs/<epic-slug>-01-<feature-slug>`
`specs/<epic-slug>-02-<feature-slug>`
...

Do not create those directories yet.

Only record the intended directory in the roadmap.

## Phase 6 — Write roadmap.md

Create the epic directory if needed:

`specs/<epic-slug>/`

Write:

`specs/<epic-slug>/roadmap.md`

using this structure:

# Roadmap: <Linear Project name>

Tracker epic: <Linear project ID> · <Linear project URL>

Intent: <one or two sentence outcome>

Status: draft

| ID | Sub-feature | Intent | In scope | Deferred to | Depends on | Directory |
|----|-------------|--------|----------|-------------|------------|-----------|
| R1 | ... | ... | ... | ... | none | specs/... |

## Epic boundaries

### In scope

- ...

### Deferred

- ...

## Source

- Linear project: <URL>
- Team: <team>
- Generated from project state on: <YYYY-MM-DD>

Do not include:

- user stories
- FR identifiers
- implementation design
- file-level implementation tasks
- architecture not required to define the slice boundaries

Those belong to later Spec Kit phases.

## Phase 7 — Validate

Before finishing, verify:

- every roadmap entry has a unique R-ID;
- every entry has an intent;
- every entry has an explicit scope boundary;
- every entry identifies what is deferred;
- all dependencies reference valid roadmap IDs;
- dependency ordering contains no cycle;
- every entry has an intended feature directory;
- no feature directory was actually created;
- no `spec.md`, `plan.md`, or `tasks.md` was generated;
- Linear was not modified.

If any validation fails, fix the draft before reporting completion.

## Completion Report

Report:

- Linear project name and ID
- roadmap path
- git branch
- number of proposed slices
- slice IDs and names
- important assumptions made during decomposition

State clearly:

`ROADMAP STATUS: DRAFT — human review required before feature specification.`

Do not commit, push, create Linear milestones, or start specification.
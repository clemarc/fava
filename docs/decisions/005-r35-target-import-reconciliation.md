# DEC-005: Reconcile the R3.5 T005 target import

Status: proposed for owner merge. Owner authorization was given on 2026-10-24
after the integration assessor identified the conflict below.

## Scope

The milestone resolver normally requires a PR headed by `milestone/r3.5` to
target `main`. That remains the policy.

PR [#41](https://github.com/clemarc/fava/pull/41) was instead a one-time,
automatic target import into the already-open T005 task branch after checkpoint
C015 moved the milestone target. Its immutable identity is:

- head: `milestone/r3.5` at `195631baf6deb20fcfce595fb43287cbde6a6206`;
- base: `task/r3.5/t005`;
- merge: `611f56ebac503c206c8c310161a6f3d6bcbceb36`.

The merge has the task branch as first parent and the C015 milestone target as
second parent. Its tree is Git's automatic merge tree; it contains no conflict
resolution or task-scope edit.

## Decision

The resolver may reconcile only this closed, merged PR with every identifier
above unchanged. The exception is represented as an exact immutable record in
`tools/sdd/milestone.py` and has regression coverage for every identity field.
It does not permit a future reverse-target PR, a different task, another
milestone, an open PR, or a changed merge/head/base.

## Consequences

This restores structural assessment of the already-published T005 PR without
rewriting PR #41 or weakening normal destination checks. It does not authorize
T005 integration by itself: current CI, signed history, Codex completion,
coordinator evidence, structural assessment, and the guarded task merge remain
required. This governance change targets `main` and requires an owner merge
before it can be imported into `milestone/r3.5`.

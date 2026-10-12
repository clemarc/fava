# R1–R3 single-PR delivery pilot

The owner explicitly authorized one continuous R1–R3 implementation task and one
PR against main, with separate milestone plans, tasks, decisions and verified CI
checkpoints. No automatic merge, requirement changes, R4 work or quality-gate
exemption is authorized. This is a delivery exception, not a constitution or
playbook amendment.

Approved specifications: PR #3, merged at
`d6a2f4be72f51f5f734b4c22de362fae07341572`.

For these three exact directories only, the deterministic lifecycle validator
accepts a preceding planning commit on the implementation branch instead of a
separate merged planning PR. The specification must already exist in the PR base;
both plan.md and tasks.md must exist in the implementation commit's parent. Each
implementation commit must carry `Delivery-Pilot: healthkit-r1-r3`. All ordinary
FR/task/trailer, requirement immutability, native and regression gates still run.
Unrelated features retain the normal merged-planning requirement. Commits are
published and signature-verified using the existing GraphQL workflow.

Milestone order: R1 native build and simulator checkpoint → R2 checkpoint → R3
checkpoint. Physical-device acceptance remains pending until actually performed.
The approved specs still say Draft; their merge establishes the controlled
requirements contract. Do not change that historical wording during this task.

Linear projection uses existing CLI commands, stable repository keys in item
descriptions, read-before-write duplicate checks and a recorded dry-run. No custom
synchronization infrastructure is introduced. Tasks remain open until verified.

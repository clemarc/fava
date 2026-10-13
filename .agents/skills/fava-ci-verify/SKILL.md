---
name: fava-ci-verify
description: Verify and deliver a scoped Fava change from Codex Cloud through signed GitHub commits, a pull request and the latest applicable CI checks, with lifecycle-specific destinations and no main merge.
---

Read `AGENTS.md`, `.specify/memory/constitution.md`,
`docs/process/sdd-playbook.md` and `docs/process/ci-and-agent-verification.md`.
Use the latter for commands, onboarding, rulesets and troubleshooting; do not
invent missing feature artifacts or validation evidence.

1. Confirm the assigned scope, active feature directory and lifecycle stage.
   Read its approved spec, available plan/tasks and decision log. Work in small
   task batches. Never alter an approved requirements contract during implementation.
2. Run `python3 .github/checks/sdd.py`, validator fixtures, commit-builder tests
   and `python3 .github/checks/tooling.py`. For spec changes use
   `$speckit-checklist`; for planning use `$speckit-analyze` once its prerequisites
   exist. Resolve critical findings and attach a report to the PR or append one
   under the active feature's checklists. For implementation completion use
   `$speckit-converge` after implement/tasks, then verify any appended tasks.
   These agent checks supplement deterministic CI. Do not call analyze/converge
   against nonexistent spec/plan/tasks. Governance work uses a documented review
   against the constitution and mission instead.
3. Run available component tests. In Linux cloud, native Xcode validation awaits
   macOS Actions. Record durable decisions before regenerating derived artifacts.
   Tick tasks only with verification evidence; identify pending physical-device
   acceptance. Use synthetic workouts exclusively.
4. Stage exactly the reviewed changes, inspect the staged diff, and prepare a
   message with valid Spec/Task/Implements trailers or an explicit SDD-Type
   exception. Follow `docs/process/github-cloud-commits.md` and the existing
   `tools/github/prepare-commit.py` builder. Never target main. Create a dedicated
   branch from the inspected parent via an authorized GitHub API if needed.
   Query its current head and supply expectedHeadOid. Stop and reconcile an
   expected-head mismatch. Never publish unsigned local/REST fallback commits.
5. Submit createCommitOnBranch using existing authorized cloud credentials.
   Reject API errors. Inspect ambiguous responses before retrying. Verify the
   returned SHA is the branch head, parent/message/tree equal the intended
   change, and GitHub GraphQL/REST signature state is valid/Verified. Record the
   actual authenticated authorship. Do not claim signing when verification fails.
6. Resolve the lifecycle destination before publication: roadmap/specification,
   governance and final milestone → main; preparation/task/checkpoint → registered
   milestone branch. Use `docs/process/sdd-v2.md` and the shared milestone resolver.
   Preparation is owner-merged; task integration is allowed only to that milestone
   after owner governance adoption and every current head/target gate passes.
   Create/update the same PR against the inspected destination. Describe relevant
   specs, FRs/tasks,
   local validation, agent findings, decisions and checks unavailable in cloud.
   Never enable auto-merge or merge to main. Governance amendments are proposals
   until
   the owner reviews and merges them.
7. Monitor Actions for the **latest PR head SHA**, including Fava CI and its
   reusable native job. Confirm expected checks started. Poll to terminal state;
   distinguish success, failure, cancellation, missing check and intentional
   native skip. Read failing steps/logs and relevant artifacts; never rely on an
   older green SHA or a skipped job as native test evidence.
8. On failure, diagnose actual logs, make a scoped fix, rerun applicable local
   checks, publish another verified GraphQL commit on the same branch, verify
   the new SHA and monitor its CI. Allow at most **two automatic correction
   cycles**; after that report the blocker unless more attempts are authorized.
9. Declare ready for human review only when deterministic gates, applicable
   Xcode compilation/simulator tests and ci-required passed for the latest SHA,
   traceability remains intact, and outstanding device checks are explicit.
   Before R1, report native CI as provisioned but unvalidated. Report exact
   limitations, URLs, SHA, signing result and correction attempts.

Linear is optional progress projection, never a CI dependency. For authorized
cloud operations read `.agents/skills/linear-cli/SKILL.md` and
`docs/process/linear-integration.md`; use the pinned project-local CLI and injected
LINEAR_API_KEY, never native MCP or a second API client. Use
`tools/sdd/linear_projection.py` for dry-run and explicitly authorized
milestone projection with stable keys and verification. Never claim status
updates without actual evidence. Git owns task completion; record partial/pending
results. No new synchronization service or tracker CI dependency. Never expose
credentials or health data.

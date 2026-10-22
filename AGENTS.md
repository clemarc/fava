# Fava agent operations

- Follow `.specify/memory/constitution.md` and `docs/process/sdd-playbook.md`.
  Work only within approved scope and the correct active Spec Kit directory.
  Use small task batches; preserve requirements and completed feature history.
- Apply `docs/process/writing.md` when writing or reviewing specs, documentation
  and PR descriptions. Cut filler and repeated material; preserve precise,
  testable requirements, references and evidence.
- Run relevant Spec Kit checklist/analyze/converge checks when their lifecycle
  prerequisites exist. Mandatory tests override optional-test core templates.
  Record durable decisions and mark tasks complete only with verification.
- Use `.agents/skills/fava-ci-verify/SKILL.md` before declaring delivery ready.
  Follow `docs/process/ci-and-agent-verification.md` for local checks and CI.
- In Codex Cloud publish through GitHub GraphQL createCommitOnBranch; use
  `tools/github/prepare-commit.py` and `docs/process/github-cloud-commits.md`.
  Verify identity, branch, complete tree and GitHub signature. Preserve SDD
  trailers. This overrides local auto-commit hooks in Spec Kit Git skills.
  Never silently substitute unsigned local/REST commits or commit to main.
- Use `.agents/skills/fava-milestone-prepare/SKILL.md` and
  `.agents/skills/fava-milestone-implement/SKILL.md` for owner-started milestone
  tasks. Resolve only through `tools/sdd/milestone.py`; read
  `docs/process/sdd-v2.md` and `docs/process/sdd-v2-settings.md`. Set the resolved
  SPECIFY_FEATURE_DIRECTORY explicitly; inspect refs/PRs/ledger before checkout.
  Use no prior-chat assumptions, resets, duplicate PRs or inferred numbering.
- Create/update governance and final milestone PRs against main without merging
  or enabling auto-merge. Prep targets milestone and is owner-merged. Only after
  owner adoption of SDD v2 may the implementation coordinator integrate gated
  task/checkpoint PRs into a registered milestone branch. Until that governance
  merge, all agent merges remain prohibited. Never merge/auto-merge to main.
  Monitor Actions for its latest SHA, read actual failure logs and correct at
  most three cycles unless further attempts are authorized. Escalate with
  `.specify/templates/escalation-template.md`: findings/evidence, attempted fixes,
  a concrete proposed patch and validation plan, risks and exact owner decision.
  Human owner review remains mandatory for preparation/main/governance. Task
  review is independent of the worker; head/target changes invalidate evidence.
  Explicitly request subagents where supported; isolate their checkouts and writes.
  Coordinator alone writes shared ledger/tasks/decisions; integrate serially.
  Quality checklists are reviewer-owned. Read actual Codex findings; record
  evidence-backed disposition before resolving discussions. Report pending
  physical iPhone/iPad acceptance; never equate automated readiness to completion.
- For cloud Linear operations use `.agents/skills/linear-cli/SKILL.md` and the
  project-local `./node_modules/.bin/linear` after `npm ci`. Never rely on native
  Linear MCP in cloud. Preserve `.codex/config.toml` for local developers.
  Follow `docs/process/linear-integration.md`; Git owns task definitions and
  completion. Use `tools/sdd/linear_projection.py` for authorized milestone
  dry-run/upserts. Verify actual keys/hierarchy/status; report partial/pending
  projection honestly. No tracker write or R3.5 preparation in governance work.
- Use injected LINEAR_API_KEY only, with LINEAR_IGNORE_ENV_FILE=1 and LINEAR_DEBUG=0.
  Do not run interactive auth/config, token-output commands, HTTP debug logging,
  shell tracing, environment dumps or the companion skill's curl client fallback.
  Preserve proxy/CA trust. Never persist/expose credentials or upload real health
  data. Public tests/logs/artifacts must contain synthetic data only.

## Review guidelines

Use `.agents/skills/fava-independent-review/SKILL.md` for independent reviews,
including Codex PR review. Follow its review procedure within the runtime's
actual capabilities; report unavailable checks or evidence explicitly.

- Review the complete change against approved scope, requirements and task
  dependencies, including affected callers and tests.
- Check that each task can integrate with compatible APIs, truthful UI and the
  minimum regression coverage needed when its behavior activates.
- Examine valid workflows as well as rejection cases, especially amendments,
  target imports, documentation/tooling tasks and interruption/resume.
- Check lifecycle transitions and retained evidence identity and chronology;
  favorable report fields cannot replace actual proof.
- Report concrete defects with triggers, consequences and precise code references.
  Preserve existing regression assertions and distinguish missing verification
  from a demonstrated bug.

The shared procedure does not replace the separate reviewer, configured Codex
review, current CI or owner approval gates. A worker's self-check is not
independent review.

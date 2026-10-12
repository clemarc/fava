# Fava agent operations

- Follow `.specify/memory/constitution.md` and `docs/process/sdd-playbook.md`.
  Work only within approved scope and the correct active Spec Kit directory.
  Use small task batches; preserve requirements and completed feature history.
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
- Create/update a PR against main without merging or enabling auto-merge.
  Monitor Actions for its latest SHA, read actual failure logs and correct at
  most two cycles unless further attempts are authorized. Report blocked checks.
  Human owner review is mandatory; proposed governance changes await that review.
- For cloud Linear operations use `.agents/skills/linear-cli/SKILL.md` and the
  project-local `./node_modules/.bin/linear` after `npm ci`. Never rely on native
  Linear MCP in cloud. Preserve `.codex/config.toml` for local developers.
  Follow `docs/process/linear-integration.md`; Git owns task definitions and
  completion. Projection is pending; do not claim task statuses were synced.
- Use injected LINEAR_API_KEY only, with LINEAR_IGNORE_ENV_FILE=1 and LINEAR_DEBUG=0.
  Do not run interactive auth/config, token-output commands, HTTP debug logging,
  shell tracing, environment dumps or the companion skill's curl client fallback.
  Preserve proxy/CA trust. Never persist/expose credentials or upload real health
  data. Public tests/logs/artifacts must contain synthetic data only.

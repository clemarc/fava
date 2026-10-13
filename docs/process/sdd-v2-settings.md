# SDD v2 GitHub settings proposal

Read-only inspection on 2026-10-13 found main ruleset **24928891**, active,
targeting ~DEFAULT_BRANCH with no bypass actors. Existing rules: deletion and
force-push protection, required signatures, PRs with zero required approvals,
merge method only, no code-owner/last-push approval, no stale-review dismissal,
no thread-resolution requirement and extra approval for unattributed changes.
No status checks are required. No milestone ruleset was returned. Repository
allows merge commits only; squash/rebase and auto-merge are disabled. These are
observed protections, not a claim that proposed CI/review gates are enforced.

After governance/latest CI validation, the owner should modify main ruleset:
retain signatures, PRs, deletion/force-push blocks and empty bypass; require
**ci-required** from GitHub Actions with branches up to date and conversation
resolution. Preserve merge commits; leave auto-merge off. Keep zero approvals
for the solo owner process if identity separation is not configured. Human
review remains a process requirement; zero approvals cannot enforce it.

Create a separate active ruleset targeting `refs/heads/milestone/*`: PR-only,
verified signed commits, ci-required from Actions with up-to-date branches,
conversation resolution, deletion/force-push protection, merge commits only,
no bypass. Preserve task/planning history. Configure these rules before enabling
agent task integration; do not change protections to unblock a failed task.
No rulesets, credentials or repository settings are changed by the workflow PR.

The Cloud credential currently authenticates as **clemarc**, the owner. GitHub
cannot distinguish an owner click from an agent API merge using that identity;
signed commits attest credential/commit identity, not human intent. A signed
owner merge is durable evidence plus a process rule, not technical proof of a
human operating the credential. The coordinator must obey main/prep prohibitions.

Stronger enforcement requires a separately provisioned GitHub App/bot identity
with permission to integrate milestone PRs and **no ability to update/merge main**,
plus owner-only main update restrictions, no bypass for that app, and required
owner approval for preparation. Validate the applicable plan/ruleset feature
availability first. Restrict main updates by actor rather than granting a bypass;
the app still obeys required CI/signatures on milestone branches. GitHub PR authors
cannot approve their own PR, so owner/app separation permits enforceable owner
approval. Independent Cloud subagents often still share the same GitHub identity;
their reports supply process evidence, not an extra GitHub approving actor.
Do not provision tokens/apps/keys, weaken gates or change settings silently.
If separation is not adopted, document the residual process-only human boundary.

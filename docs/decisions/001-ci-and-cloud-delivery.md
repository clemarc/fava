# ADR-001: Deterministic CI and verified cloud delivery

Date: 2026-10-12. Status: proposed; accepted only after owner review/merge.

Fava's Spec Kit 1.0.13 repository has an agreed roadmap, Git/roadmap extensions,
project-local Linear CLI/skill and a GraphQL index request builder, but no native
project or CI. The constitution freezes merged feature directories, conflicting
with its living-spec rule and the staged spec → planning → implementation loop.
The generic playbook also assumes headless analysis, multiple reviewers and a
custom tracker adapter, which do not fit this authorized solo cloud pilot.

Use small standard-library Python gates and GitHub Actions as deterministic
merge evidence; use installed checklist/analyze/converge as agent review. Approved
requirements become controlled on spec merge; active derived artifacts can grow,
append-only decisions preserve rationale, and explicit completed features freeze
entirely. Supersession opens a new contract. No product requirement is rewritten.
Constitution 1.1.0 proposes these clarified boundaries and delivery obligations.

Use a Linux aggregate and an explicitly pinned standard macOS/Xcode reusable job.
Until R1 supplies the real app, record native onboarding and no native evidence;
project presence automatically ends that exception. Require real shared-scheme
tests, locked package resolution and separate HealthKit physical-device acceptance.

Reuse createCommitOnBranch tooling and the existing authorized cloud credential;
verify signature/identity/tree and preserve independent SDD trailers. Keep Linear
CLI and local MCP, with task projection pending. The human owner reviews every PR
and merges manually; no extra reviewer, auto-merge or agent bypass. Require the
aggregate and signing in a main ruleset only after their actual operation is
verified. The owner activates rules separately; this PR does not alter rulesets.

Consequences: structural gates cannot assess semantic requirements/test adequacy;
agent reviews and human acceptance remain necessary. No API-key CI agent, custom
Linear API client, community gate extension or fabricated Swift app is introduced.
Native execution cannot be proven until R1; public logs must use synthetic data.
Detailed operations live in docs/process/ci-and-agent-verification.md.

# CI and agent verification

Fava's public GitHub Free repository delivers through PRs against `main`. Codex
Cloud validates tooling on Linux, publishes verified GitHub GraphQL commits and
monitors Actions; the owner reviews and merges manually. This setup changes no
R1–R3 product requirements and creates no placeholder application.

## CI architecture

`.github/workflows/sdd-quality.yml` runs on every PR, main push and manual dispatch,
without workflow path filters. All checks use read-only `contents` permission,
checkout without persisted credentials, bounded timeouts and concurrency
cancellation for superseded PR commits. PR checkout uses the actual head SHA;
validation compares its merge base with the PR base and checks every new commit.

| Check | Runner | Responsibility |
| --- | --- | --- |
| `sdd-quality` | ubuntu-24.04 | Structure, lifecycle, scoped IDs, traceability, per-commit trailers |
| `tooling-validation` | ubuntu-24.04 | Positive/negative fixtures, existing commit-builder tests, skill/guidance checks, workflow syntax and shell syntax |
| `ci-applicability` | ubuntu-24.04 | Determine native requirement; fail if native onboarding is abused |
| `ios-build-test` (reusable job) | macos-26 | Real Xcode build and simulator tests when required |
| `ci-required` | ubuntu-24.04 | Aggregate all applicable job results; fail closed |

The aggregate requires successful SDD, tooling and applicability jobs. Required
native validation must succeed. Only `onboarding`, `documentation` or `sdd-only` permits a
skipped native job; unknown applicability, unexpected skip/success, failure,
cancellation and missing output fail. If the entire workflow cannot start,
GitHub's required aggregate remains unsatisfied and merge stays blocked. A green
aggregate in onboarding means the applicable tooling gates passed; it does **not**
mean the app built or tests ran. Never describe a skipped job as native success.

## Deterministic SDD gates

`.github/checks/sdd.py` uses only Python's standard library and Git, mutates no
specs and needs no API credentials. It checks:

- Constitution presence; roadmap header/table, unique R IDs, explicit scope and
  dependencies, valid dependency references and acyclic ordering. Agreed roadmap
  rows cannot be removed/rewritten; add superseding slices instead.
  Inserted slices may use a decimal ID such as `R3.5` without renumbering agreed
  rows. The full ID must resolve in dependencies and parent links; feature
  directories retain the existing epic-NN-slug format.
- Approved naming: epic-NN-slug, NNN-slug or YYYYMMDD-HHMMSS-slug. Directory paths
  must match roadmap entries. Roadmap slices intentionally precede feature specs:
  a future expected directory need not exist yet. Once its spec exists, its
  `Parent roadmap: specs/<epic>/roadmap.md → entry Rn` must resolve both ways.
- FR-NNN definitions, feature-scoped uniqueness and references; numbered user
  story headings must cite applicable FRs in their own section. FR/US/T identities
  are qualified by the feature in cross-feature contexts.
- Unique TNNN task IDs, valid FR and [USN] mappings, complete FR coverage when
  tasks exist, exact file paths, valid/acyclic task dependencies. Future task file
  paths need not exist before implementation. Open [P] tasks cannot share files
  with another open task or have unmet dependencies.
- `tasks.md` requires `plan.md`; spec/checklist-only PRs need neither. Planning
  follows a merged spec; source implementation follows a merged plan/tasks.
- Merged requirements cannot change or disappear. Only verified completion
  status metadata may change in the contract. Active derived artifacts may change;
  decision logs remain append-only and use unique DEC-NNN headings. A feature
  with `Status: completed` in the base is entirely frozen. Superseding features
  must name an existing predecessor, never themselves.
- Reconciliation PRs touching `specs/_system/` must account for each completed
  feature FR using `FR-NNN (<feature-directory>)`, with explicit supersession text
  where appropriate. This is an identifier coverage gate; the owner reviews the
  semantic correctness of reconciliation.

Use core story headings `### User Story 1 - …` (US1) or `### US1 …`. Tasks follow:

```markdown
## Phase 1: Setup
- [ ] T001 Configure settings in Fava/Config.swift (FR-exempt: shared initialization)
## Phase 2: User Story 1
- [ ] T002 [P] [US1] Test empty results in FavaTests/ReaderTests.swift (FR-001)
- [ ] T003 [US1] Implement reading in Fava/Reader.swift (FR-001) (depends on T002)
```

Setup/Foundational tasks may omit FRs only with a reasoned `FR-exempt:` statement.
Every task outside those phases needs [USN], including cross-cutting tasks (list
multiple stories when applicable). All FRs in a spec with tasks must be accounted
for; deferred requirements belong in another slice rather than disappearing from
coverage. Mark completed tasks [X] only when the tests/evidence support completion.

## Commit messages

Commit validation is independent of API/local creation. Every source/test or
unknown application-path commit needs terminal Git trailers:

```text
feat: handle empty workout reads

Spec: specs/healthkit-run-library-02-run-ingestion
Task: T002, T003
Implements: FR-001 FR-002
```

One feature per commit; split work spanning features. Repeated Task/Implements
trailers and comma/space-separated identifiers are supported. Implements must
match the union of the cited tasks' FR mappings. For a wholly FR-exempt Setup or
Foundational batch, omit Implements rather than fabricate FRs; Spec/Task still
resolve to explicit exempt tasks.

Non-implementation commits use exactly one `SDD-Type:` trailer:

| Value | Exception |
| --- | --- |
| `bootstrap` | Initial repository scaffolding |
| `process` | Constitution, process documentation and decisions |
| `roadmap` | Roadmap creation/maintenance |
| `specification` | Requirements/checklists only |
| `planning` | Derived feature design/task artifacts |
| `tooling` | CI, skills and project tooling |
| `reconciliation` | Current-state requirement maintenance |

Exceptions cannot cover application source/tests or unknown paths. Spec artifact
changes require a spec lifecycle type rather than a generic tooling/process type.
Reconciliation only permits `_system` and governance paths. SDD-Type records
intent; the validator also examines paths and enforces frozen contracts. Human
review verifies that the exception accurately describes the change. The owner must
preserve the applicable trailers in squash/merge commit messages; main-push CI
validates them independently too.

## Local checks and Spec Kit

From the repository root (Python 3.9+):

```sh
python3 .github/checks/sdd.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .github/checks -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/github -p 'test_*.py' -v
python3 .github/checks/tooling.py
# With the reviewed actionlint 1.7.12 binary on PATH:
actionlint -shellcheck=
# After staging, validate a proposed message:
python3 .github/checks/sdd.py --message-file /tmp/fava-commit-message.txt
# After publishing/fetching, use the actual PR merge-base:
python3 .github/checks/sdd.py --base BASE_SHA --head HEAD
```

Fixtures cover valid and invalid lifecycle, IDs, links, coverage, trailer,
dependency, native applicability and aggregate states. Existing builder tests
cover exact staged bytes/deletions, exclusions, unsupported modes, empty requests,
main rejection and parent mismatch. `tooling.py` checks discovery/front matter,
guidance references, action pins, lock consistency and narrow credential/export
patterns. This is not a comprehensive secret scanner: inspect the complete staged
diff and test data before publishing.

Installed Spec Kit is **1.0.13**, with `git` and `fava-roadmap` extensions. Installed
agent skills include `$speckit-checklist`, `$speckit-analyze` and
`$speckit-converge`. Checklist reviews requirement quality in specification PRs;
analyze reviews spec/plan/tasks consistency in planning/implementation PRs;
converge assesses completion after implement and may append traceable tasks.
Set `SPECIFY_FEATURE_DIRECTORY` to the intended feature; use
`SPECIFY_FEATURE_NO_PERSIST=1` for read-only validation. Core optional-test defaults
are overridden by the constitution's mandatory tests. Git auto-commit hooks remain
disabled and the verified-cloud policy overrides any skill's unsigned commit path.
The roadmap extension's generic MCP instructions are overridden by AGENTS for cloud.

Store reports in active feature checklists or attach them to the PR, with command,
findings, disposition and SHA context. Do not invoke tools whose artifacts do not
yet exist. This CI/governance PR has no feature spec/plan/tasks and uses a mission
and constitution review instead. No independently validated headless Spec Kit
runner is installed. Agent findings are review obligations, not invented CI jobs.
No community CI quality-gate extension is installed: the existing extensions have
no deterministic Fava traceability gate, and Archive/Canon or other community
extensions would require source, version compatibility and maintenance review.
Use the local deterministic gates first; no OpenAI key is needed in Actions.

## Native validation and R1 activation

Native CI was activated and verified by R1 at signed commit
`7bcfec6f49e142f3dc85fa99f3227201f79b636e` in
[run 38305400468](https://github.com/clemarc/fava/actions/runs/38305400468):
Xcode 26.6 built Fava and each iPhone/iPad simulator passed 13 tests.
This establishes automated validation, not physical-device HealthKit acceptance. Applicability discovers tracked Xcode containers,
and also checks the base so deleting a project cannot restore onboarding. Swift or
other native artifacts without a project fail. Once a project exists, native
build/tests skip changes limited to documentation or `specs/` artifacts (including
roadmaps, contracts and synthetic fixture data). Changes limited to those paths
plus the SDD validators/fixtures listed in `SDD_ONLY_PATHS` in
`.github/checks/native.py` use `sdd-only` and also skip native build/tests.
SDD and tooling tests, applicability and `ci-required` still run on every PR;
there are no workflow path filters that leave required checks pending.

App source/tests/assets, Xcode files, dependencies, native CI configuration,
`.github/checks/native.py`, `.github/checks/aggregate.py`, workflow changes and
unknown paths still require native CI. A mixed application/spec PR must build and
test; a native artifact cannot gain an exemption merely by moving into `specs/`.
The classifier/aggregate policy change itself requires native validation once;
subsequent spec/roadmap or SDD-only changes use the new exemption.

R1 must:

1. Deliver the approved real Swift/SwiftUI iPhone/iPad Xcode project/workspace and
   track a shared scheme under `xcshareddata/xcschemes/`. Include all applicable
   unit/integration/UI test targets or a tracked test plan in its Test action.
2. Add `.github/ios.json` with exactly these keys, substituting the actual names:
   `{"container": "Fava.xcodeproj", "scheme": "Fava"}`. A workspace uses its
   `.xcworkspace` path instead. Commit Package.resolved for remote Swift packages.
3. On a Mac, verify `xcodebuild -list -json -project Fava.xcodeproj` (or -workspace),
   then `python3 .github/checks/native.py test`. The script discovers available iOS
   runtime/devices and intersects them with the scheme's supported destinations.
   It selects one available iPhone; no specific model name is assumed.
4. Open the R1 implementation PR, verify the applicability state is `required`,
   observe a real macOS `ios-build-test`, inspect logs/xcresult and confirm nonzero
   test count, successful compilation, tests and ci-required on the latest SHA.
   Record exact SHA, build and nonzero test evidence in the feature and PR. The code exception automatically stops applying
   as soon as the project exists; no toggle can keep native validation disabled.

The reusable `.github/workflows/ios-ci.yml` uses standard Apple Silicon **macos-26**
with explicit **Xcode 26.6** (`DEVELOPER_DIR`); missing Xcode fails instead of
selecting latest. The image includes iOS simulators; xcodebuild launches them for
unit, integration and UI tests. The build SDK pin does not set Fava's minimum iOS
deployment target, which belongs in R1's approved design.
See the [runner image documentation](https://github.com/actions/runner-images/blob/main/images/macos/macos-26-arm64-Readme.md).
Runner images evolve: review a pin update if that version is removed. No larger
runner, Apple membership, signing certificate, provisioning profile or store
credential is required. Simulator code signing is disabled. Dependency resolution
uses committed Swift package versions, disables automatic updates and fails on
missing pins; no app dependency cache is added before there are dependencies.

The script discovers shared schemes/build targets through xcodebuild, validates
configured test membership, preserves compiler output, runs explicit-destination
build then `xcodebuild test`, and rejects a zero-test result. Logs and xcresult
bundles are retained five days; DerivedData is not uploaded. The script supports
`--family iPad` for future coverage without changing the discovery design.
Native execution and xcresult parsing require the first real macOS run; Linux
fixture tests prove selection/control logic only.

Mocks verify HealthKit-facing abstractions using synthetic workouts. Simulator app
tests should exercise loading, empty, failure, navigation and applicable UI flows
as each feature is implemented. Before accepting a HealthKit feature, separately
record physical iPhone/iPad checks: install/launch, HealthKit capability/availability,
request flow including cancel/failure and privacy/read-denial semantics, reading
known device workouts, no-data and missing-value behavior, repeat reads and
navigation. Empty reads never establish denial of read permission. Record only
sanitized outcomes and device/OS versions, never real exports/screenshots/history.
Simulator tests do not prove real authorization or access to physical-device history.

## Verified publication and Actions monitoring

Use the existing [GraphQL workflow](github-cloud-commits.md), mutation and index
builder in `tools/github/`. Query viewer/repository/default branch and branch head
using existing authorized API credentials. Create a non-main maintenance/feature
branch if absent. Review the exact staged diff, build with expectedHeadOid, submit,
reject GraphQL errors and inspect ambiguous responses before retrying. Unsupported
modes/symlinks/submodules stop publication. Preserve complete bytes and deletions.
The builder also refuses main and a parent different from local HEAD.

Verify signature.isValid, state VALID and wasSignedByGitHub; REST must report
verification.verified true with reason valid. Fetch the returned SHA, check the
branch head, parent, full message and tree against `git write-tree`. Record SHA,
branch, authenticated displayed authorship and whether all intended files match.
The authenticated identity determines authorship; never spoof another author.
Existing FAVA_GITHUB_API_TOKEN is a protected cloud network binding, not a new
repository token. Do not place it in Actions. If authorization, tool access, branch
state or unsupported files block delivery, retain reviewable changes and report
that exact blocker; never claim Verified or silently use unsigned git/REST writes.

Use `.agents/skills/fava-ci-verify/SKILL.md` for the delivery loop. Create/update the
PR against main; inspect checks/workflow runs whose head SHA equals the current PR
head. CLI examples use the existing binding without printing it:

```sh
GH_DEBUG= GH_TOKEN="$FAVA_GITHUB_API_TOKEN" gh pr checks PR_NUMBER --repo clemarc/fava
GH_DEBUG= GH_TOKEN="$FAVA_GITHUB_API_TOKEN" gh run list --repo clemarc/fava --commit HEAD_SHA
GH_DEBUG= GH_TOKEN="$FAVA_GITHUB_API_TOKEN" gh run view RUN_ID --repo clemarc/fava --log-failed
```

Confirm expected runs started, monitor until terminal and inspect logs/artifacts.
If gh log downloads are blocked at a redirected Actions storage host, use the
already-authorized GitHub integration's workflow job-log/artifact tools. In this
setup the connector retrieved logs successfully while direct downloads were
proxy-denied; do not bypass the proxy or add credentials to work around it.
On failure diagnose actual evidence, fix within scope, rerun checks, make a new
verified GraphQL commit on the same branch and monitor the new SHA. Two automatic
correction cycles maximum; thereafter report the blocker. A skipped, cancelled,
missing or old successful check cannot prove the latest native change passed.

## Owner's main ruleset

Do not enable a required check until its first successful real PR run is visible.
Inspection on 2026-10-12 found an active `main` ruleset (ID 24928891), targeting
the default branch with no bypass actors. It already requires PRs, signed commits,
blocks deletion/force pushes and requires zero approvals. It has no required CI
checks; review-thread resolution is disabled. Auto-merge is already disabled.

After this PR's latest checks pass, the owner should edit Settings → Rules →
Rulesets → **main**, rather than create a duplicate ruleset:

- Retain name `main`; Enforcement **Active**; target default branch
  `main`; bypass list **empty**, including agents/admin automation.
- Require a pull request before merging, **0 required approvals** (solo owner
  reviews manually); require conversation resolution. Do not require code-owner
  or another-person approval; disable extra approval for unattributed changes
  for this solo process. Keep human review as the documented process gate.
- Require status checks: select **ci-required**, source **GitHub Actions**, with
  branches up to date before merging. This aggregate includes all mandatory gates;
  requiring the skipped native check separately would block legitimate onboarding
  and documentation PRs. Optional visible sdd/tooling checks may also be required
  after their successful runs; never require a check name never emitted.
- Block force pushes and restrict deletions. Require signed commits only after
  actual GraphQL signing is verified; audit unsigned ancestors before applying it.
- Settings → General → Pull Requests: leave **Allow auto-merge disabled**.
  Merge remains a manual human action. Never weaken protection for agent failures.

Ruleset updates are separate from this PR's code. No ruleset is changed by this
setup; verify checks first and let the owner apply these exact settings. Workflow
changes themselves remain subject to owner review; aggregate logic cannot secure
an adversarial edit to its own workflow without that review.

## Linear and public security boundary

Reuse the pinned project-local Linear CLI and companion skill; see
[Linear integration](linear-integration.md). Preserve local MCP configuration.
Project → epic, milestone → roadmap slice, parent issue → story, sub-issue → task;
repository keys (feature/TNNN, feature/USN) identify projected work. Task projection
is not implemented, no statuses are updated here, and no second GraphQL client or
synchronization service is introduced. LINEAR_API_KEY is for authorized cloud CLI
operations only and never a CI dependency or Actions secret.

Public source/history/PRs/logs/artifacts require synthetic fixtures only, no real
HealthKit exports and no credentials. No environment dumps, debug headers,
pull_request_target, privileged PR code, Apple/OpenAI/Linear Actions secrets or
third-party actions beyond pinned checkout/artifact upload. Review Action/tool
updates on a branch. Keep API request/response files private in /tmp. Standard
public hosted runners are free; prioritize native reliability over minute savings.

## Troubleshooting and deferred work

| Symptom | Action |
| --- | --- |
| Missing FR/story/task/path | Follow the named artifact/ID in the gate output; regenerate derived tasks from the approved spec, never invent IDs |
| Frozen contract violation | Create a superseding feature, or retain only allowed active derived changes |
| Native onboarding failure | R1 must supply the real container, shared test scheme and configuration; do not create a disposable app |
| No simulator/Xcode/scheme/tests | Inspect version/devices/destinations/test-summary logs; review the runner pin and shared test selection |
| Missing/cancelled CI | Inspect the latest SHA/run, Actions permissions and YAML; ci-required must remain unsatisfied until resolved |
| API authentication/permission error | Check safe runtime readiness and actual HTTP error, existing credential/workflow permission; no new token fallback |
| expectedHeadOid mismatch/timeout | Re-read branch head and reconcile/fetch before a new request; avoid duplicate writes |
| Linear outage | Report projection pending; keep SDD/native CI independent |

Deferred: initial real native run and R1 acceptance, iPad CI expansion, dependency
cache if justified, full secret scanning, broader semantic/path analysis, tested
Linear task projection and reviewed community extensions. Deterministic checks
validate structural contracts; agent analysis and human review remain responsible
for requirement meaning and test sufficiency.

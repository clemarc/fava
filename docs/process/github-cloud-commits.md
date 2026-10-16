# Verified GitHub commits from Codex Cloud

Fava requires verified commit signatures. Codex Cloud must publish commits with
GitHub's GraphQL `createCommitOnBranch` mutation, rather than publishing unsigned
local commits. GitHub creates and signs the commit server-side where supported;
no personal SSH/GPG private signing key is supplied to the worker.

This rule covers process maintenance and feature work, including the existing
Spec Kit Git extension's auto-commit hooks. Preserve the constitution's applicable
`Spec:`, `Task:`, and `Implements:` trailers; the API message accepts a headline
and body. Local developers may continue using their own verified signing keys.
Do not weaken branch protection or merge automatically.

The [GitHub API reference](https://docs.github.com/en/graphql/reference/commits#createcommitonbranch)
documents signing and authorship. The author comes from the authenticated
credential; callers cannot specify arbitrary author/committer identities.
GitHub's signature attests to the API-created commit, rather than being a
signature made with the user's personal private key. Ordinary `git push`, the
REST Git Database API, and generic file-update APIs must not be assumed to sign
commits. Check the actual signature every time.

## Cloud authentication and access

Supply an existing authorized GitHub API credential as a Personal vault
**network secret** requested by the Fava environment under
`FAVA_GITHUB_API_TOKEN`, with allowed destination `api.github.com`.
The credential needs access to `clemarc/fava` and permission to write repository
contents. A credential restricted to this repository is preferred. Changes to
workflow files additionally require the applicable workflow permission.
Do not use a repository deploy key: SSH authentication cannot authorize this
HTTPS GraphQL API.

Keep the inherited HTTP/HTTPS proxy and CA trust. The worker may receive a
placeholder; the proxy substitutes the protected credential for the allowed
HTTPS destination. Do not put the real credential in a local process, file,
Git config, command-line argument, or repository. Do not print the placeholder,
authorization headers, environment values, credential lengths or prefixes, or
enable shell tracing/HTTP debug logs.

The example below selects this protected binding as `GH_TOKEN` for the command
only. This intentionally selects the configured API credential rather than an
unrelated bootstrap Git transport credential. Do not change the existing
Linear secret or local MCP authentication.

Check the safe runtime readiness report and run a read-only authentication
query before writes (clear `GH_DEBUG` for these commands):

```sh
GH_DEBUG= GH_TOKEN="$FAVA_GITHUB_API_TOKEN" gh api graphql \
  -f query='query { viewer { login } }'
```

If the binding is missing, stop before running the command. A bare `Forbidden`
connection error may be a proxy destination denial; distinguish it from a
GitHub HTTP authentication/permission error. The GitHub connector's permission
to create a PR does not establish direct worker access to GraphQL. If only REST
connector tools are available, report that limitation and leave reviewed
changes staged. Never fall back to an unsigned commit or unprotected token.

Environment configuration changes must use Codex Cloud's configuration workflow.
Republish and start a task from the updated environment when required; existing
tasks can retain their earlier configuration.

## Prepare the exact commit

1. Inspect repository guidance and the destination branch. Confirm its current
   full HEAD SHA and fetch that commit into the local repository. Use a dedicated
   task branch; do not target `main` directly.
2. Complete the authorized changes and relevant checks. Stage only intended
   paths. Review `git diff --cached <expected-parent>` and run
   `git diff --cached --check <expected-parent>`. Check that no credentials or
   unrelated changes are included.
3. Put the complete conventional commit message and applicable trailers into a
   temporary text file using a file-editing tool.
4. Build the request with `tools/github/prepare-commit.py`. It reads the Git
   index, including staged deletions, and never commits, pushes, or calls APIs.
   It excludes unstaged and untracked changes. Content is base64-encoded without
   altering bytes. Renames are represented as a deletion and addition.

For example, replace the placeholders with the inspected branch and its full
HEAD SHA (do not run with literal placeholders):

```sh
python3 tools/github/prepare-commit.py \
  --repository clemarc/fava \
  --branch YOUR_TASK_BRANCH \
  --parent EXPECTED_FULL_HEAD_SHA \
  --message-file /tmp/fava-commit-message.txt \
  --output /tmp/fava-commit-request.json
```

The output must be a new file. Inspect its changed paths and message, without
dumping sensitive file contents. `expectedHeadOid` is a concurrency guard:
GitHub must reject the write if someone has advanced the destination branch.
Reinspect before rebuilding a rejected request.

GraphQL file additions do not offer a file-mode field. The builder rejects
changed executables, symlinks, submodules, and mode changes involving them, so
it cannot silently convert them to regular files. Unchanged modes are preserved
by the parent tree. If a change requires those modes, stop and arrange a verified
alternative with the user; do not use unsigned REST commits as a fallback.

The request builder uses standard-library Python (3.9 or newer); API execution
uses `gh`. Run its offline tests before changing the builder:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tools/github -p 'test_*.py' -v
```

Tests check staged byte preservation, unstaged/untracked exclusion, deletions,
mode rejection, empty requests, and protection of an existing request file.

## Create and verify the commit

The branch must already exist. Create a new branch from the inspected parent
using an authorized GitHub branch tool/API before submitting the mutation.
Then execute the reviewed request:

```sh
GH_DEBUG= GH_TOKEN="$FAVA_GITHUB_API_TOKEN" gh api graphql \
  --input /tmp/fava-commit-request.json \
  > /tmp/fava-commit-response.json
```

Use `tools/github/create-commit-on-branch.graphql` as the mutation. Its response
requests the commit OID, URL, tree OID, and signature. Success requires no
GraphQL errors, `signature.isValid == true`, `signature.state == "VALID"`, and
`signature.wasSignedByGitHub == true`. A null/invalid signature is a failed
verification even if a commit was created. Report the actual result.

The mutation creates a commit **and advances the branch**; it is a write, not
a signing dry-run. After a timeout or ambiguous response, inspect the branch
before retrying to avoid duplicate commits. Do not create a second commit
blindly. The unchanged expected-parent guard helps reject duplicate execution.

Fetch the verified commit, compare its complete tree with the intended Git
index (`git write-tree`), and confirm the expected parent and message. GitHub's
REST commit verification field must also report `verified: true` and reason
`valid`. Only then present/update the PR and report a verified commit.

To reconcile the local branch, first confirm the fetched tree exactly matches
the index and there are no remaining unstaged tracked edits or unrelated staged
changes. `git reset --soft <verified-commit>` then moves local HEAD while
preserving the index and working files. Do not discard user changes.

## Replace an existing unsigned PR commit

Appending a signed commit leaves the unsigned ancestor in the PR. Instead:

- Inspect the PR's current head and its original base/parent; preserve the full
  original change plus the newly authorized documentation/tooling changes.
- Create an isolated replacement branch from that parent, so the unsigned
  commit is not an ancestor.
- Stage the complete intended tree and prepare the request relative to that
  parent. Include this workflow's changes in the same API-created commit.
- Verify the signature, parent, complete tree, and diff before updating the
existing PR branch. Replace its head only with an explicit expected-old-SHA
  lease; never overwrite another contributor's intervening change. If a lease
  fails, inspect and reconcile rather than forcing over it.
- Keep the existing PR when possible. If replacement is blocked by policy,
  leave the new verified branch for review and report the limitation. Do not
  merge or relax protections.

## Verification record

On 2026-10-12, the existing Linear integration commit was confirmed unsigned.
The REST Git commit and file-update APIs also produced unsigned test commits.
The task's direct GraphQL authentication probe failed with
`Post "https://api.github.com/graphql": Forbidden`; the environment had no
`FAVA_GITHUB_API_TOKEN` binding and did not allow `api.github.com`.
The available GitHub connector did not expose arbitrary GraphQL requests.
This is an API access/configuration blocker, not evidence that
`createCommitOnBranch` cannot sign commits. Record a successful mutation and
actual verification here only after the configured environment passes the test.


On 2026-10-12, this CI setup task used the already-bound cloud network secret
and successfully executed createCommitOnBranch on `chore/ci-agent-verification`.
Commit `4652930e8c7940c92bf1f930f3a7cb1630fa0b71` was verified through GraphQL
(isValid true, state VALID, wasSignedByGitHub true) and REST (verified true,
reason valid). Authenticated author: Clement Le Marc (`clemarc`); committer:
GitHub. The remote branch head, expected parent, full message and fetched tree
matched the staged tree containing all 17 intended files. No unsigned local
commit or git push was used. This resolves the earlier access blocker above.

[PR #6](https://github.com/clemarc/fava/pull/6) and
[the initial Actions run](https://github.com/clemarc/fava/actions/runs/38276897331)
record the test: sdd-quality, tooling-validation, ci-applicability and ci-required
passed against that SHA; ios-build-test was explicitly skipped in native onboarding.
This verifies API publication and applicable CI, not a native build. Subsequent
commits must still be individually verified and monitored; the PR's latest head
and run are the final delivery evidence. Rulesets were not changed.

## SDD v2 integration commits

After owner governance adoption, task/checkpoint PRs may target only the registered
milestone integration branch under [SDD v2](sdd-v2.md). Preparation and main merges
remain owner actions. The prior no-agent-merge rule remains until adoption.

GitHub GraphQL publication still signs ordinary commits. PR integration uses
GitHub's merge operation only after all head/target gates pass, with the expected
PR-head SHA guard and a just-inspected target. No API provides an atomic lease
for both PR head and target: serialize integration, require up-to-date protected
branches and stop/revalidate on target movement; concurrent external writes are
an acknowledged race requiring owner coordination/settings. Verify the resulting
merge's REST/GraphQL signature, both parents, full tree, destination and PR linkage
before declaring integration. A missing/invalid signature blocks further progress;
never silently assume GitHub merge commits are Verified.

Retain merge commits/source history. Source-bearing merges use the union of real
Spec/Task/Implements mappings; non-source prep/checkpoint merges use SDD-Type:
planning. Milestone/Integration-PR trailers aid navigation, never grant approval.
Main's owner merge must preserve applicable trailers too. The deterministic
promotion proof verifies the pinned public GitHub owner merge and ancestry;
local private signing keys are neither installed nor exposed to Cloud.

Use the [owner merge message handoff](ci-and-agent-verification.md#owner-merge-message-handoff)
to provide a copyable title/body and verify the subsequent main-push run. A
verified PR-head commit does not supply trailers to GitHub's future merge message.

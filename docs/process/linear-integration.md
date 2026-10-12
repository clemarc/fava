# Linear CLI integration

Fava uses the community [schpet/linear-cli](https://github.com/schpet/linear-cli)
as a project-local development tool so Codex Cloud can access Linear without
depending on MCP. `package.json` pins `@schpet/linear-cli` to **3.0.0** and
`package-lock.json` locks its dependency tree. Node and npm run tooling only;
Fava remains a native Swift/SwiftUI application.
Setup was verified with Node 24.19.0 and npm 11.9.0; use a current supported
Node release because the locked installer dependencies require modern Node.

The local Linear MCP configuration in `.codex/config.toml` remains available
for local Codex sessions. Its `FAVA_LINEAR_API_KEY` binding is separate from
the cloud CLI's `LINEAR_API_KEY` binding.

## Installation and agent discovery

From the repository root:

```sh
npm ci
./node_modules/.bin/linear --version
./node_modules/.bin/linear --help
```

The original dependency installation is:

```sh
npm install --save-dev --save-exact @schpet/linear-cli@3.0.0
```

Do not install the CLI globally. Use the installed dependency with
`./node_modules/.bin/linear` from the repository root so missing tooling fails
immediately without npm package resolution. `npx --no-install` can still query
registry metadata or select cached/global tooling when the local binary is absent;
it does not guarantee local-only execution. The npm package downloads a
platform-specific prebuilt binary from its GitHub release during installation.
Allow npm registry access and GitHub release downloads, including redirect hosts such as
`release-assets.githubusercontent.com`, through the cloud proxy; keep TLS
verification and the configured CA trust enabled. Linux requires a supported
glibc platform (3.0.0 specifies glibc 2.35 or newer).

The official companion skill was installed project-locally using the skills CLI
(installer version 1.7.2 at setup):

```sh
npx skills add schpet/linear-cli --skill linear-cli -a codex -y
```

Codex discovers `.agents/skills/linear-cli/SKILL.md`. The skill's reference files
and `skills-lock.json` are committed so future sessions do not need to reinstall
it. No unrelated skills were installed. Existing Spec Kit skills are preserved.
Whitespace-only blank lines in generated reference help were normalized to pass
`git diff --check`; the upstream skill instructions are otherwise unchanged.

Security and compatibility review: the installed skill contains Markdown
instructions and references, with no executable scripts. It documents both
reads and mutations, interactive authentication, token output, and a curl
fallback. Those examples do not authorize writes or credential disclosure.
Fava's `AGENTS.md` takes precedence: use the pinned local CLI, injected
environment authentication, and repository-owned definitions. Never run
`linear auth token` or the token-based curl example, persist credentials, or
enable debug HTTP logging or shell tracing. The upstream `allowed-tools`
metadata is not a security boundary or a replacement for Codex permissions.
Inspect actual CLI help before using a recipe: the vendored skill comes from
upstream development and may describe options newer than the pinned release.
Review both dependency and skill updates on a branch before committing them.

## Project defaults

The tracked `.linear.toml` contains only non-secret defaults:

```toml
workspace = "clemarc"
team_id = "FAV"
```

Run commands from the repository root. Validate the team default with
`./node_modules/.bin/linear team id`; it must print `FAV`. Do not run interactive
`linear config`, which could overwrite these defaults. Environment overrides
such as `LINEAR_TEAM_ID` can take precedence; avoid unintended overrides.

The epic is [HealthKit Run Library](https://linear.app/clemarc/project/healthkit-run-library-21526adc665b),
UUID `f823cc39-b818-460f-8682-bb4ec831885a`, in team `FAV`.

## Authentication: local and Codex Cloud

For local CLI use, supply an existing authorized key as `LINEAR_API_KEY` through
a trusted secret manager into the command environment. Do not put it in shell
history, `.env`, `.linear.toml`, repository files, or command-line arguments.
Local Codex may continue using its existing MCP setup independently.

For Codex Cloud, the existing `LINEAR_API_KEY` secret in the Codex Cloud Personal
vault must be bound to the selected environment as the environment variable
`LINEAR_API_KEY`, with `api.linear.app` allowed for network-secret injection.
The worker may receive a proxy placeholder rather than the real key. The CLI
sends it through the inherited HTTPS proxy; the proxy substitutes the protected
credential for the allowed destination. Treat that placeholder as sensitive.
Keep the inherited proxy and CA settings. Do not replace the binding with an
unprotected key, create another key, or use a local keychain.

CLI 3.0.0 accepts `LINEAR_API_KEY` without an interactive login. It takes
precedence over stored credentials. The API key determines the authenticated
workspace; `.linear.toml` does not restrict which workspace a key can access.
Confirm `clemarc` with `auth whoami`. Do not add `--workspace` when using
`LINEAR_API_KEY`: 3.0.0 rejects that combination. Use `--no-input` for cloud
commands. Set `LINEAR_IGNORE_ENV_FILE=1` to prevent loading `.env` files and
`LINEAR_DEBUG=0` to keep error debugging disabled.

Check availability without showing a value, length, or prefix:

```sh
if [ -n "${LINEAR_API_KEY:-}" ]; then
  echo "LINEAR_API_KEY is available"
else
  echo "LINEAR_API_KEY is missing"
fi
```

## Read-only verification

Inspect supported syntax first:

```sh
./node_modules/.bin/linear team --help
./node_modules/.bin/linear project --help
./node_modules/.bin/linear auth whoami --help
./node_modules/.bin/linear team list --help
./node_modules/.bin/linear project view --help
```

Then verify from the repository root in a shell with the injected environment:

```sh
export LINEAR_IGNORE_ENV_FILE=1
export LINEAR_DEBUG=0
./node_modules/.bin/linear --no-input team id
./node_modules/.bin/linear --no-input auth whoami
./node_modules/.bin/linear --no-input team list --json
./node_modules/.bin/linear --no-input project view f823cc39-b818-460f-8682-bb4ec831885a --json
```

Success requires actual authenticated API reads: `auth whoami` must resolve a
user in `clemarc`; teams must include key `FAV`; the project must match the UUID,
name, URL, and team above. Help output and a present variable do not establish
connectivity. These commands do not create, update, archive, or delete items.

Setup verification on 2026-10-12 used the injected cloud environment and CLI
3.0.0. `npm ci`, version/help checks, and the team-default check passed.
Authenticated reads resolved Clement LM in `clemarc`, found `fava` (`FAV`), and
retrieved the expected HealthKit Run Library project and its `FAV` team.
The network-secret placeholder worked without credential or proxy changes.
No Linear items or milestones were modified.

## Troubleshooting cloud network-secret injection

Inspect the selected environment's configuration and safe runtime readiness
report; do not dump the process environment or read secret files. Configured
bindings with unknown or stale readiness are not proof of injection. Record the
actual command's exit status and non-secret error, keeping headers and key
values out of logs.

| Failure | Diagnosis and next step |
| --- | --- |
| Variable missing | Check the Personal vault binding and that the selected environment receives `LINEAR_API_KEY`. Recreate/restart the environment after a reviewed configuration change if needed. |
| CLI usage/auth selection error before HTTP | Inspect installed help; remove conflicting `--workspace`, use `LINEAR_API_KEY`, and avoid login/token/config commands. A placeholder does not itself mean the key is invalid. |
| Linear rejects authentication (exit 4, HTTP 401/403) | Check injection readiness and destination binding first, then the existing key's validity and authorization. Do not expose or replace it with an unprotected key. |
| Proxy denies a destination | Check HTTP network policy and secret allowed domains for `api.linear.app`. Change policy through the cloud configuration workflow, never by bypassing the proxy. |
| Sandbox reports `connect EPERM` before reaching the proxy | Grant the command's network permission through Codex's supported permission mechanism while preserving the proxy. This is distinct from a Linear authentication error. |
| npm registry request stalls | npm may need an explicit proxy selector: `npm --proxy="$HTTPS_PROXY" ci`. Use a writable npm cache if the default cache is restricted. Do not print proxy environment values. |
| TLS, DNS, timeout, rate limit, or server error (often exit 5) | Preserve proxy and CA trust; inspect safe runtime diagnostics and retry read-only commands when appropriate. Never disable certificate verification or enable verbose HTTP logging. |
| Linear GraphQL/entity error (exit 1 or 3) | Confirm the UUID, workspace, team, permissions, and current CLI syntax. Report the actual API error rather than claiming connectivity to that entity. |

If a ready binding still fails only in the CLI, investigate whether the CLI
honors the inherited proxy and forwards the placeholder unchanged to the
allowed API host. Report a demonstrated CLI/proxy incompatibility separately
from missing secrets, rejected keys, destination restrictions, or Linear API
errors. Runtime readiness was reported as unknown during setup, but the actual
authenticated reads succeeded; no cloud configuration change was required.

## Spec Kit authority and future task projection

Repository files remain authoritative. Linear must never become the source of
requirements. Read `.specify/memory/constitution.md`,
`docs/process/sdd-playbook.md`, and the relevant roadmap, specs, plans,
decisions, and `tasks.md` before any projection. The constitution's pilot rule
projects implementation tasks; it takes precedence over the playbook's general
convention of keeping tasks out of trackers. Fava's intended mapping is:

| Linear artifact | Repository meaning |
| --- | --- |
| Linear Project | SDD epic |
| Linear milestone | Roadmap entry |
| Linear parent issue | User story |
| Linear sub-issue | Implementation task |

Task projection will be implemented separately. A future Fava-specific
synchronization skill must consume this installed CLI and enforce:

- Stable repository keys: roadmap path plus R-ID, feature directory plus US-ID,
  and feature directory plus T-ID (for example, `001-workout-summary/T014`).
  Preserve retained keys during regeneration; never reuse retired keys or use
  issue titles as identity.
- Idempotent creation/update by repository key: rerunning the same projection
  produces no duplicates or unnecessary changes. Detect ambiguous/duplicate
  keys and stop before writing.
- A reviewable dry-run before writes, showing proposed changes and drift against
  Git-owned artifacts. Link each projection to its source in Git.
- No automatic deletion, and no bidirectional requirements synchronization.
  Report retired keys and drift; resolve scope and task-definition changes in
  the repository before re-projecting them.
- Task completion driven by `tasks.md`, with Linear status reflecting verified
  task completion and applicable checks. Use one writer for status; avoid
  competing native state automation.

This integration adds no synchronization engine, Fava-specific sync skill,
tracker workflow, or application feature. It does not change the roadmap or
existing milestones.

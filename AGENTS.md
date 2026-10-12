For local Linear access, use the project-configured Linear MCP server.
Treat Linear as a projection of repository state.
Do not change requirement or task scope in Linear.

For Linear operations in Codex Cloud, use `.agents/skills/linear-cli/SKILL.md`;
do not rely on MCP availability. Run the project-installed dependency from the
repository root with `npx --no-install linear` (install with `npm ci` first).
Use `.linear.toml` defaults: workspace `clemarc`, team `FAV`.

Authenticate the cloud CLI only through the injected `LINEAR_API_KEY`; preserve
the network proxy and CA trust. Never expose credentials or authorization headers,
print environment values, run `linear auth token`, enable HTTP debug logging or
shell tracing, or persist credentials in config files or a keychain. Do not run
interactive authentication or configuration commands in Codex Cloud. These rules
override the companion skill's generic authentication and curl examples.

Read the constitution and relevant repository roadmap, specs, plans, decisions,
and `tasks.md` before projecting work. Git owns those artifacts; Linear provides
planning and verified progress visibility. Never modify Linear requirements or
task definitions independently of the repository. Task synchronization is a
separate implementation; see `docs/process/linear-integration.md` for its contract.

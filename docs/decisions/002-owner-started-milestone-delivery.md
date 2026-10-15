# ADR-002: Owner-started milestone preparation and implementation

Date: 2026-10-13. Status: proposed; adopted only after owner governance merge.

The existing single-branch delivery loop requires manually carrying feature/branch
context and treats planning in a final milestone PR as unapproved because it is
absent from main's PR base. Introduce two repository skills taking only a canonical
roadmap ID, a shared read-only resolver, feature-local execution ledger and one
Cloud coordinator. Keep Git authoritative and use the pinned CLI for Linear.

Owner merges roadmap/specification to main, reviews/merges preparation to a
registered milestone branch, then starts implementation. The coordinator may
integrate independently reviewed, signed, validated task/checkpoint PRs only to
that milestone after governance adoption. Main remains owner-only by policy.
Serialize shared state and integrations; use isolated workers where supported.
Goal mode is not advertised by the inspected runtime and is not assumed.

Constitution 2.0.0 is a major amendment because limited integration authority
replaces the blanket merge prohibition. It preserves approved requirements,
supersession, mandatory tests/native validation, signed trailers, owner review,
physical iPhone/iPad acceptance and frozen history. No application change or
R3.5 preparation is part of this amendment. #8 and #9 are merged as rechecked.

Offline promotion checks cryptographically verify the signed owner planning merge
and Git ancestry before every source commit. Live reconstruction also verifies
actual merged GitHub PRs. A ledger/trailer/branch cannot create approval. Keep
both parents and task commits. The historical R1–R3 exception is unchanged.

Limitations: deterministic checks do not assess requirement meaning; linked
semantic/native/review evidence must be inspected by the coordinator/reviewer.
All current Cloud workers publish as the same GitHub owner, so GitHub cannot
technically distinguish an agent merge from human intent. Separate app/owner
identities and owner-only main restrictions require explicit configuration;
no credentials/settings are provisioned here. Ruleset proposals and observed
settings are separate in docs/process/sdd-v2-settings.md. CLI projection mutations
are tested with synthetic clients; live read access is verified, with no R3.5
task projection or tracker writes in this governance task.

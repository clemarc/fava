# Resolver and integration measurements

Use opt-in measurements when investigating repeated verification:

```sh
python3 tools/sdd/milestone.py R3.5 --phase implement --measure --purpose diagnostic
python3 tools/sdd/integration.py R3.5 --pr NUMBER --measure --purpose integration
```

The existing helper still performs every gate and emits its usual output.
One sanitized JSON record is appended to ignored `artifacts/sdd-metrics.jsonl`,
including on a gate exception. Allowed purpose labels are `resolve`, `integration`,
`recovery`, `diagnostic`, `benchmark` and `test`. No API argument, credential,
response body, report content, path, branch or object identity enters the record.
Output failure emits a sanitized warning and preserves the actual gate result.
Without `--measure`, no measurement file is written and counters stay disabled.

| Field | Meaning |
| --- | --- |
| `invocation_id`, `purpose`, `observed_at` | Fresh invocation identity, operation label and UTC start |
| `wall_seconds`, `spans` | Total wall time and inclusive resolver/assessor/history helper call durations |
| `historical_records_visited` | Approval, task, preparation, publication, reservation and review-policy history visits |
| `historical_object_inspections` | Visits that perform inspection rather than an existing per-invocation deduplication |
| `repeated_historical_object_visits`, `repeated_historical_object_inspections` | Repeated keys within this invocation, distinguished from skipped duplicate work |
| `per_invocation_deduplications` | Existing task-proof deduplication hits; no new reuse behavior |
| `immutable_object_verifications`, `repeated_immutable_object_verifications` | GitHub commit and pinned offline signature verification attempts; repeats within each kind |
| `github_commands`, `github_duration_seconds`, `github_errors` | Shared gh-boundary command count, total duration and failed commands |
| `github_request_count`, `github_request_count_exact` | Exact request count where gh API responses expose it; null/false for opaque or failed commands |
| `github_request_count_lower_bound` | Successfully observed API pages plus one for each successful opaque command; failed transports contribute zero |
| `live_gate_refresh_seconds` | Sum of dynamic GitHub command durations in current integration assessment, excluding historical helper scopes and immutable commit requests |
| `retries`, `invocation_failed` | Automatic transport retries (currently zero) and actual invocation failure |

The shared API helper uses one request per returned page. A failed paginated
command may have sent an unknown number before failure; `gh pr view` may perform
several internal GraphQL requests. Those cases make exact request count unknown.
Do not label gh command counts as exact HTTP counts or count ordinary live
refreshes as retries. Inclusive nested span durations must not be summed as total
wall time. Live refresh measures GitHub time, not CPU parsing or the entire gate.

Counters reset per invocation. Temporary in-memory identity sets count repetitions
only; they neither skip verification nor persist object identities or acceptance
proof. The existing in-assessment deduplication and fail-closed behavior remain.
This phase does not introduce persistent immutable-proof caching.

Before considering SHA-bound reuse, collect representative successful resolver
and assessor observations with historical counts, duplicate costs, live refresh
and errors separated. Review exact immutable proof inputs, policy/target binding,
revocation and invalidation rules independently. A SHA alone cannot cache live
review, CI, branch protection, current head/target or merge permission.

A read-only diagnostic on the active R3.5 history stopped after 10.50 seconds,
15 observed GitHub API requests and six historical visits/signature checks. It
correctly failed on the existing PR #41 milestone-to-task import destination
classification. This partial invocation is not a completed-history performance
baseline or evidence of a workflow improvement; no gate was bypassed to finish it.

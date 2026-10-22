# Codex review timing and bounded recovery

Snapshot: 2026-10-22, PRs #1–#36. The [request dataset](codex-review-timing.csv)
contains all 55 observed manual review comments, result links and exclusions.

| Clean sample: 36 pairs across 20 PRs | Request to observed result |
| --- | --- |
| Mean | 5m 36s (336.11 seconds) |
| Minimum | 1m 22s |
| Maximum | 12m 39s |
| Median | 5m 03s |
| P95, nearest rank | 12m 17s |

Include an unedited request containing exactly one full SHA followed by its first
same-head immutable bot receipt or submitted bot review, with no overlapping
same-head requests. Exclude 19 requests: nine multi-SHA, one edited, five
overlapping and four without bound completion. Automatic triggers are not
standalone observations but may overlap manual requests. These figures measure
observed latency, not causal processing time or a service guarantee.

The clean sample excludes important ambiguous stalls: PR #28's original request
preceded a receipt by 36m 09s, while its retry preceded that same receipt by
1m 20s. PR #35's original request preceded a receipt by 5h 30m 59s; an edited retry
preceded it by 2m 52s. Neither proves which request caused completion. PR #36 took
8m 39s but is excluded because its request included both head and target SHAs.
Keep exclusions visible when selecting operational limits; do not treat the
clean maximum as a worst-case bound.

Recalculate the summary from the retained dataset:

```sh
python3 tools/sdd/codex_review_timing.py docs/process/codex-review-timing.csv
```

## Coordinator procedure

The helper inspects live PR head, actual request/result evidence and retained
request attempts. Default invocation is read-only:

```sh
python3 tools/sdd/codex_review.py --pr NUMBER
```

The coordinator polls once per minute while continuing independent ready work.
Use `--retry` to authorize one eligible initial request or bounded retry. The
helper never runs an unattended sleep loop, changes task state or merges a PR.
Requests contain exactly one full SHA; put target details elsewhere. Retain fresh
immutable comments; do not edit an old request to change its SHA or reuse reactions.

- Check actual same-head completion before every request. Completion still needs
  review dispositions and all applicable integration evidence.
- If no request exists, send one initial request. If a current review is marked
  running, poll without issuing duplicates.
- Allow at most one retry after an actual failed/cancelled review, or after
  20 minutes without recognized running/completed evidence. The threshold exceeds
  the observed clean maximum while leaving time for an additional attempt.
- Stop at 45 minutes from the first same-head request, including across restarts.
  A still-running review stops as blocked; it does not trigger another request.
  Exhausted retry budget also blocks. Retain the actual evidence and precise
  blocker for owner disposition. Silence never establishes unavailability or
  completion.
- Same-head request retries do not consume source correction publications. They
  also do not reset existing correction counts, the review deadline or findings.
  A changed head requires new current-head proof; an old review cannot approve it.
- After an ambiguous API write, inspect actual comments before retrying. Only
  one coordinator writes requests. A request marker supports restart recovery;
  it is not review completion or an atomic lock against concurrent writers.

Mutable activity summaries may guide scheduling but cannot prove completion.
Actual authenticated review submissions, supported immutable receipts or timely
request reactions supply the existing completion proof. Missing access, unknown
states and malformed evidence are reported without weakening integration gates.

# A1: registration-aware native scheduling pilot

The pilot is implemented but disabled. `.github/native-scheduling.json` contains
an empty `enabled_milestones` list. Activation requires an owner-reviewed target
configuration change for the selected milestone and normal signed import of the
reviewed workflow/configuration. This work changes no repository variable,
required check, ruleset, active execution record or historical checkpoint.

The owner's completed spike decision is to retain parallel native execution.
The paired observation at source `29a3c1c1bc4e0e824205f15c519356f0d1d4da8b`
compared conventional run `40177650811` with verified shared run `40177650776`:

| Architecture | Runner consumption | Elapsed | Executed tests |
| --- | --- | --- | --- |
| Existing parallel iPhone/iPad | 32.8 runner-minutes | 18m42s | 41 per family |
| Shared-build prototype | 36.9 runner-minutes | 20m05s | 41 per family |

Both passed their applicable evidence gates; this is one paired observation.
Production does not migrate to shared build-for-testing/test-without-building.
Keep the parallel matrix and its independent family acceptance gates. Do not
introduce persistent DerivedData caching or cross-commit native evidence reuse.
The completed report is `docs/experiments/native-ci-shared-build-spike.md` on the
spike branch; that branch and its experimental files remain untouched here.

The scheduler reads configuration from the event's exact target SHA, never from
the candidate head. Only same-repository `task/<milestone>/...` PRs targeting the
matching registered milestone qualify. It resolves the canonical feature and
ledger through the existing roadmap helper. Missing/uncertain evidence runs full
native validation; it never creates an acceptance exemption.

For an enabled task, a GitHub-signed source head strictly predating PR opening,
possibly followed only by signed pure automatic target imports, gets a separate
`ios-compile-feedback` job while registration remains unimported. It performs the
existing deterministic project validation and a generic iOS Simulator Xcode
build, without simulator boot or test-product sharing. The job explicitly says
that no simulator tests ran. Linux SDD/tooling checks still run normally.

The existing canonical registration must bind the actual numeric PR, branch,
task IDs and initial head at zero corrections. The scheduler reuses
`ledger.target_import` and `task_publication_progress`, pinned signatures and
ancestry. Full native begins after a signed automatic import carries the
canonical registration into the task. The source ledger alone cannot establish
registration. Any post-opening/corrective source publication runs full native,
including when registration evidence is missing or inconsistent. Existing
reservation/count/import gates still reject invalid source publication.

Native applicability remains `required`. `aggregate.validate` is unchanged:
skipping full native leaves **ci-required failed**, even if compilation feedback
passes. Deferred initial heads cannot integrate. Both full iPhone/iPad jobs,
nonzero tests, exact-head review, current-target checks and every existing
acceptance gate remain mandatory. Compilation feedback is never native proof.

The existing PR-scoped concurrency group and `pull_request` triggers remain.
Signed imports published through the approved GitHub mechanism advance the
task PR and trigger `synchronize`; do not substitute `GITHUB_TOKEN` publication,
which can suppress downstream workflows. A checkpoint PR has its own concurrency
group and cannot cancel a task run. The known registration import precedes the
qualifying native run. Later actual head/target changes still invalidate evidence.
Same-head reruns retain their event/identity and all existing retry limits;
final imported-head reruns still execute both families. Manual dispatch has no
task event context and conservatively runs full native.

This changes scheduling only. It does not allow dependent source preparation
before canonical predecessor completion and needs none of the Phase 6 sequencing
exception. Allowing a deferred head to pass ci-required, weakening registration
or correction reservations, reusing pre-import native/review results, or reducing
acceptance coverage would be governance changes and are not implemented.

## Rollout and measurement

After owner review, select a future milestone and add its exact normalized ID to
the target-side configuration through the normal reviewed/signed path. Do not
edit active R3.5 execution records or replay its completed checkpoints. Before
rollout, verify actual PR synchronization with the approved credential, full
native/review triggering after registration import, corrective-head execution,
same-head retry, and skipped/cancelled/timed-out aggregate rejection.

For each candidate and device job retain run/attempt/head, scheduling decision,
start/end, queue time, conclusion and supersession/import relationship. Measure:

- Runner time: sum started native jobs plus compilation-feedback runner time.
- Elapsed time: initial publication through eligible current-head native/review
  completion, reporting queueing and concurrent work separately.
- Defect discovery: initial source publication through the first actionable
  preflight/compiler/test diagnostic. Report the check, phase and diagnostic
  timestamp; compare matching revisions with ordinary full-native scheduling.
  A successful build proves no test-defect latency. If exact first diagnostic
  timing is unavailable, report it unavailable; label a failed-phase completion
  time only as an upper bound. Do not treat missing defects as zero latency.

Within the existing architecture, each subprocess phase now emits
`FAVA_NATIVE_PHASE` JSON with UTC observation time, phase, start/completion,
outcome and monotonic duration. The same sanitized rows are retained in
`artifacts/native-phases.log` through the existing diagnostics glob. Build/test
commands, destinations and acceptance results are unchanged. Capture dependencies,
device/destination selection, build, tests and result-summary durations separately.
Simulator boot remains included in `xcodebuild test`; report it unknown rather
than inventing an isolated boot duration. Job queue/allocation time still comes
from authoritative GitHub metadata. Missing phase completion after cancellation
is incomplete timing, not a test failure.

Report expected configured suite coverage and observed executed counts for each
family (41 each in the completed comparison). Both families and nonzero actual
tests remain mandatory; a changed reviewed suite needs its own expected count.
Retain skipped, cancelled, timed-out, superseded, unavailable and infrastructure
classifications separately. Only started jobs consume measured runner time;
compilation-only feedback has no simulator test count or acceptance result.

The supplied baseline is 86.1 superseded runner-minutes from seven started jobs,
within 395.1 native runner-minutes across 23 started device jobs. That 21.8% share
is a potential avoided-cost bound, not measured savings. Subtract compilation
feedback cost and account for other supersession causes. No active pilot run,
runner-time reduction or elapsed-time improvement is claimed before rollout.
The separate performance spike retains ownership of shared-build/test experiments;
this pilot does not modify its branch or production test-product architecture.

Rollback by removing the enabled milestone from trusted target configuration;
the scheduler then always runs the original full native workflow. Reverting this
slice also restores the original workflow condition. Never weaken required checks
to make a deferred head mergeable.

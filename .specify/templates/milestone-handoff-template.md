# Milestone owner testing and review: [ID]

State: ready-for-owner; physical acceptance pending unless linked below.
Milestone PR to main: [URL]. Exact tested revision: [full SHA].

## Automated evidence

[Latest CI/ci-required URLs, actual macOS build, simulator families/counts and
xcresult evidence, whole-milestone regression, signature and review evidence]

## Task and acceptance coverage

[Task → FR/US/acceptance scenarios → test/result matrix, including failure cases]

## Data and races

[Migration/legacy adoption, persistence/provenance failure, concurrent reads,
clear/late completion and relaunch evidence with synthetic fixtures only]

## Physical iPhone and iPad instructions

[Separate device/OS walkthroughs: install, populated/empty launch, real deliberate
HealthKit access, known workouts, successful-empty/subset, retention/relaunch,
refresh/retry, confirmed clear/cancel, unit preferences and accessibility.
Sanitized outcomes only. No real health exports/history/screenshots.]

## Accessibility and performance

[VoiceOver/Dynamic Type, both-family layout, measured performance/results or
explicit pending checks; owner device testing is not proved by simulator tests]

## Findings, limitations and Linear

[Outstanding comment links/severity/rationale/attempted fixes/owner decision,
verified tracker state and pending keys; distinguish blockers from deferred scope]

## Acceptance and freeze

[Owner-provided iPhone evidence link] / [Owner-provided iPad evidence link].
After authorized fixes and both-family acceptance, propose verified completion
metadata and freeze. Never main merge or auto-merge by an agent.

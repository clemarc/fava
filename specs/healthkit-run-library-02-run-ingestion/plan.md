# Implementation Plan: R2 Run Ingestion

Input: approved R2 spec.md (PR #3). Dependency: R1 verified source checkpoint
7bcfec6f49e142f3dc85fa99f3227201f79b636e / Actions run 38305400468, both families.

## Summary
Read all accessible running workouts through a one-shot HKSampleQuery with running
predicate, no date cutoff and HKObjectQueryNoLimit. Map complete results to Codable
source observations; deduplicate by workout UUID. Keep current-attempt state
separate from the saved last-successful collection; replace saved data only on a
complete successful result, including empty. R3 owns user read triggers and list UI.

## Technical Context
Reuse Swift 5/Xcode 26.6 and iOS/iPadOS 17+, Apple frameworks only. Main-actor
observable controller, injectable callback reader and snapshot-store protocols.
No background observers, accounts, backend, writes or extra health permissions.
Atomic protected JSON under Application Support, excluded from backups. No DB or
additional package. Missing cache means never loaded; saved [] means previously
loaded empty. Corrupt/unreadable cache produces a distinct local storage notice,
not a fabricated empty read. Failed save keeps prior saved result and exposes
failure; source result is not published as a persisted success until save succeeds.

## Constitution Check
Approved spec immutable, R1 authorization preserved, no source-of-truth change.
Snapshot is a derived observation with explicit provenance, never permission state.
Every FR maps to mandatory unit tests; R1 simulator UI regression retained. Signed
planning precedes source implementation through the narrow authorized pilot.
CLI Linear keys map stories/tasks; no projection backend. Physical HealthKit reads
remain manual acceptance. Post-design review: compliant, no unresolved unknowns.

## Structure and data flow
Fava/RunRecord.swift: Codable UUID, Date source instant, recorded duration, optional
WorkoutDistance (value plus unit). HKQuantity exposes a physical quantity without a
public original-storage-unit accessor; adapter reads its exact metre representation
and explicitly retains metre units. Presentation conversion belongs only to R3.
Fava/HealthKitWorkoutReader.swift: injectable WorkoutQueryStore, production
HKHealthStore wrapper, .running predicate and unlimited complete query.
Fava/RunSnapshotStore.swift: versioned complete JSON snapshot, atomic file write,
complete-file protection and backup exclusion; injectable directory for tests.
Fava/RunIngestion.swift: saved collection/provenance, observable six-state attempt,
overlap guard, explicit read, outcome and storage failure handling. Fresh session
restores only complete saved records, never an attempt. Backgrounding does not
invent a result; callbacks belong to the current attempt.
Fava/FavaApp.swift owns one controller and provides it to the existing view tree;
no read occurs until R3 adds deliberate navigation/refresh triggers.
FavaTests/RunIngestionTests.swift exercises synthetic HealthKit workouts, source
failures, retries, snapshots, replacement, interrupted/relaunch and exact values.
Update existing project file test membership. No new user-facing library in R2.

## Verification and delivery
Plan/tasks/analyze/Linear → test-first model/query/snapshot batches → local gates →
signed implementation → full native matrix with R1 regression → convergence and
recorded checkpoint. SC-001–004/006 synthetic fixtures; SC-005 physical read on
one iPhone and iPad remains pending. R3 starts only after applicable native and SDD
CI pass on the published R2 implementation commit.

## Complexity
One small protected JSON file; complete replacement avoids append/reconciliation
semantics. Unlimited one-shot query is the smallest API matching all-history
coverage. Large-history performance remains a device acceptance observation.

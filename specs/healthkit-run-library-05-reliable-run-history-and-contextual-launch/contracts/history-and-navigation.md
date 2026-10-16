# History and navigation contracts

## Storage boundary

T001 introduces an additive typed history store boundary while retaining the old
RunSnapshotStoring API for unchanged callers. T002 switches all callers/conformers
and tests together, then removes transitional APIs if unused. The active boundary
loads typed retained history, commits a whole history
document, and clear atomically using the same protected path. Its test doubles
support load/save/clear failure injection and inspection of committed bytes.
Load failures are distinguishable from absence. Writes are synchronous and
serialized through the MainActor model; no asynchronous write may outlive its
generation. Preserve the legacy RunSnapshot decoder for schema 1.

## Model boundary

RunIngestionModel exposes readable history, local recovery, saved observation,
current attempt, transport-active state, canRead, retryLocalLoad, requestRead and
confirmedClear. A pure merge helper builds candidates without side effects.
Complete source success and local saving outcome are separate values. canRead
requires available source, no transport in flight, and no local recovery error.
Clear remains available during a read. Duplicate or stale callbacks do nothing
except release their own transport token. Availability refresh never starts work.
During obsolete transport drain, controls explain that the previous read is
finishing; no new query begins. Local retry never invokes WorkoutReading.

## User interface boundary

| Context/action | Required behavior |
| --- | --- |
| Populated launch | Saved rows and saved-history notice first; one guarded entry read, no authorization. |
| Absent/empty launch | Setup/access and deliberate library navigation; prior empty wording differs from never-read. |
| Recovery | Local error, Retry saved history and Settings/confirmed clear; no source overwrite or automatic access. |
| Library entry/Refresh/Retry | One available read, reuse active query, retain selectable rows and exact UUID handoff. Saving-failure Retry starts a new source read. |
| Settings | One action from library; Device/Kilometres/Miles, access and Clear Local Run History. Done returns in one action from any nested access content. |
| Access | Opening content makes zero authorization requests. Explicit request delegates to existing workout-only state machine; neutral completion, cancellation, failure and unavailability remain distinct. |
| Clear confirmation | Name all local summaries/read metadata, preserved units/HealthKit workouts/permissions and possible later reimport. Separate Cancel and destructive confirm. Success dismisses settings and routes setup without a read. Failure stays in prior route and announces failure. |

History/provenance notices show latest saved observation time and returned count,
never retained count as source count. Each row exposes its last observed instant
or unknown and whether it was unobserved in the latest saved observation.
No saved observation means unknown membership, not a fabricated absence claim.
Current attempt notices never mutate these labels on failure. Empty wording:
"This read returned no accessible runs. Displayed runs were saved earlier."
Conditional guidance explains earlier choices may need changing in Health or
system Settings, then returning and Refresh; never claim denial/deletion or
promise another permission sheet. Earlier-session observations are labelled prior.

Use text/symbols and accessibility values, not color alone. Expose roles,
selected/disabled states, outcome announcements and destructive confirmation.
All notices/actions scroll and remain reachable at every Dynamic Type size on
compact iPhone/resized iPad. Reuse source-time sorting, unit conversion and selection;
no R4 content, writes to HealthKit, new permissions or background reconciliation.

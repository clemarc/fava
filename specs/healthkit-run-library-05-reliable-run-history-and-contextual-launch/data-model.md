# Retained history model

Design names describe new Swift types; approved product meanings remain in spec.md.

| Entity | Fields and validation |
| --- | --- |
| RetainedRunHistory | schemaVersion=2; runs keyed uniquely by UUID; lastObservedAtByID with optional instants; latestSavedObservation optional. Every provenance key belongs to runs. |
| SavedReadObservation | observedAt Date (optional only for genuinely untimed legacy data); returnedIDs Set<UUID>; outcome nonempty/empty derived from returnedIDs. Every returned ID belongs to runs; empty is a valid success. |
| RunRecord | Preserve UUID, startDate instant, finite nonnegative duration, optional finite nonnegative recorded distance and original unit. Missing and zero differ. Source data is never changed by display settings. |
| LocalHistoryState | absent, readable(history), recovery(error). Readable-empty is distinct from absent and recovery. Unsupported version, malformed/invalid values or read failure preserve the original document. |
| ReadAttempt | idle, loading, sourceFailure, unavailable, sourceSuccess(returnedCount, savingFailure optional). Current session only; never restore active state on launch. |
| InFlightRead | token UUID and captured history generation. Separate from visible attempt and persists in memory through successful clear until callback drains. Duplicate callbacks cannot commit twice. |
| LaunchRoute | setup when absent/readable-empty; library when populated; recovery on unreadable. Clear success selects setup. Ordinary reads do not unexpectedly replace the user's visible route. |

Schema 1: decode existing RunSnapshot unchanged, validate all records, deduplicate
UUIDs deterministically with the first record retained. R2/R3 replaced the whole
collection after each complete success, so seed latestSavedObservation and every
row time from valid capturedAt, with all saved IDs as returned membership. Saved
empty is a prior successful-empty observation, timed when capturedAt is known.
For supported older documents with absent/null capturedAt, keep observation and
per-row times unknown while retaining the prior-success/membership evidence. A
present malformed timestamp is recovery. Never use migration/launch/workout time.
Use the existing JSON numeric reference-date convention, not Unix seconds. The
migration decoder may use decodeIfPresent for omitted/null capturedAt; a present
invalid/nonfinite date is corruption. Newly accepted reads always have a clock
time. Nil load means never-read (DEC-007 supersedes DEC-001 timestamp semantics). Do not eagerly rewrite the legacy file. Schema 2
validation rejects orphan provenance, missing returned identities, invalid numeric
values and unsupported versions without treating the file as absent.

Complete read: deduplicate returned IDs deterministically, union by UUID, replace
returned summaries, keep unreturned summaries and times, set returned rows' time
to the injected clock instant and latestSavedObservation to that read. Empty
advances only the latest observation. Persist the entire candidate once, then
publish. Persistence failure discards the candidate and leaves all saved fields
unchanged; the current source-success/save-failure notice remains separate.

Clear: encode and atomically replace with a valid schema-2 empty tombstone with
no observation, provenance or legacy capture fields. There is no second legacy
file to fall back to. Once durable write succeeds, clear in-memory history and
selection, advance generation and route setup. Keep units in their existing
UserDefaults storage. Failure retains the previous file/view/route and allows
retry. The tombstone contains no run or read-history metadata.

Relaunch loads only committed history. No attempt, transport token, active access
request or route stack is persisted. Restored app data follows the same load
rules; absent app data starts setup. Backup exclusion remains best effort storage
policy, never a promise about reinstall, cloud restoration or system permissions.

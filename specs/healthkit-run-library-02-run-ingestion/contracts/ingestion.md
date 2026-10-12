# R2 contracts

WorkoutReader: availability and read(completion Result<[RunRecord], Error>).
No authorization request and no partial publication. Production query uses workout
sample type, running predicate, unlimited count, no date boundary or sort truncation.
Query failure rejects even supplied samples. Missing callback samples without
error are a malformed response and fail, rather than fabricated successful-empty.

SnapshotStore: load optional complete snapshot; save complete snapshot atomically.
Controller: requestRead is explicit, checks availability and prevents overlap;
only complete unique records persist. Failed cache save preserves previous records
and reports failure. PreviouslyLoaded flag is true on restore or new attempt and
false only for a complete current successful outcome. No stale attempt is persisted.
UI wording/actions and refresh/entry behavior are R3 contracts, not R2 changes.

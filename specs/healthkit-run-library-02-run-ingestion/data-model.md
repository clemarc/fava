# R2 data model

RunRecord: id UUID (HealthKit workout UUID), startDate Date (source instant),
duration TimeInterval (source recorded duration, including zero), optional
WorkoutDistance { value Double, unit DistanceUnit }. Unit values: metres,
kilometres, miles; nil distance is not zero. HealthKit adapter records metres.
Source values are immutable in app models; UUID determines identity, never summary.

RunSnapshot: schemaVersion 1, runs [RunRecord], capturedAt Date. Complete unique
collection only. File absent → no saved collection; saved [] → previously loaded
empty. Decode/version errors → local cache notice, no invented successful read.

IngestionState: notRequested/loading/successfulNonempty/successfulEmpty/failed/
unavailable. Stored only in memory; saved result is distinct. Each explicit attempt
gets a new UUID, allows one active reader, atomically commits on success and
preserves prior snapshot on failure/unavailability/interruption. New session starts
notRequested even with a restored collection, identified as previously loaded.

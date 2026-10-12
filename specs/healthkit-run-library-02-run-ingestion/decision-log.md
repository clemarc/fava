# R2 decisions

## DEC-001 All-history complete running query
Use workout sample type with HealthKit running predicate and unlimited query.
No date/age exclusion, separate measurement samples or background observer.
Failure rejects supplied intermediate records. UUID identifies and deduplicates.

## DEC-002 Source values and distance representation
Use workout.startDate and workout.duration directly; do not use elapsed time.
Optional totalDistance remains nil when absent and zero when recorded zero.
HKQuantity has no public original-unit accessor; its exact physical metre value
is retained with an explicit metre unit. Synthetic distance-unit values can be
retained unchanged; R3 alone owns presentation conversions.

## DEC-003 Protected derived snapshot with independent attempt state
Persist a versioned complete snapshot by atomic protected JSON replacement in
Application Support and exclude it from backup. Retain only successful results;
failed source/cache writes preserve the old saved result. Restore no loading or
permission state. Corrupt cache gets a local-storage notice, not an empty read.
No database, sync service or health-data writes are added.

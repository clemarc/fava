# R2 research

- HKSampleQuery plus HKQuery.predicateForWorkouts(with: .running) and
  HKObjectQueryNoLimit retrieves the specified classification and full history.
  No anchored/background query or date predicate is needed for explicit snapshots.
- HKWorkout.uuid/startDate/duration/totalDistance preserve source identity and
  recorded values; end-start is deliberately not used for duration. HKQuantity
  converts compatible physical distance to explicitly recorded metres; it has no
  public accessor for an original stored unit. No separate distance samples needed.
- An atomic versioned JSON file is sufficient for a complete snapshot, including
  empty. File protection and backup exclusion keep health-derived data local.
  Alternatives: Core Data and ongoing anchored reconciliation add unapproved scope.
- A main-actor guard blocks a second read before callbacks. No loading state is
  persisted. A failed source/cache operation preserves the last saved collection.

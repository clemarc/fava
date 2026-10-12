# R1 data model

HealthAccessAvailability: available/unavailable, evaluated before each request.
HealthAccessState: idle/requesting/completed/failed/cancelled/unavailable.
HealthAccessOutcome: completed/failed/cancelled from the system callback only.
Request: no persisted state, workouts or permission values. Fresh model starts
idle or unavailable; temporary backgrounding does not initiate another operation.
All state transitions run on the main actor. Active request → exactly one terminal
outcome; only explicit actions enter requesting. Retry rechecks availability.

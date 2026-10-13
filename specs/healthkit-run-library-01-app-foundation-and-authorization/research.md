# R1 research

- Decision: minimum iOS/iPadOS 17, universal target. Rationale: iPad HealthKit support
  and native SwiftUI APIs; older iPad environments cannot meet the same capability.
  Alternative: iOS-only support rejected by the approved device-family requirement.
- Decision: model the observable request, never read authorization. HKHealthStore
  request success cannot establish permission. Alternatives: authorizationStatus
  or empty-read inference rejected by FR-007 and FR-011.
- Decision: injectable store protocol and main-actor state controller. Rationale:
  synchronous overlap guard with controlled asynchronous completions in tests.
  Alternative: architecture/dependency libraries unnecessary for this scope.
- Decision: checked-in Xcode project, shared unit/UI test scheme, native CI on both
  families. Rationale: no generator runtime dependency; actual Apple compilation
  is the gate. Linux cannot substantiate Apple API compile or system permissions.

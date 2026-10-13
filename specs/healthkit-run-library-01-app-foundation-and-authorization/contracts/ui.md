# R1 UI and adapter contracts

Initial screen identifies Fava and its purpose, explains workout-record read use,
and offers Request HealthKit access plus Run library. No automatic request.
Request control disabled while requesting or unavailable. Outcome messages:
completed: Request completed. Readable workouts depend on your Health settings.
failed: HealthKit request failed. You can try again.
cancelled: Request not completed
unavailable: HealthKit is unavailable on this device.
Retry remains a deliberate action; no promise of a new system sheet.
Library foundation says where runs will be browsed and offers native back.
Texts wrap and scroll at all Dynamic Type sizes; standard controls expose roles,
names, enabled states and progress. Outcome updates announce through UIKit.
Store contract: availability + request(read: workoutType only, share: empty).
No reads, writes, accounts or network. Error-user-canceled is the only cancellation
mapping. No read-permission state is stored or inferred.

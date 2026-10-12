# R3 presentation contracts

Initial/access screen → Run library: show saved snapshot immediately and request
one R2 read if available. Repeated open while active reuses attempt; view resize
or recompute requests no read. Refresh and Retry disabled while loading/unavailable.
Every state keeps one-action native back to R1. No read action authorizes HealthKit.

Not requested: no read requested. Loading: loading running workouts.
Successful nonempty: current complete runs loaded. Successful empty: no running
workouts were returned by this read (no denied/history claim).
Failed: running workouts could not be loaded; retry when available.
Unavailable: HealthKit unavailable; no unusable request. Saved rows/empty snapshot
remain labeled Previously loaded during active/unsuccessful attempts. Cache errors
carry R2's separate local notice. Selection hands off exact UUID, marks selected
row and announces selection; no R4 screen/content.

Each row: local start date/time, recorded duration, available distance with km/mi,
or Distance unavailable. Current locale/time zone and two-decimal rounding only;
no source value, date/order, ID or nil/zero changes. Unit preference never reads.
Settings sheet: Device initially selected, Kilometres/Miles alternatives, selected
state announced, choice retained locally, Done returns in one action.

# R3 decisions

## DEC-001 Chronological native list and exact selection
Use a SwiftUI List with vertically wrapped summaries, Date newest-first and UUID
stable tie order. Selection records/hands off source UUID and selected row state;
no R4 view, summary-derived identity or silent cap is introduced.

## DEC-002 Explicit entry reads and independent provenance
Request R2 ingestion once from deliberate root-to-library navigation and explicit
Refresh/Retry, never view body/onAppear. Preserve saved rows and saved-empty meaning
beside current notices. Settings uses a modal sheet over the mounted destination;
changing/dismissing settings is not another entry. Native back remains one action.

## DEC-003 Retained presentation-only distance mode
Use UserDefaults for Device/Kilometres/Miles; Device resolves current locale
measurement-system preference, fixed choices override it. Two-decimal visible
rounding, explicit units and missing indicator. Dates/durations/source values and
IDs remain unchanged; preference changes never request ingestion.

## DEC-004 Deterministic simulator fixtures with isolated storage
DEBUG-only providers and separate cache/defaults sessions drive CI, including real
local snapshot relaunch. Existing R1 health fixtures also use synthetic reads in
R3 to avoid real HealthKit data in public tests. Release never selects fixtures.
Physical HealthKit, VoiceOver and device acceptance remain separate evidence.

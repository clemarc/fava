# R3 validation guide

Linux: deterministic SDD/tooling and validator/builder unittest discovery.
macOS Xcode 26.6: python3 .github/checks/native.py test; repeat --family iPad.
Expect all R1/R2 regression plus RunLibraryTests and RunLibraryUITests.
Synthetic fixtures verify newest-first/stable ties/full history, current locale,
duration and converted distances, zero/nil, exact selection, unit persistence,
entry/refresh/retry/overlap, saved rows and empty provenance during refresh,
successful empty replacement and relaunch with retained data. UI tests cover
all Dynamic Type library action reachability and largest-size settings, both families.

Physical acceptance remains pending: authorized HealthKit end-to-end on one iPhone
and iPad, populated/empty/read failure where feasible, saved refresh/relaunch,
offline browsing/reading, source values/units, selection, all Dynamic Type sizes,
VoiceOver names/roles/enabled/selected/outcome announcements, resized iPad and launch
measurements carried from R1. Record only sanitized outcome and device/OS, no real
history or screenshots in public artifacts. R4 detail is deliberately absent.

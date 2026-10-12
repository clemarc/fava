# R2 validation

Run python3 .github/checks/sdd.py and python3 .github/checks/tooling.py on Linux;
run existing validator/commit-builder unittest discovery. On Xcode 26.6 macOS run
python3 .github/checks/native.py test and --family iPad. Expect R1 regression plus
RunIngestionTests. Verify recent/multi-year and mixed-activity synthetic workouts,
duplicate UUIDs, missing/zero distance, recorded-vs-elapsed duration, ten repeated
reads, overlap/failure/retry/unavailable, saved empty/nonempty, atomic replacement,
cache failure and relaunch after interrupted refresh. Public fixtures synthetic.

Manual: one iPhone/iPad with controlled accessible running history, deliberate
R1 access, an explicit read once R3 supplies its trigger, offline read, decline/no
accessible results, large history, older records and missing values. Record only
sanitized outcome/device/OS, never real records. NOT performed in this task.

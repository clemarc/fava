# R1 validation guide

On Linux: python3 .github/checks/sdd.py; python3 .github/checks/tooling.py;
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .github/checks -p 'test_*.py';
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/github -p 'test_*.py'.
On macOS with Xcode 26.6: python3 .github/checks/native.py test; repeat with
--family iPad. Expect build success and nonzero passing unit/UI tests.

Physical checks pending: install/sign for one iPhone and iPad with iOS 17+;
launch 20 times per family and record sanitized timing; navigate offline;
request workout-only read access deliberately; allow/decline/re-request, observe
neutral completion, cancel where system reports it; background/return; test
VoiceOver announcements and every Dynamic Type size in compact/resized layouts.
Record sanitized outcome/device/OS only. These steps have NOT been performed.

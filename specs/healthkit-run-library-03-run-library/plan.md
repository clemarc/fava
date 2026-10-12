# Implementation Plan: R3 Run Library

Input: approved R3 specification (PR #3); R2 checkpoint
5c65aa2f4cfdd9335046f7061702e20872d9921f / run 38307744070 passed all mandatory gates.
R1/R2 contracts remain unchanged; same draft implementation PR #7.

## Summary and technical context
Reuse iOS/iPadOS 17+, Swift 5/Xcode 26.6, SwiftUI and Apple frameworks only.
A native List presents R2's complete snapshot with newest-first Date sorting and
UUID tie-breaking. A separate notice describes current attempt state; previously
loaded provenance remains explicit during active/failed/unavailable refreshes.
Root navigation deliberately triggers one read per destination entry; recomputing
views or opening/dismissing settings does not count as entering the destination.
Settings is a modal native sheet over the mounted library, with one Done action.
Refresh/retry call R2 only; no automatic authorization. R1 remains accessible by
native back in every state. Source availability updates on foreground return.

## Constitution Check
Native/local-first/HealthKit authoritative; derived display never mutates source.
Mandatory unit and UI tests use synthetic values and cover failure and accessibility.
No new dependency, services, permissions, background updates or R4 screen.
Approved spec immutable; append DEC rationale, stable task/Linear identity.
Signed preceding plan commit and implementation trailers; latest native matrix
and aggregate required. Physical/device acceptance remains separately pending.
Post-design review: compliant; no technical unknowns or material product decisions.

## Structure
Fava/RunLibraryPresentation.swift: date/recorded-duration/distance formatting,
chronological rows, distinct attempt notice, selection UUID handoff.
Fava/DistanceSettings.swift: Device/Kilometres/Miles, persisted UserDefaults mode;
Device resolves current Locale.measurementSystem each presentation, metric → km,
US/UK → miles. Injectable device resolver verifies changes independent of storage.
Available distance converts from source units, rounded to 2 fractional digits;
missing values explicitly unavailable, zeros retained. No inferred measurements.
Fava/RunLibraryView.swift: native adaptive scrollable List, wrapped vertical row
summaries and named refresh/retry actions, saved-empty/nonempty provenance, errors,
progress, selected state and VoiceOver announcements. Settings sheet with three
standard accessible buttons and current selection, one-action Done.
Fava/RootView.swift: explicit library destination action triggers R2 read once;
active attempts are reused. Existing root access and back navigation retained.
Fava/FavaApp.swift: lifetime R2 model, unit settings and selection; DEBUG-only
synthetic library provider and isolated cache/defaults fixtures for CI. Release
always real HealthKit/local snapshot. UI fixture relaunch preserves its own saved
cache and settings, without touching production health-derived storage.
Fava/SyntheticLibraryFixtures.swift: deterministic DEBUG running records/outcomes.
FavaTests/RunLibraryTests.swift and FavaUITests/RunLibraryUITests.swift verify
presentation, identities, preferences, read triggers, all read-state/provenance
combinations, persistence, large history and accessible UI behavior. Keep R1/R2 tests.

## Verification and delivery
Tests before corresponding implementation. Local deterministic gates and review;
then signed source publication, CI on both families, actual logs/xcresult counts,
converge, task/Linear evidence, final cross-milestone review and signed record.
All 17 FRs mapped to tasks. SC-001/002/003/005/007 use synthetic unit/UI fixtures;
SC-004 actual VoiceOver/resized-device walkthrough and SC-006 physical end-to-end
remain pending. No claims of device access from simulator tests. R4 selection is
an observable UUID handoff plus row selected state, never a detail screen.

## Complexity
One list and one settings sheet. No filters, search, custom sorting, new summary
fields or navigation abstraction beyond SwiftUI's destination state.

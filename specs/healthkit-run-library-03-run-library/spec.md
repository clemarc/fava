# Feature Specification: Run Library

**Feature Branch**: `healthkit-run-library-01-app-foundation-and-authorization` (shared R1–R3 specification delivery branch)

**Created**: 2026-10-12

**Status**: Draft

**Input**: Prepare the approved Run Library milestone. Parent roadmap: specs/healthkit-run-library/roadmap.md → entry R3

**Component**: Personal iPhone and iPad application.

**Supersedes**: None; first specification for R3.

Scope boundary: R3 turns R1's navigable run-library foundation into a chronological list using R2's complete ingested or previously loaded run collection. It owns readable basic summaries, a distance-unit preference in an app settings screen, user-facing read triggers, loading/empty/failure/unavailable presentations, retry, and identity-preserving selection for later detail navigation. R1 retains installation and deliberate HealthKit authorization; R2 retains eligibility, complete read outcomes, uniqueness, summary source values, and local saved-result retention. R4 owns the individual run-detail screen. Search, filters, custom sorting, new workout measurements, analytics, automatic background updates, ongoing source-change reconciliation, health-data writes, accounts, cloud services, iCloud sync, and sharing are outside R3.

## Clarifications

### Session 2026-10-12

- Q: When should opening the run library trigger a fresh HealthKit read? → A: Show saved runs immediately, then read on each library entry; also allow manual refresh.
- Q: Which distance units should the run library display? → A: Device-preferred kilometres or miles by default, with an app settings screen to choose Device, Kilometres, or Miles.
- Q: How should the library show saved runs while refreshing or after a read fails? → A: Keep saved runs visible, with a loading or failure notice and retry when available.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse readable run summaries (Priority: P1)

**Requirements**: FR-001, FR-002, FR-003, FR-004, FR-011, FR-012.

As a person looking for a run, I want to browse my running history in chronological order with readable dates, durations, and available distances, so I can distinguish the run I want without needing detailed analysis.

**Why this priority**: Browsing is the visible value of the completed foundation and ingestion milestones.

**Independent Test**: Supply synthetic R2 results in scrambled order with absent and zero distances, same-time distinct identities, and multi-year history. Inspect list content, ordering, accessibility, and reachability on both device families without real HealthKit or R4 detail implementation.

**Acceptance Scenarios**:

1. **Given** a complete nonempty R2 collection, **When** the person opens the library, **Then** there is one row per source workout identity, ordered by workout start instant with the newest first, and all runs remain reachable by scrolling.
2. **Given** a run with a source start date/time, recorded duration, and available distance, **When** its row is presented, **Then** those values appear with understandable formatting and a distance unit, without pace, calories, or fabricated measurements.
3. **Given** a run with absent distance and a different run with recorded zero distance, **When** both rows are presented, **Then** missing distance is visibly unavailable while recorded zero is shown as zero with its unit.
4. **Given** distinct source identities with identical start instants or identical summaries, **When** the list is presented repeatedly from the same collection, **Then** both runs remain separate and their tied ordering is stable.
5. **Given** compact iPhone or resized iPad layouts at any Dynamic Type size, including accessibility sizes, **When** the person browses with or without VoiceOver, **Then** every row's summary and action remains readable and reachable, with no clipped or overlapping content; scrolling is permitted.
6. **Given** the device's current date/time preferences or time zone change, **When** the same collection is presented, **Then** labels use those current preferences without altering source start instants or chronological order.
7. **Given** a previously loaded collection and no network connection, **When** the person browses rows, selects a run, uses settings, or returns to the initial/access experience, **Then** those actions remain usable without an account or backend; any locally available HealthKit read follows the usual result rules.

---

### User Story 2 - Understand loading, empty, and unsuccessful reads (Priority: P1)

**Requirements**: FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014.

As a person opening or updating my run library, I want to understand whether Fava is loading runs, has completed an empty read, or could not complete a read, so I can take an appropriate next action without being told an unsupported permission status.

**Why this priority**: Honest state presentation makes a saved or currently readable collection useful when access or reads are limited.

**Independent Test**: Supply each R2 outcome with no saved result, a saved nonempty result, and a saved empty result. Exercise read initiation, refresh, retry, repeated activation, relaunch, and navigation independently of actual HealthKit and R4.

**Acceptance Scenarios**:

1. **Given** no saved result and no active read, **When** the person enters the library while HealthKit is available, **Then** one fresh R2 read begins, loading is conveyed without first claiming successful-empty or granted/denied permission, and return navigation remains available.
2. **Given** a read is active, **When** the person views the library or repeats its read action, **Then** loading is conveyed, no concurrent read begins, and return navigation remains available.
3. **Given** the latest read completes successfully with no eligible accessible runs, **When** the library displays the result, **Then** it shows a neutral successful-empty presentation, offers the defined read action and a route to R1's deliberate access experience, and does not claim the person has no recorded history or denied permission.
4. **Given** a read fails and no saved collection exists, **When** the library shows the outcome, **Then** it displays a readable read-failure message and a retry action, without calling it empty or denied permission.
5. **Given** HealthKit is unavailable, **When** the library shows the outcome, **Then** it explains source unavailability rather than successful-empty or authorization failure, prevents unusable read initiation, and preserves return navigation.
6. **Given** a failed read and HealthKit is available, **When** the person chooses retry, **Then** exactly one R2 attempt begins and its eventual outcome replaces the current attempt state without prompting for permission automatically.
7. **Given** a saved nonempty or empty result, **When** Fava is relaunched and the library is opened, **Then** the saved result is identified as previously loaded, no stale loading state is restored, and no current read-permission choice is asserted.
8. **Given** a saved nonempty result, **When** a later read completes successfully with an empty result, **Then** old rows are removed and the successful-empty result replaces the saved collection; the prior runs are not appended to it.
9. **Given** the person returns from the library to the access experience, **When** they deliberately request access, **Then** R1's request-completion, error, and cancellation behavior is preserved and not presented as a completed ingestion result.
10. **Given** a saved nonempty or empty result and HealthKit is available, **When** the person enters the library, **Then** that previously loaded result appears without waiting for a new read and one fresh R2 read begins; the saved result is not represented as that attempt's completed outcome.
11. **Given** the library is visible and no read is active, **When** the person chooses Refresh, **Then** one fresh R2 read begins using all accessible running history without automatically requesting permission.
12. **Given** a read remains active, **When** the person returns to the library or chooses Refresh again, **Then** the existing attempt continues and no additional concurrent read begins. After that attempt finishes, a later library entry starts one new read when HealthKit is available.
13. **Given** a saved collection is available, **When** a refresh is loading, fails, or finds HealthKit unavailable, **Then** previously loaded rows remain visible, browsable, and selectable with a separate loading, failure, or unavailability notice. Failed refresh offers retry when HealthKit is available; the saved result never implies that the newer attempt succeeded.
14. **Given** the saved collection is empty, **When** a refresh is loading, fails, or finds HealthKit unavailable, **Then** the library identifies the empty collection as previously loaded and shows the new attempt's distinct notice rather than claiming a new successful-empty read.

---

### User Story 3 - Select the intended run (Priority: P2)

**Requirements**: FR-002, FR-011, FR-015.

As a person who has identified a run, I want selection to refer to that exact workout, so later detail navigation does not open another run with a similar date or summary.

**Why this priority**: Selection establishes R4's identity handoff without implementing its detail presentation in R3.

**Independent Test**: Supply synthetic rows with matching summaries and capture selected identity at the detail-navigation handoff. Confirm source identity rather than list position or summary text identifies the selection; R4's detailed view is not a prerequisite.

**Acceptance Scenarios**:

1. **Given** a run row in the completed or previously loaded collection, **When** the person selects it, **Then** the identity handed off for later detail navigation is exactly that row's HealthKit workout identity.
2. **Given** two rows have identical dates and summaries, **When** either is selected, **Then** each selection produces its own distinct source identity rather than a guessed match or row index.
3. **Given** VoiceOver is enabled, **When** the person discovers and activates a row, **Then** its summary identifies the intended run and the same source identity is selected as with visual interaction.

---

### User Story 4 - Choose distance display units (Priority: P2)

**Requirements**: FR-004, FR-011, FR-016, FR-017.

As a person browsing my runs, I want an app settings screen where I can follow my device's distance units or choose kilometres or miles, so summaries use units I understand.

**Why this priority**: A visible, persistent preference supports the owner's requested control over basic summary formatting.

**Independent Test**: Supply synthetic distance values and controlled device unit preferences. Open settings from the library, choose each option, relaunch, and inspect formatting without reading new workouts or implementing other settings.

**Acceptance Scenarios**:

1. **Given** no prior distance-unit choice, **When** the person opens the app settings screen from the library, **Then** Device is selected and library distances follow the device's current preferred kilometres or miles; Kilometres and Miles are also selectable.
2. **Given** a saved or completed collection, **When** the person chooses Kilometres or Miles, **Then** its displayed distances are converted to that unit without changing source values, identities, dates, duration, ordering, or missing-value status. Changing the preference itself does not initiate a read; later library entry follows the normal entry-read rule.
3. **Given** a saved unit preference, **When** Fava is relaunched or the device's distance preference changes, **Then** the app retains its selected mode: fixed Kilometres/Miles stay fixed, while Device follows the device's current preference.
4. **Given** VoiceOver or any Dynamic Type size, **When** the person opens settings, discovers the selected mode, changes it, and returns to the library, **Then** the controls, selected state, and return action remain readable, operable, and reachable; returning to the library takes one navigation action.

### Edge Cases

- Never-read, saved-empty, loading, newly successful-empty, failed, and unavailable are different presentations; an absent collection does not prove an empty successful read.
- A saved collection can be useful across launches but does not establish current source visibility or read permission.
- Loading, failed, and unavailable refreshes keep saved rows usable with a separate current-attempt notice. A saved-empty collection also retains its prior-result meaning during an unsuccessful or unfinished refresh.
- A new complete read result replaces the prior collection; intermediate records never appear as a successfully loaded list.
- Missing distance uses a clear unavailable indicator. Zero distance and zero recorded duration are not replaced with fabricated nonzero values.
- Same-time distinct runs remain distinct and stable in order; multi-year history is reachable without a silent row cap.
- Current locale/time-zone labels can change without changing source identities, source instants, or chronological order.
- Distance-unit changes affect display only. A recorded zero remains zero in every unit; absent distance remains unavailable. Fixed app unit modes override device preferences, while Device mode follows them across launches.
- Backgrounding or termination cannot turn a loading attempt into a completed empty result. Relaunch can restore a saved collection, but never a stale loading indicator.
- A library entry means navigating to the destination or opening it after a fresh launch; recomputing or resizing the visible screen is not another entry. Launching into another screen does not trigger a library read, and repeated entries while a read is active reuse that attempt.
- Request completion, declined read access, technical read failure, and system-reported authorization cancellation must not be conflated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The library MUST be reachable through R1's navigation and show R2's complete latest successful collection or its explicitly previously loaded saved collection, with one row per source identity and no silent truncation. Acceptance: US1 scenario 1; US2 scenarios 7 and 8.
- **FR-002**: Rows MUST be ordered newest-first by source workout start instant. Equal-start-time identities MUST remain separate with deterministic, stable ordering for the same collection. Sorting MUST NOT depend on formatted date text. Acceptance: US1 scenarios 1, 4, and 6; US3 scenario 2.
- **FR-003**: Each row MUST show start date/time and recorded duration from R2, plus distance when available. It MUST NOT substitute elapsed or inferred moving time, invent source values, or add richer measurements. Acceptance: US1 scenarios 2 and 3.
- **FR-004**: Date/time labels MUST follow current device locale, clock, and time-zone preferences. Distance display MUST default to Device mode using the device's current preferred kilometres or miles, with app settings overrides for Kilometres and Miles. Display conversion MUST preserve the source physical distance, subject only to visible rounding, and MUST NOT modify R2's saved values. A unit MUST accompany numeric distance, and absent distance MUST be clearly unavailable rather than zero. Acceptance: US1 scenarios 2, 3, and 6; US4 scenarios 1–3.
- **FR-005**: On each library entry while HealthKit is available, Fava MUST show any previously loaded saved result without waiting for a new read and request one fresh R2 ingestion attempt. Without a saved result, it MUST show loading rather than successful-empty. The library MUST also offer an explicitly labelled Refresh action while HealthKit is available and no read is active. Entry means navigating to the destination or opening it after a fresh launch, not resizing or recomputing an already visible screen. Active attempts MUST be reused rather than overlapped. No entry, refresh, or retry may automatically initiate HealthKit authorization. Acceptance: US2 scenarios 1, 2, and 10–12.
- **FR-006**: The library MUST distinguish not-requested, loading, successful-nonempty, successful-empty, failed, and unavailable attempt outcomes, separately from whether a previously loaded saved result exists. Acceptance: US2 scenarios 1–8.
- **FR-007**: A successful-empty presentation MUST describe the read result neutrally, offer the defined read action and navigation to R1's deliberate access experience, and avoid claims about read denial or the person's entire recorded history. Acceptance: US2 scenario 3.
- **FR-008**: A failed read MUST display a readable read-failure explanation and offer an explicit retry when HealthKit is available. Unavailability MUST have a distinct explanation, prevent unusable read initiation, and preserve navigation. Acceptance: US2 scenarios 4–6.
- **FR-009**: During loading, failed, or unavailable reads, the library MUST keep previously loaded saved rows visible, browsable, and selectable and display the current attempt's separate loading, failure, or unavailability notice. A failed read MUST offer retry when HealthKit is available. A saved-empty collection MUST likewise be identified as previously loaded, separately from the current attempt's notice. Saved results MUST NOT imply that the newer attempt succeeded or that current read access is available. Acceptance: US2 scenarios 10, 13, and 14; US3 scenario 1.
- **FR-010**: Repeated library entries or read/refresh/retry actions while loading MUST NOT create concurrent R2 reads. Refresh and retry MUST communicate that initiation is unavailable during the active attempt. Navigation back to the initial/access experience MUST remain usable in every library state. Acceptance: US2 scenarios 2, 5, 6, 9, and 12.
- **FR-011**: App-owned row summaries, selection, read/refresh/retry actions, state messages, and distance-unit settings MUST extend R1's VoiceOver and all-Dynamic-Type accessibility baseline to the library on compact iPhone and resized iPad layouts. Accessible names, roles, enabled and selected states, and loading/outcome changes MUST be conveyed, with readable content and reachable actions without clipping or overlap; scrolling is permitted. Acceptance: US1 scenario 5; US3 scenario 3; US4 scenario 4.
- **FR-012**: Browsing a saved collection, navigation, and requesting an available local HealthKit read MUST NOT require an account, backend service, or network connection. The library MUST reuse R1's deliberate authorization flow and R2's identities/outcomes rather than deriving permission state from request completion, empty reads, or saved records. Acceptance: US1 scenario 7; US2 scenarios 3, 7, and 9.
- **FR-013**: Every complete successful read MUST replace the presented saved collection, including removing prior rows when the new result is successful-empty. Failed or active attempt records MUST NOT become a successfully loaded list. Acceptance: US2 scenario 8 and complete-result edge cases.
- **FR-014**: Relaunch MUST restore the saved collection according to R2 and identify it as previously loaded, without restoring stale loading or asserting current source visibility. Returning from background MUST preserve usable navigation and reflect any actual read outcome. Acceptance: US2 scenario 7 and interrupted-read edge cases.
- **FR-015**: Selecting a row MUST identify that exact HealthKit workout for later detail navigation, independent of formatted summaries and row positions. R3 MUST NOT require or implement R4's run-detail content; its identity handoff MUST be independently testable. Acceptance: US3 scenarios 1–3.
- **FR-016**: The person MUST be able to reach an app settings screen from the library, select Device, Kilometres, or Miles as the distance-unit mode, identify the currently selected mode, and return to the library in one navigation action. Device MUST be the initial default. Only this distance-unit setting is required by R3; other settings are outside its scope. Acceptance: US4 scenarios 1 and 4.
- **FR-017**: Fava MUST retain the selected distance-unit mode locally across launches. Fixed Kilometres/Miles modes MUST override the device preference; Device mode MUST follow its current preference. Changing the setting itself MUST reformat available rows without triggering ingestion or changing source values, identities, dates, durations, ordering, or missing-value status. Acceptance: US4 scenarios 2 and 3.

### Key Entities

- **Library Row**: A presentation of one R2 run, retaining its HealthKit workout identity and displaying its source start date/time, recorded duration, and optional distance.
- **Library Presentation**: A complete latest-successful or previously loaded saved collection together with a separate current read-attempt outcome. A saved empty collection is distinguishable from never completing a read.
- **Run Selection**: The exact source workout identity selected for a later detail-navigation handoff; no detailed measurements or R4 screen are introduced.
- **Distance-Unit Preference**: A locally retained presentation choice of Device, Kilometres, or Miles; Device resolves to the device's current preferred distance unit. It changes labels and conversions, not the saved HealthKit observations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Across synthetic mixed-order, multi-year, duplicate-delivery, and same-time fixtures, 100% of R2's unique identities appear once, all remain reachable, ordering is newest-first and stable for ties, and selection returns the exact selected identity.
- **SC-002**: Every summary fixture displays the source start instant in current device date/time preferences, source recorded duration, and available distance under Device, Kilometres, and Miles modes. Displayed converted values differ from the exact physical-distance conversion by no more than half the smallest displayed increment. Missing and zero distance are distinguishable in 100% of applicable fixtures, and changing units leaves source values and identities unchanged.
- **SC-003**: Across never-read, saved-empty, loading, nonempty, empty, failed, unavailable, relaunch, and refresh fixtures, all defined presentations convey their actual read/result provenance, no concurrent read begins, and no unsupported read-permission claim appears. Every available-source entry or explicit Refresh with no active attempt requests exactly one fresh read; saved results are shown before waiting for completion. Saved rows remain visible and selectable throughout loading, failure, and unavailability with a separate current-attempt notice and retry when available. Resizing or recomputing the visible screen requests no extra read.
- **SC-004**: On compact iPhone and resized iPad layouts at all system Dynamic Type sizes, every app-owned row, message, action, and distance-unit setting remains readable/reachable with no clipped or overlapping content. VoiceOver walkthroughs can discover and select the intended row, request a read/retry, understand loading/outcomes, choose and identify the unit mode, and use return navigation; automated accessibility/layout checks supplement device walkthroughs.
- **SC-005**: In every library read state, return to the initial/access experience requires no more than one app navigation action; returning from app settings to the library also takes one navigation action. In a failed state with HealthKit available, one retry action begins one new read without initiating permission automatically.
- **SC-006**: On one supported iPhone and one supported iPad, a sanitized end-to-end demonstration covers R1's deliberate access flow, an R2 result, and the corresponding R3 library state and identity selection. Synthetic automated tests independently cover library presentation; physical HealthKit evidence supplements them and is not replaced by simulator fixtures.
- **SC-007**: Every unit-preference fixture starts in Device mode without a prior choice, preserves a chosen mode across relaunch, and follows later device-unit changes only in Device mode. Unit-setting changes request zero new ingestion operations and preserve every source identity and saved summary value.

## Assumptions

- R3 depends directly on [R2](../healthkit-run-library-02-run-ingestion/spec.md) and transitively on [R1](../healthkit-run-library-01-app-foundation-and-authorization/spec.md). R2 reads all accessible running history and locally saves its last successful collection across launches.
- R1's destination is a neutral foundation when only R1 is delivered; R3 adds the populated and read-state presentations at the same destination without rewriting R1's authorization contract.
- Newest-first is the standard chronological browsing default; custom sorting remains deferred. Stable ties do not merge source identities.
- R2 provides start instants, recorded duration, and available distance with units. R3 owns display formatting, not source-value inference, eligibility, read authorization, or deduplication logic.
- The owner requested an app settings screen as part of distance display. Device is the default, and fixed unit overrides are ordinary retained presentation preferences; no other settings, custom sorting, additional measurements, or HealthKit permissions are added.
- Each library-entry-triggered read is a foreground response to deliberate navigation, not automatic background observation or authorization. Saved-result presence never proves current read access, and entry reads reuse an already active attempt.
- Supported OS versions and implementation choices remain for planning. R4's detailed screen is not an R3 prerequisite; a controlled selection consumer can verify the identity handoff.
- Automated tests and public evidence use synthetic records only; physical-device evidence records sanitized outcomes and device/OS versions.

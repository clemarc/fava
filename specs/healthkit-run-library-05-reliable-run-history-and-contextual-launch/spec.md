# Feature Specification: Reliable Run History and Contextual Launch

**Feature Branch**: `001-reliable-run-history`

**Created**: 2026-10-13

**Status**: Draft

**Input**: User description: "r3.5". Parent roadmap: specs/healthkit-run-library/roadmap.md → entry R3.5

**Component**: Personal iPhone and iPad application.

Supersedes: specs/healthkit-run-library-02-run-ingestion and specs/healthkit-run-library-03-run-library and specs/healthkit-run-library-01-app-foundation-and-authorization, limited to the qualified clauses below.

Scope boundary: R3.5 changes startup destination, local retention of imported runs, read-result provenance, recovery guidance, and confirmed local clearing. It reuses R1's deliberate workout-only access flow, R2's complete source reads and identities, and R3's library and distance settings. It is independently usable before R4. Run detail, visual-identity redesign, Home/dashboard analytics, search/filter/custom sorting, richer measurements, automatic background/edit/deletion reconciliation, workout writes, new health permissions, accounts, iCloud, backend services, sharing, and AI remain outside this slice.

### Controlled supersession

Requirement identifiers below are local to R3.5. Predecessor identifiers in this section are qualified by milestone and linked source specification; historical files remain untouched.

- [R2](../healthkit-run-library-02-run-ingestion/spec.md): replaces FR-013's complete saved-collection replacement on every successful read, including US2 scenarios 6–7 and associated empty-replacement criteria. Imported identities absent from later reads are retained; the latest complete read remains a separate observation. Eligibility, complete-result boundaries, successful-empty outcomes and prohibition on permission inference remain in force.
- [R3](../healthkit-run-library-03-run-library/spec.md): replaces FR-001's restriction to the latest successful/saved collection and FR-013's complete replacement/removal rule, including US2 scenario 8 and related criteria/fixtures. FR-006–FR-009 and FR-014 are extended to describe retained history separately from the latest read and per-run last observation. FR-005's one-read-per-library-entry rule and FR-010's concurrency protection remain. FR-010's initial/access return path becomes library → Settings, with deliberate access reachable there. Formatting, units, accessibility and exact selection identity remain in force.
- [R1](../healthkit-run-library-01-app-foundation-and-authorization/spec.md): qualifies FR-002's initial-screen access-action placement and FR-003's initial-screen return path for returning launches with saved runs: the library is the initial destination and Settings leads to deliberate access. First/no-saved-run launch retains setup/access. Authorization semantics and permissions are unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Return directly to useful runs (Priority: P1)

**Requirements**: FR-001, FR-002, FR-003, FR-004, FR-014, FR-015, FR-016, FR-017, FR-018.

As a returning person, I want Fava to open my saved run library without repeating setup, while keeping access and settings available when needed.

**Why this priority**: Saved history should be immediately useful even when a new read is slow or unavailable.

**Independent Test**: Launch with synthetic populated, empty, absent, unreadable and older saved data on each device family. Observe destination and navigation before completing any source read.

**Acceptance Scenarios**:

1. **Given** at least one saved run, **When** Fava launches, **Then** the library is the initial destination, saved rows appear without waiting for a read, and they are identified as previously imported.
2. **Given** first installation, saved-empty history or successfully cleared history, **When** Fava launches, **Then** setup explains Fava's purpose and offers deliberate access and library navigation without claiming that no source workouts exist. A known prior empty read is described as a prior observation, separately from never having read.
3. **Given** any library state, **When** the person opens Settings, **Then** distance units and deliberate HealthKit access are discoverable, and library return takes one navigation action. Opening Settings or access does not request authorization.
4. **Given** available HealthKit and no active read, **When** the library is entered after launch or deliberate navigation, **Then** one read checks for new data without requesting authorization; saved rows remain usable. Resizing, recomputing or foregrounding the visible screen does not count as another entry.
5. **Given** interrupted work from an earlier session, **When** Fava relaunches, **Then** history remains available, earlier read/access requests are not restored as active, and no access request starts automatically.
6. **Given** saved runs and an existing unit preference, **When** the person browses, changes units or selects matching-looking rows, **Then** source chronology, values, distinct identities and exact selection handoff are preserved; units survive relaunch and changing units itself requests no read.
7. **Given** saved history cannot be read locally, **When** Fava launches, **Then** it shows a local-history recovery error rather than successful-empty, preserves stored data, and offers deliberate retry or confirmed clearing without automatically requesting authorization.

---

### User Story 2 - Preserve history across changing source visibility (Priority: P1)

**Requirements**: FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-014, FR-016, FR-017, FR-018.

As a person with imported runs, I want empty or smaller reads to leave my history available, with honest information about which runs were observed again.

**Why this priority**: A read cannot establish why an earlier identity is absent; useful history must not disappear silently.

**Independent Test**: Start with synthetic A/B, read B/C, then zero records, fail, report unavailability and relaunch. Inspect history, latest outcome, provenance and persistence without run detail.

**Acceptance Scenarios**:

1. **Given** saved A/B, **When** a complete successful read returns B/C, **Then** history contains A/B/C once each; returned B uses its newly observed source summary, C is added, and A retains its old summary and is distinguishable as unobserved in that read. The read is successful-nonempty with two returned identities, not three.
2. **Given** populated history, **When** a complete read returns zero accessible running workouts, **Then** the attempt is successful-empty, saved rows stay usable, and a separate notice says this read returned no accessible runs and displayed runs were saved earlier. No deletion, denial or current-access claim appears.
3. **Given** retained history after an empty read, **When** Refresh is chosen repeatedly, **Then** every available, non-overlapping attempt follows the same retention rules; repeated empty observations neither clear history nor become failures.
4. **Given** absent/empty history, **When** a read succeeds with zero records, **Then** the library shows a neutral successful-empty observation and access guidance without fabricating runs or claiming denial.
5. **Given** saved history, **When** a read loads, fails after intermediate records or is unavailable, **Then** saved rows stay usable, incomplete records do not alter durable history, the separate attempt state is accurate, and retry is available only with an available source and no active read.
6. **Given** duplicate deliveries and different identities with equal summaries, **When** a complete result is accepted, **Then** identities occur once, distinct runs stay separate, and order uses source start time with stable ties.
7. **Given** an imported run is deleted in HealthKit or becomes unreadable, **When** later reads omit it, **Then** its saved summary remains distinguishable as unobserved; Fava neither infers the cause nor deletes/recreates it automatically. The person can clear all local history deliberately.
8. **Given** saved observations, including older history without freshness timestamps, **When** Fava relaunches or adopts that history, **Then** identities/summaries survive, earlier observations remain labelled prior, and unknown times are not invented.
9. **Given** a successful source read but failure to save its updates, **When** the result is reported, **Then** source outcome and local-saving failure are distinguished, prior durable history is preserved, and unsaved updates are not described as available after relaunch.

---

### User Story 3 - Understand freshness and recover deliberately (Priority: P2)

**Requirements**: FR-002, FR-003, FR-004, FR-008, FR-009, FR-010, FR-014, FR-015, FR-016.

As a person browsing runs, I want to distinguish saved observations from a new read and recover access without misleading permission claims.

**Why this priority**: Retention must not imply that historical summaries prove present access or synchronization.

**Independent Test**: Supply synthetic outcomes, controlled observation times and partially returned identities. Follow refresh, Settings and request-completion guidance without inspecting actual permission choices.

**Acceptance Scenarios**:

1. **Given** saved runs, **When** provenance is inspected, **Then** each run's last observed time is available, or explicitly unknown for older data. A visible library notice identifies saved history; runs missing from the latest complete read are individually distinguishable without color alone.
2. **Given** a successful-empty read after a populated read, **When** freshness is inspected, **Then** the latest successful read time advances, runs' last observed times do not, and retained runs are not described as refreshed. A subsequent failed attempt leaves successful-observation times unchanged and has its own notice.
3. **Given** an empty outcome or access completion without another permission sheet, **When** guidance is read, **Then** Fava conditionally explains that earlier choices may need changing in Health or system Settings, followed by returning and Refresh. It neither detects denial nor promises to force the sheet.
4. **Given** an active read, **When** Refresh/Retry is chosen or the library is reentered, **Then** that attempt continues without another concurrent read and controls convey their unavailable state. A later deliberate action after completion can read again.
5. **Given** no network connection, **When** saved history is browsed or an available local read requested, **Then** no account/backend is required and the same outcome/retention rules apply.
6. **Given** compact iPhone or resized iPad, VoiceOver or any Dynamic Type size, **When** notices, provenance, Settings, access, refresh/retry and return paths are used, **Then** content is readable, actions reachable, and names, roles, selected/enabled states and outcome changes conveyed. Scrolling is allowed.

---

### User Story 4 - Clear local history intentionally (Priority: P2)

**Requirements**: FR-001, FR-003, FR-011, FR-012, FR-013, FR-014, FR-015, FR-017, FR-019.

As a person removing saved observations from Fava, I want confirmed clearing that does not delete HealthKit workouts or change my permissions.

**Why this priority**: Durable retention needs deliberate, understandable privacy control.

**Independent Test**: Use synthetic history, units and pending reads; exercise cancellation, confirmation, failure, relaunch and later import without deleting source workouts.

**Acceptance Scenarios**:

1. **Given** history or a local recovery error, **When** Clear Local Run History is chosen in Settings, **Then** confirmation explains removal of all Fava-saved run summaries and read-history metadata, preservation of HealthKit workouts/permissions and unit preferences, and possible reimport on later library entry. Cancel and an explicitly destructive confirm action are distinguishable.
2. **Given** confirmation, **When** cancelled, **Then** history, observation metadata and preferences are unchanged.
3. **Given** confirmation, **When** clearing succeeds, **Then** local history/observation metadata are durably removed, setup is shown, and relaunch restores no cleared rows. Clearing starts no source read/access request and preserves units.
4. **Given** a read already in progress, **When** clearing succeeds and that old read later finishes, **Then** it cannot restore cleared data. Only a later library entry or deliberate Refresh after clearing may import again.
5. **Given** durable clearing fails, **When** the action ends, **Then** failure is reported without claiming erasure, prior durable history/navigation remain, and deliberate retry is possible.
6. **Given** a fresh installation without restored app data, **When** Fava launches, **Then** no history is saved and setup appears. Restored app data follows normal history rules; Fava promises neither cloud recovery nor that reinstall revokes permission or deletes source workouts.

### Edge Cases

- Successful-empty, unavailable source, failed read and unreadable local save are distinct; none establishes denial or source deletion.
- A subset is a complete observation of currently accessible records, not permission to discard absent identities. Failed/interrupted reads contribute no partial updates.
- A newly observed identity with missing distance replaces that identity's earlier distance with explicit absence; an unobserved identity retains its old summary. Recorded zero stays zero.
- Older saved-empty differs from never-read. Clearing removes both history and provenance, not just visible rows. Missing legacy observation times stay unknown.
- Source deletion, revocation and genuine no-history cannot be distinguished from missing identities alone. Per-run deletion/reconciliation is deferred.
- Relaunch cannot restore interrupted progress; rotation, foregrounding and unit changes do not independently read. Rows remain selectable during loading/failure/unavailability.
- Local clearing and late completion cannot silently restore erased history. Later intentional library entry can import the same identities again.
- Locale/time-zone labels can change, but source instants and chronology do not. Observation times describe observations, not permission or a synchronization guarantee.
- Reset/reinstall depends on whether app data is absent or restored; HealthKit choices remain independent.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Launch MUST open the library with readable populated history and show saved rows before waiting for a read. First installation, readable empty history and confirmed clearing MUST open setup without claiming source history is empty. Acceptance: US1 scenarios 1–2; US4 scenarios 3 and 6.
- **FR-002**: Setup/access/empty wording MUST distinguish never-read, prior empty and current successful-empty observations, and MUST NOT infer permission, deletion or no recorded history from saved data, request completion or zero records. Acceptance: US1 scenario 2; US2 scenarios 2 and 4; US3 scenarios 2–3.
- **FR-003**: Settings MUST be reachable from the library in one action, expose Device/Kilometres/Miles and deliberate HealthKit access, provide confirmed clearing, and return to the library in one action. Setup MUST retain access and library navigation. Opening Settings/access MUST NOT request authorization. Acceptance: US1 scenario 3; US4 scenario 1.
- **FR-004**: Each available-source library entry without an active read MUST start one foreground read to check for new data; saved history MUST appear independently. Entries during a read MUST reuse it. Refresh and failure Retry MUST be explicit available actions. No entry/read/retry may request authorization automatically; resizing, foregrounding or recomputing the visible screen MUST NOT independently read. Acceptance: US1 scenario 4; US3 scenario 4.
- **FR-005**: Local history MUST retain imported identities until confirmed clearing. Complete successful reads MUST add new identities and update summaries of returned identities without removing unreturned identities or merging distinct matching-looking runs. Acceptance: US2 scenarios 1, 6 and 7.
- **FR-006**: Zero accessible running workouts MUST remain successful-empty and preserve imported runs/summaries. Repeated empty reads MUST follow the same rule without being relabelled failure or clearing history. Acceptance: US2 scenarios 2–4.
- **FR-007**: Only complete successful results may update history. Loading, failed, unavailable and interrupted attempts MUST preserve durable history; incomplete records MUST NOT count as successfully imported. Successful source reads with saving failure MUST show separate feedback and MUST NOT imply durable retention of unsaved updates. Acceptance: US2 scenarios 5 and 9.
- **FR-008**: Attempt outcomes MUST be distinguishable from history. Populated history plus successful-empty MUST show rows and a separate no-accessible-runs-returned notice; subset reads MUST distinguish returned runs from unobserved history. Retained history MUST NOT be collectively labelled freshly read. Acceptance: US2 scenarios 1–2 and 5; US3 scenarios 1–2.
- **FR-009**: Fava MUST retain the time and returned identities of the latest complete successful observation, including empty, and each run's last observed time when known. Times MUST be available in the library; missing legacy times MUST be explicitly unknown. Empty reads advance only the successful-observation time; failures/unavailability advance neither it nor per-run times. Earlier-session outcomes MUST be labelled prior, not current active attempts. Acceptance: US2 scenario 8; US3 scenarios 1–2.
- **FR-010**: Missing identities MUST NOT be treated as deletion or revoked permission, even after repeated reads. R3.5 MUST NOT automatically remove/recreate them in HealthKit or promise background/edit/deletion synchronization. Acceptance: US2 scenarios 3 and 7; US3 scenario 3.
- **FR-011**: Clear Local Run History MUST require Settings confirmation explaining all-history scope, retained units, unchanged HealthKit workouts/permissions and possible reimport. Cancellation MUST leave data unchanged. Per-run clearing is outside scope. Acceptance: US4 scenarios 1–2.
- **FR-012**: Confirmed successful clearing MUST durably remove all local run summaries/identities and observation metadata, preserve units/system-managed access choices, show setup, and start no source read/access request. Pre-clear pending reads MUST NOT repopulate data; a later intentional library entry/Refresh may import again. Acceptance: US4 scenarios 3–4.
- **FR-013**: Failed clearing MUST report failure, preserve durable history/navigation and permit retry without claiming erasure. Acceptance: US4 scenario 5.
- **FR-014**: Settings access MUST preserve R1's workout-only, deliberate, non-overlapping flow and distinct completion/failure/cancellation/unavailability outcomes. Completion/empty guidance MUST conditionally explain changing earlier choices in Health or system Settings, then returning and refreshing; it MUST NOT promise another permission sheet or detected denial. Acceptance: US1 scenarios 3 and 5; US3 scenario 3; US4 scenario 1.
- **FR-015**: Startup, setup, Settings, history/provenance, notices, refresh/retry and clearing MUST support VoiceOver and every Dynamic Type size on compact iPhone/resized iPad. Names, roles, selected/enabled states and outcome changes MUST be conveyed; readable content/reachable actions MUST avoid clipping/overlap. Scrolling is allowed; provenance MUST NOT rely on color alone. Acceptance: US3 scenarios 1 and 6; all accessible user journeys.
- **FR-016**: History browsing and available local reads MUST need no account/backend/network. Summaries MUST remain derived HealthKit observations, not a competing authority or proof of present access. Acceptance: US2 scenarios 2, 7 and 8; US3 scenario 5.
- **FR-017**: R3.5 MUST preserve source instants, recorded duration, optional distance/zero distinctions, newest-first ordering with stable ties, exact selected-identity handoff, and retained Device/Kilometres/Miles preferences. Units affect display only and MUST NOT themselves read. Richer measurements/R4 content remain excluded. Acceptance: US1 scenario 6; US2 scenarios 1 and 6; US4 scenario 3.
- **FR-018**: R2/R3 saved identities/summaries MUST remain usable after adoption without fabricated observation times. Unreadable local history MUST produce a separate recovery error, preserve stored data and offer deliberate retry or confirmed clearing. Acceptance: US1 scenario 7; US2 scenario 8.
- **FR-019**: Absent app data after reset/reinstall MUST show setup; restored data MUST follow normal history rules. Local clearing/reinstall MUST NOT promise cloud restoration, source deletion or permission reset. Acceptance: US4 scenario 6.

### Key Entities

- **Retained Run History**: Imported source workout identities and latest observed source summaries; later absence does not delete them.
- **Run Observation Provenance**: Last observed time when known and membership in the latest successful read; neither establishes permission.
- **Latest Read Observation**: Time, returned identities and successful nonempty/empty outcome, separate from current attempts and retained history.
- **Launch Context**: Readable populated, readable empty/absent, or local-history recovery error, without inferring authorization.
- **Local Clearing Confirmation**: Consent to remove all Fava run/observation data while retaining units, source workouts and system-managed permissions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every populated-history launch fixture opens the library with browsable rows before a new read completes. On one supported iPhone and iPad, the usable saved-history screen appears within 2 seconds with synthetic 1,000-run history and no network. All absent/empty/cleared fixtures show setup; unreadable-history fixtures show recovery error.
- **SC-002**: In populated/subset/duplicate/repeated-empty/failed/unavailable/interrupted fixtures, 100% of retained identities occur once until clearing; returned summaries update accurately, unobserved summaries survive, and incomplete results never become durable history.
- **SC-003**: Every provenance fixture distinguishes retained rows, returned identities and outcomes. Empty reads advance zero per-run times; failure/unavailability advance zero successful-observation times. All missing legacy times remain unknown, with zero unsupported permission/deletion claims.
- **SC-004**: All clearing fixtures preserve data on cancellation/failure and erase run/observation data through relaunch on successful confirmation, keeping units and source workouts/permissions unchanged. Zero pre-clear pending reads restore history. Later deliberate reimport preserves identity rules.
- **SC-005**: Settings is reachable from the library in one action, access in at most one further action, and library return in one. Each eligible entry or Refresh/Retry starts exactly one read; actions during loading start zero additional reads and zero automatic access requests.
- **SC-006**: On compact iPhone/resized iPad at every Dynamic Type size, all specified content/actions remain readable/reachable without clipping/overlap. VoiceOver walkthroughs can identify launch context, saved/unobserved history, outcomes, guidance, units and destructive confirmation and complete all four journeys.
- **SC-007**: Sanitized physical iPhone and iPad demonstrations cover saved-history launch, deliberate access, nonempty then empty/subset observations where reproducible, retention/refresh, units and clearing. Synthetic automated acceptance tests independently cover every outcome/race; fixtures do not establish real HealthKit behavior or device acceptance.

## Assumptions

- Owner merge of [PR #8](https://github.com/clemarc/fava/pull/8) approves R3.5's roadmap, present in main at `0f6b64a2041e015f63369b5ad7c4f871cc053063`. [FAV-36](https://linear.app/clemarc/issue/FAV-36/r35-specify-reliable-run-history-and-contextual-launch) provides intake context; Git remains authoritative and this contract requires review/merge.
- Draft default for owner review: keep setup when no saved runs exist, preserving the existing no-history entry experience.
- Owner response on 2026-10-13: keep all imported runs, update returned identities and label unobserved history, including after nonempty subset reads.
- Owner response on 2026-10-13: "Yes to check for new data only" to automatic library-entry reads. This preserves entry reads to discover new data without treating them as deletion reconciliation; returned identities refresh their observed summaries under the retention contract.
- Clearing removes all run history/observation metadata, not units, permission choices or source workouts. Returning to setup prevents clearing itself from initiating reimport; later intentional library entry can read again.
- R1/R2/R3 remain dependencies except qualified superseded clauses above. Migration and storage mechanics belong to planning; adoption must preserve existing history and report unknown timestamps honestly.
- The 2-second/1,000-run launch budget is a proposed acceptance target, not existing performance evidence.
- After implementation, native automated checks run on macOS CI. Fixtures/public artifacts use synthetic data; device evidence records sanitized outcomes, model/OS and revision. Prior R1–R3 evidence does not establish R3.5 acceptance.
- This invocation creates specification/quality artifacts only. Planning, tasks, Linear projection and application implementation follow later approved lifecycle stages. No Linear status change is performed.

# Feature Specification: Run Ingestion

**Feature Branch**: `healthkit-run-library-01-app-foundation-and-authorization` (shared R1–R3 specification delivery branch)

**Created**: 2026-10-12

**Status**: Draft

**Input**: Prepare the approved Run Ingestion milestone. Parent roadmap: specs/healthkit-run-library/roadmap.md → entry R2

**Component**: Personal iPhone and iPad application.

**Supersedes**: None; first specification for R2.

Scope boundary: R2 reads accessible HealthKit running workouts and makes their identities and available summary values available for later presentation. It owns running-workout eligibility, read-result correctness, duplicate prevention, and verifiable empty and failed reads. R1 owns installation, navigation foundation, and deliberate workout-record access requests. R3 owns the user-facing run library, its loading/empty/failure presentations, and the user interaction that requests ingestion. R4 owns individual run details. Automatic background updates, ongoing reconciliation of edited or deleted workouts, health-data writes, accounts, cloud services, iCloud sync, sharing, and analytics are outside R2.

## Clarifications

### Session 2026-10-12

- Q: How much running-workout history should R2 read from HealthKit? → A: All accessible running-workout history, with no date limit.
- Q: Which summary values should R2 provide for each run in the initial library? → A: Start date/time, recorded duration, and distance when available.
- Q: Should ingested runs remain available after Fava is closed and reopened? → A: A saved run is fine: retain the last successful result across launches as previously loaded, replacing it after a successful read.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Make accessible runs available (Priority: P1)

**Requirements**: FR-001, FR-002, FR-003, FR-004, FR-005, FR-012.

As a person who wants to browse my running history, I want Fava to read the running workouts accessible through HealthKit, so later screens can use my actual workouts rather than invented or unrelated records.

**Why this priority**: A correct result is the prerequisite for R3's library and R4's detail selection.

**Independent Test**: Request a read using synthetic running and non-running workouts, then inspect the resulting identities and summary values without requiring a populated run-library screen. Independently demonstrate a read on each physical device family using only sanitized outcomes; fixtures do not establish real HealthKit access.

**Acceptance Scenarios**:

1. **Given** accessible running and non-running workouts across the person's available history, **When** ingestion is requested, **Then** all accessible running workouts are returned with their original identities, start date/time, recorded duration, and distance when available, without a date cutoff or silent record-count cap.
2. **Given** indoor and outdoor workouts classified by HealthKit as running, **When** ingestion is requested, **Then** both are eligible regardless of their age; walking, cycling, and other non-running activities are excluded.
3. **Given** an eligible workout with no recorded distance, **When** its result is produced, **Then** the run remains available with its source start date/time and recorded duration, and distance is explicitly absent rather than replaced with a fabricated zero.
4. **Given** R1's request-completion state or a previous permission choice, **When** ingestion is requested, **Then** Fava bases its result on the current readable records and does not treat request completion as proof of read authorization.
5. **Given** accessible runs recorded recently, more than 12 months ago, and several years ago, **When** ingestion completes successfully, **Then** every eligible source identity appears exactly once without an age-based exclusion.
6. **Given** a run whose elapsed start-to-end time differs from its recorded duration, **When** its summary is produced, **Then** duration equals the source workout's recorded duration; Fava does not substitute elapsed wall-clock time or infer moving time.
7. **Given** HealthKit is available locally and the device has no network connection, **When** ingestion is requested, **Then** no Fava account or backend is required and the read follows the same complete-result and failure rules without writing health data.

---

### User Story 2 - Read repeatedly without duplicate runs (Priority: P1)

**Requirements**: FR-003, FR-006, FR-007, FR-008, FR-009, FR-013.

As a person returning to Fava, I want repeated reads to identify the same workout consistently and avoid duplicate runs, so later browsing does not count the same record more than once.

**Why this priority**: Repeatability protects the integrity of the first usable library.

**Independent Test**: Read a synthetic collection repeatedly, include duplicate deliveries of one workout identity, and request a read while another is active. Inspect identities, result boundaries, and read-operation count independently of R3.

**Acceptance Scenarios**:

1. **Given** unchanged accessible records, **When** the same coverage is read repeatedly, **Then** each successful result contains exactly one run per HealthKit workout identity and retains those identities across reads.
2. **Given** identical workout identity appears more than once in one read result, **When** the result is made available, **Then** that identity occurs once; distinct identities with matching dates or summary values remain distinct runs.
3. **Given** a read is active, **When** another read is requested, **Then** at most one read operation remains active and no consumer observes a partial result as a completed collection.
4. **Given** a previous completed result, **When** a later read begins, **Then** the new attempt is explicitly loading and its eventual outcome is distinguishable from that previous result.
5. **Given** a successful nonempty or empty result was saved, **When** Fava is closed and reopened, **Then** that complete result and its source identities are available as previously loaded without restoring a loading attempt or asserting current read access.
6. **Given** a saved result, **When** a later read completes successfully, **Then** the saved collection is replaced by that complete result, including replacement with an empty collection; records from earlier reads are not appended to the new result.
7. **Given** a saved result, **When** a later read fails, becomes unavailable, or is interrupted before completion, **Then** the saved result remains intact and distinguishable from the unsuccessful or unfinished attempt.

---

### User Story 3 - Distinguish empty, unavailable, and failed reads (Priority: P2)

**Requirements**: FR-007, FR-008, FR-010, FR-011, FR-012, FR-014.

As a person whose runs cannot currently be retrieved, I want Fava to distinguish a completed empty read from an unsuccessful read, so the library can explain the current outcome without making unsupported permission claims.

**Why this priority**: Reliable outcome distinctions are required for R3's loading, empty, failure, and retry experiences.

**Independent Test**: Supply successful empty results, source unavailability, failures before or after intermediate records, and a subsequent successful retry. Inspect terminal results independently of UI wording or layout.

**Acceptance Scenarios**:

1. **Given** a read completes successfully with no accessible eligible running workouts, **When** its outcome is exposed, **Then** it is successful-empty, without a claim that the person has never recorded runs or denied read access.
2. **Given** HealthKit is unavailable, **When** ingestion is requested, **Then** the result is unavailable rather than successful-empty, and no access request is initiated automatically.
3. **Given** a read fails, including after intermediate records have arrived, **When** the failure is reported, **Then** the attempt ends as failed and its incomplete records are not published as a successful result.
4. **Given** a failed or unavailable attempt, **When** a new read is explicitly requested after the source becomes usable, **Then** the attempt follows the same eligibility, uniqueness, and outcome rules and does not automatically request permission.
5. **Given** a request-completion, failure, or cancellation outcome from R1, **When** a readable result or read failure is exposed, **Then** authorization-request state and ingestion state remain distinct.
6. **Given** a read is active, **When** Fava is backgrounded or terminated before completion, **Then** no fabricated successful or empty result replaces the last successful saved collection; a fresh launch restores that collection as previously loaded without restoring the interrupted attempt as loading.

### Edge Cases

- Read denial, restricted visibility, and genuinely absent eligible workouts can yield the same empty result; R2 never infers which cause applies.
- Accessible history may span multiple years or contain many records; a successful result must not silently exclude older runs or truncate the source collection.
- Distinct workouts with identical timestamps or summaries keep separate source identities.
- Missing distance remains absent; a genuine recorded zero distance remains zero. Recorded duration is preserved even when elapsed wall-clock time differs.
- A read that fails after returning intermediate records must not become a partially successful library.
- A saved collection is the last successful observation, not a guarantee of current source visibility. A successful empty read replaces a saved nonempty collection; failed or unavailable attempts do not erase it or masquerade as success.
- A repeated read is a new requested observation of all accessible running history, not background synchronization or an ongoing edit/deletion reconciliation guarantee.
- Eligibility follows HealthKit's running classification; R2 does not reconstruct runs from steps, routes, walking workouts, or segments of other activity types.
- Backgrounding or terminating Fava must not turn a pending attempt into an empty or completed result. A fresh session must not restore a stale in-progress attempt.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: R2 MUST read only workouts classified by HealthKit as running, including indoor and outdoor running, without inferring runs from other activities or requesting additional health categories. Acceptance: US1 scenarios 1 and 2.
- **FR-002**: Each successful ingestion MUST include all currently accessible running-workout history, with no date cutoff or silent record-count cap. Older eligible runs MUST NOT be excluded because of their age. Acceptance: US1 scenarios 1, 2, and 5; fixtures include recent, older-than-12-month, and multi-year records.
- **FR-003**: Each ingested run MUST retain its HealthKit workout identity. Distinct identities MUST remain distinct even when their dates and summaries match. Acceptance: US1 scenario 1; US2 scenarios 1 and 2.
- **FR-004**: Each run MUST expose its source workout start date/time, recorded duration, and distance when available for later presentation. Start date/time MUST preserve the source instant, and duration MUST preserve the source workout's recorded duration rather than substituting elapsed wall-clock time or inferred moving time. Distance MUST retain its source value and unit without fabrication. Average pace, calories, heart rate, route, splits, and other richer measurements are outside this milestone. R2 MUST NOT introduce extra read permissions to obtain richer health measurements. Acceptance: US1 scenarios 1, 3, and 6.
- **FR-005**: Optional source values that are absent MUST remain explicitly absent. R2 MUST NOT fabricate distance, duration, other measurements, or workout records; a recorded zero MUST remain distinguishable from an absent value. Acceptance: US1 scenario 3 and missing-value edge cases.
- **FR-006**: Each completed result MUST contain no more than one run for each HealthKit workout identity. Repeated ingestion MUST NOT create duplicate runs. Acceptance: US2 scenarios 1 and 2.
- **FR-007**: Consumers MUST be able to distinguish not-requested, loading, successful-nonempty, successful-empty, failed, and unavailable outcomes. Each completed outcome MUST belong to the current read attempt. Acceptance: US2 scenarios 3 and 4; US3 scenarios 1–3.
- **FR-008**: A read attempt MUST make its complete successful result available together. Intermediate records from a failed or active attempt MUST NOT be exposed as a completed collection. Acceptance: US2 scenario 3; US3 scenario 3.
- **FR-009**: Fava MUST prevent concurrent ingestion operations caused by repeated read requests. A prior completed result MUST NOT be labelled as the successful outcome of a newer loading or failed attempt. Acceptance: US2 scenarios 3 and 4.
- **FR-010**: A successful read containing zero eligible accessible running workouts MUST produce successful-empty. Fava MUST NOT equate that result with read denial, a lack of recorded history, or a technical failure. Acceptance: US3 scenario 1.
- **FR-011**: A source failure or unavailability MUST produce the corresponding unsuccessful outcome and permit a later explicitly requested read. It MUST NOT produce successful-empty or initiate an access request automatically. Acceptance: US3 scenarios 2–4.
- **FR-012**: R2 MUST use HealthKit as the authoritative source, preserve R1's deliberate authorization flow, and avoid treating request completion as proof of current read access. It MUST NOT write health data or require a Fava account, backend service, or network connection for ingestion. Acceptance: US1 scenarios 4 and 7; US3 scenarios 2, 4, and 5.
- **FR-013**: Fava MUST save the last complete successful ingestion result locally and make it available across launches with its source identities and summary values, identified as previously loaded. Each later successful read MUST replace the saved collection completely, including an empty result; failed, unavailable, or interrupted attempts MUST preserve the prior saved result without presenting it as their successful outcome. Saved values MUST remain a derived observation of HealthKit and MUST NOT imply current permission or current source visibility. Acceptance: US2 scenarios 4–7.
- **FR-014**: Backgrounding or termination MUST NOT produce a fabricated completed or empty read result. A fresh session MUST NOT restore a stale loading attempt. Acceptance: US3 scenario 6 and the interrupted-read edge case.

### Key Entities

- **Ingested Run**: One accessible workout classified as running, identified by its HealthKit workout identity and carrying its source start date/time, recorded duration, and distance when available. Start date/time is an instant, not a formatted date label; distance has a value and unit or is absent. No pace or richer health measurements are required.
- **Ingestion Attempt**: One requested observation of the agreed history coverage, with explicit loading and terminal outcome boundaries.
- **Ingestion Result**: The complete unique run collection from a successful attempt, including an empty collection, or a distinct failure/unavailability outcome. It describes readable results, not permission choices.
- **Saved Run Collection**: The complete collection from the last successful read, kept locally across launches with source identities and summary values and marked as previously loaded. Its presence and contents are distinct from the state of any current read attempt; a saved empty result differs from never having completed a read.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Across synthetic eligibility fixtures covering recent, older-than-12-month, and multi-year records, 100% of accessible eligible runs and no excluded activity records appear in the completed result, without a date cutoff or silent record-count cap and preserving each source identity and available agreed summary value.
- **SC-002**: Ten repeated successful reads of an unchanged fixture produce identical unique identity sets, and duplicate deliveries never create more than one record per source identity.
- **SC-003**: Every summary fixture preserves the source start instant, recorded duration, and available distance value/unit. All absent-distance fixtures remain explicitly absent; recorded-zero fixtures remain distinguishable from absent values, and recorded duration is preserved when it differs from elapsed time.
- **SC-004**: Across empty, nonempty, failed, unavailable, overlapping-request, and interrupted-read fixtures, 100% produce the defined attempt state, no concurrent read, no incomplete successful collection, and no unsupported read-permission claim.
- **SC-005**: On one supported physical iPhone and one supported physical iPad, a controlled ingestion demonstration yields the current accessible running records or the defined empty/unsuccessful outcome without new write permissions. Record only sanitized outcome and device/OS information, not real workout history; synthetic automated checks remain mandatory.
- **SC-006**: Across saved-nonempty, saved-empty, successful-replacement, failed-refresh, unavailable-refresh, and interrupted-refresh fixtures, 100% preserve the defined saved/current-attempt distinction. Relaunch restores the exact saved identity set and summary values with no stale loading state, failed attempts preserve that set, and successful reads replace rather than append to it.

## Assumptions

- R2 depends on [R1](../healthkit-run-library-01-app-foundation-and-authorization/spec.md). Its installation/navigation and workout-record access-request behavior are reused, not redefined.
- R2 can be verified through its observable read outcomes without an R3 screen. R3 decides how a person requests a read and presents the result; R2 does not introduce a second authorization flow.
- Supported operating-system versions and read implementation mechanisms are planning decisions shared with R1.
- R1's workout-record-only access scope is reused for start date/time, recorded duration, and distance available on the workout record. R2 does not read separate distance samples or richer data requiring extra permissions. R3 owns formatting these values for display.
- Only explicitly requested reads are required, each covering all currently accessible running history; automatic background observation and ongoing edited/deleted-workout reconciliation remain deferred by the roadmap.
- Saving a completed result is derived local retention, not a second authoritative workout source. Replacing that snapshot on an explicitly requested successful read does not add automatic observation, per-record synchronization, or ongoing source-change reconciliation.
- All automated fixtures and public logs or artifacts use synthetic records. Physical-device evidence is sanitized and supplements automated correctness checks.

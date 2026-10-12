# Feature Specification: App Foundation and HealthKit Authorization

**Feature Branch**: `healthkit-run-library-01-app-foundation-and-authorization`

**Created**: 2026-10-07

**Status**: Draft

**Input**: User description: "healthkit-run-library"; selected slice: "R1". Parent roadmap: specs/healthkit-run-library/roadmap.md → entry R1

**Component**: Personal iPhone and iPad application.

**Supersedes**: None; first specification for R1.

Scope boundary: R1 establishes installation, launch, the initial screen and navigation, and the HealthKit access-request experience. R2 owns retrieving running workouts and handling empty read results; R3 owns the populated run library and its loading, empty, and read-failure presentations; R4 owns individual run details. R1 does not retrieve workouts, display workout summaries, or write health data. Accounts, cloud services, iCloud sync, sharing, AI analysis, and advanced analytics remain outside the epic.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Launch and navigate Fava (Priority: P1)

**Requirements**: FR-001, FR-002, FR-003, FR-012.

As a person installing Fava on my iPhone or iPad, I want a usable initial screen that explains the app's purpose and lets me find the run-library destination, so I understand where my running workouts will appear.

**Why this priority**: Installation and usable navigation establish the entry point for every later slice.

**Independent Test**: Install and launch on each device family without requesting health access. Verify that the purpose, access action, and run-library destination are discoverable and navigation works. Automated checks cover launch and navigation; demonstrate installation and layout on both device families.

**Acceptance Scenarios**:

1. **Given** Fava is newly installed on a supported iPhone or iPad, **When** the person launches it, **Then** the initial screen identifies Fava, explains its running-workout browsing purpose, and offers a labeled HealthKit access action without automatically requesting access.
2. **Given** the initial screen before any request, **When** the person opens the run-library destination, **Then** the destination identifies itself as the future place to browse runs without claiming that workouts were imported or that none exist.
3. **Given** the run-library destination, **When** the person uses the provided return navigation, **Then** the initial screen and access action are reachable without restarting.
4. **Given** Fava has been closed, **When** the person reopens it, **Then** it opens a usable screen without automatically requesting access or requiring an account or network connection to navigate.

---

### User Story 2 - Request access deliberately (Priority: P1)

**Requirements**: FR-002, FR-004, FR-006, FR-007, FR-009, FR-011, FR-012.

As a person who wants to use my running workouts in Fava, I want to understand why workout access is needed and choose when to request it, so I retain control of my health data.

**Why this priority**: A deliberate, accurate access flow is the prerequisite for R2.

**Independent Test**: Exercise initiation, completion, repeated initiation, and relaunch with controlled request outcomes without reading workouts. Automated checks cover app-owned behavior; demonstrate the system permission experience on both device families where HealthKit is available.

**Acceptance Scenarios**:

1. **Given** HealthKit is available and no request is active, **When** the person chooses the access action after seeing its explanation, **Then** Fava initiates the system-managed request for workout-record read access, requests no writes or unrelated health categories, and explains that the purpose is to browse running workouts.
2. **Given** a request is active, **When** the person taps the action again, **Then** no concurrent request begins and the interface indicates that the current request is in progress.
3. **Given** the person allows read access in the system permission experience, **When** the request completes without an error, **Then** Fava ends its progress indication, remains usable, and reports request completion without asserting that read access was granted or runs were imported.
4. **Given** the person declines read access in the system permission experience, **When** the request completes without an error, **Then** Fava presents the same neutral completion behavior and does not claim to know the read-permission choice.
5. **Given** a previous request has completed, **When** the person uses the action again, **Then** Fava can initiate another request as allowed by the system without promising that a permission sheet will appear or overriding previous choices.
6. **Given** a request completed in a previous session, **When** Fava is relaunched, **Then** completion is not presented as proof of current read access and any new request requires explicit user action.

---

### User Story 3 - Recover from an unavailable or failed request (Priority: P2)

**Requirements**: FR-005, FR-006, FR-008, FR-009, FR-010, FR-012.

As a person unable to complete a health-access request, I want a clear explanation and a usable way forward, so I can understand what happened and try again when appropriate.

**Why this priority**: Recoverable states keep the foundation useful when access cannot proceed.

**Independent Test**: Supply unavailable and request-error outcomes independently of workout data. Automated checks verify messages, navigation, retry, and absence of overlapping requests.

**Acceptance Scenarios**:

1. **Given** HealthKit is unavailable in the current device environment, **When** the person opens the access experience, **Then** Fava explains the unavailability, prevents request initiation, and leaves navigation usable.
2. **Given** HealthKit is available, **When** a request reports an error, **Then** Fava ends its progress indication, shows a readable request-failure message without labeling read permission as denied, and provides retry.
3. **Given** a previous request failed and HealthKit remains available, **When** the person retries, **Then** exactly one new request begins and follows the same completion or failure rules as the initial attempt.
4. **Given** a request is interrupted while Fava is temporarily in the background, **When** the person returns, **Then** navigation remains usable, any reported completion or error is reflected, and no extra request begins automatically.

### Edge Cases

- Read access is declined or partly allowed: completion remains neutral; Fava does not infer the permission choice.
- Permissions are changed outside Fava: prior completion is not proof of current access and relaunch does not automatically request access.
- A repeated request completes without displaying a sheet: Fava accepts completion without fabricating a prompt.
- Rapid repeated taps: at most one request can be active.
- The app is backgrounded or terminated during a request: return remains usable; a fresh launch must not restore a stale in-progress indication or start another request automatically.
- HealthKit is unavailable: navigation works and no request is attempted.
- No running workouts exist: R1 behaves identically because it does not read workouts; empty-result handling belongs to R2.
- Compact iPhone layouts and resized iPad layouts: purpose text, access actions, state messages, and navigation remain readable and operable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Fava MUST be installable and launchable on supported iPhone and iPad environments with a usable initial screen. Acceptance: US1 scenarios 1 and 4.
- **FR-002**: The initial screen MUST identify Fava, explain its running-workout browsing purpose, and show a labeled access action. Launch and relaunch MUST NOT automatically request HealthKit access. Acceptance: US1 scenarios 1 and 4; US2 scenario 6.
- **FR-003**: The person MUST be able to reach an identified run-library destination and return to the initial screen. In R1 this destination MUST make no claim about imported workouts, workout counts, or absence of workouts. Acceptance: US1 scenarios 2 and 3.
- **FR-004**: Before initiation, Fava MUST explain that workout-record read access supports browsing running workouts. It MUST request only workout-record read access and MUST NOT request health-data writes or additional health categories in R1. Acceptance: US2 scenario 1.
- **FR-005**: Fava MUST check HealthKit availability before initiating a request. If unavailable, it MUST explain why initiation is unavailable, prevent the request, and preserve navigation. Acceptance: US3 scenario 1.
- **FR-006**: When HealthKit is available, explicit user action MUST initiate the system-managed request. Fava MUST indicate an active request and prevent concurrent requests from repeated actions. Acceptance: US2 scenarios 1 and 2; US3 scenario 3.
- **FR-007**: On completion without error, Fava MUST end its progress indication and remain usable with neutral completion wording. It MUST NOT assert that read permission was granted, denied, or unchanged, or that ingestion succeeded. Acceptance: US2 scenarios 3 and 4.
- **FR-008**: On a reported request error, Fava MUST end its progress indication, display a readable request-failure message distinct from a read-permission denial claim, and offer retry when HealthKit is available. Acceptance: US3 scenarios 2 and 3.
- **FR-009**: After completion or failure, Fava MUST allow another user-initiated request when HealthKit is available, respect system-managed choices, and avoid promising another permission sheet. Acceptance: US2 scenario 5; US3 scenario 3.
- **FR-010**: Return from the background MUST preserve navigation and reflect any reported outcome without automatically starting another request. A fresh launch MUST NOT present an earlier interrupted request as active. Acceptance: US3 scenario 4 and the interruption edge case.
- **FR-011**: Fava MUST NOT treat prior completion as proof of current read access. R1 MUST NOT retrieve workouts or infer authorization from workout results; retrieval and empty-result handling belong to R2. Acceptance: US2 scenario 6 and the externally changed permissions and no-workouts edge cases.
- **FR-012**: Navigation, purpose text, access actions, and outcome messages MUST remain readable and operable on compact iPhone and resized iPad layouts. Launch, navigation, and request initiation MUST NOT require a Fava account, backend service, or network connection. Acceptance: US1 scenarios 1–4 and the layout edge case; exercise request initiation offline where HealthKit is available.

### Key Entities

- **Health Access Request**: A user-initiated request to read workout records, with observable states of not in progress, in progress, completed without error, and failed. These states describe the request, not the person's read-permission choices. R1 stores no workout records.
- **Health Access Availability**: Whether the current device environment supports the requested access. Unavailability prevents initiation but does not prevent navigation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On both supported device families, at least 95% of 20 measured launches per family show the usable initial screen within 3 seconds, without an automatic access request.
- **SC-002**: From the initial screen, a person can find the access explanation and initiate a request in no more than two app actions, and reach the run-library destination and return in no more than two navigation actions total.
- **SC-003**: Across all defined completion, decline, repeated-request, failure, unavailability, and interruption cases, 100% leave navigation usable, produce no concurrent requests, and display no unsupported claim about read permission or imported workouts.
- **SC-004**: The installation-to-access journey can be demonstrated on one supported iPhone and one supported iPad, including launch, deliberate initiation, neutral completion, and return to navigation.
- **SC-005**: In a walkthrough on each device family, a reviewer can use the visible purpose text and explanation to accurately describe why workout access is requested and recognize that completion does not guarantee readable workouts, without additional verbal guidance.

## Assumptions

- The agreed R1 roadmap directory is used so the roadmap and specification resolve to one another without changing the agreed decomposition.
- R1 has no preceding feature dependency. R2 depends on this foundation; ingestion is not required to demonstrate R1.
- The run-library destination is a navigable foundation for R3, not a populated list or an empty-results presentation. R1 does not require an import action.
- Supported operating-system versions will be settled during planning under the constitution's iPhone and iPad requirement. Availability is evaluated for the current environment rather than assumed from device family alone.
- Read access covers workout records; the explanation describes their intended use for running workouts. Selecting running workouts from readable records belongs to R2.
- Completion describes the system-managed request rather than read authorization. This follows [Apple's authorization guidance](https://developer.apple.com/documentation/healthkit/hkauthorizationstatus), which states that read-permission denial is not disclosed to apps.
- The constitution's platform, local-first, and authoritative-source rules govern planning. Later workout presentation must use HealthKit as its authoritative source.
- App-owned acceptance behavior and relevant failure cases require automated tests under the constitution. Real-device demonstrations supplement those checks for installation, layout, and system permissions; they do not replace automated checks.
- Launch timing measures the initial screen on supported test devices. Time in a system permission sheet or waiting for user choices is excluded.

# Roadmap: HealthKit Run Library

Tracker epic: P-FAV-1 · https://linear.app/clemarc/project/healthkit-run-library-21526adc665b

Intent: Let a person install Fava on iPhone or iPad, request HealthKit access, and bring their running workouts into a browsable run library. They can open an individual run and inspect its available workout summary, with HealthKit remaining the authoritative data source.

Status: agreed

The R1–R4 baseline remains agreed. The R3.5 amendment below is proposed for owner
review in this PR; it becomes approved only when the owner approves and merges
the roadmap amendment. No R3.5 feature artifacts are authorized before that merge.

| ID | Sub-feature | Intent | In scope | Deferred to | Depends on | Directory |
|----|-------------|--------|----------|-------------|------------|-----------|
| R1 | App foundation and HealthKit authorization | Let the person install and launch Fava on iPhone or iPad, then initiate HealthKit access. | A native Swift/SwiftUI app with a usable initial screen and navigation ready for the run library; a user-facing HealthKit access flow for reading running workouts; handling HealthKit unavailability and completion or failure of the access request without claiming that an empty result proves read permission was denied; installation, launch, and the access flow are demonstrable on both device families. | R2: retrieving workouts and handling empty read results; R3: browsing runs; R4: workout detail; health-data writes remain outside this epic. | none | specs/healthkit-run-library-01-app-foundation-and-authorization |
| R2 | Run ingestion | Make accessible HealthKit running workouts available to Fava. | Read running workouts and expose their identities and available summary values for later presentation; repeated ingestion does not duplicate runs; empty results and read failures have verifiable outcomes; HealthKit remains authoritative. | R3: the user-facing run list; R4: the individual run screen; automatic background updates and ongoing reconciliation of edited or deleted workouts are deferred beyond this initial import slice. | R1 | specs/healthkit-run-library-02-run-ingestion |
| R3 | Run library | Let the person browse the runs available to Fava. | A chronological run list using ingested workouts, basic summaries sufficient to distinguish runs, and loading, empty, and failure presentations; selection identifies the chosen run for detail navigation. | R4: displaying the selected run's detail; search, filters, and custom sorting are deferred beyond this initial browsing slice; advanced trends and analytics remain outside this epic. | R2 | specs/healthkit-run-library-03-run-library |
| R3.5 | Reliable run history and contextual launch | Make returning use immediate and preserve useful personal running history without implying current HealthKit access. | Launch into the run library when saved runs exist, with appropriate first-run/no-saved-data states and deliberate HealthKit setup/access reachable through Settings; retain imported source identities and available summaries across relaunch, failed/unavailable reads and successful-empty reads; distinguish retained/possibly stale history from the latest read outcome; deliberate refresh/retry and offline browsing; confirmed explicit local-data clearing; preserve R1–R3 functionality, unit preferences and VoiceOver/Dynamic Type accessibility. | R4: individual run detail; exact first-run/empty destinations, freshness messaging, repeated-empty refresh, evidence for source deletion, readable-subset changes and reset/reinstall semantics require R3.5 specification/clarification; full automatic background/edit/deletion reconciliation, visual-identity redesign, Home/dashboard analytics, AI, accounts, iCloud, backend and new health-data permissions remain outside this slice. | R1, R2, R3 | specs/healthkit-run-library-05-reliable-run-history-and-contextual-launch |
| R4 | Run detail | Let the person inspect a run selected from the library. | Open the selected workout, show its available basic summary values, handle missing values or an unavailable workout, and return to the library; the library-to-detail journey is demonstrable on iPhone and iPad. | AI analysis, advanced trends and analytics, sharing, and editing workouts remain outside this epic; richer route, sample, and split presentations are deferred beyond the proposed basic detail slice. | R3 | specs/healthkit-run-library-04-run-detail |

## R3.5 amendment — reliable run history and contextual launch

Proposed on 2026-10-13 from [FAV-36](https://linear.app/clemarc/issue/FAV-36/r35-specify-reliable-run-history-and-contextual-launch).

### Order, dependencies and directory

- Deliver R3.5 after R3 and before R4. R1–R4 identifiers, directories and agreed
  rows are preserved verbatim. R4's existing R3 dependency remains its technical
  prerequisite; this amendment adds the delivery-order constraint before R4.
- R3.5 reuses R1's deliberate access flow, R2's source identities and read
  outcomes, and R3's library and unit settings. It must be independently testable
  without R4 detail, using synthetic launch, retention, refresh, clearing and
  accessibility fixtures; eventual native verification runs on macOS CI, with
  separate sanitized physical iPhone/iPad HealthKit acceptance steps.
- Reserve `specs/healthkit-run-library-05-reliable-run-history-and-contextual-launch`.
  `05` is the next unused per-epic directory number, not a renumbering of R4 or
  the R3.5 milestone. The directory is recorded here only and is not created by
  the roadmap amendment.

### Forward-looking supersession

- The future R3.5 spec must explicitly name both
  `specs/healthkit-run-library-02-run-ingestion` and
  `specs/healthkit-run-library-03-run-library` as predecessors, qualifying the
  requirements by their source feature. It will supersede R2 FR-013's
  successful-empty saved-snapshot replacement and R3 FR-013's removal of saved
  rows, including R2 US2 scenario 6, R3 US2 scenario 8 and related acceptance
  criteria/fixtures. Historic R1–R3 feature directories remain untouched.
- A successful read with zero accessible running workouts remains
  `successful-empty`; it is neither a failed read nor evidence of deletion,
  revoked permission, or no recorded history. The new retention contract will
  preserve prior imported runs while reporting the new empty observation
  separately, never labelling retained history as freshly read or proving
  current access. HealthKit remains authoritative; retained summaries are local
  derived observations, with no competing health-data source or sync guarantee.
- Only the later approved R3.5 contract and implementation change this behavior.
  This roadmap amendment does not revise the delivered snapshot-replacement
  behavior, rewrite historical requirements/tests, or introduce application code.

### Specification approval boundary

After the owner approves and merges this roadmap PR, a separate task starts from
updated `main`, sets the newly approved feature directory, and runs
`$speckit-specify` then `$speckit-clarify` for R3.5 only. That specification must
settle first-launch/saved-empty destinations, freshness information and empty-read
messaging, repeated deliberate refresh, confirmed local clearing and its scope,
intentional HealthKit deletion/readable-subset changes, and reset/reinstall
handling. Automatic source-deletion reconciliation remains deferred unless
separately approved. Planning, tasks, tracker projection and implementation follow
their own later approved lifecycle stages.

## Epic boundaries

### In scope

- Native app foundation, HealthKit authorization, run ingestion, run library, and run detail, as explicitly stated in the Linear project.
- Installation, access request, import, browsing, and inspection of an individual run form the epic's complete user journey.
- A personal iPhone and iPad application written in Swift with SwiftUI, governed by the repository constitution.
- Local-first behavior with HealthKit as the authoritative source for health and workout data; any local cache or derived presentation must not become a competing source of truth.
- Proposed initial capability: read accessible running workouts, browse their basic summaries, and inspect a selected workout. Exact summary fields and acceptance behavior belong to subsequent feature specifications after roadmap agreement.

### Deferred

- Explicitly deferred by the Linear project: AI analysis, backend/cloud services, accounts, iCloud sync, sharing, and advanced trends and analytics.
- Proposed decomposition assumptions for human review: health-data writes and workout editing; automatic background updates and ongoing reconciliation of edited or deleted workouts; search, filters, and custom sorting; richer route, sample, and split presentations. The project does not explicitly settle these boundaries; this draft proposes keeping the first run-library journey focused on an initial import and basic inspection.

## Source

- Linear project: https://linear.app/clemarc/project/healthkit-run-library-21526adc665b
- Stable project UUID: f823cc39-b818-460f-8682-bb4ec831885a
- Team: fava (FAV)
- Project status at generation: Backlog
- Project summary: Install Fava, authorize access to HealthKit, import running workouts, browse runs, and inspect an individual run.
- Project description: In scope: native app foundation, HealthKit authorization, run ingestion, run library, run detail. Deferred: AI analysis, backend/cloud services, accounts, iCloud sync, sharing, advanced trends and analytics. Detailed scope and requirements move to the Git repository once roadmap/specification begins.
- Generated from project state on: 2026-10-06

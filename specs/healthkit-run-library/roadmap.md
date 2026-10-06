# Roadmap: HealthKit Run Library

Tracker epic: P-FAV-1 · https://linear.app/clemarc/project/healthkit-run-library-21526adc665b

Intent: Let a person install Fava on iPhone or iPad, request HealthKit access, and bring their running workouts into a browsable run library. They can open an individual run and inspect its available workout summary, with HealthKit remaining the authoritative data source.

Status: agreed

| ID | Sub-feature | Intent | In scope | Deferred to | Depends on | Directory |
|----|-------------|--------|----------|-------------|------------|-----------|
| R1 | App foundation and HealthKit authorization | Let the person install and launch Fava on iPhone or iPad, then initiate HealthKit access. | A native Swift/SwiftUI app with a usable initial screen and navigation ready for the run library; a user-facing HealthKit access flow for reading running workouts; handling HealthKit unavailability and completion or failure of the access request without claiming that an empty result proves read permission was denied; installation, launch, and the access flow are demonstrable on both device families. | R2: retrieving workouts and handling empty read results; R3: browsing runs; R4: workout detail; health-data writes remain outside this epic. | none | specs/healthkit-run-library-01-app-foundation-and-authorization |
| R2 | Run ingestion | Make accessible HealthKit running workouts available to Fava. | Read running workouts and expose their identities and available summary values for later presentation; repeated ingestion does not duplicate runs; empty results and read failures have verifiable outcomes; HealthKit remains authoritative. | R3: the user-facing run list; R4: the individual run screen; automatic background updates and ongoing reconciliation of edited or deleted workouts are deferred beyond this initial import slice. | R1 | specs/healthkit-run-library-02-run-ingestion |
| R3 | Run library | Let the person browse the runs available to Fava. | A chronological run list using ingested workouts, basic summaries sufficient to distinguish runs, and loading, empty, and failure presentations; selection identifies the chosen run for detail navigation. | R4: displaying the selected run's detail; search, filters, and custom sorting are deferred beyond this initial browsing slice; advanced trends and analytics remain outside this epic. | R2 | specs/healthkit-run-library-03-run-library |
| R4 | Run detail | Let the person inspect a run selected from the library. | Open the selected workout, show its available basic summary values, handle missing values or an unavailable workout, and return to the library; the library-to-detail journey is demonstrable on iPhone and iPad. | AI analysis, advanced trends and analytics, sharing, and editing workouts remain outside this epic; richer route, sample, and split presentations are deferred beyond the proposed basic detail slice. | R3 | specs/healthkit-run-library-04-run-detail |

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

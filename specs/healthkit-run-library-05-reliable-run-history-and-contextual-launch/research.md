# R3.5 research

Baseline: 922b9c9ab0c25559bfd327fff1b74127e1952f31, 2026-10-16.
Research used repository source, approved contract and predecessor verification;
no claim about undocumented Apple permission choices is needed.

| Decision | Evidence and rationale | Alternative considered |
| --- | --- | --- |
| Single content-versioned file, DEC-001 | RunSnapshotStore.swift already uses protected atomic writes to runs-v1.json; one file prevents fallback resurrection. DEC-007 corrects the initial timestamp conclusion: the whole legacy snapshot came from one completed read, so valid capturedAt establishes all saved rows’ prior observation time. | A second v2 file would require a multi-file transaction and durable fallback suppression. |
| Save before publish, DEC-002 | RunIngestion.swift publishes only after save, but currently replaces the complete collection and collapses saving failure into source failure. Preserve its transactional boundary while changing merge/outcome semantics. | Publishing new rows before saving contradicts clarified FR-007. |
| Separate local recovery, DEC-003 | Current init catches load failure and recommends a new source read, which could overwrite unreadable history. | Treating error as empty loses the recovery distinction in FR-018. |
| Generation plus transport token, DEC-004 | WorkoutReading exposes callback reads without cancellation; requestRead currently uses one attemptID. MainActor synchronous store calls permit a single commit boundary. | Clearing attemptID alone permits overlapping physical reads after clear. |
| Explicit route events, DEC-005 | RootView currently starts setup and requests once on its library button; RunLibraryView settings sheet leaves library mounted. | onAppear/scenePhase reads repeat on presentation or foregrounding. |

R1–R3 Swift source and tests match recorded R3 source f112ed33ffeb6a31256f1ffb764aceda88ccd523
at this baseline (Info.plist has subsequent metadata). PR #7's signed owner merge
ae763f34a17324ff4e51abe6881be479f8638782 integrates those dependencies. Their
verification records identify successful 13/25/41-test family checkpoints, with
physical acceptance still pending. Main push run 38920312080 passed at the inspected
baseline. These establish integration prerequisites, not R3.5 acceptance.

Existing replacement assertions in RunIngestionTests.swift and RunLibraryUITests.swift
must adopt the approved controlled supersession; preserve all other regression
assertions. FoundationUITests launch helpers must support both contextual launch
and setup fixtures. No new package, HealthKit permission, background query, detail
screen or service is required. Research unknowns are resolved by DEC-001–008;
performance and physical-device results remain measurements for implementation.

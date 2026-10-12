# R1–R3 Specification Consistency Review

Date: 2026-10-12
Scope: three specification contracts in one delivery PR, against the agreed HealthKit Run Library roadmap and constitution 1.1.0.
Delivery branch: `healthkit-run-library-01-app-foundation-and-authorization`.
Base: main `03fb483a0b20283eb4cc1497eed3f5d45665a46a`; R1 was validated from signed head `783a69179685a636a8cbcc6b121ff6c02fea5745` without repeating specify/clarify or changing its requirements.

## Review result

No unresolved critical/high findings, product clarification markers, scope overlaps, or contradictory assumptions remain. All 44 functional requirements have feature-local story mappings and citations to existing numbered acceptance scenarios. The three built-in requirements-quality checklists pass 48/48 criteria. These are specification-quality findings, not implementation or real-device test results.

| Milestone | Canonical feature directory | Requirements | Stories | Acceptance scenarios | Measurable outcomes | Dependency |
|---|---|---:|---:|---:|---:|---|
| R1 | `specs/healthkit-run-library-01-app-foundation-and-authorization` | 13 | 3 | 16 | 6 | none |
| R2 | `specs/healthkit-run-library-02-run-ingestion` | 14 | 3 | 20 | 6 | R1 |
| R3 | `specs/healthkit-run-library-03-run-library` | 17 | 4 | 28 | 7 | R2; R1 transitively |

## Accepted product clarifications

| Milestone | Owner answer | Integration |
|---|---|---|
| R1 | VoiceOver and every Dynamic Type size, including accessibility sizes | FR-012, US1 scenario 5, SC-006 |
| R1 | System-reported cancellation shows “Request not completed”, with deliberate retry when available | FR-013, US3 scenarios 3–5, SC-003 |
| R2 | All accessible running history without a date limit | FR-002, US1 scenarios 1, 2, and 5, SC-001 |
| R2 | Start date/time, recorded duration, and distance when available | FR-004, US1 scenarios 1, 3, and 6, SC-003 |
| R2 | Saved runs are fine across launches: keep the last successful result as previously loaded | FR-013, US2 scenarios 4–7, SC-006 |
| R3 | Show saved runs immediately, then read on each library entry; allow manual refresh | FR-005, US2 scenarios 1, 2, and 10–12, SC-003 |
| R3 | Device-preferred units by default, with an app settings screen | FR-004, FR-016, FR-017, US4, SC-002 and SC-007 |
| R3 | Keep saved rows visible during loading/failure, with a distinct current-attempt notice and retry when available | FR-009, US2 scenarios 13 and 14, SC-003 |

Identifiers in this table are scoped by their milestone and its canonical directory above; repeated FR/US/SC numbers across milestones are intentional.

## Scope ownership and handoffs

| Concern | Owner | Consumer and boundary |
|---|---|---|
| Install/launch, navigation foundation, deliberate workout-record read-access request | R1 | R2/R3 reuse it; neither starts permission requests automatically |
| Source eligibility, all-history reads, canonical identity, source start instant/recorded duration/available distance | R2 | R3 formats and displays the result without reading richer categories or inferring new measurements |
| Complete results, deduplication, read outcomes, saved last-successful collection | R2 | R3 consumes the current attempt and saved collection separately |
| Foreground library entry, Refresh/Retry, loading/empty/error/unavailable messages | R3 | Invokes R2 once per valid trigger; an active attempt is reused |
| Chronological rows and distance settings | R3 | Settings control display formatting only, retain the selected mode, and preserve R2 values |
| Intended run selection | R3 | Hands off the exact source workout identity; actual detail content and unavailable-detail recovery remain R4 |

R1's neutral destination and prohibition on reading workouts apply to R1's demonstrable foundation. R2 adds ingestion and R3 adds populated presentation in later milestone composition; neither rewrites R1's authorization contract. The agreed dependency chain remains R1 → R2 → R3 → future R4.

## Shared read and saved-result semantics

| Situation | R2 contract | R3 presentation |
|---|---|---|
| No completed read and no saved result | not-requested before an available-source trigger | Library entry starts one read and shows loading; no premature successful-empty or permission claim |
| Saved nonempty/empty result at entry | Saved result is independent of the current attempt | Show previously loaded rows/empty result without waiting; start one fresh read when available |
| Loading with saved rows | No partial successful result; saved collection stays intact | Keep saved rows browsable/selectable with a separate loading notice |
| Complete nonempty success | Replace the saved collection with this complete unique set | Show its rows newest-first with exact source identities |
| Complete empty success | Replace the saved collection with empty | Remove old rows; show neutral successful-empty, without inferring denial or absent recorded history |
| Read failure or HealthKit unavailable | Distinct unsuccessful state; preserve the last saved collection | Preserve previously loaded rows/empty presentation with a separate notice; retry only when available |
| Interrupted/terminated attempt | No false completion or saved partial data; no stale loading restored | Restore only a previously loaded complete collection; a later available-source library entry starts a fresh attempt |

Access-request completion, failure, and system-reported cancellation in R1 are not ingestion outcomes. In particular, cancelled authorization never becomes a successfully empty ingestion, and request completion never guarantees readable records. Saved runs never prove current source visibility or permission.

## Findings and disposition

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| CF-001 | Medium, resolved | “Saved run” could imply a second authoritative source or an unbounded synchronization promise | R2 FR-013 defines a derived last-successful snapshot. A successful explicit read replaces it, including empty; this adds no automatic source observation or per-record edit/deletion reconciliation |
| CF-002 | Medium, resolved | “Read on entry” could accidentally request authorization or start repeated reads on view/layout updates | R3 FR-005/FR-010 distinguish deliberate entry, Refresh, and an active attempt; layout updates do not reread and no trigger starts authorization |
| CF-003 | Medium, resolved | R3 unit preferences could alter saved source quantities or silently expand settings scope | The owner requested the screen. R3 FR-016/FR-017 require only distance units, retain the preference, and preserve source values; a setting change itself does not read, while later navigation follows the entry rule |
| CF-004 | Low, resolved | R2 interrupted/offline behavior was expressed in edge cases without enough numbered acceptance evidence | Added R2 US1 scenario 7 and US3 scenario 6 and linked FR-012/FR-014 |
| CF-005 | Low, resolved | R3's offline/local-first requirement had an accessibility citation rather than direct offline acceptance | Added R3 US1 scenario 7 and linked FR-012 |
| CF-006 | Medium, resolved | Loading, failed refresh, and saved-empty could be mistaken for a new successful result | Owner chose visible saved results with separate attempt notices; R3 US2 scenarios 13/14 and FR-009 cover both saved nonempty and empty |

The usual newest-first chronological default, stable ordering for equal start instants, current device date/time formatting, and ordinary persistent unit-preference behavior are documented defaults. They add no user-selectable sorting, richer measurement, or new authorization scope.

## Requirement and acceptance audit

- Each milestone has consecutive, unique, feature-local FR identifiers. Each FR is listed in an applicable story and cites valid numbered acceptance scenarios; every story has an independent test description and priority.
- R1 can be tested with navigation and controlled authorization outcomes without ingestion or a populated list.
- R2 can be tested using synthetic read outcomes and a consuming result observer without R3 screens; its saved/relaunch and repeated-read behavior is observable.
- R3 can be tested with synthetic R2 results and an identity-selection observer without actual HealthKit or R4's detail screen. US4 independently tests display settings.
- Missing distance, recorded zero, recorded-versus-elapsed duration, duplicate identities, distinct matching summaries, multi-year history, current date/time preferences, converted units, accessibility, concurrency, interruptions, and read-result provenance have explicit acceptance evidence.
- Automated checks remain mandatory for every implemented user story. Physical iPhone/iPad HealthKit evidence must be recorded separately with sanitized outcomes; synthetic fixtures and simulator results do not establish physical-device authorization or real source access.

## Constitution and roadmap compliance

Flow-Forward is preserved: these are unmerged Draft specification contracts; no specification is marked completed and no merged requirements are changed. The approved roadmap is byte-identical to main. Every spec uses the exact agreed directory and parent entry. The owner-requested distance settings screen is confined to R3 basic-summary formatting, with no new roadmap slice or unrelated settings.

Swift/SwiftUI native iPhone/iPad and local-first/HealthKit-authoritative constraints remain inherited from the constitution; no application implementation is introduced. No plan, tasks, research, data model, or app source was generated. No external tracker changes were made. R4 detail, search, filtering, custom sorting, richer measurements, background observation, ongoing source-change reconciliation, writes, accounts, cloud services, sync, sharing, and analytics remain outside this delivery.

## Clarification coverage and deferred work

| Clarification taxonomy | Status | Evidence or disposition |
|---|---|---|
| Functional scope and behavior | Clear | Explicit milestone boundaries and R4 deferrals |
| Domain and data model | Resolved | Stable source identities, agreed summaries, distinct attempts and saved snapshots |
| Interaction and UX | Resolved | Entry/Refresh/Retry, visible saved results, settings and selection |
| Non-functional quality | Resolved | VoiceOver/all Dynamic Type, local/offline behavior, measurable correctness and failure coverage |
| External dependencies | Clear | HealthKit only, workout-record read scope, unavailability and failures |
| Edge cases | Resolved | Empty/failed/partial/interrupted/concurrent/missing/zero/tied/saved-result cases |
| Constraints and tradeoffs | Clear | Constitution and unchanged roadmap; derived local retention rather than ongoing sync |
| Terminology and consistency | Clear | Source identity, recorded duration, saved collection, current attempt, and permission-choice distinctions |
| Completion signals | Clear | 19 measurable outcomes, independent synthetic evidence, separate physical-device requirements |
| Placeholders | Deferred to planning | Supported OS versions and implementation mechanisms; no unanswered material product marker |

No material product clarification is waiting for an owner answer. Implementation architecture, source-query mechanisms, supported deployment versions, and diagnostic detail belong to later planning. Formal spec/plan/tasks analysis and convergence were not invoked because their lifecycle prerequisites intentionally do not exist.

## Quality checklist and local verification evidence

- Built-in quality review: R1 16/16 unchanged; R2 11/16 → 16/16; R3 11/16 → 16/16, with no final unchecked built-in items.
- Reviewer-owned custom artifacts: existing R1 clarification checklist, new R2 ingestion checklist, and new R3 library checklist each have 8 unchecked human-review items. Agent review found no critical inconsistencies; these markers are not implementation or product-answer status.
- `python3 .github/checks/sdd.py --base origin/main --head HEAD`: passed against the working specification tree and the existing signed R1 history. Each new message is also validated when staged, and published head is validated again.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .github/checks -p 'test_*.py' -q`: 20 fixture tests passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/github -p 'test_*.py' -q`: 7 commit-builder tests passed.
- `python3 .github/checks/tooling.py`: passed.
- `python3 .github/checks/native.py classify --base origin/main`: onboarding. No app project exists; native CI is provisioned but unvalidated and its intentional skip is not native-test evidence.
- Acceptance-reference audit checked all 44 FR/story mappings and all cited numbered scenarios, exact roadmap directory/entry relationships, local links, absence of product markers, and absence of plan/tasks.
- Git whitespace checks passed; roadmap bytes and R1 specification/checklist bytes remain unchanged by this delivery.

The existing before-specify branch hook was run once per new feature with the exact delivery branch and existing-branch reuse; each command had an explicit agreed `SPECIFY_FEATURE_DIRECTORY` and no feature-state persistence. Clarify/checklist hooks were disabled. The checklist helper's plan prerequisite was adapted using the checked-in template and spec-only context rather than creating missing planning artifacts.

Publication uses separate GraphQL-signed feature commits and a review-report commit on the same branch, with expected-head guards and exact tree/parent/message/signature verification. Final latest-head Actions results and commit URLs are recorded in the combined PR description after publication. Human owner review remains mandatory before merge; this review does not authorize merging.

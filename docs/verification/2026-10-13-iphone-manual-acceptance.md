# Physical iPhone manual acceptance: partial observation

Date reported: 2026-10-13. Tester: repository owner, reporting in the Codex chat.
Device and OS, as reported: iPhone 13 mini, iOS 27.
Installed commit, installation method and signing profile: not supplied.
The current PR #7 head when this report was recorded was
`a8d42b87af07117847e91bb5f87ed147107e1b4d`; this is repository context,
not a claim that the owner tested that revision. No physical device was attached
to the cloud worker and no independent device measurement was performed.

The owner reported: "tested on my phone an apps launches, request healthkit
permissions then displays real run". The following observations are recorded as
user-reported passes for this limited path:

| Milestone | Reported observation | Coverage boundary |
| --- | --- | --- |
| R1 | Application launches and requests HealthKit permissions on the physical iPhone. | Supports the iPhone launch/request aspects of FR-001 and FR-006. Request initiation timing, categories, neutral completion wording, denied/cancelled/repeated requests and navigation were not explicitly checked. |
| R2 | A real run becomes available after the request flow. | Supports actual device retrieval in US1. Complete history, running-only eligibility, identity, source-value fidelity, repeat reads, snapshot persistence and failure/empty cases were not explicitly checked. |
| R3 | The application displays the real run. | Supports the populated-library portion of FR-001 and the iPhone end-to-end demonstration in SC-006. Formatting, ordering, selection, unit settings and other library states were not explicitly checked. |

This report does not establish every clause of any referenced FR or success
criterion. It does not assert that request completion proves permission, and
does not claim a known-workout/source-value comparison or an entire-history audit.
No personal workout identifiers, dates, distances, screenshots or exports are
included.

## Remaining acceptance

- Confirm the installed revision and installation method before attributing
  these observations to an exact build.
- Physical iPad installation, request, real retrieval, library and selection.
- Remaining authorization outcomes and navigation/background behavior; record
  cancellation/failure/unavailability as not exercised if not safely reproducible.
- Known-history/source-value comparison, repeat refresh without duplicates,
  saved-data relaunch, offline use and neutral empty/read-error presentations.
- Library order/formatting, selection, distance modes and retained preference.
- Actual VoiceOver, every Dynamic Type size, orientation/resized iPad layouts,
  device clock/time-zone/measurement preferences and purpose comprehension.
- Twenty measured launches per device family against R1 SC-001.

The milestone quickstart files remain the full acceptance checklists. All three
specifications remain active; no task, story or feature acceptance status changes
on the basis of this partial report. Linear implementation tasks remain Done and
stories remain In Review pending the remaining evidence and owner acceptance.
No merge or auto-merge is authorized by this report.

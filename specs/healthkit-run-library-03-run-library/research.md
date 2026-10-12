# R3 research

- SwiftUI List provides lazy, scrollable native row rendering on both families.
  Date ordering plus UUID ties avoids locale-dependent sorting or merged runs.
- DateFormatter current locale/time-zone short time follows current clock format;
  DateComponentsFormatter displays recorded duration. NumberFormatter with two
  decimals provides explicit km/mi units and testable half-increment rounding.
- A persisted distance mode is presentation-only; Device reads current locale
  measurement-system preference. No cached preference inference from source records.
- Trigger ingestion on explicit root-to-library navigation, not body or onAppear.
  R2 rejects overlap; a settings sheet leaves the library mounted and does not
  create a destination re-entry. Active callback continues across backgrounding.
- Standard buttons, wrapped text and native scrolling support VoiceOver and all
  Dynamic Type sizes; actual VoiceOver and iPad resize require manual walkthroughs.

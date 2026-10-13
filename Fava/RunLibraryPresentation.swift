import Combine
import Foundation

enum RunLibraryPresentation {
    static func rows(_ runs: [RunRecord]) -> [RunRecord] {
        runs.sorted { a, b in
            a.startDate == b.startDate ? a.id.uuidString < b.id.uuidString : a.startDate > b.startDate
        }
    }
    static func notice(_ state: IngestionState) -> String {
        switch state {
        case .notRequested: return "No read requested yet."
        case .loading: return "Loading running workouts…"
        case .successfulNonempty: return "Runs loaded from the latest read."
        case .successfulEmpty: return "No running workouts were returned by this read."
        case .failed: return "Running workouts could not be loaded. You can try again."
        case .unavailable: return "HealthKit is unavailable on this device."
        }
    }
}

enum RunFormatting {
    static func start(_ date: Date, locale: Locale, timeZone: TimeZone) -> String {
        let formatter = DateFormatter()
        formatter.locale = locale
        formatter.timeZone = timeZone
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
    static func duration(_ seconds: TimeInterval) -> String {
        let formatter = DateComponentsFormatter()
        formatter.allowedUnits = [.hour, .minute, .second]
        formatter.unitsStyle = .positional
        formatter.zeroFormattingBehavior = .pad
        return formatter.string(from: seconds) ?? "Duration unavailable"
    }
    static func distance(_ distance: WorkoutDistance?, unit: DistanceDisplayUnit, locale: Locale) -> String {
        guard let distance else { return "Distance unavailable" }
        let formatter = NumberFormatter()
        formatter.locale = locale
        formatter.numberStyle = .decimal
        formatter.minimumFractionDigits = 2
        formatter.maximumFractionDigits = 2
        let value = formatter.string(from: NSNumber(value: distance.metres / unit.metresPerUnit)) ?? "—"
        return value + " " + unit.symbol
    }
}

@MainActor
final class RunSelection: ObservableObject {
    @Published private(set) var selectedID: UUID?
    private let handoff: (UUID) -> Void
    init(handoff: @escaping (UUID) -> Void = { _ in }) { self.handoff = handoff }
    func select(_ id: UUID) {
        selectedID = id
        handoff(id)
    }
}

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
        case .notRequested: return "No read requested in this session."
        case .loading: return "Loading running workouts…"
        case .failed: return "Running workouts could not be loaded. You can try again."
        case .unavailable: return "HealthKit is unavailable on this device."
        case .sourceSuccess(let count, savingFailed: true):
            return "This read returned \(count) \(count == 1 ? "run" : "runs"), but they could not be saved locally. Saved history is unchanged. Retry performs a new read."
        case .sourceSuccess(0, savingFailed: false):
            return "This read returned no accessible runs. Displayed runs were saved earlier."
        case .sourceSuccess(let count, savingFailed: false):
            return "This read returned \(count) \(count == 1 ? "run" : "runs"). The observation was saved."
        }
    }

    static func savedHistoryCount(_ history: RetainedRunHistory?) -> String {
        let count = history?.runs.count ?? 0
        return "Saved history: \(count) \(count == 1 ? "run" : "runs")."
    }

    static func savedObservation(_ history: RetainedRunHistory?, isPrior: Bool, locale: Locale, timeZone: TimeZone) -> String {
        guard let observation = history?.latestSavedObservation else { return "No saved read observation." }
        let count = observation.returnedIDs.count
        let prefix = isPrior ? "Prior saved read" : "Latest saved read"
        let time = observation.observedAt.map { "Saved observation: " + RunFormatting.start($0, locale: locale, timeZone: timeZone) + "." }
            ?? "Saved observation time unknown."
        return "\(prefix) returned \(count) \(count == 1 ? "run" : "runs"). \(time)"
    }

    static func rowProvenance(_ id: UUID, history: RetainedRunHistory?, locale: Locale, timeZone: TimeZone) -> String {
        let membership: String
        if let observation = history?.latestSavedObservation {
            membership = observation.returnedIDs.contains(id) ? "Returned by latest saved read." : "Unobserved in latest saved read."
        } else {
            membership = "Latest saved read membership unknown."
        }
        let date = history?.lastObservedAtByID[id]
        let time = date.map { RunFormatting.start($0, locale: locale, timeZone: timeZone) } ?? "unknown"
        return "\(membership) Last observed: \(time)."
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

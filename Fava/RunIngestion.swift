import Combine
import Foundation

enum IngestionState: Equatable {
    case notRequested, loading, failed, unavailable
    case sourceSuccess(returnedCount: Int, savingFailed: Bool)

    var offersRetry: Bool {
        switch self {
        case .failed, .sourceSuccess(_, savingFailed: true): return true
        default: return false
        }
    }
}

enum LocalHistoryState: Equatable {
    case absent
    case readable(RetainedRunHistory)
    case recovery(String)
}

// Candidate construction has no clock, storage or publication side effects.
enum RunHistoryMerge {
    static func candidate(saved: RetainedRunHistory?, returned: [RunRecord], observedAt: Date) throws -> RetainedRunHistory {
        try saved?.validate()
        var returnedIDs = Set<UUID>()
        var unique: [RunRecord] = []
        for record in returned {
            // Invalid duplicate deliveries cannot be hidden by first-wins deduplication.
            try record.validateForHistory()
            if returnedIDs.insert(record.id).inserted { unique.append(record) }
        }
        var runs = saved?.runs ?? []
        var positions = Dictionary(uniqueKeysWithValues: runs.enumerated().map { ($0.element.id, $0.offset) })
        var times = saved?.lastObservedAtByID ?? [:]
        for record in unique {
            if let position = positions[record.id] {
                runs[position] = record
            } else {
                positions[record.id] = runs.count
                runs.append(record)
            }
            times[record.id] = observedAt
        }
        return try RetainedRunHistory(runs: runs, lastObservedAtByID: times,
                                      latestSavedObservation: SavedReadObservation(observedAt: observedAt, returnedIDs: returnedIDs))
    }
}

@MainActor
final class RunIngestionModel: ObservableObject {
    @Published private(set) var state: IngestionState = .notRequested
    @Published private(set) var localHistory: LocalHistoryState = .absent
    @Published private(set) var isPriorSavedObservation = false
    @Published private(set) var isAvailable = false
    @Published private var inFlightRead: InFlightRead?
    private let reader: WorkoutReading
    private let historyStore: RunHistoryStoring
    private let clock: () -> Date
    private var historyGeneration: UInt64 = 0
    private var isCompletingRead = false

    private struct InFlightRead {
        let token: UUID
        let generation: UInt64
    }

    init(reader: WorkoutReading, historyStore: RunHistoryStoring, clock: @escaping () -> Date = Date.init) {
        self.reader = reader
        self.historyStore = historyStore
        self.clock = clock
        isAvailable = reader.isAvailable
        loadLocalHistory()
    }

    var savedHistory: RetainedRunHistory? {
        if case .readable(let history) = localHistory { return history }
        return nil
    }
    var localRecoveryMessage: String? {
        if case .recovery(let message) = localHistory { return message }
        return nil
    }
    var isTransportActive: Bool { inFlightRead != nil }
    var canRead: Bool { isAvailable && !isTransportActive && localRecoveryMessage == nil }

    func updateAvailability() { isAvailable = reader.isAvailable }

    func retryLocalLoad() {
        guard localRecoveryMessage != nil, !isTransportActive else { return }
        loadLocalHistory()
    }

    private func loadLocalHistory() {
        do {
            let history = try historyStore.loadHistory()
            try history?.validate()
            localHistory = history.map(LocalHistoryState.readable) ?? .absent
            isPriorSavedObservation = history?.latestSavedObservation != nil
            historyGeneration += 1
        } catch {
            localHistory = .recovery("Saved run history could not be read. Retry saved history before reading running workouts; the saved document has been kept.")
        }
    }

    func requestRead() {
        guard !isTransportActive, localRecoveryMessage == nil else { return }
        updateAvailability()
        guard isAvailable else { state = .unavailable; return }
        let read = InFlightRead(token: UUID(), generation: historyGeneration)
        // Install the physical guard before calling readers that may complete synchronously.
        inFlightRead = read
        state = .loading
        reader.read { [weak self] result in self?.finishRead(result, read: read) }
    }

    private func finishRead(_ result: Result<[RunRecord], Error>, read: InFlightRead) {
        guard inFlightRead?.token == read.token, !isCompletingRead else { return }
        // Consume this callback before store hooks can synchronously deliver duplicates.
        isCompletingRead = true
        // Keep the physical guard through the commit, including injected store callbacks.
        defer {
            inFlightRead = nil
            isCompletingRead = false
        }
        guard read.generation == historyGeneration else { return }
        switch result {
        case .failure:
            state = .failed
        case .success(let records):
            let candidate: RetainedRunHistory
            do {
                candidate = try RunHistoryMerge.candidate(saved: savedHistory, returned: records, observedAt: clock())
            } catch {
                state = .failed
                return
            }
            let returnedCount = candidate.latestSavedObservation?.returnedIDs.count ?? 0
            do {
                try historyStore.saveHistory(candidate)
            } catch {
                state = .sourceSuccess(returnedCount: returnedCount, savingFailed: true)
                return
            }
            localHistory = .readable(candidate)
            isPriorSavedObservation = false
            state = .sourceSuccess(returnedCount: returnedCount, savingFailed: false)
        }
    }
}

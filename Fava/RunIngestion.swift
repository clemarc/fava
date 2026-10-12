import Combine
import Foundation

enum IngestionState: Equatable {
    case notRequested, loading, successfulNonempty, successfulEmpty, failed, unavailable
}

@MainActor
final class RunIngestionModel: ObservableObject {
    @Published private(set) var state: IngestionState = .notRequested
    @Published private(set) var savedSnapshot: RunSnapshot?
    @Published private(set) var isPreviouslyLoaded = false
    @Published private(set) var isAvailable = false
    @Published private(set) var cacheNotice: String?
    private let reader: WorkoutReading
    private let snapshotStore: RunSnapshotStoring
    private var attemptID: UUID?

    init(reader: WorkoutReading, snapshotStore: RunSnapshotStoring) {
        self.reader = reader
        self.snapshotStore = snapshotStore
        isAvailable = reader.isAvailable
        do {
            let saved = try snapshotStore.load()
            savedSnapshot = saved
            isPreviouslyLoaded = saved != nil
        } catch {
            cacheNotice = "Previously loaded runs could not be restored. You can request a fresh read."
        }
    }

    var canRead: Bool { isAvailable && state != .loading }

    func updateAvailability() { isAvailable = reader.isAvailable }

    func requestRead() {
        guard state != .loading else { return }
        updateAvailability()
        isPreviouslyLoaded = savedSnapshot != nil
        guard isAvailable else { state = .unavailable; return }
        let identifier = UUID()
        attemptID = identifier
        state = .loading
        reader.read { [weak self] result in
            guard let self, self.attemptID == identifier, self.state == .loading else { return }
            self.attemptID = nil
            switch result {
            case .failure:
                self.state = .failed
            case .success(let records):
                var identities = Set<UUID>()
                let unique = records.filter { identities.insert($0.id).inserted }
                let snapshot = RunSnapshot(runs: unique)
                do {
                    try self.snapshotStore.save(snapshot)
                    self.savedSnapshot = snapshot
                    self.isPreviouslyLoaded = false
                    self.cacheNotice = nil
                    self.state = unique.isEmpty ? .successfulEmpty : .successfulNonempty
                } catch {
                    self.state = .failed
                    self.cacheNotice = "Runs could not be saved locally. Previously loaded runs have been kept. Try again."
                }
            }
        }
    }
}

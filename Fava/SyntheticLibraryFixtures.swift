#if DEBUG
import Foundation

@MainActor
final class SyntheticWorkoutReader: WorkoutReading {
    let fixture: String
    private(set) var reads = 0
    var isAvailable: Bool { !fixture.contains("unavailable") }
    init(fixture: String) { self.fixture = fixture }
    enum SyntheticError: Error { case failed }

    static let runs: [RunRecord] = [
        RunRecord(id: UUID(uuidString: "00000000-0000-0000-0000-000000000002")!, startDate: Date(timeIntervalSince1970: 1_704_067_200), duration: 90, distance: WorkoutDistance(value: 0, unit: .metres)),
        RunRecord(id: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!, startDate: Date(timeIntervalSince1970: 1_704_067_200), duration: 90, distance: nil),
        RunRecord(id: UUID(uuidString: "00000000-0000-0000-0000-000000000003")!, startDate: Date(timeIntervalSince1970: 1_000_000_000), duration: 3600, distance: WorkoutDistance(value: 5000, unit: .metres))
    ]

    func read(completion: @escaping (Result<[RunRecord], Error>) -> Void) {
        reads += 1
        guard !fixture.contains("pending") else { return }
        let result: Result<[RunRecord], Error>
        if fixture.contains("failed") || (fixture == "failure-then-success" && reads == 1) {
            result = .failure(SyntheticError.failed)
        } else if fixture == "empty" || (fixture == "entry-switches" && reads > 1) {
            result = .success([])
        } else { result = .success(Self.runs) }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { completion(result) }
    }

    static func snapshotStore(fixture: String, session: String) -> FileRunSnapshotStore {
        let directory = URL.applicationSupportDirectory.appendingPathComponent("Fava-UITests-" + session, isDirectory: true)
        let cache = FileRunSnapshotStore(directory: directory)
        if fixture.hasPrefix("saved-"), !FileManager.default.fileExists(atPath: cache.fileURL.path) {
            try? cache.save(RunSnapshot(runs: fixture == "saved-empty-pending" ? [] : runs))
        }
        return cache
    }
}
#endif

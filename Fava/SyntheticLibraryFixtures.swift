#if DEBUG
import Foundation
import SwiftUI

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
    static let priorTime = Date(timeIntervalSince1970: 1_700_000_000)
    static var initialRuns: [RunRecord] { [runs[1], runs[0]] }
    static var subsetRuns: [RunRecord] {
        let b = runs[0]
        return [RunRecord(id: b.id, startDate: b.startDate, duration: 180, distance: nil), runs[2]]
    }
    var observationTime: Date {
        Date(timeIntervalSince1970: 1_704_067_200).addingTimeInterval(Double(reads) * 60)
    }

    func read(completion: @escaping (Result<[RunRecord], Error>) -> Void) {
        reads += 1
        SyntheticLaunchProbe.shared.reads += 1
        guard !fixture.contains("pending") else { return }
        let result: Result<[RunRecord], Error>
        if fixture.hasPrefix("save-failure-") {
            result = .success(reads == 1 ? Self.subsetRuns : [])
        } else if fixture == "retention-sequence" {
            result = .success(reads == 1 ? Self.initialRuns : (reads == 2 ? Self.subsetRuns : []))
        } else if fixture.contains("failed") || (fixture == "failure-then-success" && reads == 1) {
            result = .failure(SyntheticError.failed)
        } else if fixture == "empty" || fixture == "saved-empty-result" || (fixture == "entry-switches" && reads > 1) {
            result = .success([])
        } else { result = .success(Self.runs) }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { completion(result) }
    }

    static func snapshotStore(fixture: String, session: String) -> FileRunSnapshotStore {
        let directory = URL.applicationSupportDirectory.appendingPathComponent("Fava-UITests-" + session, isDirectory: true)
        let cache = FileRunSnapshotStore(directory: directory)
        // Fixture seeding never overwrites a prior session's committed bytes.
        if !FileManager.default.fileExists(atPath: cache.fileURL.path) {
            if fixture == "save-failure-populated" || fixture == "recovery-read-error" || fixture == "recovery-read-once" || fixture == "recovery-empty-once" || fixture == "recovery-absent-once" {
                if fixture != "recovery-absent-once" {
                    try? cache.save(RunSnapshot(runs: fixture == "recovery-empty-once" ? [] : initialRuns, capturedAt: priorTime))
                }
            } else if fixture == "save-failure-empty" {
                try? cache.save(RunSnapshot(runs: [], capturedAt: priorTime))
            } else if fixture == "save-failure-untimed" || fixture == "saved-untimed-pending" {
                if let encoded = try? JSONEncoder().encode(initialRuns),
                   let records = try? JSONSerialization.jsonObject(with: encoded),
                   let data = try? JSONSerialization.data(withJSONObject: ["schemaVersion": 1, "runs": records]) {
                    try? RunHistoryFileIO.live.writeAtomically(data, cache.fileURL)
                }
            } else if fixture == "recovery-corrupt" {
                try? RunHistoryFileIO.live.writeAtomically(Data("corrupt synthetic history".utf8), cache.fileURL)
            } else if fixture.hasPrefix("saved-") {
                try? cache.save(RunSnapshot(runs: fixture == "saved-empty-pending" ? [] : runs, capturedAt: priorTime))
            }
        }
        if fixture.hasPrefix("save-failure-") {
            return FileRunSnapshotStore(directory: directory, historyIO: RunHistoryFileIO(
                read: RunHistoryFileIO.live.read, writeAtomically: { _, _ in throw SyntheticError.failed }))
        }
        if fixture == "recovery-read-once" || fixture == "recovery-empty-once" || fixture == "recovery-absent-once" || fixture == "recovery-read-error" {
            var loads = 0
            return FileRunSnapshotStore(directory: directory, historyIO: RunHistoryFileIO(
                read: { url in
                    loads += 1
                    if loads == 1 || fixture == "recovery-read-error" { throw CocoaError(.fileReadNoPermission) }
                    return try RunHistoryFileIO.live.read(url)
                }, writeAtomically: RunHistoryFileIO.live.writeAtomically))
        }
        return cache
    }
}

// Observable, DEBUG-only evidence for synthetic UI tests. No production data.
@MainActor
final class SyntheticLaunchProbe: ObservableObject {
    static let shared = SyntheticLaunchProbe()
    @Published var reads = 0
    @Published var requests = 0
}

@MainActor
final class SyntheticAccessProbe: HealthAccessProviding {
    private let provider: HealthAccessProviding
    init(provider: HealthAccessProviding) { self.provider = provider }
    var isAvailable: Bool { provider.isAvailable }
    func request(completion: @escaping (HealthAccessOutcome) -> Void) {
        SyntheticLaunchProbe.shared.requests += 1
        provider.request(completion: completion)
    }
}

@MainActor
struct SyntheticLaunchEvidence: View {
    let route: LaunchRoute
    @ObservedObject private var probe = SyntheticLaunchProbe.shared
    var body: some View {
        VStack {
            Text("Launch route: \(String(describing: route))").accessibilityIdentifier("launch-route")
            Text("Source reads: \(probe.reads)").accessibilityIdentifier("source-read-count")
            Text("Access requests: \(probe.requests)").accessibilityIdentifier("access-request-count")
        }
        .font(.caption)
        // Test instrumentation keeps a constant footprint; app content still
        // exercises the requested Dynamic Type category.
        .dynamicTypeSize(.medium)
    }
}
#endif

import XCTest
import HealthKit
@testable import Fava

@MainActor
final class RunIngestionTests: XCTestCase {
    final class Reader: WorkoutReading {
        var isAvailable = true
        var reads = 0
        var completion: ((Result<[RunRecord], Error>) -> Void)?
        func read(completion: @escaping (Result<[RunRecord], Error>) -> Void) {
            reads += 1
            self.completion = completion
        }
    }
    final class MemoryStore: RunSnapshotStoring {
        var snapshot: RunSnapshot?
        var failLoad = false
        var failSave = false
        func load() throws -> RunSnapshot? {
            if failLoad { throw Failure.synthetic }
            return snapshot
        }
        func save(_ snapshot: RunSnapshot) throws {
            if failSave { throw Failure.synthetic }
            self.snapshot = snapshot
        }
    }
    enum Failure: Error { case synthetic }
    final class QueryStore: WorkoutQueryStore {
        var isAvailable = true
        var sampleType: HKSampleType?
        var predicate: NSPredicate?
        var limit: Int?
        var samples: [HKSample]? = []
        var error: Error?
        func query(sampleType: HKSampleType, predicate: NSPredicate, limit: Int, completion: @escaping ([HKSample]?, Error?) -> Void) {
            self.sampleType = sampleType
            self.predicate = predicate
            self.limit = limit
            completion(samples, error)
        }
    }
    private func record(_ id: UUID = UUID(), distance: WorkoutDistance? = nil) -> RunRecord {
        RunRecord(id: id, startDate: Date(timeIntervalSince1970: 1_500_000_000), duration: 90, distance: distance)
    }
    private func workout(activity: HKWorkoutActivityType = .running, yearOffset: Int = 0, distance: HKQuantity? = nil, indoor: Bool = false) -> HKWorkout {
        let start = Date(timeIntervalSince1970: 1_500_000_000 + Double(yearOffset) * 31_536_000)
        return HKWorkout(activityType: activity, start: start, end: start.addingTimeInterval(180), duration: 90, totalEnergyBurned: nil, totalDistance: distance, metadata: [HKMetadataKeyIndoorWorkout: indoor])
    }
    private func result(_ reader: HealthKitWorkoutReader) async -> Result<[RunRecord], Error> {
        await withCheckedContinuation { continuation in reader.read { continuation.resume(returning: $0) } }
    }

    func testQueryCoversAllRunningHistoryAndPreservesSourceValues() async throws {
        let store = QueryStore()
        let recent = workout(yearOffset: 9, distance: HKQuantity(unit: .mile(), doubleValue: 1))
        let old = workout(yearOffset: -3, indoor: true)
        let zero = workout(distance: HKQuantity(unit: .meter(), doubleValue: 0))
        store.samples = [recent, old, zero, workout(activity: .walking), workout(activity: .cycling)]
        let records = try await result(HealthKitWorkoutReader(store: store)).get()
        XCTAssertEqual(store.sampleType, HKObjectType.workoutType())
        XCTAssertEqual(store.limit, HKObjectQueryNoLimit)
        XCTAssertEqual(store.predicate?.predicateFormat, HKQuery.predicateForWorkouts(with: .running).predicateFormat)
        XCTAssertEqual(Set(records.map(\.id)), Set([recent.uuid, old.uuid, zero.uuid]))
        let run = try XCTUnwrap(records.first { $0.id == recent.uuid })
        XCTAssertEqual(run.startDate, recent.startDate)
        XCTAssertEqual(run.duration, 90)
        XCTAssertNotEqual(run.duration, recent.endDate.timeIntervalSince(recent.startDate))
        XCTAssertEqual(try XCTUnwrap(run.distance).value, 1609.344, accuracy: 0.000001)
        XCTAssertEqual(run.distance?.unit, .metres)
        XCTAssertNil(records.first { $0.id == old.uuid }?.distance)
        XCTAssertEqual(records.first { $0.id == zero.uuid }?.distance?.value, 0)
    }

    func testQueryErrorsRejectIntermediateSamplesAndMalformedResponses() async {
        let store = QueryStore()
        store.samples = [workout()]
        store.error = Failure.synthetic
        if case .success = await result(HealthKitWorkoutReader(store: store)) { XCTFail("Partial records must fail") }
        store.error = nil
        store.samples = nil
        if case .success = await result(HealthKitWorkoutReader(store: store)) { XCTFail("Missing response is not empty success") }
    }

    func testTenRepeatReadsDeduplicateUUIDButKeepMatchingSummaries() {
        let reader = Reader(); let cache = MemoryStore()
        let model = RunIngestionModel(reader: reader, snapshotStore: cache)
        let first = record(); let second = record()
        for _ in 0..<10 {
            model.requestRead()
            reader.completion?(.success([first, first, second]))
            XCTAssertEqual(model.state, .successfulNonempty)
            XCTAssertEqual(Set(model.savedSnapshot?.runs.map(\.id) ?? []), [first.id, second.id])
            XCTAssertEqual(model.savedSnapshot?.runs.count, 2)
        }
        XCTAssertEqual(reader.reads, 10)
    }

    func testLargeCollectionHasNoSilentCap() {
        let reader = Reader();let model = RunIngestionModel(reader: reader, snapshotStore: MemoryStore())
        let runs = (0..<2000).map { _ in record() }
        model.requestRead();reader.completion?(.success(runs))
        XCTAssertEqual(model.savedSnapshot?.runs.count, runs.count)
    }

    func testRecordedZeroDurationAndDistanceUnitsAreNotInferredOrRewritten() {
        let reader = Reader(); let cache = MemoryStore()
        let model = RunIngestionModel(reader: reader, snapshotStore: cache)
        let zero = RunRecord(id: UUID(), startDate: Date(timeIntervalSince1970: 1_500_000_000), duration: 0,
                             distance: WorkoutDistance(value: 0, unit: .kilometres))
        let missing = RunRecord(id: UUID(), startDate: zero.startDate, duration: 0, distance: nil)
        model.requestRead(); reader.completion?(.success([zero, missing]))
        XCTAssertEqual(cache.snapshot?.runs, [zero, missing])
        XCTAssertEqual(model.savedSnapshot?.runs.first?.duration, 0)
        XCTAssertEqual(model.savedSnapshot?.runs.first?.distance?.unit, .kilometres)
        XCTAssertNil(model.savedSnapshot?.runs.last?.distance)
    }

    func testOverlapGuardAndSavedCollectionRemainSeparateFromActiveAttempt() {
        let reader = Reader();let cache = MemoryStore();let old = record()
        cache.snapshot = RunSnapshot(runs: [old])
        let model = RunIngestionModel(reader: reader, snapshotStore: cache)
        XCTAssertEqual(model.state, .notRequested)
        XCTAssertTrue(model.isPreviouslyLoaded)
        model.requestRead();model.requestRead()
        XCTAssertEqual(reader.reads, 1)
        XCTAssertEqual(model.state, .loading)
        XCTAssertEqual(model.savedSnapshot?.runs, [old])
        reader.completion?(.failure(Failure.synthetic))
        XCTAssertEqual(model.state, .failed)
        XCTAssertEqual(cache.snapshot?.runs, [old])
        XCTAssertTrue(model.isPreviouslyLoaded)
    }

    func testSuccessfulEmptyReplacesSavedNonemptyAndRetryReplacesRatherThanAppends() {
        let reader = Reader();let cache = MemoryStore();cache.snapshot = RunSnapshot(runs: [record()])
        let model = RunIngestionModel(reader: reader, snapshotStore: cache)
        model.requestRead();reader.completion?(.success([]))
        XCTAssertEqual(model.state, .successfulEmpty)
        XCTAssertEqual(cache.snapshot?.runs, [])
        XCTAssertFalse(model.isPreviouslyLoaded)
        let new = record()
        model.requestRead();reader.completion?(.success([new]))
        XCTAssertEqual(cache.snapshot?.runs, [new])
    }

    func testUnavailableIsNotEmptyAndLaterExplicitReadWorks() {
        let reader = Reader();reader.isAvailable = false
        let cache = MemoryStore();cache.snapshot = RunSnapshot(runs: [])
        let model = RunIngestionModel(reader: reader, snapshotStore: cache)
        model.requestRead()
        XCTAssertEqual(model.state, .unavailable)
        XCTAssertEqual(reader.reads, 0)
        XCTAssertEqual(model.savedSnapshot?.runs, [])
        XCTAssertTrue(model.isPreviouslyLoaded)
        reader.isAvailable = true;model.requestRead()
        XCTAssertEqual(reader.reads, 1)
        reader.completion?(.success([]))
        XCTAssertEqual(model.state, .successfulEmpty)
    }

    func testFreshSessionRestoresNonemptyAndEmptyWithoutInterruptedAttempt() {
        for runs in [[record()], []] {
            let cache = MemoryStore();cache.snapshot = RunSnapshot(runs: runs)
            let reader = Reader();let first = RunIngestionModel(reader: reader, snapshotStore: cache)
            first.requestRead()
            let fresh = RunIngestionModel(reader: Reader(), snapshotStore: cache)
            XCTAssertEqual(fresh.state, .notRequested)
            XCTAssertEqual(fresh.savedSnapshot?.runs, runs)
            XCTAssertTrue(fresh.isPreviouslyLoaded)
            XCTAssertEqual(first.state, .loading)
            XCTAssertEqual(cache.snapshot?.runs, runs)
        }
    }

    func testCacheSaveFailurePreservesPriorSnapshotAndLoadFailureIsNotEmpty() {
        let reader = Reader();let cache = MemoryStore();let old = record()
        cache.snapshot = RunSnapshot(runs: [old]);cache.failSave = true
        let model = RunIngestionModel(reader: reader, snapshotStore: cache)
        model.requestRead();reader.completion?(.success([record()]))
        XCTAssertEqual(model.state, .failed)
        XCTAssertEqual(cache.snapshot?.runs, [old])
        XCTAssertEqual(model.savedSnapshot?.runs, [old])
        cache.failLoad = true
        let fresh = RunIngestionModel(reader: Reader(), snapshotStore: cache)
        XCTAssertEqual(fresh.state, .notRequested)
        XCTAssertNil(fresh.savedSnapshot)
        XCTAssertNotNil(fresh.cacheNotice)
    }

    func testSnapshotFileRoundTripsAndReplacesCompleteValues() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = FileRunSnapshotStore(directory: directory)
        XCTAssertNil(try store.load())
        let original = record(distance: WorkoutDistance(value: 1, unit: .miles))
        try store.save(RunSnapshot(runs: [original]))
        XCTAssertEqual(try FileRunSnapshotStore(directory: directory).load()?.runs, [original])
        try store.save(RunSnapshot(runs: []))
        XCTAssertEqual(try store.load()?.runs, [])
        try Data("invalid synthetic JSON".utf8).write(to: store.fileURL)
        XCTAssertThrowsError(try store.load())
    }

    func testR1RequestStateIsIndependentAndIngestionNeverRequestsAuthorization() {
        let provider = HealthAccessTests.Provider()
        let access = HealthAccessModel(provider: provider)
        let reader = Reader();let model = RunIngestionModel(reader: reader, snapshotStore: MemoryStore())
        access.request();provider.completion?(.cancelled)
        model.requestRead();reader.completion?(.success([]))
        XCTAssertEqual(access.state, .cancelled)
        XCTAssertEqual(provider.requests, 1)
        XCTAssertEqual(model.state, .successfulEmpty)
    }
}

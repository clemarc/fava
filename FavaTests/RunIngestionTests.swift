import XCTest
import HealthKit
@testable import Fava

@MainActor
final class RunIngestionTests: XCTestCase {
    final class Reader: WorkoutReading {
        var isAvailable = true
        var reads = 0
        var completions: [(Result<[RunRecord], Error>) -> Void] = []
        var immediateResult: Result<[RunRecord], Error>?
        func read(completion: @escaping (Result<[RunRecord], Error>) -> Void) {
            reads += 1
            completions.append(completion)
            if let immediateResult { completion(immediateResult) }
        }
        func complete(_ result: Result<[RunRecord], Error>, at index: Int? = nil) {
            completions[index ?? (completions.count - 1)](result)
        }
    }
    final class MemoryStore: RunHistoryStoring {
        var history: RetainedRunHistory?
        var failLoad = false
        var failSave = false
        var loads = 0
        var saves = 0
        var onSave: ((RetainedRunHistory) -> Void)?
        func loadHistory() throws -> RetainedRunHistory? {
            loads += 1
            if failLoad { throw Failure.synthetic }
            return history
        }
        func saveHistory(_ history: RetainedRunHistory) throws {
            saves += 1
            onSave?(history)
            if failSave { throw Failure.synthetic }
            self.history = history
        }
        func clearHistory() throws {
            try saveHistory(RetainedRunHistory(runs: []))
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
    private let firstTime = Date(timeIntervalSinceReferenceDate: 1_000)
    private func record(_ id: UUID = UUID(), duration: Double = 90, distance: WorkoutDistance? = nil) -> RunRecord {
        RunRecord(id: id, startDate: Date(timeIntervalSince1970: 1_500_000_000), duration: duration, distance: distance)
    }
    private func history(_ runs: [RunRecord], at date: Date? = nil) throws -> RetainedRunHistory {
        try RetainedRunHistory.adoptingLegacy(runs: runs, capturedAt: date)
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
        let model = RunIngestionModel(reader: reader, historyStore: cache, clock: { self.firstTime })
        let first = record(); let second = record()
        for _ in 0..<10 {
            model.requestRead()
            reader.complete(.success([first, first, second]))
            XCTAssertEqual(model.state, .sourceSuccess(returnedCount: 2, savingFailed: false))
            XCTAssertEqual(Set(model.savedHistory?.runs.map(\.id) ?? []), [first.id, second.id])
            XCTAssertEqual(model.savedHistory?.runs.count, 2)
        }
        XCTAssertEqual(reader.reads, 10)
        XCTAssertEqual(cache.saves, 10)
    }

    func testLargeCollectionHasNoSilentCap() {
        let reader = Reader(); let model = RunIngestionModel(reader: reader, historyStore: MemoryStore())
        let runs = (0..<2000).map { _ in record() }
        model.requestRead(); reader.complete(.success(runs))
        XCTAssertEqual(model.savedHistory?.runs.count, runs.count)
    }

    func testRecordedZeroDurationAndDistanceUnitsAreNotInferredOrRewritten() {
        let reader = Reader(); let cache = MemoryStore()
        let model = RunIngestionModel(reader: reader, historyStore: cache)
        let zero = record(duration: 0, distance: WorkoutDistance(value: 0, unit: .kilometres))
        let missing = record(duration: 0)
        model.requestRead(); reader.complete(.success([zero, missing]))
        XCTAssertEqual(cache.history?.runs, [zero, missing])
        XCTAssertEqual(model.savedHistory?.runs.first?.duration, 0)
        XCTAssertEqual(model.savedHistory?.runs.first?.distance?.unit, .kilometres)
        XCTAssertNil(model.savedHistory?.runs.last?.distance)
    }

    func testSubsetReadUnionsIDsAndReplacesCompleteReturnedSummaries() throws {
        let reader = Reader(); let cache = MemoryStore()
        let a = record(); let b = record(distance: WorkoutDistance(value: 1, unit: .miles)); let c = record()
        var now = firstTime
        var clockCalls = 0
        let model = RunIngestionModel(reader: reader, historyStore: cache, clock: { clockCalls += 1; return now })
        model.requestRead(); reader.complete(.success([a, b]))
        let updatedB = record(b.id, duration: 0, distance: nil)
        now = firstTime.addingTimeInterval(60)
        model.requestRead(); reader.complete(.success([updatedB, c, updatedB]))
        let saved = try XCTUnwrap(model.savedHistory)
        XCTAssertEqual(saved.runsByID, [a.id: a, b.id: updatedB, c.id: c])
        XCTAssertEqual(saved.lastObservedAtByID, [a.id: firstTime, b.id: now, c.id: now])
        XCTAssertEqual(saved.latestSavedObservation, SavedReadObservation(observedAt: now, returnedIDs: [b.id, c.id]))
        XCTAssertEqual(model.state, .sourceSuccess(returnedCount: 2, savingFailed: false))
        XCTAssertEqual(cache.history, saved)
        XCTAssertEqual(clockCalls, 2)
    }

    func testRepeatedEmptyAdvancesOnlyObservationAndLaterReadRetainsHistory() throws {
        let reader = Reader(); let cache = MemoryStore(); let a = record()
        cache.history = try history([a], at: firstTime)
        var now = firstTime
        let model = RunIngestionModel(reader: reader, historyStore: cache, clock: { now })
        for _ in 0..<2 {
            now = now.addingTimeInterval(60)
            model.requestRead(); reader.complete(.success([]))
            XCTAssertEqual(model.state, .sourceSuccess(returnedCount: 0, savingFailed: false))
            XCTAssertEqual(model.savedHistory?.runs, [a])
            XCTAssertEqual(model.savedHistory?.lastObservedAtByID, [a.id: firstTime])
            XCTAssertEqual(model.savedHistory?.latestSavedObservation, SavedReadObservation(observedAt: now, returnedIDs: []))
        }
        let b = record()
        model.requestRead(); reader.complete(.success([b]))
        XCTAssertEqual(model.savedHistory?.runs, [a, b])
    }

    func testOverlapGuardAndSavedHistoryRemainSeparateFromActiveAttempt() throws {
        let reader = Reader(); let cache = MemoryStore(); cache.history = try history([record()], at: firstTime)
        let model = RunIngestionModel(reader: reader, historyStore: cache)
        let prior = model.savedHistory
        XCTAssertEqual(model.state, .notRequested)
        XCTAssertTrue(model.isPriorSavedObservation)
        model.requestRead(); model.requestRead()
        XCTAssertEqual(reader.reads, 1)
        XCTAssertTrue(model.isTransportActive)
        XCTAssertFalse(model.canRead)
        XCTAssertEqual(model.savedHistory, prior)
        reader.complete(.failure(Failure.synthetic))
        XCTAssertEqual(model.state, .failed)
        XCTAssertEqual(cache.history, prior)
        XCTAssertTrue(model.isPriorSavedObservation)
        XCTAssertFalse(model.isTransportActive)
    }

    func testDuplicateAndPreviousCallbacksCannotReleaseNewTransportOrCommitTwice() {
        let reader = Reader(); let cache = MemoryStore()
        let model = RunIngestionModel(reader: reader, historyStore: cache)
        let first = record(); let second = record()
        model.requestRead(); reader.complete(.success([first]), at: 0)
        reader.complete(.success([]), at: 0)
        XCTAssertEqual(cache.saves, 1)
        model.requestRead()
        for result in [Result<[RunRecord], Error>.success([record()]), .success([]), .failure(Failure.synthetic)] {
            reader.complete(result, at: 0)
            XCTAssertTrue(model.isTransportActive)
            XCTAssertEqual(model.state, .loading)
            XCTAssertFalse(model.canRead)
            XCTAssertEqual(cache.saves, 1)
        }
        model.requestRead()
        XCTAssertEqual(reader.reads, 2)
        reader.complete(.success([second]), at: 1)
        XCTAssertEqual(model.savedHistory?.runs, [first, second])
        XCTAssertEqual(cache.saves, 2)
        XCTAssertFalse(model.isTransportActive)
    }

    func testImmediateCallbackHasGuardInstalledAndPublishesOnlyAfterPersistence() throws {
        let reader = Reader(); let cache = MemoryStore(); let prior = try history([record()], at: firstTime)
        cache.history = prior
        let returned = record()
        reader.immediateResult = .success([returned])
        var clockCalls = 0
        let model = RunIngestionModel(reader: reader, historyStore: cache, clock: { clockCalls += 1; return self.firstTime })
        var injectedDuplicates = false
        cache.onSave = { _ in
            guard !injectedDuplicates else { return }
            injectedDuplicates = true
            for result in [Result<[RunRecord], Error>.success([self.record()]), .success([]), .failure(Failure.synthetic)] {
                reader.complete(result, at: 0)
                XCTAssertEqual(cache.saves, 1)
                XCTAssertEqual(clockCalls, 1)
                XCTAssertEqual(model.state, .loading)
                XCTAssertEqual(model.savedHistory, prior)
                XCTAssertTrue(model.isTransportActive)
            }
            XCTAssertEqual(model.savedHistory, prior)
            XCTAssertTrue(model.isPriorSavedObservation)
            XCTAssertTrue(model.isTransportActive)
            model.requestRead()
            XCTAssertEqual(reader.reads, 1)
        }
        model.requestRead()
        XCTAssertEqual(cache.saves, 1)
        XCTAssertEqual(clockCalls, 1)
        XCTAssertEqual(model.state, .sourceSuccess(returnedCount: 1, savingFailed: false))
        let expected = try RunHistoryMerge.candidate(saved: prior, returned: [returned], observedAt: firstTime)
        XCTAssertEqual(model.savedHistory, expected)
        XCTAssertEqual(model.savedHistory, cache.history)
        XCTAssertEqual(model.savedHistory?.runs, prior.runs + [returned])
        XCTAssertFalse(model.isPriorSavedObservation)
        XCTAssertFalse(model.isTransportActive)
    }

    func testUnavailableIsNotEmptyAndAvailabilityRefreshStartsNoWork() throws {
        let reader = Reader(); reader.isAvailable = false
        let cache = MemoryStore(); cache.history = try history([], at: firstTime)
        let model = RunIngestionModel(reader: reader, historyStore: cache)
        let prior = model.savedHistory
        model.requestRead()
        XCTAssertEqual(model.state, .unavailable)
        XCTAssertEqual(reader.reads, 0)
        XCTAssertEqual(model.savedHistory, prior)
        XCTAssertTrue(model.isPriorSavedObservation)
        reader.isAvailable = true; model.updateAvailability()
        XCTAssertEqual(reader.reads, 0)
        XCTAssertEqual(model.state, .unavailable)
        model.requestRead(); reader.complete(.success([]))
        XCTAssertEqual(model.state, .sourceSuccess(returnedCount: 0, savingFailed: false))
    }

    func testFreshSessionRestoresNonemptyAndEmptyWithoutInterruptedAttempt() throws {
        for runs in [[record()], []] {
            let cache = MemoryStore(); cache.history = try history(runs, at: firstTime)
            let reader = Reader(); let first = RunIngestionModel(reader: reader, historyStore: cache)
            first.requestRead()
            let freshReader = Reader(); let fresh = RunIngestionModel(reader: freshReader, historyStore: cache)
            XCTAssertEqual(fresh.state, .notRequested)
            XCTAssertEqual(fresh.savedHistory, cache.history)
            XCTAssertTrue(fresh.isPriorSavedObservation)
            XCTAssertFalse(fresh.isTransportActive)
            XCTAssertEqual(freshReader.reads, 0)
            XCTAssertEqual(first.state, .loading)
        }
    }

    func testSaveFailurePreservesExactHistoryAcrossPriorStatesAndRelaunchAndRetryReadsAgain() throws {
        let a = record(); let b = record(); let unsaved = record(a.id, duration: 180)
        let priors: [RetainedRunHistory?] = [nil, try history([], at: firstTime), try history([a], at: firstTime), try history([a])]
        for prior in priors {
            for result in [[unsaved, b], []] {
                let cache = MemoryStore(); cache.history = prior; cache.failSave = true
                let reader = Reader()
                let model = RunIngestionModel(reader: reader, historyStore: cache, clock: { self.firstTime.addingTimeInterval(60) })
                let origin = model.isPriorSavedObservation
                model.requestRead(); reader.complete(.success(result))
                XCTAssertEqual(model.state, .sourceSuccess(returnedCount: result.count, savingFailed: true))
                XCTAssertEqual(model.savedHistory, prior)
                XCTAssertEqual(cache.history, prior)
                XCTAssertEqual(model.isPriorSavedObservation, origin)
                XCTAssertTrue(model.canRead)
                let fresh = RunIngestionModel(reader: Reader(), historyStore: cache)
                XCTAssertEqual(fresh.savedHistory, prior)
                XCTAssertEqual(fresh.isPriorSavedObservation, origin)
                XCTAssertEqual(fresh.state, .notRequested)
                cache.failSave = false
                model.requestRead()
                XCTAssertEqual(reader.reads, 2)
                reader.complete(.success([b]))
                XCTAssertEqual(model.state, .sourceSuccess(returnedCount: 1, savingFailed: false))
                XCTAssertEqual(model.savedHistory?.latestSavedObservation?.returnedIDs, [b.id])
            }
        }
    }

    func testSourceFailurePreservesHistoryAndCurrentSessionObservationOrigin() throws {
        let reader = Reader(); let cache = MemoryStore()
        let model = RunIngestionModel(reader: reader, historyStore: cache)
        model.requestRead(); reader.complete(.success([record()]))
        let saved = model.savedHistory
        model.requestRead(); reader.complete(.failure(Failure.synthetic))
        XCTAssertEqual(model.state, .failed)
        XCTAssertEqual(model.savedHistory, saved)
        XCTAssertFalse(model.isPriorSavedObservation)
        cache.failSave = true
        model.requestRead(); reader.complete(.success([]))
        XCTAssertEqual(model.savedHistory, saved)
        XCTAssertFalse(model.isPriorSavedObservation)
        XCTAssertEqual(cache.saves, 2)
    }

    func testInvalidDuplicateOrClockRejectsEntireBatchWithoutSaving() throws {
        let a = record(); let invalid = record(a.id, duration: -1)
        for records in [[a, invalid], [invalid, a]] {
            let cache = MemoryStore(); cache.history = try history([record()], at: firstTime)
            let reader = Reader(); let model = RunIngestionModel(reader: reader, historyStore: cache)
            let prior = model.savedHistory
            model.requestRead(); reader.complete(.success(records))
            XCTAssertEqual(model.state, .failed)
            XCTAssertEqual(model.savedHistory, prior)
            XCTAssertEqual(cache.saves, 0)
        }
        let cache = MemoryStore(); let reader = Reader()
        let model = RunIngestionModel(reader: reader, historyStore: cache,
                                      clock: { Date(timeIntervalSinceReferenceDate: .infinity) })
        model.requestRead(); reader.complete(.success([a]))
        XCTAssertEqual(model.state, .failed)
        XCTAssertEqual(cache.saves, 0)
    }

    func testRecoveryBlocksEveryReadAndLocalRetryNeverQueriesOrSaves() throws {
        let cache = MemoryStore(); cache.failLoad = true
        let reader = Reader(); let model = RunIngestionModel(reader: reader, historyStore: cache)
        XCTAssertNotNil(model.localRecoveryMessage)
        XCTAssertFalse(model.canRead)
        model.requestRead(); model.updateAvailability(); model.requestRead()
        XCTAssertEqual(reader.reads, 0)
        model.retryLocalLoad()
        XCTAssertNotNil(model.localRecoveryMessage)
        XCTAssertEqual(cache.loads, 2)
        cache.history = try history([record()]); cache.failLoad = false
        model.retryLocalLoad()
        XCTAssertNil(model.localRecoveryMessage)
        XCTAssertEqual(model.savedHistory, cache.history)
        XCTAssertEqual(model.state, .notRequested)
        XCTAssertTrue(model.isPriorSavedObservation)
        XCTAssertEqual(reader.reads, 0)
        XCTAssertEqual(cache.saves, 0)
        model.retryLocalLoad()
        XCTAssertEqual(cache.loads, 3, "A non-recovery retry cannot reload history during normal operation")
    }

    func testRealFileLegacyFailureAndRecoveryPreserveBytesAndRelaunch() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let file = FileRunSnapshotStore(directory: directory)
        for runs in [[record()], []] {
            let object: [String: Any] = ["schemaVersion": 1, "runs": try JSONSerialization.jsonObject(with: JSONEncoder().encode(runs))]
            let bytes = try JSONSerialization.data(withJSONObject: object)
            try bytes.write(to: file.fileURL)
            let failing = FileRunSnapshotStore(directory: directory, historyIO: RunHistoryFileIO(
                read: { try Data(contentsOf: $0) }, writeAtomically: { _, _ in throw Failure.synthetic }))
            let reader = Reader(); let model = RunIngestionModel(reader: reader, historyStore: failing)
            let prior = model.savedHistory
            XCTAssertEqual(prior?.latestSavedObservation, SavedReadObservation(observedAt: nil, returnedIDs: Set(runs.map(\.id))))
            model.requestRead(); reader.complete(.success([record()]))
            XCTAssertEqual(model.savedHistory, prior)
            XCTAssertEqual(try Data(contentsOf: file.fileURL), bytes)
            let fresh = RunIngestionModel(reader: Reader(), historyStore: file)
            XCTAssertEqual(fresh.savedHistory, prior)
            XCTAssertTrue(fresh.isPriorSavedObservation)
        }
        for bytes in [Data("broken synthetic document".utf8), Data("{\"schemaVersion\":9,\"runs\":[]}".utf8)] {
            try bytes.write(to: file.fileURL)
            let reader = Reader(); let model = RunIngestionModel(reader: reader, historyStore: file)
            model.requestRead(); model.retryLocalLoad(); model.requestRead()
            XCTAssertEqual(reader.reads, 0)
            XCTAssertNotNil(model.localRecoveryMessage)
            XCTAssertEqual(try Data(contentsOf: file.fileURL), bytes)
        }
    }

    #if DEBUG
    func testSyntheticFixtureFailuresPreserveOriginalFilesAndUseControlledClock() async throws {
        var directories: [URL] = []
        defer { for directory in directories { try? FileManager.default.removeItem(at: directory) } }
        for fixture in ["save-failure-populated", "save-failure-absent", "save-failure-empty", "save-failure-untimed"] {
            let store = SyntheticWorkoutReader.snapshotStore(fixture: fixture, session: UUID().uuidString)
            directories.append(store.fileURL.deletingLastPathComponent())
            let bytes = try? Data(contentsOf: store.fileURL)
            let source = SyntheticWorkoutReader(fixture: fixture)
            let result: Result<[RunRecord], Error> = await withCheckedContinuation { continuation in
                source.read { continuation.resume(returning: $0) }
            }
            let reader = Reader()
            let model = RunIngestionModel(reader: reader, historyStore: store, clock: { source.observationTime })
            let prior = model.savedHistory
            model.requestRead(); reader.complete(result)
            XCTAssertEqual(model.state, .sourceSuccess(returnedCount: 2, savingFailed: true))
            XCTAssertEqual(model.savedHistory, prior)
            XCTAssertEqual(try? Data(contentsOf: store.fileURL), bytes)
            XCTAssertEqual(try FileRunSnapshotStore(directory: store.fileURL.deletingLastPathComponent()).loadHistory(), prior)
            XCTAssertEqual(source.reads, 1)
        }
        let source = SyntheticWorkoutReader(fixture: "retention-sequence")
        let cache = MemoryStore(); let reader = Reader()
        let model = RunIngestionModel(reader: reader, historyStore: cache, clock: { source.observationTime })
        for count in [2, 2, 0, 0] {
            let result: Result<[RunRecord], Error> = await withCheckedContinuation { continuation in
                source.read { continuation.resume(returning: $0) }
            }
            model.requestRead(); reader.complete(result)
            XCTAssertEqual(model.state, .sourceSuccess(returnedCount: count, savingFailed: false))
            XCTAssertEqual(model.savedHistory?.latestSavedObservation?.observedAt, source.observationTime)
        }
        XCTAssertEqual(model.savedHistory?.runs.count, 3)
    }
    #endif

    func testR1RequestStateIsIndependentAndIngestionNeverRequestsAuthorization() {
        let provider = HealthAccessTests.Provider()
        let access = HealthAccessModel(provider: provider)
        let reader = Reader(); let model = RunIngestionModel(reader: reader, historyStore: MemoryStore())
        access.request(); provider.completion?(.cancelled)
        model.requestRead(); reader.complete(.success([]))
        XCTAssertEqual(access.state, .cancelled)
        XCTAssertEqual(provider.requests, 1)
        XCTAssertEqual(model.state, .sourceSuccess(returnedCount: 0, savingFailed: false))
    }
}

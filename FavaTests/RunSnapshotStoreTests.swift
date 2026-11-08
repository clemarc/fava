import Foundation
import XCTest
@testable import Fava

final class RunSnapshotStoreTests: XCTestCase {
    enum Failure: Error { case injected }

    private var directory: URL!
    private let observedAt = Date(timeIntervalSinceReferenceDate: 123_456.25)
    private let firstID = UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
    private let secondID = UUID(uuidString: "00000000-0000-0000-0000-000000000002")!

    override func setUpWithError() throws {
        directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws {
        try FileManager.default.removeItem(at: directory)
    }

    private func run(_ id: UUID, duration: Double = 0, distance: WorkoutDistance? = nil,
                     startDate: Date = Date(timeIntervalSinceReferenceDate: -1_200)) -> RunRecord {
        RunRecord(id: id, startDate: startDate, duration: duration, distance: distance)
    }

    private func jsonValue<T: Encodable>(_ value: T) throws -> Any {
        try JSONSerialization.jsonObject(with: JSONEncoder().encode(value), options: [.fragmentsAllowed])
    }

    private func legacyData(_ runs: [RunRecord], capturedAt: Any?) throws -> Data {
        var object: [String: Any] = ["schemaVersion": 1, "runs": try jsonValue(runs)]
        if let capturedAt { object["capturedAt"] = capturedAt }
        return try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys])
    }

    private func changing(_ data: Data, _ change: (inout [String: Any]) throws -> Void) throws -> Data {
        var object = try XCTUnwrap(try JSONSerialization.jsonObject(with: data) as? [String: Any])
        try change(&object)
        return try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys])
    }

    private func history() throws -> RetainedRunHistory {
        try RetainedRunHistory(
            runs: [run(firstID, distance: WorkoutDistance(value: 0, unit: .miles)), run(secondID)],
            lastObservedAtByID: [firstID: observedAt],
            latestSavedObservation: SavedReadObservation(observedAt: observedAt, returnedIDs: [firstID]))
    }

    private func write(_ data: Data, to store: FileRunSnapshotStore) throws {
        try data.write(to: store.fileURL)
    }

    private func failingStore() -> FileRunSnapshotStore {
        FileRunSnapshotStore(directory: directory, historyIO: RunHistoryFileIO(
            read: { try Data(contentsOf: $0) }, writeAtomically: { _, _ in throw Failure.injected }))
    }

    func testLegacyCallerContractAndDecoderRemainUnchanged() throws {
        let store: RunSnapshotStoring = FileRunSnapshotStore(directory: directory)
        XCTAssertNil(try store.load())
        let snapshot = RunSnapshot(runs: [run(firstID)], capturedAt: observedAt)
        try store.save(snapshot)
        XCTAssertEqual(try store.load(), snapshot)
        try store.save(RunSnapshot(runs: [], capturedAt: observedAt))
        XCTAssertEqual(try store.load()?.runs, [])
        for time in [nil, NSNull()] as [Any?] {
            XCTAssertThrowsError(try JSONDecoder().decode(RunSnapshot.self, from: legacyData([], capturedAt: time)))
        }
    }

    func testTypedLoadDistinguishesAbsentSavedEmptyAndReadFailure() throws {
        let store = FileRunSnapshotStore(directory: directory)
        XCTAssertNil(try store.loadHistory())
        let bytes = try legacyData([], capturedAt: observedAt.timeIntervalSinceReferenceDate)
        try write(bytes, to: store)
        let empty = try XCTUnwrap(try store.loadHistory())
        XCTAssertEqual(empty.runs, [])
        XCTAssertEqual(empty.latestSavedObservation, SavedReadObservation(observedAt: observedAt, returnedIDs: []))
        let unreadable = FileRunSnapshotStore(directory: directory, historyIO: RunHistoryFileIO(
            read: { _ in throw CocoaError(.fileReadNoPermission) }, writeAtomically: { _, _ in XCTFail("No load writes") }))
        XCTAssertThrowsError(try unreadable.loadHistory())
        XCTAssertEqual(try Data(contentsOf: store.fileURL), bytes)
    }

    func testTypedLoadReadsDirectlyAndOnlyGenuineNotFoundMeansAbsent() throws {
        let bytes = try legacyData([run(firstID)], capturedAt: nil)
        var reads = 0
        let virtual = FileRunSnapshotStore(directory: directory, historyIO: RunHistoryFileIO(
            read: { _ in reads += 1; return bytes }, writeAtomically: { _, _ in XCTFail("No load writes") }))
        XCTAssertFalse(FileManager.default.fileExists(atPath: virtual.fileURL.path))
        XCTAssertEqual(try virtual.loadHistory()?.runs, [run(firstID)])
        XCTAssertEqual(reads, 1)
        let missing = FileRunSnapshotStore(directory: directory, historyIO: RunHistoryFileIO(
            read: { _ in throw CocoaError(.fileReadNoSuchFile) }, writeAtomically: { _, _ in XCTFail("No load writes") }))
        XCTAssertNil(try missing.loadHistory())
        for error in [Failure.injected as Error, NSError(domain: "SyntheticOtherDomain", code: NSFileReadNoSuchFileError)] {
            let failing = FileRunSnapshotStore(directory: directory, historyIO: RunHistoryFileIO(
                read: { _ in throw error }, writeAtomically: { _, _ in XCTFail("No load writes") }))
            XCTAssertThrowsError(try failing.loadHistory())
        }
    }

    func testLegacyAdoptionPreservesKnownTimeValuesFirstIdentityAndOriginalBytes() throws {
        let store = FileRunSnapshotStore(directory: directory)
        let first = run(firstID, distance: WorkoutDistance(value: 0, unit: .kilometres))
        let duplicate = run(firstID, duration: 90, distance: WorkoutDistance(value: 2, unit: .miles))
        let matching = run(secondID, distance: WorkoutDistance(value: 0, unit: .kilometres))
        let bytes = try legacyData([first, duplicate, matching], capturedAt: observedAt.timeIntervalSinceReferenceDate)
        try write(bytes, to: store)
        let adopted = try XCTUnwrap(try store.loadHistory())
        XCTAssertEqual(adopted.schemaVersion, 2)
        XCTAssertEqual(adopted.runs, [first, matching])
        XCTAssertEqual(adopted.runsByID, [firstID: first, secondID: matching])
        XCTAssertEqual(adopted.lastObservedAtByID, [firstID: observedAt, secondID: observedAt])
        XCTAssertEqual(adopted.latestSavedObservation,
                       SavedReadObservation(observedAt: observedAt, returnedIDs: [firstID, secondID]))
        XCTAssertEqual(try Data(contentsOf: store.fileURL), bytes)
        XCTAssertEqual(try FileRunSnapshotStore(directory: directory).loadHistory(), adopted)
        XCTAssertEqual(try Data(contentsOf: store.fileURL), bytes)
    }

    func testMissingAndNullLegacyTimeRemainUnknownForPopulatedAndEmptyHistory() throws {
        let store = FileRunSnapshotStore(directory: directory)
        for runs in [[RunRecord](), [run(firstID)]] {
            for time in [nil, NSNull()] as [Any?] {
                let bytes = try legacyData(runs, capturedAt: time)
                try write(bytes, to: store)
                let adopted = try XCTUnwrap(try store.loadHistory())
                XCTAssertEqual(adopted.runs, runs)
                XCTAssertEqual(adopted.lastObservedAtByID, [:])
                XCTAssertEqual(adopted.latestSavedObservation,
                               SavedReadObservation(observedAt: nil, returnedIDs: Set(runs.map(\.id))))
                XCTAssertEqual(try Data(contentsOf: store.fileURL), bytes)
            }
        }
    }

    func testMalformedPresentLegacyTimeIsRecoveryWithoutChangingBytes() throws {
        let store = FileRunSnapshotStore(directory: directory)
        for time in ["not a date", true, [123], ["time": 123]] as [Any] {
            let bytes = try legacyData([run(firstID)], capturedAt: time)
            try write(bytes, to: store)
            XCTAssertThrowsError(try store.loadHistory())
            XCTAssertEqual(try Data(contentsOf: store.fileURL), bytes)
        }
        let overflow = Data("{\"schemaVersion\":1,\"runs\":[],\"capturedAt\":1e400}".utf8)
        try write(overflow, to: store)
        XCTAssertThrowsError(try store.loadHistory())
        XCTAssertEqual(try Data(contentsOf: store.fileURL), overflow)
    }

    func testEveryLegacyRowIsValidatedBeforeFirstWinsDeduplication() throws {
        let store = FileRunSnapshotStore(directory: directory)
        let first = run(firstID)
        for invalid in [run(firstID, duration: -1), run(firstID, distance: WorkoutDistance(value: -1, unit: .metres))] {
            let bytes = try legacyData([first, invalid], capturedAt: observedAt.timeIntervalSinceReferenceDate)
            try write(bytes, to: store)
            XCTAssertThrowsError(try store.loadHistory())
            XCTAssertEqual(try Data(contentsOf: store.fileURL), bytes)
        }
    }

    func testHistoryRoundTripPreservesUnknownTimesMissingAndZeroDistanceAndMembership() throws {
        let original = try history()
        let decoded = try JSONDecoder().decode(RetainedRunHistory.self, from: JSONEncoder().encode(original))
        XCTAssertEqual(decoded, original)
        XCTAssertEqual(decoded.runs.first?.distance?.value, 0)
        XCTAssertEqual(decoded.runs.first?.distance?.unit, .miles)
        XCTAssertNil(decoded.runs.last?.distance)
        XCTAssertNil(decoded.lastObservedAtByID[secondID])
        XCTAssertFalse(try XCTUnwrap(decoded.latestSavedObservation).returnedIDs.contains(secondID))
        XCTAssertEqual(decoded.runs.first?.startDate, Date(timeIntervalSinceReferenceDate: -1_200))
    }

    func testHistoryConstructionRejectsDuplicateIDsOrphanMetadataAndInvalidValues() throws {
        XCTAssertThrowsError(try RetainedRunHistory(runs: [run(firstID), run(firstID)]))
        XCTAssertThrowsError(try RetainedRunHistory(runs: [run(firstID)], lastObservedAtByID: [secondID: observedAt]))
        XCTAssertThrowsError(try RetainedRunHistory(runs: [run(firstID)], latestSavedObservation:
                                                    SavedReadObservation(observedAt: observedAt, returnedIDs: [secondID])))
        for value in [-1.0, Double.infinity, -Double.infinity, Double.nan] {
            XCTAssertThrowsError(try RetainedRunHistory(runs: [run(firstID, duration: value)]))
            XCTAssertThrowsError(try RetainedRunHistory(runs: [run(firstID, distance: WorkoutDistance(value: value, unit: .miles))]))
        }
        for value in [Double.infinity, -Double.infinity, Double.nan] {
            let date = Date(timeIntervalSinceReferenceDate: value)
            XCTAssertThrowsError(try RetainedRunHistory(runs: [run(firstID, startDate: date)]))
            XCTAssertThrowsError(try RetainedRunHistory(runs: [run(firstID)], lastObservedAtByID: [firstID: date]))
            XCTAssertThrowsError(try RetainedRunHistory(runs: [run(firstID)], latestSavedObservation:
                                                        SavedReadObservation(observedAt: date, returnedIDs: [firstID])))
        }
    }

    func testKnownLatestObservationRequiresExactReturnedRowTimes() throws {
        let observation = SavedReadObservation(observedAt: observedAt, returnedIDs: [firstID])
        let invalidMaps: [[UUID: Date]] = [
            [:],
            [firstID: observedAt.addingTimeInterval(-0.001)],
            [firstID: observedAt.addingTimeInterval(0.001)]
        ]
        for times in invalidMaps {
            XCTAssertThrowsError(try RetainedRunHistory(runs: [run(firstID)], lastObservedAtByID: times,
                                                       latestSavedObservation: observation)) { error in
                XCTAssertEqual(error as? RunHistoryError, .inconsistentObservation(self.firstID))
            }
        }
        // Only returned rows must match; other retained rows may have old, future or unknown times.
        for otherTime in [nil, observedAt.addingTimeInterval(-60), observedAt.addingTimeInterval(60)] as [Date?] {
            var times = [firstID: observedAt]
            times[secondID] = otherTime
            let valid = try RetainedRunHistory(runs: [run(firstID), run(secondID)], lastObservedAtByID: times,
                                               latestSavedObservation: observation)
            XCTAssertEqual(valid.lastObservedAtByID[firstID], observedAt)
            XCTAssertEqual(valid.lastObservedAtByID[secondID], otherTime)
            XCTAssertEqual(try JSONDecoder().decode(RetainedRunHistory.self, from: JSONEncoder().encode(valid)), valid)
        }
        let savedEmpty = try RetainedRunHistory(runs: [run(firstID)], latestSavedObservation:
                                                SavedReadObservation(observedAt: observedAt, returnedIDs: []))
        XCTAssertEqual(savedEmpty.lastObservedAtByID, [:])
        XCTAssertEqual(try JSONDecoder().decode(RetainedRunHistory.self, from: JSONEncoder().encode(savedEmpty)), savedEmpty)
    }

    func testInconsistentLatestObservationCannotDecodeOrChangeStoredBytes() throws {
        let store = FileRunSnapshotStore(directory: directory)
        let valid = try JSONEncoder().encode(history())
        let invalidMaps: [[UUID: Date]] = [
            [:],
            [secondID: observedAt],
            [firstID: observedAt.addingTimeInterval(-0.001)],
            [firstID: observedAt.addingTimeInterval(0.001)]
        ]
        var variants = [try changing(valid) { $0.removeValue(forKey: "lastObservedAtByID") }]
        for times in invalidMaps {
            variants.append(try changing(valid) { $0["lastObservedAtByID"] = try jsonValue(times) })
        }
        for invalid in variants {
            XCTAssertThrowsError(try JSONDecoder().decode(RetainedRunHistory.self, from: invalid)) { error in
                XCTAssertEqual(error as? RunHistoryError, .inconsistentObservation(self.firstID))
            }
            try write(invalid, to: store)
            XCTAssertThrowsError(try store.loadHistory()) { error in
                XCTAssertEqual(error as? RunHistoryError, .inconsistentObservation(self.firstID))
            }
            XCTAssertEqual(try Data(contentsOf: store.fileURL), invalid)
            XCTAssertThrowsError(try FileRunSnapshotStore(directory: directory).loadHistory())
            XCTAssertEqual(try Data(contentsOf: store.fileURL), invalid)
        }
    }

    func testSchemaTwoDecoderCannotBypassVersionOrHistoryValidation() throws {
        let bytes = try JSONEncoder().encode(history())
        let variants = [
            try changing(bytes) { $0["schemaVersion"] = 3 },
            try changing(bytes) { $0.removeValue(forKey: "schemaVersion") },
            try changing(bytes) { $0["runs"] = try jsonValue([run(firstID), run(firstID)]) },
            try changing(bytes) { $0["runs"] = try jsonValue([run(firstID, duration: -1)]) },
            try changing(bytes) { $0["lastObservedAtByID"] = NSNull() },
            try changing(bytes) { $0["lastObservedAtByID"] = "invalid synthetic map" },
            try changing(bytes) { $0["lastObservedAtByID"] = try jsonValue([UUID(): observedAt]) },
            try changing(bytes) { $0["latestSavedObservation"] = try jsonValue(
                SavedReadObservation(observedAt: observedAt, returnedIDs: [UUID()])) }
        ]
        for invalid in variants {
            XCTAssertThrowsError(try JSONDecoder().decode(RetainedRunHistory.self, from: invalid))
        }
    }

    func testMalformedSourceDatesUUIDsAndObservationDatesCannotBeLoaded() throws {
        let store = FileRunSnapshotStore(directory: directory)
        let valid = try JSONEncoder().encode(history())
        for field in ["id", "startDate", "duration"] {
            let invalid = try changing(valid) { object in
                var runs = try XCTUnwrap(object["runs"] as? [[String: Any]])
                runs[0][field] = "invalid synthetic value"
                object["runs"] = runs
            }
            try write(invalid, to: store)
            XCTAssertThrowsError(try store.loadHistory())
            XCTAssertEqual(try Data(contentsOf: store.fileURL), invalid)
        }
        let invalidObservation = try changing(valid) { object in
            var observation = try XCTUnwrap(object["latestSavedObservation"] as? [String: Any])
            observation["observedAt"] = "invalid synthetic date"
            object["latestSavedObservation"] = observation
        }
        try write(invalidObservation, to: store)
        XCTAssertThrowsError(try store.loadHistory())
        XCTAssertEqual(try Data(contentsOf: store.fileURL), invalidObservation)
    }

    func testOverflowingSourceNumbersAreRecoveryWithoutChangingBytes() throws {
        let store = FileRunSnapshotStore(directory: directory)
        let valid = try legacyData([run(firstID)], capturedAt: observedAt.timeIntervalSinceReferenceDate)
        let object = try XCTUnwrap(try JSONSerialization.jsonObject(with: valid) as? [String: Any])
        let records = try XCTUnwrap(object["runs"] as? [[String: Any]])
        let record = try XCTUnwrap(records.first)
        for field in ["startDate", "duration"] {
            var invalidRecord = record
            invalidRecord[field] = "OVERFLOW"
            let quoted = try changing(valid) { $0["runs"] = [invalidRecord] }
            let overflow = Data(try XCTUnwrap(String(data: quoted, encoding: .utf8))
                .replacingOccurrences(of: "\"OVERFLOW\"", with: "1e400").utf8)
            try write(overflow, to: store)
            XCTAssertThrowsError(try store.loadHistory())
            XCTAssertEqual(try Data(contentsOf: store.fileURL), overflow)
        }
    }

    func testHistoryDecoderValidatesNonfiniteDatesEvenWithCustomFloatDecoding() throws {
        let encoded = try XCTUnwrap(try String(data: JSONEncoder().encode(history()), encoding: .utf8))
        let nonfinite = Data(encoded.replacingOccurrences(of: "123456.25", with: "\"Infinity\"").utf8)
        let decoder = JSONDecoder()
        decoder.nonConformingFloatDecodingStrategy = .convertFromString(
            positiveInfinity: "Infinity", negativeInfinity: "-Infinity", nan: "NaN")
        XCTAssertThrowsError(try decoder.decode(RetainedRunHistory.self, from: nonfinite))
    }

    func testCorruptionAndUnsupportedVersionsAreNeverAbsenceOrEagerlyRewritten() throws {
        let store = FileRunSnapshotStore(directory: directory)
        let valid = try JSONEncoder().encode(history())
        let unsupported = try changing(valid) { $0["schemaVersion"] = 999 }
        let absentVersion = try changing(valid) { $0.removeValue(forKey: "schemaVersion") }
        for bytes in [Data("invalid synthetic JSON".utf8), unsupported, absentVersion] {
            try write(bytes, to: store)
            XCTAssertThrowsError(try store.loadHistory())
            XCTAssertEqual(try Data(contentsOf: store.fileURL), bytes)
        }
    }

    func testFirstExplicitSaveMigratesSamePathAndPreservesUntimedPriorObservation() throws {
        let store = FileRunSnapshotStore(directory: directory)
        for runs in [[RunRecord](), [run(firstID)]] {
            for time in [observedAt.timeIntervalSinceReferenceDate, nil, NSNull()] as [Any?] {
                let legacy = try legacyData(runs, capturedAt: time)
                try write(legacy, to: store)
                let adopted = try XCTUnwrap(try store.loadHistory())
                let expectedTime: Date? = time is Double ? observedAt : nil
                XCTAssertEqual(adopted.latestSavedObservation,
                               SavedReadObservation(observedAt: expectedTime, returnedIDs: Set(runs.map(\.id))))
                XCTAssertEqual(adopted.lastObservedAtByID,
                               expectedTime == nil ? [:] : Dictionary(uniqueKeysWithValues: runs.map { ($0.id, observedAt) }))
                XCTAssertEqual(try Data(contentsOf: store.fileURL), legacy)
                try store.saveHistory(adopted)
                let object = try XCTUnwrap(try JSONSerialization.jsonObject(with: Data(contentsOf: store.fileURL)) as? [String: Any])
                XCTAssertEqual(object["schemaVersion"] as? Int, 2)
                XCTAssertNil(object["capturedAt"])
                XCTAssertEqual(store.fileURL.lastPathComponent, "runs-v1.json")
                XCTAssertEqual(try FileRunSnapshotStore(directory: directory).loadHistory(), adopted)
            }
        }
    }

    func testSchemaTwoRoundTripRetainsKnownAndUnknownRowTimesThroughSavedEmptyObservation() throws {
        let store = FileRunSnapshotStore(directory: directory)
        let timed = run(firstID)
        let untimed = run(secondID, distance: WorkoutDistance(value: 0, unit: .kilometres))
        let firstObservation = try RetainedRunHistory(
            runs: [timed, untimed],
            lastObservedAtByID: [timed.id: observedAt],
            latestSavedObservation: SavedReadObservation(observedAt: observedAt, returnedIDs: [timed.id]))

        try store.saveHistory(firstObservation)
        XCTAssertEqual(try FileRunSnapshotStore(directory: directory).loadHistory(), firstObservation)
        XCTAssertNil(try FileRunSnapshotStore(directory: directory).loadHistory()?.lastObservedAtByID[untimed.id])

        let emptyObservationTime = observedAt.addingTimeInterval(60)
        let savedEmpty = try RetainedRunHistory(
            runs: [timed, untimed],
            lastObservedAtByID: [timed.id: observedAt],
            latestSavedObservation: SavedReadObservation(observedAt: emptyObservationTime, returnedIDs: []))
        try store.saveHistory(savedEmpty)

        let relaunched = try XCTUnwrap(try FileRunSnapshotStore(directory: directory).loadHistory())
        XCTAssertEqual(relaunched, savedEmpty)
        XCTAssertEqual(relaunched.lastObservedAtByID[timed.id], observedAt)
        XCTAssertNil(relaunched.lastObservedAtByID[untimed.id])
        XCTAssertEqual(relaunched.latestSavedObservation,
                       SavedReadObservation(observedAt: emptyObservationTime, returnedIDs: []))
    }

    func testInjectedMigrationAndSaveFailuresKeepExactPriorBytesAndRelaunchState() throws {
        let store = FileRunSnapshotStore(directory: directory)
        let priorDocuments = [
            try legacyData([run(firstID)], capturedAt: observedAt.timeIntervalSinceReferenceDate),
            try legacyData([], capturedAt: observedAt.timeIntervalSinceReferenceDate),
            try legacyData([run(firstID)], capturedAt: nil),
            try legacyData([], capturedAt: NSNull()),
            try JSONEncoder().encode(history())
        ]
        for bytes in priorDocuments {
            try write(bytes, to: store)
            let prior = try XCTUnwrap(try store.loadHistory())
            XCTAssertThrowsError(try failingStore().saveHistory(prior))
            XCTAssertEqual(try Data(contentsOf: store.fileURL), bytes)
            XCTAssertEqual(try FileRunSnapshotStore(directory: directory).loadHistory(), prior)
            let replacement = try RetainedRunHistory(runs: [run(secondID, duration: 900)],
                                                     lastObservedAtByID: [secondID: observedAt.addingTimeInterval(60)],
                                                     latestSavedObservation: SavedReadObservation(
                                                        observedAt: observedAt.addingTimeInterval(60), returnedIDs: [secondID]))
            XCTAssertThrowsError(try failingStore().saveHistory(replacement))
            XCTAssertEqual(try Data(contentsOf: store.fileURL), bytes)
            XCTAssertEqual(try FileRunSnapshotStore(directory: directory).loadHistory(), prior)
        }
    }

    func testInjectedSaveFailurePreservesCorruptBytes() throws {
        let store = FileRunSnapshotStore(directory: directory)
        let corrupt = Data("corrupt synthetic history".utf8)
        try write(corrupt, to: store)
        XCTAssertThrowsError(try failingStore().saveHistory(history()))
        XCTAssertEqual(try Data(contentsOf: store.fileURL), corrupt)
        XCTAssertThrowsError(try FileRunSnapshotStore(directory: directory).loadHistory())
    }

    func testFailedFirstSaveLeavesAbsentHistoryAbsent() throws {
        let store = FileRunSnapshotStore(directory: directory)
        XCTAssertThrowsError(try failingStore().saveHistory(history()))
        XCTAssertFalse(FileManager.default.fileExists(atPath: store.fileURL.path))
        XCTAssertNil(try store.loadHistory())
    }

    func testClearCreatesDurableMetadataFreeTombstoneWithoutReadingPriorData() throws {
        let store = FileRunSnapshotStore(directory: directory)
        let original = try legacyData([run(firstID)], capturedAt: observedAt.timeIntervalSinceReferenceDate)
        let unsupported = Data("{\"schemaVersion\":999,\"runs\":[]}".utf8)
        for bytes in [original, Data("corrupt synthetic history".utf8), unsupported, try JSONEncoder().encode(history())] {
            try write(bytes, to: store)
            let noRead = FileRunSnapshotStore(directory: directory, historyIO: RunHistoryFileIO(
                read: { _ in XCTFail("Clearing must not decode corrupt history"); throw Failure.injected },
                writeAtomically: RunHistoryFileIO.live.writeAtomically))
            try noRead.clearHistory()
            let tombstone = try XCTUnwrap(try FileRunSnapshotStore(directory: directory).loadHistory())
            XCTAssertEqual(tombstone.runs, [])
            XCTAssertEqual(tombstone.lastObservedAtByID, [:])
            XCTAssertNil(tombstone.latestSavedObservation)
            let object = try XCTUnwrap(try JSONSerialization.jsonObject(with: Data(contentsOf: store.fileURL)) as? [String: Any])
            XCTAssertNil(object["capturedAt"])
            XCTAssertNil(object["lastObservedAtByID"])
            XCTAssertNil(object["latestSavedObservation"])
            XCTAssertEqual(object["schemaVersion"] as? Int, 2)
        }
    }

    func testClearOfAbsentHistoryCreatesTombstoneAndFailuresPreserveBytes() throws {
        let store = FileRunSnapshotStore(directory: directory)
        XCTAssertThrowsError(try failingStore().clearHistory())
        XCTAssertNil(try store.loadHistory())
        try store.clearHistory()
        XCTAssertNotNil(try store.loadHistory())
        let documents = [try Data(contentsOf: store.fileURL),
                         try legacyData([run(firstID)], capturedAt: observedAt.timeIntervalSinceReferenceDate),
                         Data("corrupt synthetic history".utf8), Data("{\"schemaVersion\":999}".utf8),
                         try JSONEncoder().encode(history())]
        for bytes in documents {
            try write(bytes, to: store)
            XCTAssertThrowsError(try failingStore().clearHistory())
            XCTAssertEqual(try Data(contentsOf: store.fileURL), bytes)
        }
    }
}

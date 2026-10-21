import XCTest
@testable import Fava

@MainActor
final class LaunchContextTests: XCTestCase {
    private func make(_ runs: [RunRecord]? = nil, unreadable: Bool = false) throws -> (LaunchContext, RunIngestionModel, RunIngestionTests.Reader, RunIngestionTests.MemoryStore) {
        let reader = RunIngestionTests.Reader()
        let store = RunIngestionTests.MemoryStore()
        store.history = try runs.map { try RetainedRunHistory.adoptingLegacy(runs: $0, capturedAt: nil) }
        store.failLoad = unreadable
        let ingestion = RunIngestionModel(reader: reader, historyStore: store)
        return (LaunchContext(ingestion: ingestion), ingestion, reader, store)
    }
    private var run: RunRecord {
        RunRecord(id: UUID(), startDate: Date(timeIntervalSince1970: 1_700_000_000), duration: 90, distance: nil)
    }

    func testLocalContextSelectsRouteWithoutStartingWork() throws {
        let contexts: [([RunRecord]?, Bool, LaunchRoute)] = [(nil, false, .setup), ([], false, .setup), ([run], false, .library), (nil, true, .recovery)]
        for (runs, unreadable, expected) in contexts {
            let (context, ingestion, reader, store) = try make(runs, unreadable: unreadable)
            XCTAssertEqual(context.route, expected)
            XCTAssertEqual(reader.reads, 0)
            XCTAssertEqual(store.loads, 1)
            XCTAssertFalse(ingestion.isTransportActive)
            XCTAssertEqual(ingestion.state, .notRequested)
        }
    }

    func testInitialEntryIsOnceOnlyAndSavedRowsAreIndependentOfHeldRead() throws {
        let saved = run
        let (context, ingestion, reader, _) = try make([saved])
        XCTAssertEqual(ingestion.savedHistory?.runs, [saved])
        context.startInitialEntry()
        for _ in 0..<10 { context.startInitialEntry(); context.enterLibrary(); ingestion.updateAvailability() }
        XCTAssertEqual(context.route, .library)
        XCTAssertEqual(reader.reads, 1)
        XCTAssertEqual(ingestion.savedHistory?.runs, [saved])
        XCTAssertTrue(ingestion.isTransportActive)
        reader.complete(.success([]))
        context.startInitialEntry()
        XCTAssertEqual(reader.reads, 1)
        XCTAssertEqual(context.route, .library)
    }

    func testDeliberateReentryReadsOnceAndReusesActiveTransport() throws {
        let (context, _, reader, _) = try make()
        context.startInitialEntry()
        XCTAssertEqual(reader.reads, 0)
        context.enterLibrary(); context.enterLibrary()
        XCTAssertEqual(reader.reads, 1)
        context.leaveLibrary(); context.enterLibrary()
        XCTAssertEqual(reader.reads, 1)
        reader.complete(.success([]))
        context.leaveLibrary(); context.enterLibrary(); context.startInitialEntry()
        XCTAssertEqual(reader.reads, 2)
    }

    func testRecoveryRetryReloadsWithoutReadingAndSubsequentEntryIsSeparate() throws {
        let (context, ingestion, reader, store) = try make([run], unreadable: true)
        context.startInitialEntry(); context.retryLocalLoad()
        XCTAssertEqual(context.route, .recovery)
        XCTAssertEqual(reader.reads, 0)
        XCTAssertEqual(store.saves, 0)
        store.failLoad = false
        context.retryLocalLoad()
        XCTAssertEqual(context.route, .library)
        XCTAssertEqual(reader.reads, 0, "Local reload must never query the source")
        XCTAssertNotNil(ingestion.savedHistory)
        context.startInitialEntry()
        XCTAssertEqual(reader.reads, 1, "Installed populated route has one distinct entry event")
    }

    func testRecoveryToAbsentOrEmptyStaysSetupAndRetryInsideLibraryDoesNotEnterAgain() throws {
        for runs in [nil, []] as [[RunRecord]?] {
            let (context, _, reader, store) = try make(runs, unreadable: true)
            store.failLoad = false
            context.retryLocalLoad(); context.startInitialEntry()
            XCTAssertEqual(context.route, .setup)
            XCTAssertEqual(reader.reads, 0)
        }
        let (context, ingestion, reader, store) = try make([run], unreadable: true)
        context.enterLibrary()
        XCTAssertEqual(reader.reads, 0)
        store.failLoad = false
        context.retryLocalLoad(); context.startInitialEntry()
        XCTAssertEqual(context.route, .library)
        XCTAssertEqual(reader.reads, 0)
        XCTAssertEqual(ingestion.state, .notRequested)
    }

    func testEmptyAndSavingFailureNeverReplaceEnteredRoute() throws {
        for initial in [nil, [], [run]] as [[RunRecord]?] {
            for failSave in [false, true] {
                let (context, ingestion, reader, store) = try make(initial)
                store.failSave = failSave
                context.startInitialEntry(); context.enterLibrary()
                reader.complete(.success([]))
                XCTAssertEqual(context.route, .library)
                XCTAssertEqual(ingestion.state, .sourceSuccess(returnedCount: 0, savingFailed: failSave))
                context.startInitialEntry()
                XCTAssertEqual(reader.reads, 1)
            }
        }
    }

    func testRelaunchRestoresOnlyCommittedHistoryWithoutActiveWork() throws {
        let (context, first, reader, store) = try make([run])
        context.startInitialEntry()
        XCTAssertTrue(first.isTransportActive)
        let nextReader = RunIngestionTests.Reader()
        let next = RunIngestionModel(reader: nextReader, historyStore: store)
        let nextContext = LaunchContext(ingestion: next)
        XCTAssertEqual(nextContext.route, .library)
        XCTAssertEqual(next.savedHistory, first.savedHistory)
        XCTAssertEqual(next.state, .notRequested)
        XCTAssertFalse(next.isTransportActive)
        XCTAssertEqual(nextReader.reads, 0)
        XCTAssertEqual(reader.reads, 1)
        nextContext.startInitialEntry()
        XCTAssertEqual(nextReader.reads, 1)
    }

    func testUnavailableEntryDoesNotReadAndAvailabilityChangesDoNotCreateEntry() throws {
        let (context, ingestion, reader, _) = try make([run])
        reader.isAvailable = false
        context.startInitialEntry()
        XCTAssertEqual(reader.reads, 0)
        reader.isAvailable = true
        ingestion.updateAvailability(); context.startInitialEntry()
        XCTAssertEqual(reader.reads, 0)
        context.leaveLibrary(); context.enterLibrary()
        XCTAssertEqual(reader.reads, 1)
    }
}

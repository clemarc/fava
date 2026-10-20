import XCTest
@testable import Fava

@MainActor
final class RunLibraryTests: XCTestCase {
    private let english = Locale(identifier: "en_US")
    private func fixtureRun(id: UUID = UUID(), start: Double = 1_704_067_200, duration: Double = 90, distance: WorkoutDistance? = nil) -> RunRecord {
        RunRecord(id: id, startDate: Date(timeIntervalSince1970: start), duration: duration, distance: distance)
    }

    func testChronologyStableTiesAndFullIdentityCollection() {
        let a = fixtureRun(id: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!)
        let b = fixtureRun(id: UUID(uuidString: "00000000-0000-0000-0000-000000000002")!)
        let old = fixtureRun(start: 1_000_000)
        XCTAssertEqual(RunLibraryPresentation.rows([old, b, a]).map(\.id), [a.id, b.id, old.id])
        XCTAssertEqual(RunLibraryPresentation.rows([b, old, a]).map(\.id), [a.id, b.id, old.id])
        let history = (0..<2000).map { fixtureRun(start: Double($0)) }
        XCTAssertEqual(RunLibraryPresentation.rows(history).count, history.count)
        XCTAssertEqual(RunLibraryPresentation.rows(history).first?.id, history.last?.id)
    }

    func testDateUsesCurrentLocaleAndTimeZoneWithoutChangingSource() {
        let record = fixtureRun()
        let utc = RunFormatting.start(record.startDate, locale: english, timeZone: TimeZone(secondsFromGMT: 0)!)
        let pacific = RunFormatting.start(record.startDate, locale: english, timeZone: TimeZone(identifier: "America/Los_Angeles")!)
        let french = RunFormatting.start(record.startDate, locale: Locale(identifier: "fr_FR"), timeZone: TimeZone(secondsFromGMT: 0)!)
        XCTAssertTrue(utc.contains("2024"))
        XCTAssertTrue(pacific.contains("2023"))
        XCTAssertNotEqual(utc, french)
        XCTAssertEqual(record.startDate.timeIntervalSince1970, 1_704_067_200)
    }

    func testDurationUsesRecordedSecondsIncludingZero() {
        XCTAssertTrue(RunFormatting.duration(90).hasSuffix("01:30"))
        XCTAssertTrue(RunFormatting.duration(0).contains("0"))
        XCTAssertFalse(RunFormatting.duration(0).lowercased().contains("unavailable"))
    }

    func testDistanceConversionRoundingAndNilVersusZero() {
        XCTAssertEqual(RunFormatting.distance(nil, unit: .kilometres, locale: english), "Distance unavailable")
        XCTAssertEqual(RunFormatting.distance(WorkoutDistance(value: 0, unit: .metres), unit: .kilometres, locale: english), "0.00 km")
        for metres in [0.0, 1000, 1609.344, 12345.678] {
            for unit in [DistanceDisplayUnit.kilometres, .miles] {
                let text = RunFormatting.distance(WorkoutDistance(value: metres, unit: .metres), unit: unit, locale: english)
                let number = NumberFormatter(); number.locale = english; number.numberStyle = .decimal
                let value = number.number(from: text.components(separatedBy: " ")[0])!.doubleValue
                XCTAssertEqual(value, metres / unit.metresPerUnit, accuracy: 0.00500001)
                XCTAssertTrue(text.hasSuffix(unit.symbol))
            }
        }
        XCTAssertEqual(RunFormatting.distance(WorkoutDistance(value: 1, unit: .miles), unit: .miles, locale: english), "1.00 mi")
    }

    func testDeviceModeFollowsCurrentResolverAndFixedModesOverride() {
        let suite = "FavaTests-" + UUID().uuidString
        let defaults = UserDefaults(suiteName: suite)!
        defer { defaults.removePersistentDomain(forName: suite) }
        var deviceUnit = DistanceDisplayUnit.kilometres
        let settings = DistanceSettings(defaults: defaults, deviceUnit: { _ in deviceUnit })
        XCTAssertEqual(settings.mode, .device)
        XCTAssertEqual(settings.resolvedUnit(locale: english), .kilometres)
        deviceUnit = .miles
        XCTAssertEqual(settings.resolvedUnit(locale: english), .miles)
        settings.mode = .kilometres
        XCTAssertEqual(settings.resolvedUnit(locale: english), .kilometres)
        settings.mode = .miles; deviceUnit = .kilometres
        XCTAssertEqual(settings.resolvedUnit(locale: english), .miles)
        settings.mode = .device
        XCTAssertEqual(settings.resolvedUnit(locale: english), .kilometres)
    }

    func testPreferenceRelaunchDoesNotReadOrMutateHistory() throws {
        let suite = "FavaTests-" + UUID().uuidString
        let defaults = UserDefaults(suiteName: suite)!
        defer { defaults.removePersistentDomain(forName: suite) }
        let reader = RunIngestionTests.Reader(); let cache = RunIngestionTests.MemoryStore()
        let record = fixtureRun(distance: WorkoutDistance(value: 1, unit: .miles)); cache.history = try RetainedRunHistory.adoptingLegacy(runs: [record], capturedAt: nil)
        let ingestion = RunIngestionModel(reader: reader, historyStore: cache)
        let settings = DistanceSettings(defaults: defaults)
        settings.mode = .miles
        XCTAssertEqual(DistanceSettings(defaults: defaults).mode, .miles)
        settings.mode = .kilometres
        _ = RunFormatting.distance(record.distance, unit: settings.resolvedUnit(locale: english), locale: english)
        XCTAssertEqual(ingestion.savedHistory?.runs, [record])
        XCTAssertEqual(reader.reads, 0)
    }

    func testSelectionHandsOffExactUUIDForMatchingSummaries() {
        let a = fixtureRun();let b = fixtureRun();var handedOff: [UUID] = []
        let selection = RunSelection { handedOff.append($0) }
        selection.select(a.id); XCTAssertEqual(selection.selectedID, a.id)
        selection.select(b.id); XCTAssertEqual(selection.selectedID, b.id)
        XCTAssertEqual(handedOff, [a.id, b.id])
    }

    func testSourceSaveAndPendingNoticesAreDistinctAndNeutral() {
        let states: [IngestionState] = [.notRequested, .loading, .sourceSuccess(returnedCount: 2, savingFailed: false),
            .sourceSuccess(returnedCount: 0, savingFailed: false), .failed, .unavailable,
            .sourceSuccess(returnedCount: 2, savingFailed: true), .sourceSuccess(returnedCount: 0, savingFailed: true)]
        let messages = states.map { RunLibraryPresentation.notice($0, hasSavedRows: false) }
        XCTAssertEqual(Set(messages).count, states.count)
        for message in messages {
            XCTAssertFalse(message.lowercased().contains("denied"))
            XCTAssertFalse(message.lowercased().contains("granted"))
            XCTAssertFalse(message.lowercased().contains("never recorded"))
        }
        let failedSave = RunLibraryPresentation.notice(.sourceSuccess(returnedCount: 0, savingFailed: true), hasSavedRows: false)
        XCTAssertTrue(failedSave.contains("could not be saved"))
        XCTAssertFalse(failedSave.contains("no accessible runs"))
    }

    func testEmptyNoticeDescribesDisplayedRowsOnlyWhenHistoryContainsThem() throws {
        let priors: [RetainedRunHistory?] = [nil,
            try RetainedRunHistory.adoptingLegacy(runs: [], capturedAt: nil),
            try RetainedRunHistory.adoptingLegacy(runs: [fixtureRun()], capturedAt: nil)]
        for prior in priors {
            let cache = RunIngestionTests.MemoryStore(); cache.history = prior
            let reader = RunIngestionTests.Reader()
            let model = RunIngestionModel(reader: reader, historyStore: cache)
            model.requestRead(); reader.complete(.success([]))
            let hasSavedRows = !(model.savedHistory?.runs.isEmpty ?? true)
            let notice = RunLibraryPresentation.notice(model.state, hasSavedRows: hasSavedRows)
            XCTAssertEqual(notice, hasSavedRows
                ? "This read returned no accessible runs. Displayed runs were saved earlier."
                : "This read returned no accessible runs.")
            let committed = model.savedHistory
            cache.failSave = true
            model.requestRead(); reader.complete(.success([]))
            let failedSave = RunLibraryPresentation.notice(model.state, hasSavedRows: hasSavedRows)
            XCTAssertTrue(failedSave.contains("could not be saved locally"))
            XCTAssertFalse(failedSave.contains("no accessible runs"))
            XCTAssertFalse(failedSave.contains("Displayed runs were saved earlier"))
            XCTAssertEqual(model.savedHistory, committed)
        }
    }

    func testSavedRowsAndProvenanceSurviveLoadingFailureAndUnavailability() throws {
        for runs in [[fixtureRun()], []] {
            let cache = RunIngestionTests.MemoryStore()
            cache.history = try RetainedRunHistory.adoptingLegacy(runs: runs, capturedAt: nil)
            let reader = RunIngestionTests.Reader(); let ingestion = RunIngestionModel(reader: reader, historyStore: cache)
            let prior = ingestion.savedHistory
            ingestion.requestRead()
            XCTAssertEqual(ingestion.state, .loading)
            XCTAssertTrue(ingestion.isPriorSavedObservation)
            XCTAssertEqual(RunLibraryPresentation.rows(ingestion.savedHistory?.runs ?? []), runs)
            reader.complete(.failure(RunIngestionTests.Failure.synthetic))
            XCTAssertEqual(ingestion.state, .failed)
            XCTAssertEqual(ingestion.savedHistory, prior)
            reader.isAvailable = false; ingestion.requestRead()
            XCTAssertEqual(ingestion.state, .unavailable)
            XCTAssertEqual(ingestion.savedHistory, prior)
            XCTAssertTrue(ingestion.isPriorSavedObservation)
        }
    }

    func testSavedCountsMembershipAndUnknownTimeAreIndependent() throws {
        let a = fixtureRun(); let b = fixtureRun(); let c = fixtureRun()
        let date = Date(timeIntervalSinceReferenceDate: 123_456)
        let saved = try RetainedRunHistory(runs: [a, b, c], lastObservedAtByID: [b.id: date],
            latestSavedObservation: SavedReadObservation(observedAt: date, returnedIDs: [b.id]))
        let utc = TimeZone(secondsFromGMT: 0)!
        let observation = RunLibraryPresentation.savedObservation(saved, isPrior: true, locale: english, timeZone: utc)
        XCTAssertTrue(observation.contains("Prior saved read returned 1 run"))
        XCTAssertEqual(RunLibraryPresentation.savedHistoryCount(saved), "Saved history: 3 runs.")
        XCTAssertTrue(RunLibraryPresentation.rowProvenance(a.id, history: saved, locale: english, timeZone: utc).contains("Unobserved"))
        XCTAssertTrue(RunLibraryPresentation.rowProvenance(a.id, history: saved, locale: english, timeZone: utc).contains("Last observed: unknown"))
        XCTAssertTrue(RunLibraryPresentation.rowProvenance(b.id, history: saved, locale: english, timeZone: utc).contains("Returned by latest saved read"))
        let untimed = try RetainedRunHistory.adoptingLegacy(runs: [a], capturedAt: nil)
        XCTAssertTrue(RunLibraryPresentation.rowProvenance(a.id, history: untimed, locale: english, timeZone: utc).contains("Returned by latest saved read"))
        XCTAssertTrue(RunLibraryPresentation.savedObservation(untimed, isPrior: true, locale: english, timeZone: utc).contains("time unknown"))
        let unknown = try RetainedRunHistory(runs: [a])
        XCTAssertTrue(RunLibraryPresentation.rowProvenance(a.id, history: unknown, locale: english, timeZone: utc).contains("membership unknown"))
        XCTAssertEqual(RunLibraryPresentation.savedObservation(nil, isPrior: false, locale: english, timeZone: utc), "No saved read observation.")
        let empty = try RetainedRunHistory.adoptingLegacy(runs: [], capturedAt: nil)
        XCTAssertTrue(RunLibraryPresentation.savedObservation(empty, isPrior: true, locale: english, timeZone: utc).contains("Prior saved read returned 0 runs"))
    }
}

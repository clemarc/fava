import XCTest
@testable import Fava

@MainActor
final class RunLibraryTests: XCTestCase {
    private let english = Locale(identifier: "en_US")
    private func run(id: UUID = UUID(), start: Double = 1_704_067_200, duration: Double = 90, distance: WorkoutDistance? = nil) -> RunRecord {
        RunRecord(id: id, startDate: Date(timeIntervalSince1970: start), duration: duration, distance: distance)
    }

    func testChronologyStableTiesAndFullIdentityCollection() {
        let a = run(id: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!)
        let b = run(id: UUID(uuidString: "00000000-0000-0000-0000-000000000002")!)
        let old = run(start: 1_000_000)
        XCTAssertEqual(RunLibraryPresentation.rows([old, b, a]).map(\.id), [a.id, b.id, old.id])
        XCTAssertEqual(RunLibraryPresentation.rows([b, old, a]).map(\.id), [a.id, b.id, old.id])
        let history = (0..<2000).map { run(start: Double($0)) }
        XCTAssertEqual(RunLibraryPresentation.rows(history).count, history.count)
        XCTAssertEqual(RunLibraryPresentation.rows(history).first?.id, history.last?.id)
    }

    func testDateUsesCurrentLocaleAndTimeZoneWithoutChangingSource() {
        let record = run()
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

    func testPreferenceRelaunchDoesNotReadOrMutateSnapshot() {
        let suite = "FavaTests-" + UUID().uuidString
        let defaults = UserDefaults(suiteName: suite)!
        defer { defaults.removePersistentDomain(forName: suite) }
        let reader = RunIngestionTests.Reader(); let cache = RunIngestionTests.MemoryStore()
        let record = run(distance: WorkoutDistance(value: 1, unit: .miles)); cache.snapshot = RunSnapshot(runs: [record])
        let ingestion = RunIngestionModel(reader: reader, snapshotStore: cache)
        let settings = DistanceSettings(defaults: defaults)
        settings.mode = .miles
        XCTAssertEqual(DistanceSettings(defaults: defaults).mode, .miles)
        settings.mode = .kilometres
        _ = RunFormatting.distance(record.distance, unit: settings.resolvedUnit(locale: english), locale: english)
        XCTAssertEqual(ingestion.savedSnapshot?.runs, [record])
        XCTAssertEqual(reader.reads, 0)
    }

    func testSelectionHandsOffExactUUIDForMatchingSummaries() {
        let a = run();let b = run();var handedOff: [UUID] = []
        let selection = RunSelection { handedOff.append($0) }
        selection.select(a.id); XCTAssertEqual(selection.selectedID, a.id)
        selection.select(b.id); XCTAssertEqual(selection.selectedID, b.id)
        XCTAssertEqual(handedOff, [a.id, b.id])
    }

    func testSixAttemptNoticesAreDistinctAndNeutral() {
        let states: [IngestionState] = [.notRequested, .loading, .successfulNonempty, .successfulEmpty, .failed, .unavailable]
        let messages = states.map(RunLibraryPresentation.notice)
        XCTAssertEqual(Set(messages).count, states.count)
        for message in messages {
            XCTAssertFalse(message.lowercased().contains("denied"))
            XCTAssertFalse(message.lowercased().contains("granted"))
            XCTAssertFalse(message.lowercased().contains("never recorded"))
        }
    }

    func testSavedRowsAndEmptyProvenanceSurviveLoadingFailureAndUnavailability() {
        for runs in [[run()], []] {
            let cache = RunIngestionTests.MemoryStore(); cache.snapshot = RunSnapshot(runs: runs)
            let reader = RunIngestionTests.Reader();let ingestion = RunIngestionModel(reader: reader, snapshotStore: cache)
            ingestion.requestRead()
            XCTAssertEqual(ingestion.state, .loading)
            XCTAssertTrue(ingestion.isPreviouslyLoaded)
            XCTAssertEqual(RunLibraryPresentation.rows(ingestion.savedSnapshot?.runs ?? []), runs)
            reader.completion?(.failure(RunIngestionTests.Failure.synthetic))
            XCTAssertEqual(ingestion.state, .failed)
            XCTAssertEqual(ingestion.savedSnapshot?.runs, runs)
            reader.isAvailable = false;ingestion.requestRead()
            XCTAssertEqual(ingestion.state, .unavailable)
            XCTAssertEqual(ingestion.savedSnapshot?.runs, runs)
            XCTAssertTrue(ingestion.isPreviouslyLoaded)
        }
    }
}

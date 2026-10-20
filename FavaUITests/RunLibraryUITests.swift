import XCTest

final class RunLibraryUITests: XCTestCase {
    private let firstID = "00000000-0000-0000-0000-000000000001"
    private let secondID = "00000000-0000-0000-0000-000000000002"
    private var session = UUID().uuidString

    private func launch(_ fixture: String, category: String? = nil, enterLibrary: Bool = true) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--health-fixture", "completed", "--run-fixture", fixture, "--test-session", session]
        if let category { app.launchArguments += ["-UIPreferredContentSizeCategoryName", category] }
        app.launch()
        if enterLibrary {
            let library = app.buttons["open-library"]
            reveal(library, in: app)
            library.tap()
            XCTAssertTrue(app.navigationBars["Run library"].waitForExistence(timeout: 5))
        }
        return app
    }
    private func reveal(_ element: XCUIElement, in app: XCUIApplication) {
        for _ in 0..<10 { if element.isHittable { return }; app.swipeUp() }
    }
    private func awaitMessage(_ text: String, in app: XCUIApplication) {
        expectation(for: NSPredicate(format: "label CONTAINS %@", text), evaluatedWith: app.staticTexts["library-status"])
        waitForExpectations(timeout: 8)
    }

    private func notices(in app: XCUIApplication) {
        let status = app.staticTexts["library-status"]
        for _ in 0..<10 { if status.isHittable { return }; app.swipeDown() }
    }
    private func refresh(_ app: XCUIApplication) {
        notices(in: app)
        app.buttons["refresh-runs"].tap()
    }
    private func awaitChangedLabel(_ element: XCUIElement, from prior: String) {
        expectation(for: NSPredicate(format: "label != %@", prior), evaluatedWith: element)
        waitForExpectations(timeout: 8)
    }
    private func rowLabels(_ ids: [String], in app: XCUIApplication) -> [String] {
        notices(in: app)
        return ids.map { id in
            let row = app.buttons["run-" + id]
            reveal(row, in: app)
            XCTAssertTrue(row.exists)
            return row.label
        }
    }
    private func lastObserved(_ label: String) -> String {
        label.components(separatedBy: "Last observed:").last ?? label
    }

    func testChronologicalRowsMissingZeroAndExactSelection() {
        let app = launch("runs")
        let first = app.buttons["run-" + firstID]
        reveal(first, in: app)
        XCTAssertTrue(first.waitForExistence(timeout: 5))
        let second = app.buttons["run-" + secondID]
        XCTAssertLessThan(first.frame.minY, second.frame.minY)
        XCTAssertTrue(first.label.contains("Distance unavailable"))
        XCTAssertTrue(second.label.contains("0.00"))
        reveal(second, in: app); second.tap()
        XCTAssertEqual(second.value as? String, "Selected")
        notices(in: app); reveal(first, in: app); first.tap()
        XCTAssertEqual(first.value as? String, "Selected")
        XCTAssertEqual(second.value as? String, "Not selected")
        // Selection must also work in the label's full-width trailing whitespace.
        notices(in: app); reveal(second, in: app); second.tap()
        XCTAssertEqual(second.value as? String, "Selected")
        notices(in: app); reveal(first, in: app)
        first.coordinate(withNormalizedOffset: CGVector(dx: 0.9, dy: 0.5)).tap()
        XCTAssertEqual(first.value as? String, "Selected")
        XCTAssertEqual(second.value as? String, "Not selected")
    }

    func testSavedRowsStaySelectableDuringPendingFailedAndUnavailableReads() {
        for fixture in ["saved-pending", "saved-failed", "saved-unavailable"] {
            session = UUID().uuidString
            let app = launch(fixture)
            let first = app.buttons["run-" + firstID]
            reveal(first, in: app)
            XCTAssertTrue(first.waitForExistence(timeout: 5))
            XCTAssertTrue(app.staticTexts["saved-provenance"].label.contains("Prior saved read"))
            reveal(first, in: app);first.tap()
            XCTAssertEqual(first.value as? String, "Selected")
            let read = app.buttons["refresh-runs"]
            if fixture == "saved-failed" {
                awaitMessage("could not be loaded", in: app)
                XCTAssertTrue(read.isEnabled)
            } else { XCTAssertFalse(read.isEnabled) }
            app.navigationBars.buttons.element(boundBy: 0).tap()
            XCTAssertTrue(app.buttons["request-access"].exists)
            XCTAssertTrue(app.staticTexts["access-status"].label.contains("Choose when"))
            app.terminate()
        }
    }

    func testEmptyFailureRetryAndUnavailableAreDistinct() {
        var app = launch("empty")
        awaitMessage("no accessible runs", in: app)
        XCTAssertEqual(app.staticTexts["library-status"].label, "This read returned no accessible runs.")
        XCTAssertEqual(app.staticTexts["saved-history-count"].label, "Saved history: 0 runs.")
        XCTAssertFalse(app.buttons["run-" + firstID].exists)
        XCTAssertTrue(app.buttons["refresh-runs"].isEnabled)
        app.terminate();session = UUID().uuidString
        app = launch("failure-then-success")
        awaitMessage("could not be loaded", in: app)
        app.buttons["refresh-runs"].tap()
        XCTAssertTrue(app.buttons["run-" + firstID].waitForExistence(timeout: 5))
        app.navigationBars.buttons.element(boundBy: 0).tap()
        XCTAssertTrue(app.staticTexts["access-status"].label.contains("Choose when"))
        app.terminate();session = UUID().uuidString
        app = launch("unavailable")
        awaitMessage("unavailable", in: app)
        XCTAssertFalse(app.buttons["refresh-runs"].isEnabled)
        XCTAssertFalse(app.buttons["run-" + firstID].exists)
    }

    func testSavedEmptyPendingAndRelaunchKeepPriorResultMeaning() {
        var app = launch("saved-empty-pending")
        XCTAssertTrue(app.staticTexts["saved-provenance"].label.contains("Prior saved read returned 0 runs"))
        awaitMessage("Loading", in: app)
        app.terminate()
        app = launch("empty")
        awaitMessage("no accessible runs", in: app)
        XCTAssertEqual(app.staticTexts["library-status"].label, "This read returned no accessible runs.")
        XCTAssertEqual(app.staticTexts["saved-history-count"].label, "Saved history: 0 runs.")
        XCTAssertTrue(app.staticTexts["saved-provenance"].label.contains("Latest saved read returned 0 runs"))
        XCTAssertFalse(app.buttons["run-" + firstID].exists)
        app.terminate();session = UUID().uuidString
        app = launch("runs")
        XCTAssertTrue(app.buttons["run-" + firstID].waitForExistence(timeout: 5))
        app.terminate()
        app = launch("pending")
        XCTAssertTrue(app.buttons["run-" + firstID].exists)
        XCTAssertTrue(app.staticTexts["saved-provenance"].label.contains("Prior saved read"))
        awaitMessage("Loading", in: app)
        XCTAssertFalse(app.buttons["refresh-runs"].isEnabled)
    }

    func testSettingsPersistAndDoNotReadUntilAnotherLibraryEntry() {
        var app = launch("entry-switches", category: "UICTContentSizeCategoryAccessibilityXXXL")
        let first = app.buttons["run-" + firstID]
        reveal(first, in: app)
        XCTAssertTrue(first.waitForExistence(timeout: 5))
        notices(in: app)
        let beforeSettings = app.staticTexts["saved-provenance"].label
        app.buttons["open-settings"].tap()
        XCTAssertTrue(app.buttons["unit-device"].waitForExistence(timeout: 3))
        XCTAssertEqual(app.buttons["unit-device"].value as? String, "Selected")
        let miles = app.buttons["unit-miles"]
        reveal(miles, in: app);miles.tap()
        XCTAssertEqual(miles.value as? String, "Selected")
        app.buttons["close-settings"].tap()
        reveal(first, in: app)
        XCTAssertTrue(first.exists)
        notices(in: app)
        XCTAssertEqual(app.staticTexts["saved-provenance"].label, beforeSettings, "Settings must not start the next read")
        app.navigationBars.buttons.element(boundBy: 0).tap()
        let open = app.buttons["open-library"];reveal(open, in: app);open.tap()
        awaitMessage("no accessible runs", in: app)
        reveal(first, in: app)
        XCTAssertTrue(first.exists)
        XCTAssertTrue(first.label.contains("Unobserved in latest saved read"))
        app.terminate()
        app = launch("runs")
        app.buttons["open-settings"].tap()
        XCTAssertEqual(app.buttons["unit-miles"].value as? String, "Selected")
        app.buttons["unit-kilometres"].tap()
        XCTAssertEqual(app.buttons["unit-kilometres"].value as? String, "Selected")
    }

    func testRefreshRetainsHistoryAfterEmptyAndActiveReentryDoesNotOverlap() {
        var app = launch("entry-switches")
        XCTAssertTrue(app.buttons["run-" + firstID].waitForExistence(timeout: 5))
        app.buttons["refresh-runs"].tap()
        awaitMessage("no accessible runs", in: app)
        XCTAssertEqual(app.staticTexts["library-status"].label,
                       "This read returned no accessible runs. Displayed runs were saved earlier.")
        XCTAssertTrue(app.buttons["run-" + firstID].exists)
        XCTAssertTrue(app.buttons["run-" + firstID].label.contains("Unobserved in latest saved read"))
        app.terminate();session = UUID().uuidString
        app = launch("saved-pending")
        XCTAssertFalse(app.buttons["refresh-runs"].isEnabled)
        app.navigationBars.buttons.element(boundBy: 0).tap()
        app.buttons["open-library"].tap()
        XCTAssertFalse(app.buttons["refresh-runs"].isEnabled)
        XCTAssertTrue(app.buttons["run-" + firstID].exists)
    }

    func testSubsetAndRepeatedEmptyExposeRetainedCountsMembershipAndSavedTimes() {
        let app = launch("retention-sequence")
        let thirdID = "00000000-0000-0000-0000-000000000003"
        awaitMessage("returned 2 runs", in: app)
        XCTAssertEqual(app.staticTexts["saved-history-count"].label, "Saved history: 2 runs.")
        let initial = rowLabels([firstID, secondID], in: app)
        XCTAssertTrue(initial.allSatisfy { $0.contains("Returned by latest saved read") })
        refresh(app)
        expectation(for: NSPredicate(format: "label == %@", "Saved history: 3 runs."), evaluatedWith: app.staticTexts["saved-history-count"])
        waitForExpectations(timeout: 8)
        XCTAssertTrue(app.staticTexts["saved-provenance"].label.contains("Latest saved read returned 2 runs"))
        let subset = rowLabels([firstID, secondID, thirdID], in: app)
        XCTAssertTrue(subset[0].contains("Unobserved in latest saved read"))
        XCTAssertEqual(lastObserved(subset[0]), lastObserved(initial[0]))
        XCTAssertTrue(subset[1].contains("Returned by latest saved read"))
        XCTAssertTrue(subset[1].contains("03:00"))
        XCTAssertTrue(subset[1].contains("Distance unavailable"))
        XCTAssertNotEqual(lastObserved(subset[1]), lastObserved(initial[1]))
        XCTAssertTrue(subset[2].contains("Returned by latest saved read"))
        var emptyLabels: [String] = []
        for index in 0..<2 {
            notices(in: app)
            let previousObservation = app.staticTexts["saved-provenance"].label
            refresh(app)
            awaitChangedLabel(app.staticTexts["saved-provenance"], from: previousObservation)
            XCTAssertTrue(app.staticTexts["saved-provenance"].label.contains("Latest saved read returned 0 runs"))
            XCTAssertEqual(app.staticTexts["saved-history-count"].label, "Saved history: 3 runs.")
            awaitMessage("no accessible runs", in: app)
            let labels = rowLabels([firstID, secondID, thirdID], in: app)
            XCTAssertTrue(labels.allSatisfy { $0.contains("Unobserved in latest saved read") })
            XCTAssertEqual(labels.map(lastObserved), subset.map(lastObserved))
            if index == 0 { emptyLabels = labels } else { XCTAssertEqual(labels, emptyLabels) }
        }
    }

    func testSavingFailureKeepsExactSavedViewAcrossRetryAndRelaunch() {
        for fixture in ["save-failure-populated", "save-failure-absent", "save-failure-empty", "save-failure-untimed"] {
            session = UUID().uuidString
            var app = launch(fixture)
            awaitMessage("could not be saved", in: app)
            XCTAssertTrue(app.staticTexts["library-status"].label.contains("returned 2 runs"))
            let savedNotice = app.staticTexts["saved-provenance"].label
            let countNotice = app.staticTexts["saved-history-count"].label
            let populated = fixture == "save-failure-populated" || fixture == "save-failure-untimed"
            let ids = populated ? [firstID, secondID] : []
            let labels = rowLabels(ids, in: app)
            if populated {
                XCTAssertTrue(labels.allSatisfy { $0.contains("Returned by latest saved read") })
                XCTAssertTrue(labels[1].contains("0.00"), "Unsaved B replacement must not appear")
                XCTAssertTrue(savedNotice.contains("Prior saved read returned 2 runs"))
            } else {
                XCTAssertFalse(app.buttons["run-" + firstID].exists)
                XCTAssertFalse(app.buttons["run-" + secondID].exists)
            }
            if fixture == "save-failure-absent" { XCTAssertEqual(savedNotice, "No saved read observation.") }
            if fixture == "save-failure-empty" { XCTAssertTrue(savedNotice.contains("Prior saved read returned 0 runs")) }
            if fixture == "save-failure-untimed" {
                XCTAssertTrue(savedNotice.contains("time unknown"))
                XCTAssertTrue(labels.allSatisfy { $0.contains("Last observed: unknown") })
            }
            XCTAssertFalse(app.buttons["run-00000000-0000-0000-0000-000000000003"].exists)
            refresh(app)
            awaitMessage("returned 0 runs", in: app)
            XCTAssertTrue(app.staticTexts["library-status"].label.contains("could not be saved"))
            XCTAssertFalse(app.staticTexts["library-status"].label.contains("no accessible runs"))
            XCTAssertFalse(app.staticTexts["library-status"].label.contains("Displayed runs were saved earlier"))
            XCTAssertEqual(app.staticTexts["saved-provenance"].label, savedNotice)
            XCTAssertEqual(app.staticTexts["saved-history-count"].label, countNotice)
            XCTAssertEqual(rowLabels(ids, in: app), labels)
            app.terminate()
            app = launch("pending")
            awaitMessage("Loading", in: app)
            XCTAssertEqual(app.staticTexts["saved-provenance"].label, savedNotice)
            XCTAssertEqual(app.staticTexts["saved-history-count"].label, countNotice)
            XCTAssertEqual(rowLabels(ids, in: app), labels)
            if !populated { XCTAssertFalse(app.buttons["run-" + firstID].exists) }
            XCTAssertFalse(app.buttons["run-00000000-0000-0000-0000-000000000003"].exists)
            app.terminate()
        }
    }

    func testLocalRecoveryRetryReloadsWithoutStartingASourceRead() {
        let app = launch("recovery-read-once", enterLibrary: false)
        XCTAssertTrue(app.staticTexts["setup-local-recovery"].exists)
        XCTAssertTrue(app.buttons["setup-retry-saved-history"].exists)
        XCTAssertFalse(app.staticTexts["setup-saved-provenance"].exists)
        XCTAssertFalse(app.staticTexts["No saved read observation."].exists)
        XCTAssertFalse(app.staticTexts["Saved history: 0 runs."].exists)
        let library = app.buttons["open-library"]
        reveal(library, in: app); library.tap()
        XCTAssertTrue(app.navigationBars["Run library"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["local-recovery"].exists)
        XCTAssertFalse(app.staticTexts["saved-history-count"].exists)
        XCTAssertFalse(app.staticTexts["saved-provenance"].exists)
        XCTAssertFalse(app.staticTexts["No saved read observation."].exists)
        XCTAssertFalse(app.staticTexts["Saved history: 0 runs."].exists)
        XCTAssertFalse(app.buttons["refresh-runs"].isEnabled)
        XCTAssertTrue(app.staticTexts["library-status"].label.contains("No read requested"))
        app.buttons["retry-saved-history"].tap()
        XCTAssertFalse(app.staticTexts["local-recovery"].exists)
        XCTAssertTrue(app.staticTexts["library-status"].label.contains("No read requested"))
        XCTAssertTrue(app.buttons["refresh-runs"].isEnabled)
        XCTAssertEqual(app.staticTexts["saved-history-count"].label, "Saved history: 2 runs.")
        XCTAssertTrue(app.staticTexts["saved-provenance"].label.contains("Prior saved read returned 2 runs"))
        let labels = rowLabels([firstID, secondID], in: app)
        XCTAssertTrue(labels.allSatisfy { $0.contains("Returned by latest saved read") })
        app.navigationBars.buttons.element(boundBy: 0).tap()
        XCTAssertFalse(app.staticTexts["setup-local-recovery"].exists)
        XCTAssertTrue(app.staticTexts["setup-saved-provenance"].label.contains("Prior saved read returned 2 runs"))
    }

    func testLibraryActionsAndRowsReachableAtEveryDynamicTypeSize() {
        let categories = ["UICTContentSizeCategoryXS", "UICTContentSizeCategoryS", "UICTContentSizeCategoryM", "UICTContentSizeCategoryL", "UICTContentSizeCategoryXL", "UICTContentSizeCategoryXXL", "UICTContentSizeCategoryXXXL", "UICTContentSizeCategoryAccessibilityM", "UICTContentSizeCategoryAccessibilityL", "UICTContentSizeCategoryAccessibilityXL", "UICTContentSizeCategoryAccessibilityXXL", "UICTContentSizeCategoryAccessibilityXXXL"]
        for category in categories {
            session = UUID().uuidString
            let app = launch("runs", category: category)
            let row = app.buttons["run-" + firstID]
            reveal(row, in: app)
            XCTAssertTrue(row.waitForExistence(timeout: 5))
            XCTAssertTrue(row.isHittable, category)
            XCTAssertTrue(row.label.contains("Duration"))
            row.tap();XCTAssertEqual(row.value as? String, "Selected")
            let oldest = app.buttons["run-00000000-0000-0000-0000-000000000003"]
            reveal(oldest, in: app);XCTAssertTrue(oldest.isHittable, category)
            XCTAssertTrue(app.buttons["open-settings"].isHittable)
            app.terminate()
        }
    }
}

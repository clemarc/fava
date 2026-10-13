import XCTest

final class RunLibraryUITests: XCTestCase {
    private let firstID = "00000000-0000-0000-0000-000000000001"
    private let secondID = "00000000-0000-0000-0000-000000000002"
    private var session = UUID().uuidString

    private func launch(_ fixture: String, category: String? = nil) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--health-fixture", "completed", "--run-fixture", fixture, "--test-session", session]
        if let category { app.launchArguments += ["-UIPreferredContentSizeCategoryName", category] }
        app.launch()
        let library = app.buttons["open-library"]
        reveal(library, in: app)
        library.tap()
        XCTAssertTrue(app.navigationBars["Run library"].waitForExistence(timeout: 5))
        return app
    }
    private func reveal(_ element: XCUIElement, in app: XCUIApplication) {
        for _ in 0..<10 { if element.isHittable { return }; app.swipeUp() }
    }
    private func awaitMessage(_ text: String, in app: XCUIApplication) {
        expectation(for: NSPredicate(format: "label CONTAINS %@", text), evaluatedWith: app.staticTexts["library-status"])
        waitForExpectations(timeout: 8)
    }

    func testChronologicalRowsMissingZeroAndExactSelection() {
        let app = launch("runs")
        let first = app.buttons["run-" + firstID]
        XCTAssertTrue(first.waitForExistence(timeout: 5))
        let second = app.buttons["run-" + secondID]
        XCTAssertLessThan(first.frame.minY, second.frame.minY)
        XCTAssertTrue(first.label.contains("Distance unavailable"))
        XCTAssertTrue(second.label.contains("0.00"))
        second.tap()
        XCTAssertEqual(second.value as? String, "Selected")
        first.tap()
        XCTAssertEqual(first.value as? String, "Selected")
        XCTAssertEqual(second.value as? String, "Not selected")
    }

    func testSavedRowsStaySelectableDuringPendingFailedAndUnavailableReads() {
        for fixture in ["saved-pending", "saved-failed", "saved-unavailable"] {
            session = UUID().uuidString
            let app = launch(fixture)
            let first = app.buttons["run-" + firstID]
            XCTAssertTrue(first.waitForExistence(timeout: 5))
            XCTAssertTrue(app.staticTexts["saved-provenance"].label.contains("Previously loaded"))
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
        awaitMessage("returned by this read", in: app)
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
        XCTAssertTrue(app.staticTexts["saved-provenance"].label.contains("Previously loaded empty"))
        awaitMessage("Loading", in: app)
        app.terminate();session = UUID().uuidString
        app = launch("runs")
        XCTAssertTrue(app.buttons["run-" + firstID].waitForExistence(timeout: 5))
        app.terminate()
        app = launch("pending")
        XCTAssertTrue(app.buttons["run-" + firstID].exists)
        XCTAssertTrue(app.staticTexts["saved-provenance"].label.contains("Previously loaded"))
        awaitMessage("Loading", in: app)
        XCTAssertFalse(app.buttons["refresh-runs"].isEnabled)
    }

    func testSettingsPersistAndDoNotReadUntilAnotherLibraryEntry() {
        var app = launch("entry-switches", category: "UICTContentSizeCategoryAccessibilityXXXL")
        let first = app.buttons["run-" + firstID]
        XCTAssertTrue(first.waitForExistence(timeout: 5))
        app.buttons["open-settings"].tap()
        XCTAssertTrue(app.buttons["unit-device"].waitForExistence(timeout: 3))
        XCTAssertEqual(app.buttons["unit-device"].value as? String, "Selected")
        let miles = app.buttons["unit-miles"]
        reveal(miles, in: app);miles.tap()
        XCTAssertEqual(miles.value as? String, "Selected")
        app.buttons["close-settings"].tap()
        XCTAssertTrue(first.exists, "Settings must not start the next read")
        app.navigationBars.buttons.element(boundBy: 0).tap()
        let open = app.buttons["open-library"];reveal(open, in: app);open.tap()
        awaitMessage("returned by this read", in: app)
        XCTAssertFalse(first.exists)
        app.terminate()
        app = launch("runs")
        app.buttons["open-settings"].tap()
        XCTAssertEqual(app.buttons["unit-miles"].value as? String, "Selected")
        app.buttons["unit-kilometres"].tap()
        XCTAssertEqual(app.buttons["unit-kilometres"].value as? String, "Selected")
    }

    func testRefreshReplacesWithEmptyAndActiveReentryDoesNotOverlap() {
        var app = launch("entry-switches")
        XCTAssertTrue(app.buttons["run-" + firstID].waitForExistence(timeout: 5))
        app.buttons["refresh-runs"].tap()
        awaitMessage("returned by this read", in: app)
        XCTAssertFalse(app.buttons["run-" + firstID].exists)
        app.terminate();session = UUID().uuidString
        app = launch("saved-pending")
        XCTAssertFalse(app.buttons["refresh-runs"].isEnabled)
        app.navigationBars.buttons.element(boundBy: 0).tap()
        app.buttons["open-library"].tap()
        XCTAssertFalse(app.buttons["refresh-runs"].isEnabled)
        XCTAssertTrue(app.buttons["run-" + firstID].exists)
    }

    func testLibraryActionsAndRowsReachableAtEveryDynamicTypeSize() {
        let categories = ["UICTContentSizeCategoryXS", "UICTContentSizeCategoryS", "UICTContentSizeCategoryM", "UICTContentSizeCategoryL", "UICTContentSizeCategoryXL", "UICTContentSizeCategoryXXL", "UICTContentSizeCategoryXXXL", "UICTContentSizeCategoryAccessibilityM", "UICTContentSizeCategoryAccessibilityL", "UICTContentSizeCategoryAccessibilityXL", "UICTContentSizeCategoryAccessibilityXXL", "UICTContentSizeCategoryAccessibilityXXXL"]
        for category in categories {
            session = UUID().uuidString
            let app = launch("runs", category: category)
            let row = app.buttons["run-" + firstID]
            XCTAssertTrue(row.waitForExistence(timeout: 5))
            reveal(row, in: app);XCTAssertTrue(row.isHittable, category)
            XCTAssertTrue(row.label.contains("Duration"))
            row.tap();XCTAssertEqual(row.value as? String, "Selected")
            let oldest = app.buttons["run-00000000-0000-0000-0000-000000000003"]
            reveal(oldest, in: app);XCTAssertTrue(oldest.isHittable, category)
            XCTAssertTrue(app.buttons["open-settings"].isHittable)
            app.terminate()
        }
    }
}

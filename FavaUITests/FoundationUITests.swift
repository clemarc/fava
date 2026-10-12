import XCTest

final class FoundationUITests: XCTestCase {
    private func launch(_ fixture: String = "completed", category: String? = nil) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--health-fixture", fixture]
        if let category { app.launchArguments += ["-UIPreferredContentSizeCategoryName", category] }
        app.launch()
        return app
    }

    private func reveal(_ element: XCUIElement, in app: XCUIApplication) {
        for _ in 0..<8 {
            if element.isHittable { return }
            app.swipeUp()
        }
    }

    func testLaunchNavigateReturnAndRelaunchWithoutAutomaticRequest() {
        let app = launch()
        XCTAssertTrue(app.staticTexts["access-status"].label.contains("Choose when"))
        XCTAssertTrue(app.buttons["request-access"].isEnabled)
        app.buttons["open-library"].tap()
        XCTAssertTrue(app.navigationBars["Run library"].waitForExistence(timeout: 3))
        app.navigationBars.buttons.element(boundBy: 0).tap()
        XCTAssertTrue(app.buttons["request-access"].exists)
        app.terminate()
        app.launch()
        XCTAssertTrue(app.staticTexts["access-status"].label.contains("Choose when"))
    }

    func testCompletionIsNeutralAndRepeatable() {
        let app = launch()
        app.buttons["request-access"].tap()
        let status = app.staticTexts["access-status"]
        let completed = NSPredicate(format: "label CONTAINS 'Request completed'")
        expectation(for: completed, evaluatedWith: status)
        waitForExpectations(timeout: 5)
        XCTAssertFalse(status.label.contains("granted"))
        XCTAssertFalse(status.label.contains("denied"))
        XCTAssertTrue(app.buttons["request-access"].isEnabled)
        app.buttons["request-access"].tap()
        expectation(for: completed, evaluatedWith: status)
        waitForExpectations(timeout: 5)
    }

    func testFailureAndReportedCancellationAllowRetry() {
        for fixture in ["failed", "cancelled"] {
            let app = launch(fixture)
            app.buttons["request-access"].tap()
            let predicate = NSPredicate(format: "label CONTAINS %@", fixture == "failed" ? "request failed" : "Request not completed")
            expectation(for: predicate, evaluatedWith: app.staticTexts["access-status"])
            waitForExpectations(timeout: 5)
            XCTAssertTrue(app.buttons["request-access"].isEnabled)
            XCTAssertEqual(app.buttons["request-access"].label, "Retry HealthKit request")
            app.buttons["open-library"].tap()
            XCTAssertTrue(app.navigationBars["Run library"].exists)
            app.terminate()
        }
    }

    func testUnavailableLeavesNavigationUsable() {
        let app = launch("unavailable")
        XCTAssertFalse(app.buttons["request-access"].isEnabled)
        XCTAssertTrue(app.staticTexts["access-status"].label.contains("unavailable"))
        app.buttons["open-library"].tap()
        XCTAssertTrue(app.navigationBars["Run library"].exists)
    }

    func testActiveRequestDisablesActionAndBackgroundReturnPreservesNavigation() {
        let app = launch("pending")
        app.buttons["request-access"].tap()
        XCTAssertFalse(app.buttons["request-access"].isEnabled)
        XCUIDevice.shared.press(.home)
        app.activate()
        XCTAssertTrue(app.staticTexts["access-status"].label.contains("in progress"))
        app.buttons["open-library"].tap()
        XCTAssertTrue(app.navigationBars["Run library"].exists)
    }

    func testActionsReachableAtEveryDynamicTypeSize() {
        let categories = ["UICTContentSizeCategoryXS", "UICTContentSizeCategoryS", "UICTContentSizeCategoryM", "UICTContentSizeCategoryL", "UICTContentSizeCategoryXL", "UICTContentSizeCategoryXXL", "UICTContentSizeCategoryXXXL", "UICTContentSizeCategoryAccessibilityM", "UICTContentSizeCategoryAccessibilityL", "UICTContentSizeCategoryAccessibilityXL", "UICTContentSizeCategoryAccessibilityXXL", "UICTContentSizeCategoryAccessibilityXXXL"]
        for category in categories {
            let app = launch(category: category)
            let request = app.buttons["request-access"]
            reveal(request, in: app)
            XCTAssertTrue(request.isHittable, category)
            XCTAssertFalse(request.label.isEmpty)
            let library = app.buttons["open-library"]
            reveal(library, in: app)
            XCTAssertTrue(library.isHittable, category)
            library.tap()
            XCTAssertTrue(app.navigationBars["Run library"].exists)
            app.terminate()
        }
    }
}

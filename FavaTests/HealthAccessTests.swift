import XCTest
import HealthKit
@testable import Fava

@MainActor
final class HealthAccessTests: XCTestCase {
    final class Provider: HealthAccessProviding {
        var isAvailable = true
        var requests = 0
        var completion: ((HealthAccessOutcome) -> Void)?
        func request(completion: @escaping (HealthAccessOutcome) -> Void) {
            requests += 1
            self.completion = completion
        }
    }

    func testLaunchAndFreshSessionNeverRequestOrRestoreProgress() {
        let provider = Provider()
        let first = HealthAccessModel(provider: provider)
        XCTAssertEqual(first.state, .idle)
        XCTAssertEqual(provider.requests, 0)
        first.request()
        XCTAssertEqual(first.state, .requesting)
        let fresh = HealthAccessModel(provider: provider)
        XCTAssertEqual(fresh.state, .idle)
        XCTAssertEqual(provider.requests, 1)
    }

    func testExplicitRequestGuardsOverlapAndCompletesNeutrally() {
        let provider = Provider()
        let model = HealthAccessModel(provider: provider)
        model.request()
        model.request()
        XCTAssertEqual(provider.requests, 1)
        XCTAssertEqual(model.state, .requesting)
        XCTAssertFalse(model.canRequest)
        provider.completion?(.completed)
        XCTAssertEqual(model.state, .completed)
        XCTAssertTrue(model.canRequest)
        XCTAssertFalse(model.state.message.contains("granted"))
        XCTAssertFalse(model.state.message.contains("denied"))
        model.request()
        XCTAssertEqual(provider.requests, 2)
    }

    func testFailureAndCancellationAreDistinctAndRetryable() {
        for outcome in [HealthAccessOutcome.failed, .cancelled] {
            let provider = Provider()
            let model = HealthAccessModel(provider: provider)
            model.request()
            provider.completion?(outcome)
            XCTAssertEqual(model.state, outcome == .failed ? .failed : .cancelled)
            XCTAssertTrue(model.canRequest)
            if outcome == .cancelled { XCTAssertEqual(model.state.message, "Request not completed") }
            model.request()
            XCTAssertEqual(provider.requests, 2)
        }
    }

    func testUnavailableRecheckedBeforeEveryRequest() {
        let provider = Provider()
        provider.isAvailable = false
        let model = HealthAccessModel(provider: provider)
        XCTAssertEqual(model.state, .unavailable)
        model.request()
        XCTAssertEqual(provider.requests, 0)
        provider.isAvailable = true
        model.updateAvailability()
        XCTAssertTrue(model.canRequest)
        model.request()
        provider.completion?(.completed)
        provider.isAvailable = false
        model.request()
        XCTAssertEqual(model.state, .unavailable)
        XCTAssertEqual(provider.requests, 1)
    }

    func testBackgroundAvailabilityUpdateDoesNotRestartOrLoseReportedOutcome() {
        let provider = Provider()
        let model = HealthAccessModel(provider: provider)
        model.request()
        model.updateAvailability()
        XCTAssertEqual(model.state, .requesting)
        XCTAssertEqual(provider.requests, 1)
        provider.completion?(.cancelled)
        model.updateAvailability()
        XCTAssertEqual(model.state, .cancelled)
        XCTAssertEqual(provider.requests, 1)
    }

    final class Store: HealthAuthorizationStore {
        var isAvailable = true
        var share: Set<HKSampleType> = []
        var read: Set<HKObjectType> = []
        var completion: ((Bool, Error?) -> Void)?
        func requestAuthorization(toShare: Set<HKSampleType>, read: Set<HKObjectType>, completion: @escaping (Bool, Error?) -> Void) {
            share = toShare
            self.read = read
            self.completion = completion
        }
    }

    func testAdapterRequestsOnlyWorkoutReadAndNoWrites() {
        let store = Store()
        let adapter = HealthKitAccess(store: store)
        adapter.request { _ in }
        XCTAssertEqual(store.read, [HKObjectType.workoutType()])
        XCTAssertTrue(store.share.isEmpty)
    }

    func testAdapterMapsOnlyReportedCancellationAndDoesNotInferPermission() {
        XCTAssertEqual(HealthKitAccess.outcome(success: true, error: nil), .completed)
        XCTAssertEqual(HealthKitAccess.outcome(success: false, error: nil), .failed)
        XCTAssertEqual(HealthKitAccess.outcome(success: false, error: NSError(domain: HKErrorDomain, code: HKError.Code.errorUserCanceled.rawValue)), .cancelled)
        XCTAssertEqual(HealthKitAccess.outcome(success: false, error: NSError(domain: HKErrorDomain, code: HKError.Code.errorAuthorizationDenied.rawValue)), .failed)
        XCTAssertEqual(HealthKitAccess.outcome(success: true, error: NSError(domain: "synthetic", code: 1)), .failed)
    }
}

import HealthKit

protocol HealthAuthorizationStore {
    var isAvailable: Bool { get }
    func requestAuthorization(toShare: Set<HKSampleType>, read: Set<HKObjectType>, completion: @escaping (Bool, Error?) -> Void)
}

struct SystemHealthAuthorizationStore: HealthAuthorizationStore {
    private let store = HKHealthStore()
    var isAvailable: Bool { HKHealthStore.isHealthDataAvailable() }
    func requestAuthorization(toShare: Set<HKSampleType>, read: Set<HKObjectType>, completion: @escaping (Bool, Error?) -> Void) {
        store.requestAuthorization(toShare: toShare, read: read, completion: completion)
    }
}

@MainActor
final class HealthKitAccess: HealthAccessProviding {
    private let store: HealthAuthorizationStore
    init(store: HealthAuthorizationStore = SystemHealthAuthorizationStore()) { self.store = store }
    var isAvailable: Bool { store.isAvailable }
    func request(completion: @escaping (HealthAccessOutcome) -> Void) {
        store.requestAuthorization(toShare: [], read: [HKObjectType.workoutType()]) { success, error in
            let outcome = Self.outcome(success: success, error: error)
            Task { @MainActor in completion(outcome) }
        }
    }
    nonisolated static func outcome(success: Bool, error: Error?) -> HealthAccessOutcome {
        if let error = error as NSError? {
            if error.domain == HKErrorDomain && error.code == HKError.Code.errorUserCanceled.rawValue { return .cancelled }
            return .failed
        }
        return success ? .completed : .failed
    }
}

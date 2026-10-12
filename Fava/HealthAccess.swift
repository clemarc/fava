import Combine
import Foundation

@MainActor
protocol HealthAccessProviding {
    var isAvailable: Bool { get }
    func request(completion: @escaping (HealthAccessOutcome) -> Void)
}

enum HealthAccessOutcome: Equatable { case completed, failed, cancelled }

enum HealthAccessState: Equatable {
    case idle, requesting, completed, failed, cancelled, unavailable

    var message: String {
        switch self {
        case .idle: return "Choose when to request workout access."
        case .requesting: return "Request in progress"
        case .completed: return "Request completed. Readable workouts depend on your Health settings."
        case .failed: return "HealthKit request failed. You can try again."
        case .cancelled: return "Request not completed"
        case .unavailable: return "HealthKit is unavailable on this device."
        }
    }
}

@MainActor
final class HealthAccessModel: ObservableObject {
    @Published private(set) var state: HealthAccessState
    @Published private(set) var isAvailable: Bool
    private let provider: HealthAccessProviding

    init(provider: HealthAccessProviding) {
        self.provider = provider
        isAvailable = provider.isAvailable
        state = isAvailable ? .idle : .unavailable
    }

    var canRequest: Bool { isAvailable && state != .requesting }

    func updateAvailability() {
        isAvailable = provider.isAvailable
        guard state != .requesting else { return }
        if !isAvailable { state = .unavailable }
        else if state == .unavailable { state = .idle }
    }

    func request() {
        guard state != .requesting else { return }
        updateAvailability()
        guard isAvailable else { return }
        state = .requesting
        provider.request { [weak self] outcome in
            switch outcome {
            case .completed: self?.state = .completed
            case .failed: self?.state = .failed
            case .cancelled: self?.state = .cancelled
            }
        }
    }
}

#if DEBUG
@MainActor
final class SyntheticHealthAccess: HealthAccessProviding {
    let fixture: String
    var isAvailable: Bool { fixture != "unavailable" }
    init(fixture: String) { self.fixture = fixture }
    func request(completion: @escaping (HealthAccessOutcome) -> Void) {
        guard fixture != "pending" else { return }
        let outcome: HealthAccessOutcome = fixture == "failed" ? .failed : fixture == "cancelled" ? .cancelled : .completed
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { completion(outcome) }
    }
}
#endif

import Combine

// Routes are explicit navigation context, never derived again from source outcomes.
enum LaunchRoute: Equatable {
    case setup, library, recovery
}

@MainActor
final class LaunchContext: ObservableObject {
    @Published private(set) var route: LaunchRoute
    private let ingestion: RunIngestionModel
    private var initialEntryPending: Bool

    init(ingestion: RunIngestionModel) {
        self.ingestion = ingestion
        route = Self.initialRoute(for: ingestion.localHistory)
        initialEntryPending = route == .library
    }

    private static func initialRoute(for history: LocalHistoryState) -> LaunchRoute {
        switch history {
        case .absent: return .setup
        case .readable(let saved): return saved.runs.isEmpty ? .setup : .library
        case .recovery: return .recovery
        }
    }

    // Called after the initial library destination appears. Repeated appearances,
    // layout, foregrounding and published ingestion updates cannot create entries.
    func startInitialEntry() {
        guard initialEntryPending, route == .library else { return }
        initialEntryPending = false
        ingestion.requestRead()
    }

    func enterLibrary() {
        guard route != .library else { return }
        initialEntryPending = false
        route = .library
        ingestion.requestRead()
    }

    func leaveLibrary() {
        guard route == .library else { return }
        initialEntryPending = false
        route = ingestion.localRecoveryMessage == nil ? .setup : .recovery
    }

    func retryLocalLoad() {
        ingestion.retryLocalLoad()
        guard route == .recovery else { return }
        route = Self.initialRoute(for: ingestion.localHistory)
        // Reload itself is source-free. A newly installed populated destination
        // receives its distinct initial-entry event after it appears.
        initialEntryPending = route == .library
    }
}

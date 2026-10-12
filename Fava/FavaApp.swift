import SwiftUI

@main
struct FavaApp: App {
    @StateObject private var access: HealthAccessModel
    @StateObject private var ingestion: RunIngestionModel
    @StateObject private var settings: DistanceSettings
    @StateObject private var selection = RunSelection()

    init() {
        var provider: HealthAccessProviding = HealthKitAccess()
        var reader: WorkoutReading = HealthKitWorkoutReader()
        var cache: RunSnapshotStoring = FileRunSnapshotStore()
        var defaults = UserDefaults.standard
        #if DEBUG
        let arguments = ProcessInfo.processInfo.arguments
        if let index = arguments.firstIndex(of: "--health-fixture"), arguments.indices.contains(index + 1) {
            provider = SyntheticHealthAccess(fixture: arguments[index + 1])
            reader = SyntheticWorkoutReader(fixture: "empty")
            cache = SyntheticWorkoutReader.snapshotStore(fixture: "empty", session: "R1-" + UUID().uuidString)
        }
        if let index = arguments.firstIndex(of: "--run-fixture"), arguments.indices.contains(index + 1) {
            let fixture = arguments[index + 1]
            let session = arguments.firstIndex(of: "--test-session").flatMap { arguments.indices.contains($0 + 1) ? arguments[$0 + 1] : nil } ?? UUID().uuidString
            reader = SyntheticWorkoutReader(fixture: fixture)
            cache = SyntheticWorkoutReader.snapshotStore(fixture: fixture, session: session)
            defaults = UserDefaults(suiteName: "Fava-UITests-" + session) ?? .standard
        }
        #endif
        _access = StateObject(wrappedValue: HealthAccessModel(provider: provider))
        _ingestion = StateObject(wrappedValue: RunIngestionModel(reader: reader, snapshotStore: cache))
        _settings = StateObject(wrappedValue: DistanceSettings(defaults: defaults))
    }

    var body: some Scene {
        WindowGroup {
            RootView(access: access)
                .environmentObject(ingestion)
                .environmentObject(settings)
                .environmentObject(selection)
        }
    }
}

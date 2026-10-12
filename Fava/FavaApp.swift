import SwiftUI

@main
struct FavaApp: App {
    @StateObject private var access: HealthAccessModel

    init() {
        var provider: HealthAccessProviding = HealthKitAccess()
        #if DEBUG
        let arguments = ProcessInfo.processInfo.arguments
        if let index = arguments.firstIndex(of: "--health-fixture"), arguments.indices.contains(index + 1) {
            provider = SyntheticHealthAccess(fixture: arguments[index + 1])
        }
        #endif
        _access = StateObject(wrappedValue: HealthAccessModel(provider: provider))
    }

    var body: some Scene {
        WindowGroup {
            RootView(access: access)
        }
    }
}

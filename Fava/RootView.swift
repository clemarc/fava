import SwiftUI
import UIKit

struct RootView: View {
    @ObservedObject var access: HealthAccessModel
    @EnvironmentObject private var ingestion: RunIngestionModel
    @ObservedObject var launch: LaunchContext
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.locale) private var locale
    @Environment(\.timeZone) private var timeZone

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    Text("Your running workouts, together.").font(.title).bold()
                    Text("Fava helps you browse running workouts from Apple Health on your iPhone and iPad.")
                    if let message = ingestion.localRecoveryMessage {
                        Text(message).accessibilityIdentifier("setup-local-recovery")
                        Button("Retry saved history", action: launch.retryLocalLoad)
                            .disabled(ingestion.isTransportActive)
                            .accessibilityIdentifier("setup-retry-saved-history")
                    } else {
                        Text(RunLibraryPresentation.savedObservation(ingestion.savedHistory, isPrior: ingestion.isPriorSavedObservation,
                                                                   locale: locale, timeZone: timeZone))
                            .accessibilityIdentifier("setup-saved-provenance")
                    }
                    HealthAccessContent(access: access)
                    Button("Run library") {
                        launch.enterLibrary()
                    }
                    .accessibilityIdentifier("open-library")
                }
                .padding()
                .frame(maxWidth: 640, alignment: .leading)
                .frame(maxWidth: .infinity)
            }
            .navigationTitle("Fava")
            .navigationDestination(isPresented: Binding(
                get: { launch.route == .library },
                set: { if !$0 { launch.leaveLibrary() } }
            )) {
                RunLibraryView(access: access).task { launch.startInitialEntry() }
            }
        }
        #if DEBUG
        .safeAreaInset(edge: .bottom) {
            if ProcessInfo.processInfo.arguments.contains("--health-fixture") || ProcessInfo.processInfo.arguments.contains("--run-fixture") {
                SyntheticLaunchEvidence(route: launch.route)
            }
        }
        #endif
        .onChange(of: access.state) { _, value in
            UIAccessibility.post(notification: .announcement, argument: value.message)
        }
        .onChange(of: scenePhase) { _, value in
            if value == .active { access.updateAvailability() }
        }
    }
}

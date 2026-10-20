import SwiftUI
import UIKit

struct RootView: View {
    @ObservedObject var access: HealthAccessModel
    @EnvironmentObject private var ingestion: RunIngestionModel
    @State private var libraryVisible = false
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.locale) private var locale
    @Environment(\.timeZone) private var timeZone

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    Text("Your running workouts, together.").font(.title).bold()
                    Text("Fava helps you browse running workouts from Apple Health on your iPhone and iPad.")
                    Text("Workout-record read access lets Fava use your running workouts. You choose when to request access. Fava does not write health data.")
                    if let message = ingestion.localRecoveryMessage {
                        Text(message).accessibilityIdentifier("setup-local-recovery")
                        Button("Retry saved history", action: ingestion.retryLocalLoad)
                            .disabled(ingestion.isTransportActive)
                            .accessibilityIdentifier("setup-retry-saved-history")
                    } else {
                        Text(RunLibraryPresentation.savedObservation(ingestion.savedHistory, isPrior: ingestion.isPriorSavedObservation,
                                                                   locale: locale, timeZone: timeZone))
                            .accessibilityIdentifier("setup-saved-provenance")
                    }
                    Text(access.state.message)
                        .accessibilityIdentifier("access-status")
                    if access.state == .requesting {
                        ProgressView("Request in progress")
                    }
                    Button(action: access.request) {
                        Text(access.state == .failed || access.state == .cancelled ? "Retry HealthKit request" : "Request HealthKit access")
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!access.canRequest)
                    .accessibilityIdentifier("request-access")
                    Button("Run library") {
                        guard !libraryVisible else { return }
                        libraryVisible = true
                        ingestion.requestRead()
                    }
                    .accessibilityIdentifier("open-library")
                }
                .padding()
                .frame(maxWidth: 640, alignment: .leading)
                .frame(maxWidth: .infinity)
            }
            .navigationTitle("Fava")
            .navigationDestination(isPresented: $libraryVisible) { RunLibraryView() }
        }
        .onChange(of: access.state) { _, value in
            UIAccessibility.post(notification: .announcement, argument: value.message)
        }
        .onChange(of: scenePhase) { _, value in
            if value == .active { access.updateAvailability() }
        }
    }
}

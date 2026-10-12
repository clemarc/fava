import SwiftUI
import UIKit

struct RootView: View {
    @ObservedObject var access: HealthAccessModel
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    Text("Your running workouts, together.").font(.title).bold()
                    Text("Fava helps you browse running workouts from Apple Health on your iPhone and iPad.")
                    Text("Workout-record read access lets Fava use your running workouts. You choose when to request access. Fava does not write health data.")
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
                    NavigationLink("Run library") {
                        LibraryFoundationView()
                    }
                    .accessibilityIdentifier("open-library")
                }
                .padding()
                .frame(maxWidth: 640, alignment: .leading)
                .frame(maxWidth: .infinity)
            }
            .navigationTitle("Fava")
        }
        .onChange(of: access.state) { _, value in
            UIAccessibility.post(notification: .announcement, argument: value.message)
        }
        .onChange(of: scenePhase) { _, value in
            if value == .active { access.updateAvailability() }
        }
    }
}

struct LibraryFoundationView: View {
    var body: some View {
        ScrollView {
            Text("This is where you will browse your running workouts.")
                .padding()
                .frame(maxWidth: 640, alignment: .leading)
                .frame(maxWidth: .infinity)
        }
        .navigationTitle("Run library")
    }
}

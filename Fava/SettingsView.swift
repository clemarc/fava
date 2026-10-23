import SwiftUI

struct SettingsView: View {
    @ObservedObject var settings: DistanceSettings
    @ObservedObject var access: HealthAccessModel
    let onDone: () -> Void
    var body: some View {
        NavigationStack {
            List {
                Section("Distance units") {
                    ForEach(DistanceMode.allCases, id: \.rawValue) { mode in
                        Button { settings.mode = mode } label: {
                            VStack(alignment: .leading, spacing: 8) {
                                Text(mode.title)
                                if settings.mode == mode { Label("Selected", systemImage: "checkmark") }
                            }
                            .foregroundStyle(.primary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .accessibilityElement(children: .combine)
                        }
                        .accessibilityIdentifier("unit-" + mode.rawValue)
                        .accessibilityValue(settings.mode == mode ? "Selected" : "Not selected")
                        .accessibilityAddTraits(settings.mode == mode ? .isSelected : [])
                    }
                }
                Section {
                    NavigationLink {
                        ScrollView {
                            HealthAccessContent(access: access)
                                .padding()
                                .frame(maxWidth: 640, alignment: .leading)
                                .frame(maxWidth: .infinity)
                        }
                        .navigationTitle("HealthKit access")
                        .toolbar {
                            ToolbarItem(placement: .confirmationAction) {
                                Button("Done", action: onDone).accessibilityIdentifier("close-settings")
                            }
                        }
                    } label: {
                        Text("HealthKit access")
                    }
                    .accessibilityIdentifier("open-health-access")
                }
            }
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done", action: onDone).accessibilityIdentifier("close-settings")
                }
            }
        }
    }
}


struct HealthAccessContent: View {
    @ObservedObject var access: HealthAccessModel

    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
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
            if access.state == .completed {
                Text("If earlier access choices need changing, use Health or system Settings, then return and Refresh in the run library.")
                    .accessibilityIdentifier("access-guidance")
            }
        }
    }
}

import SwiftUI
import UIKit

struct RunLibraryView: View {
    @ObservedObject var access: HealthAccessModel
    @EnvironmentObject private var ingestion: RunIngestionModel
    @EnvironmentObject private var settings: DistanceSettings
    @EnvironmentObject private var selection: RunSelection
    @Environment(\.locale) private var locale
    @Environment(\.timeZone) private var timeZone
    @Environment(\.scenePhase) private var scenePhase
    @State private var showingSettings = false

    var body: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 12) {
                    Text(RunLibraryPresentation.notice(ingestion.state, hasSavedRows: !(ingestion.savedHistory?.runs.isEmpty ?? true)))
                        .accessibilityIdentifier("library-status")
                    if ingestion.state == .loading { ProgressView("Reading running workouts") }
                    if let message = ingestion.localRecoveryMessage {
                        Text(message).accessibilityIdentifier("local-recovery")
                        Button("Retry saved history", action: ingestion.retryLocalLoad)
                            .disabled(ingestion.isTransportActive)
                            .accessibilityIdentifier("retry-saved-history")
                    } else {
                        Text(RunLibraryPresentation.savedHistoryCount(ingestion.savedHistory))
                            .accessibilityIdentifier("saved-history-count")
                        Text(RunLibraryPresentation.savedObservation(ingestion.savedHistory, isPrior: ingestion.isPriorSavedObservation,
                                                                   locale: locale, timeZone: timeZone))
                            .accessibilityIdentifier("saved-provenance")
                    }
                    if ingestion.isTransportActive, ingestion.state != .loading {
                        Text("The previous read is finishing. Wait before starting another read.")
                    }
                    Button(ingestion.state.offersRetry ? "Retry loading runs" : "Refresh runs", action: ingestion.requestRead)
                        .disabled(!ingestion.canRead)
                        .accessibilityIdentifier("refresh-runs")
                        .accessibilityHint(ingestion.isTransportActive ? "A read is already in progress." : (ingestion.localRecoveryMessage != nil ? "Retry saved history first." : "Read currently accessible running workouts without requesting authorization."))
                    if case .sourceSuccess(0, savingFailed: false) = ingestion.state {
                        Text("If earlier access choices need changing, use Health or system Settings, then return and Refresh. You can also return to Fava to deliberately request workout access.")
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 8)
            }
            Section {
                ForEach(RunLibraryPresentation.rows(ingestion.savedHistory?.runs ?? [])) { run in
                    Button {
                        selection.select(run.id)
                        UIAccessibility.post(notification: .announcement, argument: "Run selected.")
                    } label: {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(RunFormatting.start(run.startDate, locale: locale, timeZone: timeZone)).font(.headline)
                            Text("Duration: " + RunFormatting.duration(run.duration))
                            Text(RunFormatting.distance(run.distance, unit: settings.resolvedUnit(locale: locale), locale: locale))
                            Text(RunLibraryPresentation.rowProvenance(run.id, history: ingestion.savedHistory, locale: locale, timeZone: timeZone))
                                .font(.subheadline)
                            if selection.selectedID == run.id {
                                Label("Selected", systemImage: "checkmark").foregroundStyle(.tint)
                            }
                        }
                        .foregroundStyle(.primary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.vertical, 8)
                        .contentShape(Rectangle())
                        .accessibilityElement(children: .combine)
                    }
                    .buttonStyle(.plain)
                    .accessibilityIdentifier("run-" + run.id.uuidString)
                    .accessibilityValue(selection.selectedID == run.id ? "Selected" : "Not selected")
                    .accessibilityAddTraits(selection.selectedID == run.id ? .isSelected : [])
                }
            }
        }
        .listStyle(.insetGrouped)
        .navigationTitle("Run library")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Settings", systemImage: "gearshape") { showingSettings = true }
                    .accessibilityIdentifier("open-settings")
            }
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView(settings: settings, access: access, onDone: { showingSettings = false })
        }
        .onChange(of: ingestion.state) { _, state in
            UIAccessibility.post(notification: .announcement, argument: RunLibraryPresentation.notice(state, hasSavedRows: !(ingestion.savedHistory?.runs.isEmpty ?? true)))
        }
        .onChange(of: ingestion.localRecoveryMessage) { _, message in
            if let message { UIAccessibility.post(notification: .announcement, argument: message) }
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active { ingestion.updateAvailability() }
        }
    }
}

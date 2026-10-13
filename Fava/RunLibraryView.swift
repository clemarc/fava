import SwiftUI
import UIKit

struct RunLibraryView: View {
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
                    Text(RunLibraryPresentation.notice(ingestion.state))
                        .accessibilityIdentifier("library-status")
                    if ingestion.state == .loading { ProgressView("Reading running workouts") }
                    if ingestion.isPreviouslyLoaded, let saved = ingestion.savedSnapshot {
                        Text(saved.runs.isEmpty ? "Previously loaded empty collection." : "Previously loaded runs.")
                            .foregroundStyle(.secondary)
                            .accessibilityIdentifier("saved-provenance")
                    }
                    if let notice = ingestion.cacheNotice { Text(notice).foregroundStyle(.secondary) }
                    Button(ingestion.state == .failed ? "Retry loading runs" : "Refresh runs", action: ingestion.requestRead)
                        .disabled(!ingestion.canRead)
                        .accessibilityIdentifier("refresh-runs")
                        .accessibilityHint(ingestion.state == .loading ? "A read is already in progress." : "Read currently accessible running workouts without requesting authorization.")
                    if ingestion.state == .successfulEmpty {
                        Text("You can return to Fava to deliberately request workout access.").foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 8)
            }
            Section {
                ForEach(RunLibraryPresentation.rows(ingestion.savedSnapshot?.runs ?? [])) { run in
                    Button {
                        selection.select(run.id)
                        UIAccessibility.post(notification: .announcement, argument: "Run selected.")
                    } label: {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(RunFormatting.start(run.startDate, locale: locale, timeZone: timeZone)).font(.headline)
                            Text("Duration: " + RunFormatting.duration(run.duration))
                            Text(RunFormatting.distance(run.distance, unit: settings.resolvedUnit(locale: locale), locale: locale))
                            if selection.selectedID == run.id {
                                Label("Selected", systemImage: "checkmark").foregroundStyle(.tint)
                            }
                        }
                        .foregroundStyle(.primary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.vertical, 8)
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
        .sheet(isPresented: $showingSettings) { DistanceSettingsView(settings: settings) }
        .onChange(of: ingestion.state) { _, state in
            UIAccessibility.post(notification: .announcement, argument: RunLibraryPresentation.notice(state))
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active { ingestion.updateAvailability() }
        }
    }
}

struct DistanceSettingsView: View {
    @ObservedObject var settings: DistanceSettings
    @Environment(\.dismiss) private var dismiss
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
            }
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }.accessibilityIdentifier("close-settings")
                }
            }
        }
    }
}

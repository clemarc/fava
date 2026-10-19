import Foundation

protocol RunSnapshotStoring {
    func load() throws -> RunSnapshot?
    func save(_ snapshot: RunSnapshot) throws
}

protocol RunHistoryStoring {
    func loadHistory() throws -> RetainedRunHistory?
    func saveHistory(_ history: RetainedRunHistory) throws
    func clearHistory() throws
}

struct RunHistoryFileIO {
    let read: (URL) throws -> Data
    let writeAtomically: (Data, URL) throws -> Void

    static let live = RunHistoryFileIO(read: { try Data(contentsOf: $0) }, writeAtomically: { data, fileURL in
        let directory = fileURL.deletingLastPathComponent()
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        var protectedDirectory = directory
        var values = URLResourceValues()
        values.isExcludedFromBackup = true
        try protectedDirectory.setResourceValues(values)
        try data.write(to: fileURL, options: [.atomic, .completeFileProtection])
    })
}

struct FileRunSnapshotStore: RunSnapshotStoring, RunHistoryStoring {
    let fileURL: URL
    private let directory: URL
    private let historyIO: RunHistoryFileIO
    enum SnapshotError: Error { case unsupportedVersion }

    init(directory: URL = URL.applicationSupportDirectory.appendingPathComponent("Fava", isDirectory: true),
         historyIO: RunHistoryFileIO = .live) {
        self.directory = directory
        self.historyIO = historyIO
        fileURL = directory.appendingPathComponent("runs-v1.json")
    }

    func load() throws -> RunSnapshot? {
        guard FileManager.default.fileExists(atPath: fileURL.path) else { return nil }
        let snapshot = try JSONDecoder().decode(RunSnapshot.self, from: Data(contentsOf: fileURL))
        guard snapshot.schemaVersion == 1 else { throw SnapshotError.unsupportedVersion }
        return snapshot
    }

    func save(_ snapshot: RunSnapshot) throws {
        let data = try JSONEncoder().encode(snapshot)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        var protectedDirectory = directory
        var values = URLResourceValues()
        values.isExcludedFromBackup = true
        try protectedDirectory.setResourceValues(values)
        try data.write(to: fileURL, options: [.atomic, .completeFileProtection])
    }

    func loadHistory() throws -> RetainedRunHistory? {
        let data: Data
        do {
            data = try historyIO.read(fileURL)
        } catch {
            let failure = error as NSError
            if failure.domain == NSCocoaErrorDomain && failure.code == NSFileReadNoSuchFileError { return nil }
            throw error
        }
        let decoder = JSONDecoder()
        let version = try decoder.decode(HistoryVersion.self, from: data).schemaVersion
        switch version {
        case 1:
            let legacy = try decoder.decode(LegacyHistory.self, from: data)
            return try RetainedRunHistory.adoptingLegacy(runs: legacy.runs, capturedAt: legacy.capturedAt)
        case 2:
            return try decoder.decode(RetainedRunHistory.self, from: data)
        default:
            throw RunHistoryError.unsupportedVersion(version)
        }
    }

    func saveHistory(_ history: RetainedRunHistory) throws {
        try history.validate()
        let data = try JSONEncoder().encode(history)
        try historyIO.writeAtomically(data, fileURL)
    }

    func clearHistory() throws {
        try saveHistory(RetainedRunHistory(runs: []))
    }
}

private struct HistoryVersion: Decodable {
    let schemaVersion: Int
}

private struct LegacyHistory: Decodable {
    let runs: [RunRecord]
    let capturedAt: Date?
}

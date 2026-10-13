import Foundation

protocol RunSnapshotStoring {
    func load() throws -> RunSnapshot?
    func save(_ snapshot: RunSnapshot) throws
}

struct FileRunSnapshotStore: RunSnapshotStoring {
    let fileURL: URL
    private let directory: URL
    enum SnapshotError: Error { case unsupportedVersion }

    init(directory: URL = URL.applicationSupportDirectory.appendingPathComponent("Fava", isDirectory: true)) {
        self.directory = directory
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
}

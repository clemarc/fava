import Foundation

enum RunHistoryError: Error, Equatable {
    case unsupportedVersion(Int)
    case duplicateRunID(UUID)
    case invalidRecord(UUID)
    case invalidObservationDate
    case orphanProvenance(UUID)
    case orphanReturnedID(UUID)
}

struct SavedReadObservation: Codable, Equatable {
    let observedAt: Date?
    let returnedIDs: Set<UUID>
}

struct RetainedRunHistory: Codable, Equatable {
    let schemaVersion: Int
    let runs: [RunRecord]
    // Missing keys mean unknown times, including genuinely untimed legacy rows.
    let lastObservedAtByID: [UUID: Date]
    let latestSavedObservation: SavedReadObservation?

    var runsByID: [UUID: RunRecord] {
        Dictionary(uniqueKeysWithValues: runs.map { ($0.id, $0) })
    }

    init(runs: [RunRecord], lastObservedAtByID: [UUID: Date] = [:],
         latestSavedObservation: SavedReadObservation? = nil) throws {
        schemaVersion = 2
        self.runs = runs
        self.lastObservedAtByID = lastObservedAtByID
        self.latestSavedObservation = latestSavedObservation
        try validate()
    }

    func validate() throws {
        guard schemaVersion == 2 else { throw RunHistoryError.unsupportedVersion(schemaVersion) }
        var identities = Set<UUID>()
        for run in runs {
            try run.validateForHistory()
            guard identities.insert(run.id).inserted else { throw RunHistoryError.duplicateRunID(run.id) }
        }
        for (id, date) in lastObservedAtByID {
            guard identities.contains(id) else { throw RunHistoryError.orphanProvenance(id) }
            guard date.timeIntervalSinceReferenceDate.isFinite else { throw RunHistoryError.invalidObservationDate }
        }
        if let observation = latestSavedObservation {
            if let date = observation.observedAt, !date.timeIntervalSinceReferenceDate.isFinite {
                throw RunHistoryError.invalidObservationDate
            }
            for id in observation.returnedIDs where !identities.contains(id) {
                throw RunHistoryError.orphanReturnedID(id)
            }
        }
    }

    static func adoptingLegacy(runs: [RunRecord], capturedAt: Date?) throws -> RetainedRunHistory {
        if let capturedAt, !capturedAt.timeIntervalSinceReferenceDate.isFinite {
            throw RunHistoryError.invalidObservationDate
        }
        var identities = Set<UUID>()
        var unique: [RunRecord] = []
        for run in runs {
            // Even a later duplicate must be valid before it can be discarded.
            try run.validateForHistory()
            if identities.insert(run.id).inserted { unique.append(run) }
        }
        var times: [UUID: Date] = [:]
        if let capturedAt {
            for id in identities { times[id] = capturedAt }
        }
        return try RetainedRunHistory(runs: unique, lastObservedAtByID: times,
                                      latestSavedObservation: SavedReadObservation(
                                        observedAt: capturedAt, returnedIDs: identities))
    }

    private enum CodingKeys: String, CodingKey {
        case schemaVersion, runs, lastObservedAtByID, latestSavedObservation
    }

    init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        schemaVersion = try values.decode(Int.self, forKey: .schemaVersion)
        guard schemaVersion == 2 else { throw RunHistoryError.unsupportedVersion(schemaVersion) }
        runs = try values.decode([RunRecord].self, forKey: .runs)
        if values.contains(.lastObservedAtByID) {
            lastObservedAtByID = try values.decode([UUID: Date].self, forKey: .lastObservedAtByID)
        } else {
            lastObservedAtByID = [:]
        }
        latestSavedObservation = try values.decodeIfPresent(SavedReadObservation.self, forKey: .latestSavedObservation)
        try validate()
    }

    func encode(to encoder: Encoder) throws {
        try validate()
        var values = encoder.container(keyedBy: CodingKeys.self)
        try values.encode(schemaVersion, forKey: .schemaVersion)
        try values.encode(runs, forKey: .runs)
        if !lastObservedAtByID.isEmpty {
            try values.encode(lastObservedAtByID, forKey: .lastObservedAtByID)
        }
        try values.encodeIfPresent(latestSavedObservation, forKey: .latestSavedObservation)
    }
}

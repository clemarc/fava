import Foundation

enum DistanceUnit: String, Codable { case metres, kilometres, miles }

struct WorkoutDistance: Codable, Equatable {
    let value: Double
    let unit: DistanceUnit

    var metres: Double {
        switch unit {
        case .metres: return value
        case .kilometres: return value * 1000
        case .miles: return value * 1609.344
        }
    }
}

struct RunRecord: Identifiable, Codable, Equatable {
    let id: UUID
    let startDate: Date
    let duration: TimeInterval
    let distance: WorkoutDistance?

    func validateForHistory() throws {
        guard startDate.timeIntervalSinceReferenceDate.isFinite, duration.isFinite, duration >= 0 else {
            throw RunHistoryError.invalidRecord(id)
        }
        if let distance, !distance.value.isFinite || distance.value < 0 {
            throw RunHistoryError.invalidRecord(id)
        }
    }
}

struct RunSnapshot: Codable, Equatable {
    let schemaVersion: Int
    let runs: [RunRecord]
    let capturedAt: Date
    init(runs: [RunRecord], capturedAt: Date = Date()) {
        schemaVersion = 1
        self.runs = runs
        self.capturedAt = capturedAt
    }
}

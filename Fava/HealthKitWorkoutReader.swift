import HealthKit

@MainActor
protocol WorkoutReading {
    var isAvailable: Bool { get }
    func read(completion: @escaping (Result<[RunRecord], Error>) -> Void)
}

protocol WorkoutQueryStore {
    var isAvailable: Bool { get }
    func query(sampleType: HKSampleType, predicate: NSPredicate, limit: Int, completion: @escaping ([HKSample]?, Error?) -> Void)
}

struct SystemWorkoutQueryStore: WorkoutQueryStore {
    private let store = HKHealthStore()
    var isAvailable: Bool { HKHealthStore.isHealthDataAvailable() }
    func query(sampleType: HKSampleType, predicate: NSPredicate, limit: Int, completion: @escaping ([HKSample]?, Error?) -> Void) {
        let query = HKSampleQuery(sampleType: sampleType, predicate: predicate, limit: limit, sortDescriptors: nil) { _, samples, error in
            completion(samples, error)
        }
        store.execute(query)
    }
}

@MainActor
final class HealthKitWorkoutReader: WorkoutReading {
    private let store: WorkoutQueryStore
    init(store: WorkoutQueryStore = SystemWorkoutQueryStore()) { self.store = store }
    var isAvailable: Bool { store.isAvailable }
    enum ReadError: Error { case malformedResponse }

    func read(completion: @escaping (Result<[RunRecord], Error>) -> Void) {
        store.query(sampleType: HKObjectType.workoutType(), predicate: HKQuery.predicateForWorkouts(with: .running), limit: HKObjectQueryNoLimit) { samples, error in
            let result: Result<[RunRecord], Error>
            if let error { result = .failure(error) }
            else if let workouts = samples as? [HKWorkout] {
                let runs = workouts.filter { $0.workoutActivityType == .running }.map { workout in
                    RunRecord(id: workout.uuid, startDate: workout.startDate, duration: workout.duration,
                              distance: workout.totalDistance.map { WorkoutDistance(value: $0.doubleValue(for: .meter()), unit: .metres) })
                }
                result = .success(runs)
            } else { result = .failure(ReadError.malformedResponse) }
            Task { @MainActor in completion(result) }
        }
    }
}

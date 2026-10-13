import Combine
import Foundation

enum DistanceMode: String, CaseIterable { case device, kilometres, miles
    var title: String {
        switch self { case .device: return "Device"; case .kilometres: return "Kilometres"; case .miles: return "Miles" }
    }
}

enum DistanceDisplayUnit {
    case kilometres, miles
    var symbol: String { self == .kilometres ? "km" : "mi" }
    var metresPerUnit: Double { self == .kilometres ? 1000 : 1609.344 }
}

@MainActor
final class DistanceSettings: ObservableObject {
    @Published var mode: DistanceMode = .device {
        didSet { defaults.set(mode.rawValue, forKey: "distance-mode") }
    }
    private let defaults: UserDefaults
    private let deviceUnit: (Locale) -> DistanceDisplayUnit

    init(defaults: UserDefaults = .standard, deviceUnit: @escaping (Locale) -> DistanceDisplayUnit = { $0.measurementSystem == .metric ? .kilometres : .miles }) {
        self.defaults = defaults
        self.deviceUnit = deviceUnit
        mode = defaults.string(forKey: "distance-mode").flatMap(DistanceMode.init(rawValue:)) ?? .device
    }

    func resolvedUnit(locale: Locale) -> DistanceDisplayUnit {
        switch mode {
        case .device: return deviceUnit(locale)
        case .kilometres: return .kilometres
        case .miles: return .miles
        }
    }
}

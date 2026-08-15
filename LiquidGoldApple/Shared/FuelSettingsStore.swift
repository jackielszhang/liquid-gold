import Foundation
import Observation

/// Persists region, fuel, and tank size in the app-group defaults.
///
/// The widget cannot share in-memory state with the app, so this store is the
/// only place the two targets agree on "what the user selected".
@Observable
public final class FuelSettingsStore {
    public private(set) var selection: FuelSelection?
    private let defaults: UserDefaults

    public init(defaults: UserDefaults? = UserDefaults(suiteName: AppConfig.appGroupID)) {
        self.defaults = defaults ?? .standard
        self.selection = Self.loadSelection(from: self.defaults)
    }

    public var hasCompletedOnboarding: Bool {
        selection != nil
    }

    public func save(region: RegionType, fuelType: FuelType) {
        save(region: region, fuelType: fuelType, tankSizeLitres: selection?.tankSizeLitres ?? AppConfig.defaultTankSizeLitres)
    }

    public func save(region: RegionType, fuelType: FuelType, tankSizeLitres: Int) {
        let value = FuelSelection(region: region, fuelType: fuelType, tankSizeLitres: tankSizeLitres)
        defaults.set(region.rawValue, forKey: Keys.region)
        defaults.set(fuelType.rawValue, forKey: Keys.fuel)
        defaults.set(tankSizeLitres, forKey: Keys.tankSize)
        selection = value
    }

    public func update(selection: FuelSelection) {
        save(region: selection.region, fuelType: selection.fuelType, tankSizeLitres: selection.tankSizeLitres)
    }

    public static func loadSelection(from defaults: UserDefaults? = UserDefaults(suiteName: AppConfig.appGroupID)) -> FuelSelection? {
        guard
            let regionRaw = defaults?.string(forKey: Keys.region),
            let fuelRaw = defaults?.string(forKey: Keys.fuel),
            let region = RegionType(rawValue: regionRaw),
            let fuelType = FuelType(rawValue: fuelRaw)
        else {
            return nil
        }
        let tankSize = defaults?.object(forKey: Keys.tankSize) as? Int ?? AppConfig.defaultTankSizeLitres
        return FuelSelection(region: region, fuelType: fuelType, tankSizeLitres: tankSize)
    }

    private enum Keys {
        static let region = "selected-region"
        static let fuel = "selected-fuel"
        static let tankSize = "selected-tank-size"
    }
}

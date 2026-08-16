import Foundation

/// Models that match public/v1/latest.json (and the compat fuel-data.json copy).
///
/// Prices stay in integer cents so the Python pipeline and Swift decoder never
/// disagree about rounding. Display as rands happens in PriceFormatter, not here.

public enum RegionType: String, Codable, CaseIterable, Identifiable {
    case coastal
    case inland

    public var id: String { rawValue }

    public var title: String {
        switch self {
        case .coastal: "Coastal"
        case .inland: "Inland"
        }
    }

    public var priceKey: String {
        switch self {
        case .coastal: "coastal_cents_per_litre"
        case .inland: "inland_cents_per_litre"
        }
    }
}

public enum FuelType: String, Codable, CaseIterable, Identifiable {
    case petrol95
    case diesel50ppm

    public var id: String { rawValue }

    public var title: String {
        switch self {
        case .petrol95: "Petrol 95"
        case .diesel50ppm: "Diesel 50ppm"
        }
    }

    public var payloadKey: String {
        switch self {
        case .petrol95: "petrol_95"
        case .diesel50ppm: "diesel_50ppm"
        }
    }

    public var changeKey: String {
        "\(payloadKey)_estimated_change_cents"
    }
}

public struct FuelSelection: Codable, Equatable {
    public var region: RegionType
    public var fuelType: FuelType
    public var tankSizeLitres: Int

    public init(region: RegionType, fuelType: FuelType, tankSizeLitres: Int = AppConfig.defaultTankSizeLitres) {
        self.region = region
        self.fuelType = fuelType
        self.tankSizeLitres = tankSizeLitres
    }
}

public struct FuelPayload: Codable {
    public var schemaVersion: Int
    public var lastUpdated: String
    public var status: String
    public var manualOverride: Bool
    public var nextAdjustmentDate: String
    public var sourceStatus: SourceStatus
    public var prices: [String: FuelPriceSet]
    public var forecast: ForecastPayload
    public var recommendation: [String: FuelRecommendation]
    public var sources: SourceLinks

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case lastUpdated = "last_updated"
        case status
        case manualOverride = "manual_override"
        case nextAdjustmentDate = "next_adjustment_date"
        case sourceStatus = "source_status"
        case prices
        case forecast
        case recommendation
        case sources
    }
}

public struct SourceStatus: Codable {
    public var officialPrices: String
    public var forecast: String

    enum CodingKeys: String, CodingKey {
        case officialPrices = "official_prices"
        case forecast
    }
}

public struct SourceLinks: Codable {
    public var officialPricesURL: String
    public var forecastURL: String
    public var validationURL: String

    enum CodingKeys: String, CodingKey {
        case officialPricesURL = "official_prices_url"
        case forecastURL = "forecast_url"
        case validationURL = "validation_url"
    }
}

public struct FuelPriceSet: Codable {
    public var coastalCentsPerLitre: Int
    public var inlandCentsPerLitre: Int
    public var effectiveDate: String

    enum CodingKeys: String, CodingKey {
        case coastalCentsPerLitre = "coastal_cents_per_litre"
        case inlandCentsPerLitre = "inland_cents_per_litre"
        case effectiveDate = "effective_date"
    }

    public func currentPrice(for region: RegionType) -> Int {
        switch region {
        case .coastal: coastalCentsPerLitre
        case .inland: inlandCentsPerLitre
        }
    }
}

public struct ForecastPayload: Codable {
    public var asOfDate: String?
    public var petrol95EstimatedChangeCents: Int?
    public var diesel50ppmEstimatedChangeCents: Int?
    public var direction: String
    public var diesel50ppmDirection: String
    public var confidence: String
    public var sourceURL: String?

    enum CodingKeys: String, CodingKey {
        case asOfDate = "as_of_date"
        case petrol95EstimatedChangeCents = "petrol_95_estimated_change_cents"
        case diesel50ppmEstimatedChangeCents = "diesel_50ppm_estimated_change_cents"
        case direction
        case diesel50ppmDirection = "diesel_50ppm_direction"
        case confidence
        case sourceURL = "source_url"
    }

    public func change(for fuelType: FuelType) -> Int? {
        switch fuelType {
        case .petrol95: petrol95EstimatedChangeCents
        case .diesel50ppm: diesel50ppmEstimatedChangeCents
        }
    }
}

public struct RecommendedPriceSet: Codable {
    public var coastalCentsPerLitre: Int
    public var inlandCentsPerLitre: Int

    enum CodingKeys: String, CodingKey {
        case coastalCentsPerLitre = "coastal_cents_per_litre"
        case inlandCentsPerLitre = "inland_cents_per_litre"
    }

    public func price(for region: RegionType) -> Int {
        switch region {
        case .coastal: coastalCentsPerLitre
        case .inland: inlandCentsPerLitre
        }
    }
}

public struct FuelRecommendation: Codable {
    public var action: String
    public var headline: String
    public var body: String
    public var reason: String
    public var bestFillUpDate: String?
    public var nextPriceCentsPerLitre: RecommendedPriceSet?
    public var changeCentsPerLitre: Int?

    enum CodingKeys: String, CodingKey {
        case action
        case headline
        case body
        case reason
        case bestFillUpDate = "best_fill_up_date"
        case nextPriceCentsPerLitre = "next_price_cents_per_litre"
        case changeCentsPerLitre = "change_cents_per_litre"
    }
}

public enum FuelDataSource: String {
    case remote
    case cache
    case bundled
}

public struct LoadedFuelPayload {
    public var payload: FuelPayload
    public var source: FuelDataSource

    public init(payload: FuelPayload, source: FuelDataSource) {
        self.payload = payload
        self.source = source
    }
}

/// Values the dashboard and widget can render without knowing JSON keys.
public struct FuelSnapshot: Equatable {
    public var selection: FuelSelection
    public var currentPrice: Int
    public var nextPrice: Int?
    public var change: Int?
    public var estimatedTankImpact: Int?
    public var nextAdjustmentDate: Date?
    public var bestFillUpDate: Date?
    public var recommendationText: String
    public var recommendationBody: String
    public var confidenceText: String
    public var statusText: String
    public var isStale: Bool
    public var isFallback: Bool
}

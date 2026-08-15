import Foundation

public enum FuelSnapshotBuilder {
    private static let staleWindow: TimeInterval = 48 * 60 * 60

    public static func build(
        loadedPayload: LoadedFuelPayload,
        selection: FuelSelection,
        now: Date = .now
    ) -> FuelSnapshot? {
        guard
            let priceSet = loadedPayload.payload.prices[selection.fuelType.payloadKey],
            let recommendation = loadedPayload.payload.recommendation[selection.fuelType.payloadKey]
        else {
            return nil
        }

        let currentPrice = priceSet.currentPrice(for: selection.region)
        let nextPrice = recommendation.nextPriceCentsPerLitre?.price(for: selection.region)
        let updatedDate = isoDateTime(loadedPayload.payload.lastUpdated)
        let bestFillUpDate = isoDate(recommendation.bestFillUpDate)
        let nextAdjustmentDate = isoDate(loadedPayload.payload.nextAdjustmentDate)
        let isStale = updatedDate.map { now.timeIntervalSince($0) > staleWindow } ?? true
        let isFallback = loadedPayload.source != .remote
        let estimatedTankImpact = recommendation.changeCentsPerLitre.map { ($0 * selection.tankSizeLitres) / 100 }

        var statusParts: [String] = []
        if isFallback {
            statusParts.append(loadedPayload.source == .cache ? "Offline cache" : "Bundled sample")
        }
        if isStale {
            statusParts.append("Stale")
        }
        if statusParts.isEmpty {
            statusParts.append("Live data")
        }

        return FuelSnapshot(
            selection: selection,
            currentPrice: currentPrice,
            nextPrice: nextPrice,
            change: recommendation.changeCentsPerLitre,
            estimatedTankImpact: estimatedTankImpact,
            nextAdjustmentDate: nextAdjustmentDate,
            bestFillUpDate: bestFillUpDate,
            recommendationText: recommendation.headline,
            recommendationBody: recommendation.body,
            confidenceText: confidenceText(
                forecast: loadedPayload.payload.forecast,
                isStale: isStale
            ),
            statusText: statusParts.joined(separator: " • "),
            isStale: isStale,
            isFallback: isFallback
        )
    }

    private static func confidenceText(forecast: ForecastPayload, isStale: Bool) -> String {
        if isStale { return "Forecast stale" }
        switch forecast.confidence {
        case "high": return "Forecast confidence: high"
        case "medium": return "Forecast confidence: medium"
        case "low": return "Forecast confidence: low"
        default: return "Forecast confidence: unknown"
        }
    }

    private static func isoDate(_ value: String?) -> Date? {
        guard let value else { return nil }
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withFullDate]
        return formatter.date(from: value)
    }

    private static func isoDateTime(_ value: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: value)
    }
}

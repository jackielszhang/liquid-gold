import Foundation
import XCTest
@testable import LiquidGoldShared

final class FuelSharedTests: XCTestCase {
    func testDecodesSamplePayload() throws {
        let payload = try samplePayload()
        XCTAssertEqual(payload.prices["diesel_50ppm"]?.inlandCentsPerLitre, 2410)
        XCTAssertEqual(payload.recommendation["petrol_95"]?.bestFillUpDate, "2026-08-05")
    }

    func testBuildsCoastalPetrolSnapshot() throws {
        let payload = try samplePayload()
        let loaded = LoadedFuelPayload(payload: payload, source: .remote)
        let snapshot = FuelSnapshotBuilder.build(
            loadedPayload: loaded,
            selection: FuelSelection(region: .coastal, fuelType: .petrol95, tankSizeLitres: 50),
            now: timestamp("2026-07-08T22:00:00Z")
        )
        XCTAssertEqual(snapshot?.currentPrice, 2523)
        XCTAssertEqual(snapshot?.nextPrice, 2443)
        XCTAssertEqual(snapshot?.estimatedTankImpact, -40)
        XCTAssertEqual(snapshot?.confidenceText, "Forecast confidence: high")
        XCTAssertEqual(snapshot?.isStale, false)
    }

    func testMarksStaleFallbackSnapshot() throws {
        var payload = try samplePayload()
        payload.lastUpdated = "2026-07-01T00:00:00Z"
        let loaded = LoadedFuelPayload(payload: payload, source: .cache)
        let snapshot = FuelSnapshotBuilder.build(
            loadedPayload: loaded,
            selection: FuelSelection(region: .inland, fuelType: .diesel50ppm),
            now: timestamp("2026-07-08T22:00:00Z")
        )
        XCTAssertEqual(snapshot?.isStale, true)
        XCTAssertEqual(snapshot?.isFallback, true)
    }

    func testSettingsRoundTrip() throws {
        let suiteName = "test.liquidgold.\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: suiteName)!
        defaults.removePersistentDomain(forName: suiteName)
        let store = FuelSettingsStore(defaults: defaults)
        store.save(region: .inland, fuelType: .diesel50ppm)
        XCTAssertEqual(store.selection, FuelSelection(region: .inland, fuelType: .diesel50ppm))
        XCTAssertEqual(FuelSettingsStore.loadSelection(from: defaults), FuelSelection(region: .inland, fuelType: .diesel50ppm))
    }

    func testCacheRoundTrip() throws {
        let tempURL = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathComponent("fuel-data-cache.json")
        let service = FuelDataService(bundle: .module, cacheFileURL: tempURL)
        let payload = try samplePayload()
        try service.saveCachedPayload(payload)
        let cached = try service.loadCachedPayload()
        XCTAssertEqual(cached.forecast.diesel50ppmEstimatedChangeCents, 55)
    }

    private func samplePayload() throws -> FuelPayload {
        let url = Bundle.module.url(forResource: "fuel-data", withExtension: "json")!
        let data = try Data(contentsOf: url)
        return try JSONDecoder().decode(FuelPayload.self, from: data)
    }

    private func timestamp(_ value: String) -> Date {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: value)!
    }
}

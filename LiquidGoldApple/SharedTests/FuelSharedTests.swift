import Foundation
import XCTest
@testable import LiquidGoldShared

/// Shared-library contract tests.
///
/// These decode the published JSON shape and check that a snapshot still
/// reports tank impact in rands, not leftover cents.
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
        XCTAssertEqual(snapshot?.recommendationAction, "wait")
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

    func testNonOKRemotePayloadFallsBackWithoutReplacingCache() async throws {
        var remotePayload = try samplePayload()
        remotePayload.status = "error"
        StubURLProtocol.responseData = try JSONEncoder().encode(remotePayload)
        defer { StubURLProtocol.responseData = nil }

        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [StubURLProtocol.self]
        let session = URLSession(configuration: configuration)
        defer { session.invalidateAndCancel() }

        let cacheURL = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathComponent("fuel-data-cache.json")
        let service = FuelDataService(
            remoteURL: URL(string: "https://example.test/latest.json")!,
            session: session,
            bundle: .module,
            cacheFileURL: cacheURL
        )
        try service.saveCachedPayload(samplePayload())

        let loaded = try await service.loadPayload()

        XCTAssertEqual(loaded.source, .cache)
        XCTAssertEqual(loaded.payload.status, "ok")
        XCTAssertEqual(try service.loadCachedPayload().status, "ok")
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

private final class StubURLProtocol: URLProtocol {
    nonisolated(unsafe) static var responseData: Data?

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        guard
            let url = request.url,
            let data = Self.responseData,
            let response = HTTPURLResponse(url: url, statusCode: 200, httpVersion: nil, headerFields: nil)
        else {
            client?.urlProtocol(self, didFailWithError: URLError(.badServerResponse))
            return
        }
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: data)
        client?.urlProtocolDidFinishLoading(self)
    }

    override func stopLoading() {}
}

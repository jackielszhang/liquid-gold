import Foundation

public struct FuelDataService {
    public var remoteURL: URL
    public var session: URLSession
    public var bundle: Bundle
    public var appGroupID: String
    public var cacheFileURL: URL?

    public init(
        remoteURL: URL = AppConfig.remoteDataURL,
        session: URLSession = .shared,
        bundle: Bundle = .main,
        appGroupID: String = AppConfig.appGroupID,
        cacheFileURL: URL? = nil
    ) {
        self.remoteURL = remoteURL
        self.session = session
        self.bundle = bundle
        self.appGroupID = appGroupID
        self.cacheFileURL = cacheFileURL
    }

    public func loadPayload() async throws -> LoadedFuelPayload {
        if let remotePayload = try? await fetchRemotePayload() {
            try? saveCachedPayload(remotePayload)
            return LoadedFuelPayload(payload: remotePayload, source: .remote)
        }
        if let cachedPayload = try? loadCachedPayload() {
            return LoadedFuelPayload(payload: cachedPayload, source: .cache)
        }
        return LoadedFuelPayload(payload: try loadBundledPayload(), source: .bundled)
    }

    public func fetchRemotePayload() async throws -> FuelPayload {
        let (data, response) = try await session.data(from: remoteURL)
        guard let http = response as? HTTPURLResponse, 200..<300 ~= http.statusCode else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(FuelPayload.self, from: data)
    }

    public func loadCachedPayload() throws -> FuelPayload {
        let data = try Data(contentsOf: cacheURL())
        return try JSONDecoder().decode(FuelPayload.self, from: data)
    }

    public func saveCachedPayload(_ payload: FuelPayload) throws {
        let url = cacheURL()
        try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        let data = try JSONEncoder().encode(payload)
        try data.write(to: url, options: [.atomic])
    }

    public func loadBundledPayload() throws -> FuelPayload {
        guard let url = bundle.url(forResource: "fuel-data.sample", withExtension: "json") else {
            throw CocoaError(.fileNoSuchFile)
        }
        let data = try Data(contentsOf: url)
        return try JSONDecoder().decode(FuelPayload.self, from: data)
    }

    public func cacheURL() -> URL {
        if let cacheFileURL {
            return cacheFileURL
        }
        if let groupURL = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupID) {
            return groupURL.appendingPathComponent(AppConfig.cacheFilename)
        }
        let fallback = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        return fallback.appendingPathComponent(AppConfig.cacheFilename)
    }
}

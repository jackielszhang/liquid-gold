import Foundation

/// Shared constants for the app, widget, and Swift package tests.
///
/// `remoteDataURL` points at the public v1 latest snapshot on GitHub Pages.
public enum AppConfig {
    public static let appGroupID = "group.com.jackiez.liquidgold"
    public static let remoteDataURL = URL(string: "https://jackielszhang.github.io/liquid-gold/v1/latest.json")!
    public static let cacheFilename = "fuel-data-cache.json"
    public static let defaultTankSizeLitres = 50
}

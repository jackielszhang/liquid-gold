import Foundation

public enum AppConfig {
    public static let appGroupID = "group.com.jackiez.liquidgold"
    public static let remoteDataURL = URL(string: "https://raw.githubusercontent.com/jackielszhang/liquid-gold/main/public/fuel-data.json")!
    public static let cacheFilename = "fuel-data-cache.json"
    public static let defaultTankSizeLitres = 50
}

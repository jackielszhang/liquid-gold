// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "LiquidGoldShared",
    platforms: [
        .iOS(.v17),
        .macOS(.v14),
    ],
    products: [
        .library(
            name: "LiquidGoldShared",
            targets: ["LiquidGoldShared"]
        ),
    ],
    targets: [
        .target(
            name: "LiquidGoldShared",
            path: "LiquidGoldApple/Shared",
            resources: [
                .process("Resources/fuel-data.sample.json"),
            ]
        ),
        .testTarget(
            name: "LiquidGoldSharedTests",
            dependencies: ["LiquidGoldShared"],
            path: "LiquidGoldApple/SharedTests",
            resources: [
                .process("Fixtures/fuel-data.json"),
            ]
        ),
    ]
)

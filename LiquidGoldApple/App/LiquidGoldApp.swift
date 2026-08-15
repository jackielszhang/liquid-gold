import SwiftUI

/// Hosts the one shared settings store so the dashboard and settings sheet
/// always read the same region / fuel / tank size.
@main
struct LiquidGoldApp: App {
    @State private var settingsStore = FuelSettingsStore()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(settingsStore)
        }
    }
}

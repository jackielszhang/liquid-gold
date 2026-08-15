import SwiftUI

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

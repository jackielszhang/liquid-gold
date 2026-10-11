# Liquid Gold UI prototype

Run `npm install` and `npm run dev` from this folder, then open `http://127.0.0.1:4179/prototype/`. The phone frame is fixed to a 390 × 844 point viewport; DialKit sits outside the app mask. Its page selector opens Setup, Dashboard, or the Configuration sheet, and its state selector previews live, stale, loading, and unavailable data. `?setup` reopens onboarding.

The prototype fetches the public v1 API used by `AppConfig.remoteDataURL` and saves the selected region, fuel, and tank size in browser storage. DialKit layout and theme values map to SwiftUI spacing, typography, and `LiquidGoldTheme` tokens. Route values map to `SetupView`, the dashboard, and `SettingsView`; data states map to loading, stale/live, and unavailable states. Keep DialKit and the phone mask out of the SwiftUI port.

The browser model covers setup, dashboard, refresh, and a save-or-dismiss configuration sheet. Check the sheet’s native presentation and dismissal, safe-area behavior, VoiceOver order, Dynamic Type, and haptics in SwiftUI before treating the browser version as final.

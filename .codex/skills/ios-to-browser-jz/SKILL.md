---
name: ios-to-browser-jz
description: Builds an iOS app for Simulator, launches it, and starts a serve-sim localhost mirror. Use when the user asks to boot, relaunch, mirror, or reopen an iOS app in the Codex in-app browser or simulator.
---

# iOS To Browser JZ

## Quick start

Run:

```bash
./.codex/skills/ios-to-browser-jz/scripts/run-liquid-gold-browser.sh
```

This builds the default app, boots the default simulator, launches it, and starts `serve-sim` on `http://localhost:3200/`.

## Generic usage

```bash
./.codex/skills/ios-to-browser-jz/scripts/run-liquid-gold-browser.sh \
  --project /absolute/path/App.xcodeproj \
  --scheme AppScheme
```

Optional overrides:

- `--workspace /absolute/path/App.xcworkspace`
- `--bundle-id com.example.App`
- `--sim-name "iPhone 17"`
- `--sim-id <udid>`
- `--derived-data /private/tmp/some-build-dir`

## Defaults

- Project: `LiquidGold.xcodeproj`
- Simulator: `iPhone 17`
- UDID: `76D8853C-6E70-4C8D-8E1D-C11D1E9AA2B4`
- Scheme: `LiquidGold`
- Bundle ID: auto-detected, defaults to `com.jackiez.LiquidGold` for this repo
- Derived data: `/private/tmp/liquid-gold-sim`

## Notes

- Keep the terminal running while the browser mirror is in use.
- If `localhost:3200` is up but the frame is stale, rerun the script.
- If `--bundle-id` is omitted, the script reads it from the built app bundle.
- If you only need the app and not the browser mirror, stop after the `xcrun simctl launch ...` step in the script.

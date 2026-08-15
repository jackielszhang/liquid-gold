#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../" && pwd)"
SIM_NAME="${SIM_NAME:-iPhone 17}"
SIM_UDID="${SIM_UDID:-76D8853C-6E70-4C8D-8E1D-C11D1E9AA2B4}"
SCHEME="${SCHEME:-LiquidGold}"
PROJECT="${PROJECT:-$ROOT/LiquidGold.xcodeproj}"
WORKSPACE="${WORKSPACE:-}"
BUNDLE_ID="${BUNDLE_ID:-}"
DERIVED_DATA="${DERIVED_DATA:-/private/tmp/liquid-gold-sim}"

usage() {
  cat <<'EOF'
Usage:
  run-liquid-gold-browser.sh [options]

Options:
  --project PATH        Path to .xcodeproj
  --workspace PATH      Path to .xcworkspace
  --scheme NAME         Xcode scheme
  --bundle-id ID        App bundle identifier
  --sim-name NAME       Simulator name
  --sim-id UDID         Simulator UDID
  --derived-data PATH   DerivedData directory
  --help                Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      PROJECT="$2"
      shift 2
      ;;
    --workspace)
      WORKSPACE="$2"
      shift 2
      ;;
    --scheme)
      SCHEME="$2"
      shift 2
      ;;
    --bundle-id)
      BUNDLE_ID="$2"
      shift 2
      ;;
    --sim-name)
      SIM_NAME="$2"
      shift 2
      ;;
    --sim-id)
      SIM_UDID="$2"
      shift 2
      ;;
    --derived-data)
      DERIVED_DATA="$2"
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -n "$PROJECT" && -n "$WORKSPACE" ]]; then
  echo "Pass either --project or --workspace, not both." >&2
  exit 1
fi

if [[ -z "$WORKSPACE" && -z "$PROJECT" ]]; then
  echo "Missing project or workspace." >&2
  exit 1
fi

if [[ -z "$SIM_UDID" && -n "$SIM_NAME" ]]; then
  SIM_UDID="$(xcrun simctl list devices available | sed -n "s/.*$SIM_NAME (\\([A-F0-9-]*\\)).*/\\1/p" | head -n 1)"
fi

if [[ -z "$SIM_UDID" ]]; then
  echo "Could not resolve simulator UDID." >&2
  exit 1
fi

if [[ -n "$WORKSPACE" ]]; then
  BUILD_TARGET=(-workspace "$WORKSPACE")
else
  BUILD_TARGET=(-project "$PROJECT")
fi

APP_PATH="$DERIVED_DATA/Build/Products/Debug-iphonesimulator/$SCHEME.app"

echo "Building $SCHEME for $SIM_NAME..."
xcodebuild "${BUILD_TARGET[@]}" \
  -scheme "$SCHEME" \
  -destination "id=$SIM_UDID" \
  -derivedDataPath "$DERIVED_DATA" \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO \
  build

echo "Booting simulator if needed..."
xcrun simctl boot "$SIM_UDID" >/dev/null 2>&1 || true
xcrun simctl bootstatus "$SIM_UDID" -b

echo "Installing app..."
xcrun simctl install "$SIM_UDID" "$APP_PATH" >/dev/null 2>&1 || true

if [[ -z "$BUNDLE_ID" ]]; then
  BUNDLE_ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP_PATH/Info.plist" 2>/dev/null || true)"
fi

if [[ -z "$BUNDLE_ID" ]]; then
  echo "Could not determine bundle ID. Pass --bundle-id explicitly." >&2
  exit 1
fi

echo "Launching app..."
xcrun simctl launch "$SIM_UDID" "$BUNDLE_ID" || true

cleanup_serve_sim() {
  npx --yes serve-sim@latest --kill "$SIM_UDID" >/dev/null 2>&1 || true
}

trap cleanup_serve_sim EXIT INT TERM HUP
cleanup_serve_sim

echo "Starting serve-sim mirror on http://localhost:3200 ..."
npx --yes serve-sim@latest "$SIM_UDID"

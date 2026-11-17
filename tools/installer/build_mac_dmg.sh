#!/usr/bin/env bash
set -euo pipefail

ICON_PNG_256="labelme/icons/icon-256.png"
ICON_PNG_512="labelme/icons/icon-macos-512.png"
ICON_ICNS="labelme/icons/icon.icns"
APP_PATH="dist/Labelme.app"
DMG_PATH="dist/Labelme-macOS-arm64.dmg"

generate_icns() {
  echo "Generating macOS .icns icon..."
  local iconset_dir="build/Labelme.iconset"
  rm -rf "$iconset_dir"
  mkdir -p "$iconset_dir"

  sips -z 16 16     "$ICON_PNG_256" --out "$iconset_dir/icon_16x16.png" >/dev/null
  sips -z 32 32     "$ICON_PNG_256" --out "$iconset_dir/icon_16x16@2x.png" >/dev/null
  sips -z 32 32     "$ICON_PNG_256" --out "$iconset_dir/icon_32x32.png" >/dev/null
  sips -z 64 64     "$ICON_PNG_256" --out "$iconset_dir/icon_32x32@2x.png" >/dev/null
  sips -z 128 128   "$ICON_PNG_256" --out "$iconset_dir/icon_128x128.png" >/dev/null
  sips -z 256 256   "$ICON_PNG_256" --out "$iconset_dir/icon_128x128@2x.png" >/dev/null
  sips -z 256 256   "$ICON_PNG_256" --out "$iconset_dir/icon_256x256.png" >/dev/null
  sips -z 512 512   "$ICON_PNG_512" --out "$iconset_dir/icon_256x256@2x.png" >/dev/null
  sips -z 512 512   "$ICON_PNG_512" --out "$iconset_dir/icon_512x512.png" >/dev/null

  iconutil -c icns "$iconset_dir" -o "$ICON_ICNS"
  rm -rf "$iconset_dir"
  echo "Created $ICON_ICNS"
}

if [[ "${1:-}" == "--icon-only" ]]; then
  generate_icns
  exit 0
fi

if [[ ! -d "$APP_PATH" ]]; then
  echo "Error: $APP_PATH not found. Run PyInstaller first." >&2
  exit 1
fi

rm -f "$DMG_PATH"

echo "Packaging $APP_PATH into $DMG_PATH..."
if command -v create-dmg >/dev/null 2>&1; then
  create-dmg \
    --volname "Labelme" \
    --volicon "$ICON_ICNS" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "Labelme.app" 175 190 \
    --hide-extension "Labelme.app" \
    --app-drop-link 425 190 \
    --no-internet-enable \
    "$DMG_PATH" \
    "$APP_PATH" || {
      echo "create-dmg failed (often due to headless Finder), falling back to hdiutil..."
      rm -f "$DMG_PATH"
      STAGING_DIR="build/dmg_staging"
      rm -rf "$STAGING_DIR"
      mkdir -p "$STAGING_DIR"
      cp -R "$APP_PATH" "$STAGING_DIR/"
      ln -s /Applications "$STAGING_DIR/Applications"
      hdiutil create -volname "Labelme" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_PATH"
      rm -rf "$STAGING_DIR"
    }
else
  STAGING_DIR="build/dmg_staging"
  rm -rf "$STAGING_DIR"
  mkdir -p "$STAGING_DIR"
  cp -R "$APP_PATH" "$STAGING_DIR/"
  ln -s /Applications "$STAGING_DIR/Applications"
  hdiutil create -volname "Labelme" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_PATH"
  rm -rf "$STAGING_DIR"
fi

echo "Successfully created $DMG_PATH"

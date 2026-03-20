#!/usr/bin/env bash
# build_appimage.sh — Package Linux Activity Monitor as a portable AppImage
#
# Requirements:
#   pip install pyinstaller
#   Download appimagetool from https://github.com/AppImage/AppImageKit/releases
#   and place it at ~/bin/appimagetool or in PATH.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="linux-activity-monitor"
VERSION="1.0.0"
DIST_DIR="$SCRIPT_DIR/dist/$APP_NAME"

echo "==> Building with PyInstaller..."
python3 -m PyInstaller \
    --name "$APP_NAME" \
    --onedir \
    --noconfirm \
    --clean \
    --add-data "assets:assets" \
    --hidden-import "PySide6.QtCore" \
    --hidden-import "PySide6.QtWidgets" \
    --hidden-import "PySide6.QtGui" \
    main.py

echo ""
echo "==> Creating AppDir structure..."
APP_DIR="$SCRIPT_DIR/dist/${APP_NAME}.AppDir"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"

# Copy PyInstaller bundle
cp -r "$DIST_DIR/"* "$APP_DIR/usr/bin/"

# Desktop file
cat > "$APP_DIR/usr/share/applications/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Linux Activity Monitor
Comment=Monitor system activity and resource usage
Exec=$APP_NAME
Icon=$APP_NAME
Categories=System;Monitor;
Terminal=false
EOF

# AppRun script
cat > "$APP_DIR/AppRun" <<'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/linux-activity-monitor" "$@"
APPRUN
chmod +x "$APP_DIR/AppRun"

# Copy desktop file to AppDir root
cp "$APP_DIR/usr/share/applications/$APP_NAME.desktop" "$APP_DIR/"

echo ""
echo "==> Running appimagetool..."
APPIMAGETOOL=$(command -v appimagetool 2>/dev/null || echo "$HOME/bin/appimagetool")
if [ ! -x "$APPIMAGETOOL" ]; then
    echo "WARNING: appimagetool not found."
    echo "Download it from: https://github.com/AppImage/AppImageKit/releases"
    echo "The AppDir is ready at: $APP_DIR"
    echo "Run manually: appimagetool $APP_DIR ${APP_NAME}-${VERSION}-x86_64.AppImage"
else
    ARCH=x86_64 "$APPIMAGETOOL" "$APP_DIR" "${APP_NAME}-${VERSION}-x86_64.AppImage"
    echo ""
    echo "==> AppImage created: ${APP_NAME}-${VERSION}-x86_64.AppImage"
fi

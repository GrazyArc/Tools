#!/bin/bash
# install.sh
# Restore system packages and Hyprpm plugins from manifests

set -euo pipefail

PKG_DIR="packages"
PKGLIST="$PKG_DIR/pkglist.txt"
AURLIST="$PKG_DIR/aur-packages.txt"
HYPRPLUGINS="$PKG_DIR/hypr_plugins_manifest.txt"

echo "🚀 Starting GrazyOS install process..."

# Ensure packages directory exists
if [ ! -d "$PKG_DIR" ]; then
  echo "❌ Packages directory not found: $PKG_DIR"
  exit 1
fi

# 1. Install official repo packages
if [ -s "$PKGLIST" ]; then
  echo "📦 Installing official repo packages..."
  sudo pacman -S --needed - < "$PKGLIST"
else
  echo "⚠️ No official package list found at $PKGLIST"
fi

# 2. Install AUR packages (requires yay or paru)
if [ -s "$AURLIST" ]; then
  echo "📦 Installing AUR packages..."
  if command -v yay >/dev/null 2>&1; then
    yay -S --needed - < "$AURLIST"
  elif command -v paru >/dev/null 2>&1; then
    paru -S --needed - < "$AURLIST"
  else
    echo "❌ No AUR helper (yay/paru) found. Please install one first."
    exit 1
  fi
else
  echo "⚠️ No AUR package list found at $AURLIST"
fi

# 3. Restore Hyprpm plugins
if [ -s "$HYPRPLUGINS" ]; then
  echo "🖥️ Restoring Hyprpm plugins..."
  while read -r plugin; do
    [[ -z "$plugin" || "$plugin" =~ ^# ]] && continue
    hyprpm enable "$plugin" || echo "⚠️ Failed to enable plugin: $plugin"
  done < "$HYPRPLUGINS"
  hyprpm update
else
  echo "⚠️ No Hyprpm plugin manifest found at $HYPRPLUGINS"
fi

echo "✅ Install complete! Your environment is now restored."

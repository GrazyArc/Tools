#!/bin/bash
# sync_pkgs.sh
# Run on the INSTALLER HOST to validate and correct package manifests

set -e

MANIFEST_DIR="./packages"
PKGLIST="$MANIFEST_DIR/pkglist.txt"
AURLIST="$MANIFEST_DIR/aur-packages.txt"

echo "🔧 Syncing package manifests with host system..."

if [[ ! -d "$MANIFEST_DIR" ]]; then
  echo "❌ No packages/ directory found."
  exit 1
fi

# Temporary files
TMP_OFFICIAL=$(mktemp)
TMP_AUR=$(mktemp)

echo "📦 Checking official repo packages..."
while read -r pkg; do
  # If pacman can find it in repos, keep it
  if pacman -Sp --print-format "%n" "$pkg" >/dev/null 2>&1; then
    echo "$pkg" >> "$TMP_OFFICIAL"
  else
    echo "⚠️ $pkg not found in host repos — moving to AUR list"
    echo "$pkg" >> "$TMP_AUR"
  fi
done < "$PKGLIST"

echo "📦 Checking AUR packages..."
while read -r pkg; do
  # If pacman can find it in repos, move it to official
  if pacman -Sp --print-format "%n" "$pkg" >/dev/null 2>&1; then
    echo "ℹ️ $pkg is available in host repos — moving to official list"
    echo "$pkg" >> "$TMP_OFFICIAL"
  else
    echo "$pkg" >> "$TMP_AUR"
  fi
done < "$AURLIST"

# Sort + dedupe
sort -u "$TMP_OFFICIAL" > "$PKGLIST"
sort -u "$TMP_AUR" > "$AURLIST"

rm "$TMP_OFFICIAL" "$TMP_AUR"

echo "✅ Sync complete!"
echo "✅ Official packages: $PKGLIST"
echo "✅ AUR packages: $AURLIST"

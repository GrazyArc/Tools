#!/bin/bash
# get_installed_packages.sh
# Export installed packages into manifest files for reproducibility

mkdir -p packages

echo "📦 Exporting official repo packages..."
pacman -Qq | while read -r pkg; do
  # If pacman can find the package in any repo, it's official
  if pacman -Sp --print-format "%n" "$pkg" >/dev/null 2>&1; then
    echo "$pkg"
  fi
done > packages/pkglist.txt

echo "📦 Exporting AUR packages..."
pacman -Qq | while read -r pkg; do
  # If pacman CANNOT find the package, it's AUR
  if ! pacman -Sp --print-format "%n" "$pkg" >/dev/null 2>&1; then
    echo "$pkg"
  fi
done > packages/aur-packages.txt

# Check results
if [ -s packages/pkglist.txt ]; then
  echo "✅ Official repo packages saved to packages/pkglist.txt"
else
  echo "⚠️ No official packages found."
fi

if [ -s packages/aur-packages.txt ]; then
  echo "✅ AUR packages saved to packages/aur-packages.txt"
else
  echo "⚠️ No AUR packages found."
fi

echo "🎉 Package export complete!"

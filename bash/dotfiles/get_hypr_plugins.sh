#!/bin/bash
# get_hypr_plugins.sh
# Export installed Hyprpm plugins into a manifest file

OUTPUT="hypr_plugins_manifest.txt"

mkdir -p "$(dirname "$OUTPUT")"

# Grab plugin names (field 3) from hyprpm list
hyprpm list | awk '/Plugin/ {print $3}' > "$OUTPUT"

if [ -s "$OUTPUT" ]; then
  echo "✅ Hyprpm plugins exported to $OUTPUT"
else
  echo "⚠️ No plugins found. Manifest file is empty."
fi

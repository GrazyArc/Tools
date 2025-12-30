#!/usr/bin/env bash
set -euo pipefail

MIRROR="$HOME/system-mirror"

echo "=== Unmounting all bind mounts under $MIRROR ==="

# Find all mountpoints under MIRROR, sort deepest-first
mapfile -t MOUNTS < <(
    mount | awk -v m="$MIRROR" '$3 ~ "^"m {print $3}' | sort -r
)

for m in "${MOUNTS[@]}"; do
    echo "→ Unmounting $m"
    sudo umount "$m" || true
done

echo "=== All mirrors unmounted ==="

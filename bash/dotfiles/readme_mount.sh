#!/usr/bin/env bash
set -euo pipefail

MIRROR="$HOME/system-mirror"

# Directories to mirror
declare -A MAP=(
    ["/etc"]="etc"
    ["/etc/systemd"]="systemd"
    ["/etc/default"]="default"
    ["/usr/lib/systemd/system"]="systemd_units"
    ["/boot"]="boot"
    ["/home/$USER/.config"]=".config"
)

ensure_dir() {
    mkdir -p "$1"
}

mount_file_ro() {
    local src="$1"
    local dst="$2"

    echo "→ Mirroring file $src → $dst"
    mkdir -p "$(dirname "$dst")"
    touch "$dst"

    sudo mount --bind "$src" "$dst"
    sudo mount -o remount,ro,bind "$src" "$dst"
}

mount_dir_ro() {
    local src="$1"
    local dst="$2"

    echo "→ Mirroring directory $src → $dst"
    ensure_dir "$dst"

    sudo mount --bind "$src" "$dst"
    sudo mount -o remount,ro,bind "$src" "$dst"
}

echo "=== System Read‑Only Mirror Setup ==="
ensure_dir "$MIRROR"

# --- 1. Mirror dotfiles FIRST -------------------------------------------------
echo "→ Scanning for dotfiles in $HOME"

while IFS= read -r file; do
    [[ -d "$file" ]] && continue

    rel="${file#$HOME/}"
    dst="$MIRROR/home/$rel"

    mount_file_ro "$file" "$dst"
done < <(find "$HOME" -maxdepth 1 -type f -name ".*")

# --- 2. Mirror directories SECOND --------------------------------------------
for src in "${!MAP[@]}"; do
    dst="$MIRROR/${MAP[$src]}"
    mount_dir_ro "$src" "$dst"
done

echo "=== All mirrors mounted read‑only ==="

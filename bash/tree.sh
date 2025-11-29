#!/usr/bin/env bash
# tree.sh - Print folder structure with ignore support, .gitignore awareness,
#           and detailed file info output to a file.

# Usage:
#   ./tree.sh [root_dir] [output_file] [max_levels] [ignore_patterns...]
# Example:
#   ./tree.sh . tree.txt 2 "node_modules" "dist"
#
# If the third positional argument is a non-negative integer it will be
# treated as the maximum folder depth to record (0 = only the root). If the
# third argument is non-numeric it is treated as the first ignore pattern
# (backwards compatible with the prior behaviour).

ROOT="${1:-.}"
OUTFILE="${2:-tree.txt}"
# Optional max levels is the third positional argument if it's a non-negative integer
MAX_LEVEL_RAW="${3:-}"
MAX_DEPTH_ARG=""

if [[ -n "$MAX_LEVEL_RAW" && "$MAX_LEVEL_RAW" =~ ^[0-9]+$ ]]; then
  # Use this as the maxdepth for find
  MAX_DEPTH_ARG=( -maxdepth "$MAX_LEVEL_RAW" )
  # shift past root, outfile and max_levels
  shift 3
else
  # shift past root and outfile only; treat $3+ as ignore patterns
  shift 2
fi

USER_IGNORES=("$@")

# Build ignore args for 'find'
IGNORE_ARGS=()
for pat in "${USER_IGNORES[@]}"; do
  IGNORE_ARGS+=(-path "$ROOT/$pat" -prune -o)
done

# Always ignore .git folders
IGNORE_ARGS+=(-path "$ROOT/.git" -prune -o)

# If .gitignore exists, parse it into ignore args
if [[ -f "$ROOT/.gitignore" ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    IGNORE_ARGS+=(-path "$ROOT/$line" -prune -o)
  done < "$ROOT/.gitignore"
fi

# Collect all files and directories with detailed info
# Format: permissions, owner, group, size, date, path
{
  echo "Folder structure for: $ROOT"
  echo "Generated on: $(date)"
  echo "========================================="
  find "$ROOT" "${IGNORE_ARGS[@]}" ${MAX_DEPTH_ARG[@]} -print \
    | while read -r f; do
        stat --printf "%A %U %G %s %y %n\n" "$f" 2>/dev/null
      done \
    | sed -e "s|[^/]*/|   |g" -e "s|/|- |"
} > "$OUTFILE"

echo "Tree written to $OUTFILE"

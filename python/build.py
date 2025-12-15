#!/usr/bin/env python3
#
# Author: Crazygiscool
# Description: Build script for packaging the Python application using Nuitka.

import os
import sys
import subprocess
import platform
from pathspec import PathSpec

# -----------------------------
# CONFIGURATION
# -----------------------------
ENTRY = "main.py"
OUTPUT_NAME = "EXECUTABLE"

# Folders to ignore entirely
IGNORE_DIRS = {
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
    "build",
    "dist",
    "venv",
    "env",
    ".nuitka",
    ".vs",
    ".venv",
    "tests",
    "docs",
    ".github"
}

# -----------------------------
# AUTO-DETECTION
# -----------------------------
def detect_packages_and_data(root="."):
    packages = []
    data_dirs = []

    gitignore_path = os.path.join(root, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
            gitignore_spec = PathSpec.from_lines("gitwildmatch", f)
    else:
        gitignore_spec = PathSpec.from_lines("gitwildmatch", [])

    all_packages = set()

    for dirpath, dirnames, filenames in os.walk(root):
        rel_path = os.path.relpath(dirpath, root)

        if rel_path == ".":
            continue

        folder = os.path.basename(dirpath)
        if folder in IGNORE_DIRS:
            dirnames[:] = []
            continue

        if gitignore_spec.match_file(rel_path):
            dirnames[:] = []
            continue

        if "__init__.py" in filenames:
            all_packages.add(rel_path.replace("\\", "/"))

    for pkg in all_packages:
        parent = os.path.dirname(pkg)
        if parent == "" or parent == "." or parent not in all_packages:
            packages.append(pkg)

    for dirpath, dirnames, filenames in os.walk(root):
        rel_path = os.path.relpath(dirpath, root)
        if rel_path == ".":
            continue

        folder = os.path.basename(dirpath)
        if folder in IGNORE_DIRS:
            dirnames[:] = []
            continue

        if gitignore_spec.match_file(rel_path):
            dirnames[:] = []
            continue

        has_non_py = any(not f.endswith(".py") for f in filenames)
        if has_non_py:
            data_dirs.append(rel_path.replace("\\", "/"))

    return packages, data_dirs


# -----------------------------
# BUILD COMMAND GENERATION
# -----------------------------
def build_command(packages, data_dirs):
    system = platform.system().lower()

    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--onefile",
        "--follow-imports",
        "--enable-plugin=pylint-warnings",
        "--lto=yes",
        "--output-dir=build",
        f"--output-filename={OUTPUT_NAME}",
    ]

    if system != "windows":
        cmd.append("--static-libpython=yes")

    if system == "windows":
        cmd.append("--msvc=latest")
    else:
        cmd.append("--clang")

    for pkg in packages:
        cmd.append(f"--include-package={pkg}")

    for d in data_dirs:
        cmd.append(f"--include-data-dir={d}={d}")

    cmd.append(ENTRY)
    return cmd


# -----------------------------
# MAIN BUILD EXECUTION
# -----------------------------
def main():
    print("Building with Nuitka...")
    os.makedirs("build", exist_ok=True)

    print("\n=== Environment Diagnostics ===")
    print("Python:", sys.executable)
    print("Python Version:", sys.version)
    print("Platform:", platform.platform())
    print("PATH:", os.environ.get("PATH"))
    print("===============================\n")

    print("Auto-detecting packages and data directories...")
    packages, data_dirs = detect_packages_and_data()

    print("\nPython Packages Found:")
    for p in packages:
        print("   •", p)

    print("\nData Directories Found:")
    for d in data_dirs:
        print("   •", d)

    print("\nGenerating Nuitka command...\n")
    cmd = build_command(packages, data_dirs)
    print("COMMAND:")
    print(" ".join(cmd))
    print("\nRunning Nuitka...\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        print("\n=== STDOUT ===")
        print(result.stdout)

        print("\n=== STDERR ===")
        print(result.stderr)

        result.check_returncode()
        print("\nBuild complete!")
        print("Executable generated:", OUTPUT_NAME)

    except subprocess.CalledProcessError as e:
        print("\nBuild failed with exit code:", e.returncode)

        print("\n=== Captured STDOUT ===")
        print(result.stdout)

        print("\n=== Captured STDERR ===")
        print(result.stderr)

        nuitka_log = os.path.join("build", "nuitka-crash-report.txt")
        if os.path.exists(nuitka_log):
            print("\n=== Nuitka Crash Report ===")
            with open(nuitka_log, "r", errors="ignore") as f:
                print(f.read())

        sys.exit(1)


if __name__ == "__main__":
    main()

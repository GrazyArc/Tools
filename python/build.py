#!/usr/bin/env python3
#
# Author: Crazygiscool
# Description: Build script for packaging the Python application using Nuitka.

import os
import sys
import subprocess
import platform
import tempfile
import shutil
import textwrap
import argparse
from pathlib import Path

from pathspec import PathSpec # type: ignore
from cryptography.fernet import Fernet # type: ignore

# -----------------------------
# CONFIGURATION
# -----------------------------
ENTRY = "GEORGE.py"
OUTPUT_NAME = "GEORGE"
DEBUG = True  # flip this to False to silence debug output

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
    ".github",
    "Documents",
}

# Data dirs you always want bundled (runtime will expect them)
CORE_DATA_ROOTS = ["state"]  # "core" is code, not data, so not here


# -----------------------------
# ARGUMENTS
# -----------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Build Cerberus with Nuitka")
    parser.add_argument(
        "--encrypt-data",
        action="store_true",
        help="Encrypt bundled data payload after build",
    )
    parser.add_argument(
        "--upx",
        action="store_true",
        help="Enable onefile compression (UPX or built-in compression)",
    )
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Version string for packages (default: 1.0.0)",
    )
    parser.add_argument(
        "--debug-stream",
        action="store_true",
        help="Stream Nuitka output live (stdout + stderr)"
    )

    parser.add_argument( "--torch-jit", choices=["auto", "enable", "disable"], default="disable", help="Control Nuitka Torch JIT mode (default: disable)" )

    return parser.parse_args()


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
def build_command(packages, data_dirs, args):
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
        "--nofollow-import-to=tests",
        "--nofollow-import-to=pytest",
        "--nofollow-import-to=setuptools",
        "--nofollow-import-to=pip",
        "--noinclude-pytest-mode=nofollow",
        "--noinclude-setuptools-mode=nofollow",
        "--noinclude-unittest-mode=nofollow",
        "--remove-output",
        "--assume-yes-for-downloads",
    ]

    if system == "windows":
        cmd.append("--msvc=latest")
    else:
        cmd.append("--clang")
        cmd.append("--static-libpython=no")

        if args.upx:
            cmd.append("--onefile-compression=yes")

    # Torch JIT handling
    if args.torch_jit == "disable":
        cmd.append("--module-parameter=torch-disable-jit=yes")
    elif args.torch_jit == "enable":
        cmd.append("--module-parameter=torch-disable-jit=no")
    # auto = do nothing

    # Include detected packages
    for pkg in packages:
        cmd.append(f"--include-package={pkg}")

    # Include data dirs
    for d in data_dirs:
        if any(d == root or d.startswith(root + "/") for root in CORE_DATA_ROOTS):
            cmd.append(f"--include-data-dir={d}={d}")

    # Ensure CORE_DATA_ROOTS always included
    for root in CORE_DATA_ROOTS:
        if os.path.isdir(root):
            spec = f"--include-data-dir={root}={root}"
            if spec not in cmd:
                cmd.append(spec)

    cmd.append(ENTRY)
    return cmd


# -----------------------------
# DATA ENCRYPTION
# -----------------------------
def build_encrypted_payload(data_dirs, key, output_path):
    """
    Create a single encrypted payload from selected data directories.

    - Packs data_dirs into a tar-like structure in memory.
    - Encrypts with Fernet (symmetric).
    - Writes to output_path.
    """
    import tarfile
    import io

    buf = io.BytesIO()

    # Pack into tar in memory
    with tarfile.open(mode="w:gz", fileobj=buf) as tar:
        for d in data_dirs:
            if os.path.isdir(d):
                tar.add(d, arcname=d)

    buf.seek(0)
    raw = buf.read()

    f = Fernet(key)
    encrypted = f.encrypt(raw)

    with open(output_path, "wb") as f_out:
        f_out.write(encrypted)


def encrypt_data_payload(args, data_dirs):
    """
    Build an encrypted data payload and write out the key.

    Runtime responsibility:
    - Read key from env / config / hardware
    - Decrypt payload at startup
    """
    print("[*] Building encrypted data payload...")

    # Only include known roots
    selected_dirs = []
    for d in data_dirs:
        if any(d == root or d.startswith(root + "/") for root in CORE_DATA_ROOTS):
            selected_dirs.append(d)

    if not selected_dirs:
        print("[!] No data directories to encrypt (based on CORE_DATA_ROOTS). Skipping.")
        return

    key = Fernet.generate_key()
    payload_path = os.path.join("build", "cerberus_data.enc")
    build_encrypted_payload(selected_dirs, key, payload_path)

    key_path = os.path.join("build", "cerberus_data.key")
    with open(key_path, "wb") as f:
        f.write(key)

    print("[*] Encrypted data payload:", payload_path)
    print("[*] Encryption key written to:", key_path)
    print("    IMPORTANT: Do NOT ship the key in plain form with public builds.")
    print("    Integrate secure key management in runtime before using this in prod.")


# -----------------------------
# .DEB PACKAGING
# -----------------------------
def build_deb(exe_path, data_dirs, version):
    if shutil.which("dpkg-deb") is None:
        print("[!] dpkg-deb not found, skipping .deb packaging.")
        return

    print("[*] Building .deb package...")
    with tempfile.TemporaryDirectory() as tmpdir:
        deb_root = os.path.join(tmpdir, "cerberus")
        bin_dir = os.path.join(deb_root, "usr", "bin")
        share_dir = os.path.join(deb_root, "usr", "share", "cerberus")

        os.makedirs(bin_dir, exist_ok=True)
        os.makedirs(share_dir, exist_ok=True)

        shutil.copy2(exe_path, os.path.join(bin_dir, "cerberus"))

        for d in data_dirs:
            if any(d == root or d.startswith(root + "/") for root in CORE_DATA_ROOTS):
                src = d
                dst = os.path.join(share_dir, d)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)

        debian_dir = os.path.join(deb_root, "DEBIAN")
        os.makedirs(debian_dir, exist_ok=True)
        control_path = os.path.join(debian_dir, "control")

        control_content = textwrap.dedent(f"""\
            Package: cerberus
            Version: {version}
            Section: utils
            Priority: optional
            Architecture: amd64
            Maintainer: Crazygiscool
            Description: Cerberus Multi-OS USB Builder
        """)

        with open(control_path, "w") as f:
            f.write(control_content)

        output_deb = os.path.abspath(f"cerberus_{version}_amd64.deb")
        subprocess.check_call(["dpkg-deb", "--build", deb_root, output_deb])
        print("    Built .deb:", output_deb)


# -----------------------------
# ARCH PKG PACKAGING
# -----------------------------
def build_arch_pkg(exe_path, data_dirs, version):
    if shutil.which("tar") is None:
        print("[!] tar not found, skipping .pkg.tar.zst packaging.")
        return

    print("[*] Building Arch .pkg.tar.zst package...")
    with tempfile.TemporaryDirectory() as tmpdir:
        pkg_root = os.path.join(tmpdir, "pkgroot")
        bin_dir = os.path.join(pkg_root, "usr", "bin")
        share_dir = os.path.join(pkg_root, "usr", "share", "cerberus")
        os.makedirs(bin_dir, exist_ok=True)
        os.makedirs(share_dir, exist_ok=True)

        shutil.copy2(exe_path, os.path.join(bin_dir, "cerberus"))

        for d in data_dirs:
            if any(d == root or d.startswith(root + "/") for root in CORE_DATA_ROOTS):
                src = d
                dst = os.path.join(share_dir, d)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)

        pkginfo_path = os.path.join(pkg_root, ".PKGINFO")
        pkginfo_content = textwrap.dedent(f"""\
            pkgname = cerberus
            pkgver = {version}-1
            pkgdesc = Cerberus Multi-OS USB Builder
            url = https://example.com
            builddate = 0
            packager = Crazygiscool
            size = 0
            arch = x86_64
            license = custom
        """)
        with open(pkginfo_path, "w") as f:
            f.write(pkginfo_content)

        output_pkg = os.path.abspath(f"cerberus-{version}-1-x86_64.pkg.tar.zst")
        cwd = os.getcwd()
        os.chdir(pkg_root)
        try:
            subprocess.check_call(
                ["tar", "--zstd", "-cf", output_pkg, "."]
            )
        finally:
            os.chdir(cwd)

        print("    Built Arch package:", output_pkg)

def run_nuitka_stream(cmd):
    import threading
    import queue

    q = queue.Queue()

    def reader(stream, tag):
        for line in iter(stream.readline, ''):
            q.put((tag, line.rstrip()))
        stream.close()

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )

    threads = [
        threading.Thread(target=reader, args=(process.stdout, "OUT")),
        threading.Thread(target=reader, args=(process.stderr, "ERR")),
    ]

    for t in threads:
        t.daemon = True
        t.start()

    # Drain queue until process exits
    while True:
        try:
            tag, line = q.get(timeout=0.1)
            if tag == "OUT":
                print("[Nuitka]", line)
            else:
                print("[Nuitka:ERR]", line)
        except queue.Empty:
            if process.poll() is not None:
                break

    # Final drain
    while not q.empty():
        tag, line = q.get()
        if tag == "OUT":
            print("[Nuitka]", line)
        else:
            print("[Nuitka:ERR]", line)

    return process.returncode


# -----------------------------
# MAIN BUILD EXECUTION
# -----------------------------
def main():
    args = parse_args()

    print("Building with Nuitka...")
    os.makedirs("build", exist_ok=True)

    # -----------------------------
    # EXTENDED DEBUG SECTION
    # -----------------------------
    if DEBUG:
        print("\n=== EXTENDED DEBUG MODE ENABLED ===")
        print("Python Executable:", sys.executable)
        print("Python Version:", sys.version)
        print("Platform:", platform.platform())
        print("Working Directory:", os.getcwd())
        print("PATH Breakdown:")
        for p in os.environ.get("PATH", "").split(":"):
            print("   •", p)
        print("\nInstalled Nuitka Version:")
        try:
            subprocess.run([sys.executable, "-m", "nuitka", "--version"], check=False)
        except Exception as e:
            print("   [!] Failed to query Nuitka version:", e)

        print("\nChecking for UPX:")
        print("   upx found:", shutil.which("upx"))

        print("\nChecking for Clang:")
        print("   clang found:", shutil.which("clang"))

        print("\nChecking for GCC:")
        print("   gcc found:", shutil.which("gcc"))

        print("\nChecking for patchelf:")
        print("   patchelf found:", shutil.which("patchelf"))

        print("\nEnvironment Variables:")
        for k, v in os.environ.items():
            if k.startswith(("NUITKA", "PYTHON", "LD_", "PATH")):
                print(f"   {k}={v}")

        print("\n===================================\n")

    # -----------------------------
    # AUTO-DETECTION
    # -----------------------------
    print("Auto-detecting packages and data directories...")
    packages, data_dirs = detect_packages_and_data()

    print("\nPython Packages Found:")
    for p in packages:
        print("   •", p)

    print("\nData Directories Found:")
    for d in data_dirs:
        print("   •", d)

    # -----------------------------
    # COMMAND GENERATION
    # -----------------------------
    print("\nGenerating Nuitka command...\n")

    os.environ.setdefault("CFLAGS", "-Wno-macro-redefined") # Suppress _XOPEN_SOURCE warnings

    cmd = build_command(packages, data_dirs, args)

    print("COMMAND:")
    print(" ".join(cmd))

    # -----------------------------
    # PRE-FLIGHT CHECK
    # -----------------------------
    if DEBUG:
        print("\n=== PRE-FLIGHT FILESYSTEM CHECK ===")
        print("Entry file exists:", os.path.exists(ENTRY))
        print("State folder exists:", os.path.isdir("state"))
        print("Build folder exists:", os.path.isdir("build"))
        print("====================================\n")

    # -----------------------------
    # RUN BUILD WITH LIVE OUTPUT
    # -----------------------------
    print("\nRunning Nuitka...\n")

    try:
        if args.debug_stream:
            rc = run_nuitka_stream(cmd)
            if rc != 0:
                print(f"[!] Nuitka failed with exit code {rc}")
                sys.exit(rc)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            print("\n=== STDOUT ===")
            print(result.stdout)
            print("\n=== STDERR ===")
            print(result.stderr)
            result.check_returncode()

        print("\nBuild complete!")

        exe_path = os.path.join("build", OUTPUT_NAME)
        if not os.path.exists(exe_path):
            candidate = Path("build") / (OUTPUT_NAME + ".bin")
            if candidate.exists():
                exe_path = str(candidate)

        print("Executable generated:", exe_path)

        if args.encrypt_data:
            encrypt_data_payload(args, data_dirs)

        build_deb(exe_path, data_dirs, args.version)
        build_arch_pkg(exe_path, data_dirs, args.version)

    except subprocess.CalledProcessError:
        print("\nBuild failed — see logs above.")
        sys.exit(1)

        # Stream output live
        if process.stdout is not None:
            for line in process.stdout:
                print("[Nuitka]", line.rstrip())

        stderr_output = []
        if process.stderr is not None:
            for line in process.stderr:
                stderr_output.append(line)
                print("[Nuitka:ERR]", line.rstrip())

        process.wait()

        if process.returncode != 0:
            print("\n[!] Nuitka failed with exit code:", process.returncode)
            print("\n=== STDERR (captured) ===")
            print("".join(stderr_output))
            raise subprocess.CalledProcessError(process.returncode, cmd)

        print("\nBuild complete!")

        exe_path = os.path.join("build", OUTPUT_NAME)
        if not os.path.exists(exe_path):
            candidate = Path("build") / (OUTPUT_NAME + ".bin")
            if candidate.exists():
                exe_path = str(candidate)

        print("Executable generated:", exe_path)

        # Optional encrypted payload
        if args.encrypt_data:
            encrypt_data_payload(args, data_dirs)

        # Packaging
        build_deb(exe_path, data_dirs, args.version)
        build_arch_pkg(exe_path, data_dirs, args.version)

    except subprocess.CalledProcessError:
        print("\nBuild failed — see logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

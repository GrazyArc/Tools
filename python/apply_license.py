import os
import re
import difflib
import sys

# ==== CONFIGURATION ====

RAW_LICENSE_TEXT = """Copyright © 2025 Crazygiscool  
All rights reserved.

This file is part of the Crazyg project. Viewing is permitted for feedback submission (e.g. bugs, feature requests), but reproduction, modification, or distribution is strictly prohibited without explicit written permission from the owner.

By opening this file, you agree to the terms of the Non-Commercial License v1.0.

Unauthorized use is subject to copyright and intellectual property laws."""

COMMENT_STYLES = {
    ".py": '"""{}"""',
    ".md": '<!-- {} -->',
    ".txt": '# {}',
    ".json": '// {}',
    ".yaml": '# {}',
    ".yml": '# {}',
    ".ini": '; {}',
    ".cfg": '; {}'
}

SIMILARITY_THRESHOLD = 0.85
FILE_EXTENSIONS = list(COMMENT_STYLES.keys())
IGNORE_DIRS = ["venv", "__pycache__", "logs", "assets", ".git", ".vscode"]

BLACKLIST_FILES = [
    "README.md",
    "LICENSE.txt",
    "folder_structure.txt",
    "allfiles.txt"
]

# ==== LICENSE UTILITIES ====

def format_license(ext):
    style = COMMENT_STYLES.get(ext, '# {}')
    if style.count('{}') == 1:
        return style.format(RAW_LICENSE_TEXT.replace('\n', '\n' + style.format('')))
    else:
        return style.format(RAW_LICENSE_TEXT)

def license_pattern(ext):
    if ext in [".py", ".md"]:
        return r'(\"\"\"|<!--).*?Copyright.*?Unauthorized use.*?(\"\"\"|-->)'
    elif ext in [".json"]:
        return r'(//.*?Copyright.*?Unauthorized use.*?)\n'
    else:
        return r'([#;].*?Copyright.*?Unauthorized use.*?)\n'

def remove_all_license_blocks(text, pattern):
    return re.sub(pattern, "", text, flags=re.DOTALL)

def similarity(a, b):
    return difflib.SequenceMatcher(None, a.strip(), b.strip()).ratio()

def clean_and_insert_license(text, ext):
    pattern = license_pattern(ext)
    cleaned = remove_all_license_blocks(text, pattern).lstrip()
    return format_license(ext) + "\n\n" + cleaned

# ==== PER-FILE LOGIC ====

def process_file(filepath, project_root, remove_mode=False):
    rel_path = os.path.relpath(filepath, project_root)
    ext = os.path.splitext(filepath)[1]

    # 🚫 Skip LICENSE.txt and this script itself
    if os.path.basename(filepath) in ["LICENSE.txt", "apply_license.py"]:
        print(f"⏭ Skipped (protected file): {rel_path}")
        return

    if ext not in COMMENT_STYLES or rel_path in BLACKLIST_FILES:
        print(f"⏭ Skipped (blacklisted or unsupported): {rel_path}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    pattern = license_pattern(ext)

    if remove_mode:
        cleaned = remove_all_license_blocks(original, pattern).lstrip()
        if cleaned != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(cleaned)
            print(f"🧹 License removed: {rel_path}")
        else:
            print(f"✔ No license found: {rel_path}")
        return


    if remove_mode:
        cleaned = remove_all_license_blocks(original, pattern).lstrip()
        if cleaned != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(cleaned)
            print(f"🧹 License removed: {rel_path}")
        else:
            print(f"✔ No license found: {rel_path}")
        return

    match = re.search(pattern, original, flags=re.DOTALL)
    new_license = format_license(ext)

    if match:
        existing_license = match.group(0)
        score = similarity(existing_license, new_license)

        if score >= SIMILARITY_THRESHOLD:
            print(f"✔ License already present: {rel_path}")
        else:
            new_text = clean_and_insert_license(original, ext)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_text)
            print(f"🧼 Replaced outdated license: {rel_path}")
    else:
        new_text = new_license + "\n\n" + original.lstrip()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"🔐 License added: {rel_path}")

# ==== DIRECTORY SCANNER ====

def should_ignore(path):
    return any(skip in path for skip in IGNORE_DIRS)

def scan_folder(root_dir, remove_mode=False):
    for dirpath, _, filenames in os.walk(root_dir):
        if should_ignore(dirpath):
            continue
        for file in filenames:
            if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                full_path = os.path.join(dirpath, file)
                process_file(full_path, root_dir, remove_mode)

# ==== EXECUTION ====

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    remove_mode = "--remove" in sys.argv
    scan_folder(project_root, remove_mode)

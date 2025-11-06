"""Copyright © 2025 Crazygiscool  
""""""All rights reserved.
""""""Unauthorized use is subject to copyright and intellectual property laws."""

import os
from pathlib import Path
import pathspec

def load_gitignore_spec(startpath: str):
    gitignore_path = Path(startpath) / '.gitignore'
    if not gitignore_path.exists():
        return None

    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            patterns = f.read().splitlines()
    except UnicodeDecodeError:
        with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
            patterns = f.read().splitlines()

    return pathspec.PathSpec.from_lines('gitwildmatch', patterns)


def list_folder_structure(startpath: str, output_file: str):
    """Recursively list the folder structure starting from the given path,
    ignoring files and folders listed in .gitignore.
    
    Args:
        startpath (str): The path to start listing the folder structure.
        output_file (str, optional): The file to write the output to. If None, print to console.
    """
    output = []
    spec = load_gitignore_spec(startpath)

    for root, dirs, files in os.walk(startpath):
        rel_root = os.path.relpath(root, startpath)
        if spec and spec.match_file(rel_root):
            continue

        level = rel_root.count(os.sep)
        indent = ' ' * 4 * level
        output.append(f"{indent}{os.path.basename(root)}/")

        # Filter dirs in-place to avoid descending into ignored folders
        dirs[:] = [d for d in dirs if not (spec and spec.match_file(os.path.join(rel_root, d)))]

        subindent = ' ' * 4 * (level + 1)
        for f in files:
            rel_file = os.path.join(rel_root, f)
            if spec and spec.match_file(rel_file):
                continue
            output.append(f"{subindent}{f}")

    if output_file:
        with open(output_file, 'w') as file:
            file.write('\n'.join(output))
        print(f"Folder structure written to {output_file}")
    else:
        print('\n'.join(output))

# Example usage
if __name__ == "__main__":
    list_folder_structure('./', './folder_structure.txt')

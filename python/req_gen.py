import ast
import os
import sys
import builtins
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
from importlib.metadata import version, PackageNotFoundError

# 📁 Setup log file
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"requirements_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def log(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def load_gitignore(project_dir):
    ignore_set = set()
    gitignore_path = Path(project_dir) / ".gitignore"
    if gitignore_path.exists():
        for line in gitignore_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                ignore_set.add(line.split("/")[0])
    return ignore_set

def should_skip(path, ignore_set):
    parts = Path(path).parts
    return any(part in ignore_set or part == ".git" for part in parts)

def extract_imports_from_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            node = ast.parse(f.read(), filename=file_path)
        imports = set()
        for item in ast.walk(node):
            if isinstance(item, ast.Import):
                for alias in item.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(item, ast.ImportFrom):
                if item.module:
                    imports.add(item.module.split('.')[0])
        log(f"[IMPORTS] {file_path}: {sorted(imports)}")
        return imports
    except Exception as e:
        log(f"[ERROR] Failed to parse {file_path}: {e}")
        return set()

def scan_project_for_imports(project_dir):
    ignore_set = load_gitignore(project_dir)
    all_py_files = []
    import_sources = {}

    for root, _, files in os.walk(project_dir):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                if not should_skip(full_path, ignore_set):
                    all_py_files.append(full_path)

    for file_path in tqdm(all_py_files, desc="Scanning Python files"):
        imports = extract_imports_from_file(file_path)
        for package in imports:
            import_sources.setdefault(package, set()).add(file_path)

    log(f"[SUMMARY] Total unique imports: {len(import_sources)}")
    return import_sources

def resolve_versions(import_sources):
    resolved = {}
    stdlib_modules = set(sys.builtin_module_names) | set(dir(builtins))

    for package in tqdm(import_sources, desc="Resolving versions"):
        if package in stdlib_modules:
            log(f"[SKIP] {package} is a built-in module")
            continue
        try:
            pkg_version = version(package)
            resolved[package] = {
                "line": f"{package}=={pkg_version}",
                "sources": import_sources[package]
            }
            log(f"[RESOLVE] {package}=={pkg_version}")
        except PackageNotFoundError:
            log(f"[SKIP] {package} is not pip-installable")
    return resolved


def parse_existing_requirements(path="requirements.txt"):
    existing = {}
    if not Path(path).exists():
        return existing
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" in line:
            pkg, ver = line.split("==", 1)
            existing[pkg.strip()] = ver.strip()
        else:
            existing[line.strip()] = None
    return existing

def write_requirements(resolved, _, output_path="requirements.txt", project_dir="."):
    existing = parse_existing_requirements(output_path)
    new_pkgs = set(resolved)
    old_pkgs = set(existing)

    removed = old_pkgs - new_pkgs
    for pkg in sorted(removed):
        log(f"[REMOVED] {pkg} no longer imported")

    with open(output_path, "w", encoding="utf-8") as f:
        for package in tqdm(sorted(resolved), desc="Writing requirements"):
            line = resolved[package]["line"]
            sources = sorted(resolved[package]["sources"])

            annotations = []
            for src in sources:
                path = Path(src)
                if path.parent.resolve() == Path(project_dir).resolve():
                    annotations.append(path.name)
                else:
                    annotations.append(path.parent.name)

            comment = f"# Used in: {', '.join(sorted(set(annotations)))}"
            f.write(f"{line}\n{comment}\n")

    log(f"[DONE] Requirements written to {output_path}")


if __name__ == "__main__":
    project_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    log(f"[BOOT] Starting scan in {project_dir}")
    import_sources = scan_project_for_imports(project_dir)
    resolved = resolve_versions(import_sources)
    write_requirements(resolved, import_sources, project_dir=project_dir)
    log("[EXIT] Diagnostic pass complete")
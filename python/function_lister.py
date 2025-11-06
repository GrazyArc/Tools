import ast
import sys
from pathlib import Path

def list_functions(file_path: str) -> None:
    """Print all top-level function names in a Python file."""
    path = Path(file_path)
    if not path.exists() or not path.suffix == ".py":
        print(f"❌ Invalid file: {file_path}")
        return

    try:
        with path.open("r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
    except Exception as e:
        print(f"⚠️ Failed to parse {file_path}: {e}")
        return

    print(f"\n📂 Functions in {file_path}:\n")
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            print(f"🔹 {node.name}")
    print("\n✅ Done.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python function_lister.py <path_to_python_file>")
    else:
        list_functions(sys.argv[1])

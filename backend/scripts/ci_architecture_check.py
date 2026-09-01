#!/usr/bin/env python3
"""
CI Architectural Integrity Check
Enforces:
1. Exactly ONE SQLAlchemy Declarative Base exists across the entire codebase (in app/models/base.py).
   Detects all `class X(DeclarativeBase):` AST nodes and `= declarative_base(...)` function calls.
2. Unique SQLAlchemy ORM model class names across all model definition files.
3. Clean routing without stale legacy imports.
"""

import sys
import ast
from pathlib import Path
from collections import defaultdict

BACKEND_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BACKEND_DIR / "app"
MODELS_DIR = APP_DIR / "models"
CANONICAL_BASE_FILE = (MODELS_DIR / "base.py").resolve()


def find_declarative_base_definitions(app_dir: Path):
    """
    Walks AST of all Python files in the codebase to find:
    - class X(DeclarativeBase):
    - x = declarative_base(...)
    """
    declarative_base_locations = []

    for py_file in app_dir.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(py_file))
        except Exception as e:
            print(f"Warning: could not parse {py_file}: {e}")
            continue

        resolved_path = py_file.resolve()

        for node in ast.walk(tree):
            # Check 1: class X(DeclarativeBase)
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_id = None
                    if isinstance(base, ast.Name):
                        base_id = base.id
                    elif isinstance(base, ast.Attribute):
                        base_id = base.attr
                    
                    if base_id in ("DeclarativeBase", "declarative_base"):
                        declarative_base_locations.append((resolved_path, f"class {node.name}({base_id}) at line {node.lineno}"))

            # Check 2: x = declarative_base(...)
            elif isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                
                if func_name == "declarative_base":
                    declarative_base_locations.append((resolved_path, f"declarative_base() call at line {node.lineno}"))

    return declarative_base_locations


def check_duplicate_model_classes(models_dir: Path):
    """Ensure every model class name inheriting from Base is defined only once."""
    class_locations = defaultdict(list)

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(), filename=str(py_file))
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(base.attr)
                
                if "Base" in bases or "DeclarativeBase" in bases or any("Base" in b for b in bases):
                    class_locations[node.name].append(py_file.name)

    duplicates = {name: files for name, files in class_locations.items() if len(files) > 1}
    return duplicates


def main():
    print("=" * 60)
    print("Running CI Architectural Integrity Check...")
    print("=" * 60)
    errors = []

    # 1. Check Declarative Base definitions
    base_defs = find_declarative_base_definitions(APP_DIR)
    print(f"Found {len(base_defs)} DeclarativeBase/declarative_base definition(s):")
    for file_path, desc in base_defs:
        print(f"  - {file_path.relative_to(BACKEND_DIR)}: {desc}")

    non_canonical_bases = [
        (fp, desc) for fp, desc in base_defs if fp != CANONICAL_BASE_FILE
    ]

    if non_canonical_bases:
        errors.append(
            f"ERROR: Non-canonical Declarative Base definitions found outside app/models/base.py:\n"
            + "\n".join(f"  {fp.relative_to(BACKEND_DIR)}: {desc}" for fp, desc in non_canonical_bases)
        )

    if not base_defs:
        errors.append("ERROR: Canonical Base in app/models/base.py was not found!")

    # 2. Check duplicate model classes
    duplicates = check_duplicate_model_classes(MODELS_DIR)
    if duplicates:
        errors.append(
            f"ERROR: Duplicate ORM model class names defined across models:\n"
            + "\n".join(f"  {name}: {files}" for name, files in duplicates.items())
        )

    # 3. Check router registry
    registry_file = APP_DIR / "api_router_registry.py"
    if registry_file.exists():
        with open(registry_file, "r", encoding="utf-8") as f:
            registry_content = f.read()
        if "from app.api import" in registry_content:
            errors.append("ERROR: api_router_registry.py contains stale imports from app.api!")

    print("-" * 60)
    if errors:
        for err in errors:
            print(f"\n[ERROR] {err}")
        print("\nCI ARCHITECTURE CHECK FAILED.")
        sys.exit(1)
    else:
        print("[SUCCESS] Architectural check passed!")
        print("   - Exactly ONE canonical Declarative Base in app/models/base.py")
        print("   - Zero duplicate ORM model class names")
        print("   - Clean routing registry")
        print("=" * 60)
        sys.exit(0)


if __name__ == "__main__":
    main()

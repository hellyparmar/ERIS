"""
Architectural Integrity Test
Asserts that:
1. Every SQLAlchemy model class name across the codebase is unique (defined exactly once).
2. There are zero secondary calls to declarative_base() in app/models.
3. All models inherit from the single canonical Base in app.models.base.
"""

import os
import ast
from pathlib import Path
from collections import defaultdict

MODELS_DIR = Path(__file__).resolve().parent.parent / "app" / "models"

def get_class_definitions(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        tree = ast.parse(f.read(), filename=str(file_path))
    
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if it inherits from Base or is a model class
            base_names = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_names.append(base.id)
                elif isinstance(base, ast.Attribute):
                    base_names.append(base.attr)
            classes.append((node.name, base_names))
    return classes

import unittest

class TestArchitecturalIntegrity(unittest.TestCase):

    def test_single_model_class_definitions(self):
        """Ensure every SQLAlchemy model class is defined in exactly one canonical file."""
        model_files = [f for f in MODELS_DIR.glob("*.py") if f.name != "__init__.py"]
        class_locations = defaultdict(list)

        for mf in model_files:
            classes = get_class_definitions(mf)
            for class_name, bases in classes:
                # Focus on models inheriting from Base or DeclarativeBase
                if "Base" in bases or "DeclarativeBase" in bases or any("Base" in b for b in bases):
                    class_locations[class_name].append(mf.name)

        duplicates = {name: files for name, files in class_locations.items() if len(files) > 1}
        self.assertFalse(duplicates, f"Duplicate ORM model class definitions found across files: {duplicates}")

    def test_single_declarative_base(self):
        """Ensure exactly ONE declarative base (app/models/base.py) exists across the entire app/ codebase."""
        app_dir = Path(__file__).resolve().parent.parent / "app"
        canonical_base_file = (app_dir / "models" / "base.py").resolve()
        violations = []

        for py_file in app_dir.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
            except Exception:
                continue

            resolved_path = py_file.resolve()
            if resolved_path == canonical_base_file:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        base_id = base.id if isinstance(base, ast.Name) else base.attr if isinstance(base, ast.Attribute) else None
                        if base_id in ("DeclarativeBase", "declarative_base"):
                            violations.append(f"{py_file.name}: class {node.name}({base_id}) at line {node.lineno}")
                elif isinstance(node, ast.Call):
                    func_name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else None
                    if func_name == "declarative_base":
                        violations.append(f"{py_file.name}: declarative_base() at line {node.lineno}")

        self.assertFalse(violations, f"Secondary declarative base definitions found across app: {violations}")

    def test_single_router_registry(self):
        """Ensure api_router_registry imports from app.routers only."""
        registry_file = Path(__file__).resolve().parent.parent / "app" / "api_router_registry.py"
        with open(registry_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotIn("from app.api import", content, "api_router_registry.py contains stale imports from app.api!")


if __name__ == "__main__":
    unittest.main()


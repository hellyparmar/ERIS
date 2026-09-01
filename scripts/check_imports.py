"""
AST-based Linter: Check for unused imports and redefined imports in backend/app/
"""

import ast
import os
import sys
from pathlib import Path

def analyze_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
        tree = ast.parse(code, filename=str(filepath))
    except Exception:
        return []

    issues = []
    # Collect imports and usage
    imported_names = {}
    used_names = set()

    class Visitor(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                if name in imported_names:
                    issues.append(f"Line {node.lineno}: Redefined import '{name}'")
                imported_names[name] = node.lineno
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                if name in imported_names:
                    issues.append(f"Line {node.lineno}: Redefined import '{name}'")
                imported_names[name] = node.lineno
            self.generic_visit(node)

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            self.generic_visit(node)

    Visitor().visit(tree)

    # Ignore __init__.py for unused imports
    if not str(filepath).endswith("__init__.py"):
        for name, lineno in imported_names.items():
            if name not in used_names and not name.startswith("_"):
                issues.append(f"Line {lineno}: Unused import '{name}'")

    return issues

def main():
    root = Path(__file__).resolve().parent.parent / "backend" / "app"
    all_issues = {}
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        file_issues = analyze_file(path)
        if file_issues:
            all_issues[path] = file_issues

    print(f"Scanned {sum(1 for _ in root.rglob('*.py'))} files for import issues.")
    if not all_issues:
        print("SUCCESS: Zero unused or redefined import issues found!")
        sys.exit(0)

    print(f"Found issues in {len(all_issues)} files:")
    for path, issues in all_issues.items():
        print(f"\nFile: {path.relative_to(root.parent)}")
        for issue in issues[:10]:  # limit to top 10 per file
            print(f"  {issue}")

if __name__ == "__main__":
    main()

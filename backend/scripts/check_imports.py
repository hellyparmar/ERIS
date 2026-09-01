"""
check_imports.py - Static verification that every import reachable from app.main
actually resolves to a real name in its target module.

Note: Run this BEFORE every rebuild / docker rebuild: python scripts/check_imports.py
Exits non-zero and prints every offending file/import if anything is broken.
This does not require Postgres, Redis, or any installed dependency - it only
parses the Python source with the ast module.
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"


def build_file_index():
    files = {}
    for p in APP.rglob("*.py"):
        if "__pycache__" in str(p):
            continue
        rel = p.relative_to(ROOT)
        parts = list(rel.parts)
        mod = ".".join(parts[:-1] + [parts[-1][:-3]]) if parts[-1] != "__init__.py" else ".".join(parts[:-1])
        files[mod] = p
    return files


def get_imports(path, root):
    try:
        tree = ast.parse(path.read_text(errors="ignore"))
    except Exception:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                base = node.module
            elif node.level > 0:
                pkg_parts = path.relative_to(root).parts[:-1]
                level = node.level
                base_parts = pkg_parts[: len(pkg_parts) - level + 1] if level <= len(pkg_parts) else ()
                base = ".".join(base_parts) + ("." + node.module if node.module else "")
            else:
                base = None
            if base:
                for n in node.names:
                    out.append((base, None if n.name == "*" else n.name))
    return out


def resolve(mod_name, files):
    parts = mod_name.split(".")
    for i in range(len(parts), 0, -1):
        candidate = ".".join(parts[:i])
        if candidate in files:
            return candidate
    return None


def get_defined_names(path):
    try:
        tree = ast.parse(path.read_text(errors="ignore"))
    except Exception:
        return None
    names = set()

    def collect(body):
        for node in body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        names.add(t.id)
                    elif isinstance(t, ast.Tuple):
                        for el in t.elts:
                            if isinstance(el, ast.Name):
                                names.add(el.id)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    names.add(node.target.id)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for a in node.names:
                    names.add(a.asname or a.name.split(".")[0])
            elif isinstance(node, (ast.If, ast.Try)):
                for attr in ("body", "orelse", "finalbody"):
                    sub = getattr(node, attr, None)
                    if sub:
                        collect(sub)
                for h in getattr(node, "handlers", []):
                    collect(h.body)

    collect(tree.body)
    return names


def main():
    files = build_file_index()

    visited = set()
    queue = ["app.main"]
    while queue:
        mod = queue.pop()
        if mod in visited:
            continue
        visited.add(mod)
        path = files.get(mod)
        if not path:
            continue
        for base, name in get_imports(path, ROOT):
            for candidate in ([f"{base}.{name}"] if name else []) + [base]:
                resolved = resolve(candidate, files)
                if resolved and resolved not in visited:
                    queue.append(resolved)

    issues = []
    for mod in visited:
        path = files.get(mod)
        if not path:
            continue
        for base, name in get_imports(path, ROOT):
            if name is None:
                continue
            if f"{base}.{name}" in files:
                continue  # it's a real submodule import, fine
            target_path = files.get(base)
            if not target_path:
                continue  # external package or unresolvable - not our concern here
            defined = get_defined_names(target_path)
            if defined is None:
                continue
            if name not in defined:
                issues.append((str(path.relative_to(ROOT)), base, name))

    issues = sorted(set(issues))
    print(f"Reachable modules from app.main: {len(visited)}")
    print(f"Dangling imports found: {len(issues)}")
    for f, base, name in issues:
        print(f"  {f}: 'from {base} import {name}' - {name} not found in {base}")

    if issues:
        sys.exit(1)
    print("OK - no dangling imports in the live import graph.")
    sys.exit(0)


if __name__ == "__main__":
    main()

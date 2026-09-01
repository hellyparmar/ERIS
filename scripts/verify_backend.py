"""
Backend Integrity & Syntax Verification Script
Pre-commit hook / CI script that runs py_compile across all Python files in the backend.
Fails with exit code 1 if any file fails to compile.
"""

import sys
import os
import py_compile
from pathlib import Path

def main():
    root_dir = Path(__file__).resolve().parent.parent
    backend_dir = root_dir / "backend"
    
    if not backend_dir.exists():
        backend_dir = root_dir  # If run from inside backend/
        
    python_files = []
    for path in backend_dir.rglob("*.py"):
        # Skip __pycache__, .venv, env, and virtualenvs
        parts = path.parts
        if any(p in ("__pycache__", ".venv", "venv", "env", ".git") for p in parts):
            continue
        python_files.append(path)
        
    print(f"Checking syntax for {len(python_files)} Python files in backend...")
    
    errors = []
    for filepath in python_files:
        try:
            py_compile.compile(str(filepath), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append((filepath, str(exc)))
            
    if errors:
        print("\n" + "=" * 60)
        print(f"FAILED: {len(errors)} file(s) failed syntax check:")
        print("=" * 60)
        for filepath, err in errors:
            print(f"  [FAIL] {filepath.relative_to(root_dir)}\n         {err}\n")
        sys.exit(1)
        
    print(f"SUCCESS: All {len(python_files)} Python files compiled cleanly.")
    sys.exit(0)

if __name__ == "__main__":
    main()

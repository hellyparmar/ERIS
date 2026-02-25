#!/usr/bin/env python3
"""
Validate API endpoints - Syntax and Import Check
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def check_module_imports(module_path: str, module_name: str) -> bool:
    """Check if a module can be imported without errors"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} - OK")
        return True
    except SyntaxError as e:
        print(f"❌ {module_name} - SYNTAX ERROR: {e}")
        return False
    except ImportError as e:
        print(f"⚠️  {module_name} - IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ {module_name} - ERROR: {e}")
        return False

def main():
    """Validate all API routers"""
    print("=" * 60)
    print("API ENDPOINT VALIDATION")
    print("=" * 60)
    
    routers = [
        ("api/routers/phase2_gst_db", "Invoice GST API"),
        ("api/routers/phase2_credit_db", "Credit API"),
        ("api/routers/phase2_invoice_db", "Invoice API"),
    ]
    
    results = []
    for module_name, description in routers:
        print(f"\nChecking {description}...")
        try:
            result = check_module_imports(module_name, module_name)
            results.append((description, result))
        except Exception as e:
            print(f"⚠️  {description} - Could not validate: {e}")
            results.append((description, False))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for desc, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {desc}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())

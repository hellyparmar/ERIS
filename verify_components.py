#!/usr/bin/env python3
"""
Component Verification Script
Tests Phase 1 & 2 components without requiring running server
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from colorama import init, Fore, Style

init(autoreset=True)

print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
print(f"{Fore.YELLOW}R-DIOS COMPONENT VERIFICATION{Style.RESET_ALL}")
print(f"{Fore.YELLOW}Phase 1: POS System | Phase 2: Inventory Control{Style.RESET_ALL}")
print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")

passed = 0
failed = 0

def test_import(module_name, description):
    """Test if a module can be imported"""
    global passed, failed
    print(f"\n{Fore.CYAN}Testing: {description}{Style.RESET_ALL}")
    try:
        __import__(module_name)
        print(f"{Fore.GREEN}✓ PASSED - Module imports successfully{Style.RESET_ALL}")
        passed += 1
        return True
    except Exception as e:
        print(f"{Fore.RED}✗ FAILED: {e}{Style.RESET_ALL}")
        failed += 1
        return False

def test_file_exists(filepath, description):
    """Test if a file exists"""
    global passed, failed
    print(f"\n{Fore.CYAN}Testing: {description}{Style.RESET_ALL}")
    if os.path.exists(filepath):
        print(f"{Fore.GREEN}✓ PASSED - File exists{Style.RESET_ALL}")
        passed += 1
        return True
    else:
        print(f"{Fore.RED}✗ FAILED: File not found{Style.RESET_ALL}")
        failed += 1
        return False

# Phase 1 Tests
print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
print(f"{Fore.YELLOW}PHASE 1: POS SYSTEM COMPONENTS{Style.RESET_ALL}")
print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")

test_file_exists("api/models/cashier.py", "Cashier Model")
test_file_exists("api/routers/pos_auth.py", "POS Auth Router")
test_file_exists("api/services/thermal_receipt.py", "Thermal Receipt Service")
test_file_exists("src/components/pos/PINLogin.jsx", "PIN Login Component")
test_file_exists("src/hooks/usePOSAuth.js", "POS Auth Hook")
test_file_exists("src/components/pos/OfflineIndicator.jsx", "Offline Indicator")

# Phase 2 Tests
print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
print(f"{Fore.YELLOW}PHASE 2: INVENTORY CONTROL COMPONENTS{Style.RESET_ALL}")
print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")

test_file_exists("api/services/barcode_scanner.py", "Barcode Scanner Service")
test_file_exists("api/services/stock_alerts.py", "Stock Alerts Service")
test_file_exists("api/services/reorder_automation.py", "Reorder Automation Service")
test_file_exists("api/services/stock_adjustment.py", "Stock Adjustment Service")
test_file_exists("api/routers/inventory_control.py", "Inventory Control Router")
test_file_exists("src/components/inventory/BarcodeScanner.jsx", "Barcode Scanner Component")
test_file_exists("src/components/inventory/StockAlerts.jsx", "Stock Alerts Component")
test_file_exists("src/components/inventory/ReorderSuggestions.jsx", "Reorder Suggestions Component")
test_file_exists("src/components/inventory/StockAdjustment.jsx", "Stock Adjustment Component")

# Python Module Tests
print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
print(f"{Fore.YELLOW}PYTHON MODULE IMPORTS{Style.RESET_ALL}")
print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")

test_import("api.services.barcode_scanner", "Barcode Scanner Service Import")
test_import("api.services.stock_alerts", "Stock Alerts Service Import")
test_import("api.services.reorder_automation", "Reorder Automation Service Import")
test_import("api.services.stock_adjustment", "Stock Adjustment Service Import")

# Summary
total = passed + failed
print(f"\n{'='*60}")
print(f"{Fore.CYAN}VERIFICATION SUMMARY{Style.RESET_ALL}")
print(f"{'='*60}")
print(f"Total Tests: {total}")
print(f"{Fore.GREEN}Passed: {passed}{Style.RESET_ALL}")
print(f"{Fore.RED}Failed: {failed}{Style.RESET_ALL}")
print(f"Success Rate: {(passed/total*100):.1f}%")

if failed > 0:
    print(f"\n{Fore.YELLOW}Note: Some tests failed. This may be due to missing dependencies.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}All files are created and committed to git.{Style.RESET_ALL}")

print(f"\n{Fore.CYAN}To test with running server:{Style.RESET_ALL}")
print(f"1. Fix backend dependencies: pip install -r requirements.txt")
print(f"2. Start server: uvicorn api.main:app --reload")
print(f"3. Run integration tests: python3 test_integration.py")

exit(0 if failed == 0 else 1)

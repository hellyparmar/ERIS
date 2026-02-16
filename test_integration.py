#!/usr/bin/env python3
"""
Integration Test Suite for Phase 1 & 2
Tests backend API endpoints and database operations
"""
import requests
import json
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

API_BASE = "http://localhost:8000"

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def test(self, name, func):
        """Run a test and track results"""
        print(f"\n{Fore.CYAN}Testing: {name}{Style.RESET_ALL}")
        try:
            func()
            print(f"{Fore.GREEN}✓ PASSED{Style.RESET_ALL}")
            self.passed += 1
            self.tests.append((name, True, None))
        except AssertionError as e:
            print(f"{Fore.RED}✗ FAILED: {e}{Style.RESET_ALL}")
            self.failed += 1
            self.tests.append((name, False, str(e)))
        except Exception as e:
            print(f"{Fore.RED}✗ ERROR: {e}{Style.RESET_ALL}")
            self.failed += 1
            self.tests.append((name, False, str(e)))
    
    def summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"{Fore.CYAN}TEST SUMMARY{Style.RESET_ALL}")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"{Fore.GREEN}Passed: {self.passed}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.failed}{Style.RESET_ALL}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%")
        
        if self.failed > 0:
            print(f"\n{Fore.RED}Failed Tests:{Style.RESET_ALL}")
            for name, passed, error in self.tests:
                if not passed:
                    print(f"  - {name}: {error}")

runner = TestRunner()

# ============================================================================
# PHASE 1: POS SYSTEM TESTS
# ============================================================================

def test_cashier_login_valid():
    """Test cashier login with valid PIN"""
    response = requests.post(f"{API_BASE}/auth/pos/login", json={
        "cashier_id": 1,
        "pin": "1234"
    })
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "access_token" in data, "Missing access_token"
    assert "refresh_token" in data, "Missing refresh_token"
    assert data["cashier"]["name"] == "John Doe", "Wrong cashier name"

def test_cashier_login_invalid():
    """Test cashier login with invalid PIN"""
    response = requests.post(f"{API_BASE}/auth/pos/login", json={
        "cashier_id": 1,
        "pin": "0000"
    })
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

def test_pos_checkout():
    """Test POS checkout with thermal receipt"""
    response = requests.post(f"{API_BASE}/pos/checkout", json={
        "items": [
            {"product_id": 1, "quantity": 2, "unit_price": 100}
        ],
        "payment_method": "cash",
        "cashier_id": 1
    })
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == True, "Checkout failed"
    assert "thermal_receipt" in data["data"], "Missing thermal_receipt"
    assert len(data["data"]["thermal_receipt"]) > 0, "Empty thermal receipt"

def test_offline_sync():
    """Test offline transaction sync"""
    response = requests.post(f"{API_BASE}/offline/sync", json={
        "transactions": [
            {
                "offline_id": f"test_{datetime.now().timestamp()}",
                "items": [{"product_id": 1, "quantity": 1, "unit_price": 50}],
                "payment_method": "cash",
                "cashier_id": 1,
                "created_at": datetime.now().isoformat()
            }
        ]
    })
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == True, "Sync failed"
    assert data["synced"] == 1, "Expected 1 synced transaction"

# ============================================================================
# PHASE 2: INVENTORY CONTROL TESTS
# ============================================================================

def test_barcode_scan_valid():
    """Test barcode scanning with valid barcode"""
    response = requests.get(f"{API_BASE}/inventory/scan/1234567890123")
    # May return 404 if barcode doesn't exist, which is expected
    assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
    if response.status_code == 200:
        data = response.json()
        assert data["success"] == True, "Scan failed"
        assert "product" in data["data"], "Missing product data"

def test_barcode_scan_invalid():
    """Test barcode scanning with invalid format"""
    response = requests.get(f"{API_BASE}/inventory/scan/invalid")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

def test_stock_alerts_check():
    """Test stock alerts generation"""
    response = requests.post(f"{API_BASE}/inventory/alerts/check")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == True, "Alert check failed"
    assert "alerts" in data, "Missing alerts data"

def test_stock_alerts_get():
    """Test getting stock alerts"""
    response = requests.get(f"{API_BASE}/inventory/alerts")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == True, "Get alerts failed"
    assert "data" in data, "Missing data"
    assert "alerts" in data["data"], "Missing alerts array"

def test_reorder_suggestions():
    """Test reorder suggestions"""
    response = requests.get(f"{API_BASE}/inventory/reorder-suggestions?min_confidence=0")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == True, "Reorder suggestions failed"
    assert "suggestions" in data["data"], "Missing suggestions"

def test_stock_adjustment_add():
    """Test stock adjustment (add)"""
    response = requests.post(f"{API_BASE}/inventory/adjust", json={
        "product_id": 1,
        "adjustment_type": "add",
        "quantity": 5,
        "reason": "recount",
        "notes": "Integration test",
        "user_id": 1
    })
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == True, "Adjustment failed"
    assert "new_stock_level" in data["data"], "Missing new stock level"

def test_stock_adjustment_history():
    """Test stock adjustment history"""
    response = requests.get(f"{API_BASE}/inventory/adjustments?limit=10")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == True, "Get history failed"
    assert "adjustments" in data["data"], "Missing adjustments"

# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}R-DIOS INTEGRATION TEST SUITE{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Phase 1: POS System | Phase 2: Inventory Control{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    
    # Check if server is running
    try:
        requests.get(f"{API_BASE}/", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}ERROR: Backend server not running at {API_BASE}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Start server with: uvicorn api.main:app --reload{Style.RESET_ALL}")
        exit(1)
    
    print(f"\n{Fore.GREEN}✓ Backend server is running{Style.RESET_ALL}")
    
    # Phase 1 Tests
    print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}PHASE 1: POS SYSTEM TESTS{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    
    runner.test("Cashier Login (Valid PIN)", test_cashier_login_valid)
    runner.test("Cashier Login (Invalid PIN)", test_cashier_login_invalid)
    runner.test("POS Checkout with Thermal Receipt", test_pos_checkout)
    runner.test("Offline Transaction Sync", test_offline_sync)
    
    # Phase 2 Tests
    print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}PHASE 2: INVENTORY CONTROL TESTS{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    
    runner.test("Barcode Scan (Valid)", test_barcode_scan_valid)
    runner.test("Barcode Scan (Invalid)", test_barcode_scan_invalid)
    runner.test("Stock Alerts Check", test_stock_alerts_check)
    runner.test("Stock Alerts Get", test_stock_alerts_get)
    runner.test("Reorder Suggestions", test_reorder_suggestions)
    runner.test("Stock Adjustment (Add)", test_stock_adjustment_add)
    runner.test("Stock Adjustment History", test_stock_adjustment_history)
    
    # Print summary
    runner.summary()
    
    # Exit with appropriate code
    exit(0 if runner.failed == 0 else 1)

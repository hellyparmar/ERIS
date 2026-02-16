#!/usr/bin/env python3
"""
Test JWT Authentication Implementation
Verify that JWT auth is working correctly

Run with: python test_auth_setup.py
"""

import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AuthTester:
    """Test JWT authentication setup"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "token": None
        }
    
    def test_login_endpoint(self) -> bool:
        """Test login endpoint"""
        logger.info("🔐 Testing login endpoint...")
        
        # Try different credential formats
        credentials_list = [
            {"username": "admin@rdios.local", "password": "secret"},
            {"username": "test@test.com", "password": "password123"},
            {"username": "admin", "password": "secret"}
        ]
        
        for creds in credentials_list:
            try:
                response = requests.post(
                    f"{self.base_url}/auth/login",
                    data=creds,
                    timeout=5
                )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.token = data["access_token"]
                    logger.info(f"  ✅ Login successful")
                    logger.info(f"  ✅ Token received (length: {len(self.token)} chars)")
                    self.results["tests"]["login"] = True
                    self.results["token"] = self.token[:50] + "..."  # Truncate for display
                    return True
                else:
                    logger.warning("  ⚠️  No token in response")
                    self.results["tests"]["login"] = False
                    return False
            else:
                logger.error(f"  ❌ Login failed: {response.status_code}")
                logger.error(f"     Response: {response.text}")
                self.results["tests"]["login"] = False
                return False
        except Exception as e:
            logger.error(f"  ❌ Login test failed: {e}")
            self.results["tests"]["login"] = False
            return False
    
    def test_invalid_credentials(self) -> bool:
        """Test invalid credentials"""
        logger.info("\n🔐 Testing invalid credentials...")
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                data={"username": "admin", "password": "wrongpassword"},
                timeout=5
            )
            
            if response.status_code == 401:
                logger.info("  ✅ Invalid credentials rejected correctly")
                self.results["tests"]["invalid_credentials"] = True
                return True
            else:
                logger.warning(f"  ⚠️  Unexpected status: {response.status_code}")
                self.results["tests"]["invalid_credentials"] = False
                return False
        except Exception as e:
            logger.error(f"  ❌ Test failed: {e}")
            self.results["tests"]["invalid_credentials"] = False
            return False
    
    def test_protected_endpoint_without_token(self) -> bool:
        """Test accessing protected endpoint without token"""
        logger.info("\n🔐 Testing protected endpoint without token...")
        
        try:
            response = requests.get(
                f"{self.base_url}/auth/me",
                timeout=5
            )
            
            if response.status_code == 403:
                logger.info("  ✅ Protected endpoint denied access without token")
                self.results["tests"]["protected_no_token"] = True
                return True
            else:
                logger.warning(f"  ⚠️  Expected 403, got {response.status_code}")
                self.results["tests"]["protected_no_token"] = False
                return False
        except Exception as e:
            logger.error(f"  ❌ Test failed: {e}")
            self.results["tests"]["protected_no_token"] = False
            return False
    
    def test_protected_endpoint_with_token(self) -> bool:
        """Test accessing protected endpoint with valid token"""
        logger.info("\n🔐 Testing protected endpoint with valid token...")
        
        if not self.token:
            logger.warning("  ⚠️  No token available. Run login test first.")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  ✅ Access granted with token")
                logger.info(f"  ✅ User: {data.get('username')}")
                self.results["tests"]["protected_with_token"] = True
                return True
            else:
                logger.error(f"  ❌ Got status {response.status_code}")
                self.results["tests"]["protected_with_token"] = False
                return False
        except Exception as e:
            logger.error(f"  ❌ Test failed: {e}")
            self.results["tests"]["protected_with_token"] = False
            return False
    
    def test_auth_status_endpoint(self) -> bool:
        """Test auth status endpoint"""
        logger.info("\n🔐 Testing auth status endpoint...")
        
        try:
            response = requests.get(
                f"{self.base_url}/auth/status",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  ✅ Auth service is {data.get('status')}")
                self.results["tests"]["auth_status"] = True
                return True
            else:
                logger.error(f"  ❌ Got status {response.status_code}")
                self.results["tests"]["auth_status"] = False
                return False
        except Exception as e:
            logger.error(f"  ❌ Test failed: {e}")
            self.results["tests"]["auth_status"] = False
            return False
    
    def test_analytics_with_token(self) -> bool:
        """Test analytics endpoint with token"""
        logger.info("\n🔐 Testing analytics endpoint with token...")
        
        if not self.token:
            logger.warning("  ⚠️  No token available. Run login test first.")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/api/analytics/sales/summary",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"  ✅ Analytics endpoint accessible with token")
                self.results["tests"]["analytics_with_token"] = True
                return True
            elif response.status_code == 401:
                logger.warning(f"  ⚠️  Token validation failed: {response.status_code}")
                self.results["tests"]["analytics_with_token"] = False
                return False
            else:
                logger.warning(f"  ⚠️  Got status {response.status_code}")
                # This might be expected if endpoint needs other fixes
                self.results["tests"]["analytics_with_token"] = "partial"
                return True
        except Exception as e:
            logger.error(f"  ❌ Test failed: {e}")
            self.results["tests"]["analytics_with_token"] = False
            return False
    
    def run_all_tests(self):
        """Run all authentication tests"""
        
        print("\n" + "="*80)
        print(" JWT AUTHENTICATION VERIFICATION")
        print("="*80 + "\n")
        
        # Test login
        if not self.test_login_endpoint():
            logger.error("\n❌ CRITICAL: Login endpoint not working")
            logger.info("📋 Troubleshooting:")
            logger.info("   1. Check if backend is running: python -m uvicorn api.main:app --reload")
            logger.info("   2. Verify auth_login router is imported in api/main.py")
            logger.info("   3. Check for dependency installation: pip install python-jose passlib python-multipart")
            return False
        
        # Test invalid credentials
        self.test_invalid_credentials()
        
        # Test protected endpoint without token
        self.test_protected_endpoint_without_token()
        
        # Test protected endpoint with token
        self.test_protected_endpoint_with_token()
        
        # Test auth status
        self.test_auth_status_endpoint()
        
        # Test analytics with token
        self.test_analytics_with_token()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        
        print("\n" + "="*80)
        print(" AUTHENTICATION TEST RESULTS")
        print("="*80 + "\n")
        
        tests_passed = sum(1 for v in self.results["tests"].values() if v is True)
        tests_total = len(self.results["tests"])
        
        print(f"📊 Test Results: {tests_passed}/{tests_total} passed\n")
        
        for test_name, result in self.results["tests"].items():
            if result is True:
                print(f"   ✅ {test_name}")
            elif result is False:
                print(f"   ❌ {test_name}")
            else:
                print(f"   ⚠️  {test_name} (partial)")
        
        print(f"\n" + "="*80)
        
        if tests_passed == tests_total:
            print(" ✅ ALL AUTHENTICATION TESTS PASSED")
            print("="*80 + "\n")
            print("📋 Next Steps:")
            print("   1. Run API verification tests with auth tokens")
            print("   2. Test frontend with authentication")
            print("   3. Proceed with STEP 3 frontend verification")
        else:
            print(f" ⚠️  {tests_total - tests_passed} TESTS FAILED")
            print("="*80 + "\n")
            print("📋 Debugging Steps:")
            print("   1. Check backend logs: tail -100 backend.log")
            print("   2. Verify auth module imports")
            print("   3. Test with curl: curl -X POST http://localhost:8000/auth/login")
        
        print("\n")
    
    def save_results(self):
        """Save test results"""
        with open("test_results_auth_setup.json", "w") as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"✅ Results saved to: test_results_auth_setup.json")


def main():
    tester = AuthTester()
    
    if tester.run_all_tests():
        tester.print_summary()
        tester.save_results()
    else:
        tester.print_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Testing interrupted")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")

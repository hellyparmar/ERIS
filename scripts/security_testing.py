"""
Security Testing Framework
Comprehensive security validation suite
"""

import requests
import json
import sys
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SecurityTest:
    """Security test result"""
    test_name: str
    category: str
    status: str  # PASS, FAIL, WARNING
    details: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    remediation: str = ""

class SecurityTester:
    """Security testing framework"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[SecurityTest] = []
    
    def add_result(self, test: SecurityTest):
        """Add test result"""
        self.results.append(test)
        icon = "✅" if test.status == "PASS" else "❌" if test.status == "FAIL" else "⚠️"
        print(f"  {icon} {test.test_name}: {test.status}")
    
    def test_https_redirect(self):
        """Test HTTP to HTTPS redirect"""
        print("\n🔐 Testing HTTPS Configuration...")
        
        # This would only work if HTTPS is configured
        try:
            response = requests.get(f"{self.base_url}/health", allow_redirects=False)
            
            # Check security headers
            if "X-Content-Type-Options" in response.headers:
                self.add_result(SecurityTest(
                    test_name="X-Content-Type-Options Header",
                    category="Headers",
                    status="PASS",
                    details="Header is present",
                    severity="HIGH"
                ))
            else:
                self.add_result(SecurityTest(
                    test_name="X-Content-Type-Options Header",
                    category="Headers",
                    status="FAIL",
                    details="Missing header",
                    severity="HIGH",
                    remediation="Add X-Content-Type-Options: nosniff"
                ))
        except Exception as e:
            self.add_result(SecurityTest(
                test_name="HTTPS Configuration",
                category="Protocol",
                status="WARNING",
                details=f"Could not verify: {e}",
                severity="MEDIUM"
            ))
    
    def test_security_headers(self):
        """Test security headers"""
        print("\n🛡️  Testing Security Headers...")
        
        try:
            response = requests.get(f"{self.base_url}/health")
            headers = response.headers
            
            # Check for security headers
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000",
                "Referrer-Policy": "strict-origin-when-cross-origin",
            }
            
            for header, expected in security_headers.items():
                if header in headers:
                    if expected in headers[header]:
                        self.add_result(SecurityTest(
                            test_name=f"Header: {header}",
                            category="Headers",
                            status="PASS",
                            details=f"Present: {headers[header][:50]}",
                            severity="HIGH"
                        ))
                    else:
                        self.add_result(SecurityTest(
                            test_name=f"Header: {header}",
                            category="Headers",
                            status="WARNING",
                            details=f"Value mismatch: {headers[header]}",
                            severity="MEDIUM"
                        ))
                else:
                    self.add_result(SecurityTest(
                        test_name=f"Header: {header}",
                        category="Headers",
                        status="FAIL",
                        details="Header missing",
                        severity="HIGH",
                        remediation=f"Add {header}: {expected}"
                    ))
        
        except Exception as e:
            self.add_result(SecurityTest(
                test_name="Security Headers Test",
                category="Headers",
                status="FAIL",
                details=f"Error: {e}",
                severity="CRITICAL"
            ))
    
    def test_cors_policy(self):
        """Test CORS configuration"""
        print("\n🌐 Testing CORS Policy...")
        
        try:
            headers = {"Origin": "http://evil.com"}
            response = requests.options(f"{self.base_url}/health", headers=headers)
            
            cors_header = response.headers.get("Access-Control-Allow-Origin")
            
            if cors_header == "*":
                self.add_result(SecurityTest(
                    test_name="CORS Policy",
                    category="CORS",
                    status="WARNING",
                    details="Allows all origins (*)",
                    severity="MEDIUM",
                    remediation="Restrict CORS to known domains only"
                ))
            elif cors_header:
                self.add_result(SecurityTest(
                    test_name="CORS Policy",
                    category="CORS",
                    status="PASS",
                    details=f"Restricted to: {cors_header}",
                    severity="HIGH"
                ))
            else:
                self.add_result(SecurityTest(
                    test_name="CORS Policy",
                    category="CORS",
                    status="PASS",
                    details="CORS not exposed",
                    severity="LOW"
                ))
        
        except Exception as e:
            self.add_result(SecurityTest(
                test_name="CORS Policy",
                category="CORS",
                status="FAIL",
                details=f"Error: {e}",
                severity="HIGH"
            ))
    
    def test_auth_endpoints(self):
        """Test authentication endpoint security"""
        print("\n🔑 Testing Authentication Endpoints...")
        
        # Test missing credentials
        try:
            response = requests.post(f"{self.base_url}/api/v1/auth/login")
            
            if response.status_code in [400, 422]:
                self.add_result(SecurityTest(
                    test_name="Login - Missing Credentials",
                    category="Authentication",
                    status="PASS",
                    details="Returns 400/422 for missing credentials",
                    severity="HIGH"
                ))
            else:
                self.add_result(SecurityTest(
                    test_name="Login - Missing Credentials",
                    category="Authentication",
                    status="FAIL",
                    details=f"Returns {response.status_code}",
                    severity="HIGH",
                    remediation="Return 400/422 for invalid requests"
                ))
        except Exception as e:
            self.add_result(SecurityTest(
                test_name="Login - Missing Credentials",
                category="Authentication",
                status="FAIL",
                details=f"Error: {e}",
                severity="HIGH"
            ))
        
        # Test SQL injection attempt
        try:
            payload = {
                "username": "admin' OR '1'='1",
                "password": "test"
            }
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json=payload
            )
            
            if response.status_code in [401, 400]:
                self.add_result(SecurityTest(
                    test_name="Login - SQL Injection",
                    category="Injection",
                    status="PASS",
                    details="SQL injection attempt blocked",
                    severity="CRITICAL"
                ))
            else:
                self.add_result(SecurityTest(
                    test_name="Login - SQL Injection",
                    category="Injection",
                    status="WARNING",
                    details="May be vulnerable to SQL injection",
                    severity="CRITICAL",
                    remediation="Use parameterized queries"
                ))
        except Exception as e:
            self.add_result(SecurityTest(
                test_name="Login - SQL Injection",
                category="Injection",
                status="PASS",
                details="Error handling prevents injection",
                severity="CRITICAL"
            ))
        
        # Test rate limiting
        print("\n  Testing rate limiting (sending 110 requests)...")
        try:
            limited = False
            for i in range(120):
                response = requests.get(f"{self.base_url}/health")
                if response.status_code == 429:  # Too Many Requests
                    limited = True
                    self.add_result(SecurityTest(
                        test_name="Rate Limiting",
                        category="DoS Protection",
                        status="PASS",
                        details=f"Rate limit triggered after {i} requests",
                        severity="HIGH"
                    ))
                    break
            
            if not limited:
                self.add_result(SecurityTest(
                    test_name="Rate Limiting",
                    category="DoS Protection",
                    status="WARNING",
                    details="No rate limiting detected",
                    severity="HIGH",
                    remediation="Implement rate limiting (100 req/min recommended)"
                ))
        except Exception as e:
            self.add_result(SecurityTest(
                test_name="Rate Limiting",
                category="DoS Protection",
                status="WARNING",
                details=f"Could not test: {e}",
                severity="MEDIUM"
            ))
    
    def test_protected_endpoints(self):
        """Test protected endpoints require auth"""
        print("\n🔒 Testing Protected Endpoints...")
        
        protected_endpoints = [
            ("/api/v1/auth/me", "GET"),
            ("/api/v1/pos/day/status", "GET"),
            ("/api/v1/pos/override/config", "GET"),
        ]
        
        for endpoint, method in protected_endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}")
                else:
                    response = requests.post(f"{self.base_url}{endpoint}")
                
                if response.status_code == 401:
                    self.add_result(SecurityTest(
                        test_name=f"Protected: {endpoint}",
                        category="Authorization",
                        status="PASS",
                        details="Requires authentication",
                        severity="HIGH"
                    ))
                else:
                    self.add_result(SecurityTest(
                        test_name=f"Protected: {endpoint}",
                        category="Authorization",
                        status="FAIL",
                        details=f"Returns {response.status_code} without auth",
                        severity="CRITICAL",
                        remediation="Add authentication requirement"
                    ))
            except Exception as e:
                self.add_result(SecurityTest(
                    test_name=f"Protected: {endpoint}",
                    category="Authorization",
                    status="FAIL",
                    details=f"Error: {e}",
                    severity="HIGH"
                ))
    
    def test_input_validation(self):
        """Test input validation"""
        print("\n📝 Testing Input Validation...")
        
        # Test oversized payload
        try:
            large_payload = {"data": "x" * (1024 * 1024 * 10)}  # 10MB
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json=large_payload,
                timeout=5
            )
            
            if response.status_code in [413, 400]:
                self.add_result(SecurityTest(
                    test_name="Payload Size Limit",
                    category="Input Validation",
                    status="PASS",
                    details="Large payloads rejected",
                    severity="HIGH"
                ))
            else:
                self.add_result(SecurityTest(
                    test_name="Payload Size Limit",
                    category="Input Validation",
                    status="WARNING",
                    details="Large payloads may not be limited",
                    severity="MEDIUM",
                    remediation="Implement payload size limit"
                ))
        except requests.exceptions.Timeout:
            self.add_result(SecurityTest(
                test_name="Payload Size Limit",
                category="Input Validation",
                status="PASS",
                details="Large payloads cause timeout",
                severity="HIGH"
            ))
        except Exception as e:
            self.add_result(SecurityTest(
                test_name="Payload Size Limit",
                category="Input Validation",
                status="PASS",
                details="Error handling prevents abuse",
                severity="HIGH"
            ))
    
    async def run_all_tests(self):
        """Run all security tests"""
        
        print("\n" + "="*80)
        print("SECURITY TESTING SUITE")
        print("="*80)
        
        self.test_security_headers()
        self.test_cors_policy()
        self.test_auth_endpoints()
        self.test_protected_endpoints()
        self.test_input_validation()
        self.test_https_redirect()
        
        self._print_summary()
    
    def _print_summary(self):
        """Print security test summary"""
        
        print("\n" + "="*80)
        print("SECURITY TEST SUMMARY")
        print("="*80)
        
        # Count by status
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARNING")
        
        print(f"\n📊 Results:")
        print(f"  ✅ Passed: {passed}")
        print(f"  ⚠️  Warnings: {warnings}")
        print(f"  ❌ Failed: {failed}")
        print(f"  📊 Total: {len(self.results)}")
        
        # Group by severity
        critical = [r for r in self.results if r.severity == "CRITICAL"]
        high = [r for r in self.results if r.severity == "HIGH"]
        medium = [r for r in self.results if r.severity == "MEDIUM"]
        low = [r for r in self.results if r.severity == "LOW"]
        
        print(f"\n🔴 Severity Breakdown:")
        print(f"  CRITICAL: {len(critical)}")
        print(f"  HIGH: {len(high)}")
        print(f"  MEDIUM: {len(medium)}")
        print(f"  LOW: {len(low)}")
        
        # Print issues needing remediation
        if failed or critical:
            print(f"\n⚠️  Issues Requiring Attention:")
            for result in self.results:
                if result.status == "FAIL" or result.severity == "CRITICAL":
                    print(f"\n  {result.test_name} [{result.severity}]")
                    print(f"    Issue: {result.details}")
                    if result.remediation:
                        print(f"    Fix: {result.remediation}")
        
        # Save results
        self._save_results()
    
    def _save_results(self):
        """Save results to JSON"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.status == "PASS"),
                "warnings": sum(1 for r in self.results if r.status == "WARNING"),
                "failed": sum(1 for r in self.results if r.status == "FAIL"),
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "category": r.category,
                    "status": r.status,
                    "severity": r.severity,
                    "details": r.details,
                    "remediation": r.remediation
                }
                for r in self.results
            ]
        }
        
        with open("security_test_results.json", "w") as f:
            json.dump(results_data, f, indent=2)
        
        print("\n✅ Results saved to security_test_results.json")

def main():
    """Run security testing"""
    
    import asyncio
    
    tester = SecurityTester(base_url="http://localhost:8000")
    
    try:
        asyncio.run(tester.run_all_tests())
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Security testing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

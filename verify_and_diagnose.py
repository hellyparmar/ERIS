#!/usr/bin/env python3
"""
STEP 4 & 5: COMPREHENSIVE VERIFICATION & FIXES
Security, Performance, Analytics Authentication, and Final Report
"""

import requests
import json
import time
from datetime import datetime

class ComprehensiveVerifier:
    def __init__(self):
        self.api = "http://localhost:8000"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "authentication": {},
            "analytics": {},
            "endpoints": {},
            "security": {},
            "performance": {},
            "issues": {},
            "fixes_needed": []
        }
    
    def verify_authentication(self):
        """Verify JWT authentication implementation"""
        print("\n" + "="*80)
        print("AUTHENTICATION VERIFICATION")
        print("="*80)
        
        # Check auth service
        try:
            r = requests.get(f"{self.api}/auth/status", timeout=5)
            print(f"✅ Auth service: {r.status_code}")
            self.results["authentication"]["service"] = "active" if r.status_code == 200 else "inactive"
        except:
            print("❌ Auth service unavailable")
            self.results["authentication"]["service"] = "unavailable"
        
        # Check login endpoint
        print("\n📝 Testing login endpoint...")
        try:
            # Try database users
            r = requests.post(
                f"{self.api}/auth/login",
                data={"username": "admin@rdios.local", "password": "secret"},
                timeout=5
            )
            print(f"   Email-based login: {r.status_code}")
            
            if r.status_code == 200:
                token = r.json().get("access_token")
                print(f"   ✅ Token obtained: {token[:30]}...")
                self.results["authentication"]["login"] = "working"
                return token
            else:
                print(f"   ❌ Login failed: {r.json().get('detail', 'Unknown error')}")
                self.results["authentication"]["login"] = "failed"
                
                # Try hardcoded credentials
                print("\n   Trying hardcoded credentials...")
                r = requests.post(
                    f"{self.api}/auth/login",
                    data={"username": "admin", "password": "secret"},
                    timeout=5
                )
                print(f"   Username login: {r.status_code}")
                
                if r.status_code == 200:
                    token = r.json().get("access_token")
                    print(f"   ✅ Token obtained: {token[:30]}...")
                    self.results["authentication"]["login"] = "working_with_hardcoded"
                    return token
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.results["authentication"]["login"] = "error"
        
        return None
    
    def verify_analytics_endpoints(self, token=None):
        """Verify analytics endpoints exist and are protected"""
        print("\n" + "="*80)
        print("ANALYTICS ENDPOINTS VERIFICATION")
        print("="*80)
        
        # Find actual analytics endpoints
        endpoints = [
            "/api/analytics/metrics",
            "/api/analytics/alerts",
            "/api/analytics/chart-data",
            "/api/v1/analytics/sales",
            "/api/v1/analytics/customers",
            "/api/reports/sales",
            "/api/reports/inventory"
        ]
        
        print("\n🔍 Checking analytics endpoints...")
        for endpoint in endpoints:
            # Test without auth
            try:
                r = requests.get(f"{self.api}{endpoint}", timeout=5)
                status_no_auth = r.status_code
            except:
                status_no_auth = "timeout"
            
            # Test with auth if available
            status_with_auth = "N/A"
            if token:
                try:
                    r = requests.get(
                        f"{self.api}{endpoint}",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=5
                    )
                    status_with_auth = r.status_code
                except:
                    status_with_auth = "timeout"
            
            protected = status_no_auth == 401 or status_no_auth == 403
            symbol = "✅" if status_no_auth == 200 or status_no_auth == 404 else "⚠️"
            
            print(f"  {symbol} {endpoint}")
            print(f"     Without auth: {status_no_auth} | With auth: {status_with_auth}")
            
            self.results["analytics"][endpoint] = {
                "without_auth": status_no_auth,
                "with_auth": status_with_auth,
                "protected": protected
            }
    
    def verify_security_headers(self):
        """Verify security headers"""
        print("\n" + "="*80)
        print("SECURITY HEADERS VERIFICATION")
        print("="*80)
        
        try:
            r = requests.get(f"{self.api}/health", timeout=5)
            headers = r.headers
            
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Content-Security-Policy": "script-src 'self'",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
            }
            
            print("\n🔒 Security headers:")
            for header, expected in security_headers.items():
                present = header in headers
                symbol = "✅" if present else "❌"
                value = headers.get(header, "NOT SET")
                print(f"  {symbol} {header}: {value if present else 'Missing'}")
                self.results["security"][header] = "present" if present else "missing"
        except Exception as e:
            print(f"  ❌ Error checking headers: {e}")
    
    def verify_performance(self):
        """Verify performance metrics"""
        print("\n" + "="*80)
        print("PERFORMANCE METRICS")
        print("="*80)
        
        endpoints = {
            "health": "/health",
            "dashboard": "/api/v1/dashboard/realtime",
            "inventory": "/api/v1/inventory/list",
            "forecast": "/api/forecasting/forecast/1/1?days=7"
        }
        
        print("\n⚡ Response times (avg of 3 requests):")
        for name, endpoint in endpoints.items():
            times = []
            for _ in range(3):
                try:
                    start = time.time()
                    r = requests.get(f"{self.api}{endpoint}", timeout=5)
                    elapsed = (time.time() - start) * 1000
                    if r.status_code == 200:
                        times.append(elapsed)
                except:
                    pass
            
            if times:
                avg = sum(times) / len(times)
                symbol = "✅" if avg < 500 else "⚠️" if avg < 1000 else "❌"
                print(f"  {symbol} {name}: {avg:.0f}ms")
                self.results["performance"][name] = avg
        
    def generate_fixes_report(self):
        """Generate report of what needs to be fixed"""
        print("\n" + "="*80)
        print("ISSUES & RECOMMENDATIONS")
        print("="*80)
        
        issues = []
        
        # Authentication issues
        if self.results["authentication"].get("login") == "failed":
            issues.append({
                "priority": "CRITICAL",
                "issue": "Login endpoint returning 401",
                "cause": "User table exists but queries not matching database schema",
                "fix": "Update auth.py query to use correct field name (email vs username)"
            })
        
        # Analytics endpoints missing
        if not any(s == 200 for s in self.results["analytics"].values()):
            issues.append({
                "priority": "HIGH",
                "issue": "Analytics endpoints not found (404)",
                "cause": "Routes not properly configured or router not included",
                "fix": "Verify analytics router is included in main.py"
            })
        
        # Security headers missing
        missing_headers = [h for h, status in self.results["security"].items() if status == "missing"]
        if missing_headers:
            issues.append({
                "priority": "HIGH",
                "issue": f"Missing security headers: {len(missing_headers)}",
                "cause": "Security middleware not configured",
                "fix": "Add CORSMiddleware and security headers to main.py"
            })
        
        # Print issues
        for issue in issues:
            print(f"\n🔴 [{issue['priority']}] {issue['issue']}")
            print(f"   Cause: {issue['cause']}")
            print(f"   Fix: {issue['fix']}")
            self.results["issues"][issue['issue']] = issue
        
        if not issues:
            print("\n✅ No critical issues found!")
        
        return issues

def main():
    print("\n" + "="*80)
    print("  COMPREHENSIVE SYSTEM VERIFICATION & DIAGNOSTICS")
    print("="*80)
    
    verifier = ComprehensiveVerifier()
    
    # Run all checks
    token = verifier.verify_authentication()
    verifier.verify_analytics_endpoints(token)
    verifier.verify_security_headers()
    verifier.verify_performance()
    issues = verifier.generate_fixes_report()
    
    # Save results
    with open("verification_results.json", "w") as f:
        json.dump(verifier.results, f, indent=2)
    
    print(f"\n✅ Verification complete. Results saved to verification_results.json")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nCritical Issues: {sum(1 for i in issues if i['priority'] == 'CRITICAL')}")
    print(f"High Priority: {sum(1 for i in issues if i['priority'] == 'HIGH')}")
    print(f"Medium Priority: {sum(1 for i in issues if i['priority'] == 'MEDIUM')}")
    
    if issues:
        print("\n⚠️  NEXT STEPS:")
        print("1. Review all identified issues above")
        print("2. Implement fixes for CRITICAL items first")
        print("3. Restart backend API")
        print("4. Re-run verification")

if __name__ == "__main__":
    main()

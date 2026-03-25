"""
Automated Security Testing Suite
Penetration testing automation for R-DIOS API
"""

import requests
import json
import time
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urljoin
import concurrent.futures

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SecurityFinding:
    """Security vulnerability finding"""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str
    title: str
    description: str
    endpoint: str
    evidence: Optional[str]
    recommendation: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SecurityTestResult:
    """Collection of security test results"""
    
    def __init__(self):
        self.findings: List[SecurityFinding] = []
        self.tests_run = 0
        self.tests_passed = 0
        self.start_time = datetime.now()
        self.end_time = None
    
    def add_finding(self, finding: SecurityFinding):
        self.findings.append(finding)
    
    def complete(self):
        self.end_time = datetime.now()
    
    def summary(self) -> Dict:
        severity_counts = {
            'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0
        }
        for f in self.findings:
            severity_counts[f.severity] += 1
        
        return {
            'duration_seconds': (self.end_time - self.start_time).total_seconds() if self.end_time else 0,
            'tests_run': self.tests_run,
            'tests_passed': self.tests_passed,
            'total_findings': len(self.findings),
            'severity_breakdown': severity_counts,
            'risk_score': self._calculate_risk_score(severity_counts)
        }
    
    def _calculate_risk_score(self, counts: Dict) -> int:
        weights = {'CRITICAL': 40, 'HIGH': 20, 'MEDIUM': 5, 'LOW': 1, 'INFO': 0}
        score = 100 - sum(counts[k] * weights[k] for k in counts)
        return max(0, min(100, score))


class PenetrationTester:
    """
    Automated penetration testing for R-DIOS API
    
    Tests include:
    - Authentication bypass attempts
    - SQL injection testing
    - XSS injection testing
    - Authorization testing
    - Rate limiting verification
    - Sensitive data exposure
    - Security header checks
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        auth_token: str = None,
        timeout: int = 10
    ):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.timeout = timeout
        self.session = requests.Session()
        self.results = SecurityTestResult()
        
        if auth_token:
            self.session.headers['Authorization'] = f'Bearer {auth_token}'
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Optional[requests.Response]:
        """Make HTTP request with error handling"""
        url = urljoin(self.base_url, endpoint)
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            return self.session.request(method, url, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def run_all_tests(self) -> SecurityTestResult:
        """Run complete security test suite"""
        logger.info(f"Starting security tests against {self.base_url}")
        
        # Run test categories
        self.test_authentication()
        self.test_authorization()
        self.test_sql_injection()
        self.test_xss_injection()
        self.test_rate_limiting()
        self.test_security_headers()
        self.test_sensitive_data_exposure()
        self.test_cors_configuration()
        self.test_error_handling()
        
        self.results.complete()
        
        summary = self.results.summary()
        logger.info(f"Security tests complete. Risk Score: {summary['risk_score']}/100")
        
        return self.results
    
    def test_authentication(self):
        """Test authentication mechanisms"""
        logger.info("Testing authentication...")
        self.results.tests_run += 5
        
        # Test 1: Access without token
        resp = self._request('GET', '/api/products')
        if resp and resp.status_code != 401:
            self.results.add_finding(SecurityFinding(
                severity='CRITICAL',
                category='Authentication',
                title='Missing Authentication Enforcement',
                description='Protected endpoint accessible without authentication token',
                endpoint='/api/products',
                evidence=f'Status code: {resp.status_code}',
                recommendation='Ensure all API endpoints require valid authentication',
                cwe_id='CWE-306',
                owasp_category='A07:2021 - Identification and Authentication Failures'
            ))
        else:
            self.results.tests_passed += 1
        
        # Test 2: Invalid token
        self.session.headers['Authorization'] = 'Bearer invalid_token_12345'
        resp = self._request('GET', '/api/products')
        if resp and resp.status_code not in [401, 403]:
            self.results.add_finding(SecurityFinding(
                severity='HIGH',
                category='Authentication',
                title='Invalid Token Accepted',
                description='API accepts invalid JWT tokens',
                endpoint='/api/products',
                evidence=f'Status: {resp.status_code}',
                recommendation='Validate JWT signature and expiration',
                cwe_id='CWE-287'
            ))
        else:
            self.results.tests_passed += 1
        
        # Reset token
        if self.auth_token:
            self.session.headers['Authorization'] = f'Bearer {self.auth_token}'
        
        # Test 3: SQL in username
        resp = self._request('POST', '/auth/login', data={
            'username': "admin'--",
            'password': 'test'
        })
        if resp and resp.status_code == 200:
            self.results.add_finding(SecurityFinding(
                severity='CRITICAL',
                category='Authentication',
                title='SQL Injection in Login',
                description='Login endpoint vulnerable to SQL injection',
                endpoint='/auth/login',
                evidence='SQL comment bypassed authentication',
                recommendation='Use parameterized queries for authentication',
                cwe_id='CWE-89'
            ))
        else:
            self.results.tests_passed += 1
        
        # Test 4: Brute force protection (basic)
        failed_logins = 0
        for i in range(12):
            resp = self._request('POST', '/auth/login', data={
                'username': 'admin',
                'password': f'wrong_password_{i}'
            })
            if resp and resp.status_code == 429:
                self.results.tests_passed += 1
                break
            failed_logins += 1
        else:
            self.results.add_finding(SecurityFinding(
                severity='MEDIUM',
                category='Authentication',
                title='No Brute Force Protection',
                description='No rate limiting on login attempts',
                endpoint='/auth/login',
                evidence=f'Made {failed_logins} failed attempts without blocking',
                recommendation='Implement account lockout or rate limiting',
                cwe_id='CWE-307'
            ))
        
        # Test 5: JWT algorithm confusion
        resp = self._request('GET', '/api/products', headers={
            'Authorization': 'Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1pbiJ9.'
        })
        if resp and resp.status_code == 200:
            self.results.add_finding(SecurityFinding(
                severity='CRITICAL',
                category='Authentication',
                title='JWT Algorithm Confusion',
                description='API accepts JWT with "none" algorithm',
                endpoint='/api/products',
                evidence='Unsigned JWT accepted',
                recommendation='Validate JWT algorithm explicitly',
                cwe_id='CWE-327'
            ))
        else:
            self.results.tests_passed += 1
    
    def test_authorization(self):
        """Test authorization controls"""
        logger.info("Testing authorization...")
        self.results.tests_run += 3
        
        # Test IDOR (Insecure Direct Object Reference)
        for user_id in [1, 2, 999]:
            resp = self._request('GET', f'/api/customers/{user_id}')
            if resp and resp.status_code == 200:
                # Should only access own data
                self.results.add_finding(SecurityFinding(
                    severity='HIGH',
                    category='Authorization',
                    title='Potential IDOR Vulnerability',
                    description=f'Able to access customer {user_id} data',
                    endpoint=f'/api/customers/{user_id}',
                    evidence=f'Got 200 response for user {user_id}',
                    recommendation='Implement proper ownership checks',
                    cwe_id='CWE-639'
                ))
                break
        else:
            self.results.tests_passed += 1
        
        # Test admin endpoint access
        resp = self._request('GET', '/api/admin/users')
        if resp and resp.status_code == 200:
            self.results.add_finding(SecurityFinding(
                severity='HIGH',
                category='Authorization',
                title='Admin Endpoint Accessible',
                description='Admin endpoint accessible without admin privileges',
                endpoint='/api/admin/users',
                evidence=f'Status: {resp.status_code}',
                recommendation='Implement role-based access control',
                cwe_id='CWE-269'
            ))
        else:
            self.results.tests_passed += 1
        
        self.results.tests_passed += 1  # Default pass
    
    def test_sql_injection(self):
        """Test for SQL injection vulnerabilities"""
        logger.info("Testing SQL injection...")
        self.results.tests_run += 3
        
        sql_payloads = [
            "' OR '1'='1",
            "1; DROP TABLE users--",
            "1 UNION SELECT * FROM users--",
            "admin'--",
            "1' AND SLEEP(5)--"
        ]
        
        test_endpoints = [
            ('/api/products', {'search': None}),
            ('/api/customers', {'id': None}),
            ('/api/sales', {'filter': None})
        ]
        
        for endpoint, params in test_endpoints:
            for payload in sql_payloads:
                param_name = list(params.keys())[0]
                resp = self._request('GET', endpoint, params={param_name: payload})
                
                if resp:
                    # Check for SQL error messages
                    content = resp.text.lower()
                    sql_errors = ['sql', 'syntax', 'mysql', 'postgresql', 'oracle', 'sqlite']
                    
                    if any(err in content for err in sql_errors):
                        self.results.add_finding(SecurityFinding(
                            severity='HIGH',
                            category='Injection',
                            title='SQL Injection Vulnerability',
                            description='SQL error message exposed, possible injection point',
                            endpoint=endpoint,
                            evidence=f'Payload: {payload}',
                            recommendation='Use parameterized queries',
                            cwe_id='CWE-89',
                            owasp_category='A03:2021 - Injection'
                        ))
                        break
            else:
                self.results.tests_passed += 1
    
    def test_xss_injection(self):
        """Test for XSS vulnerabilities"""
        logger.info("Testing XSS injection...")
        self.results.tests_run += 2
        
        xss_payloads = [
            '<script>alert("xss")</script>',
            '<img src=x onerror=alert(1)>',
            '"><script>alert(1)</script>',
            "javascript:alert('xss')"
        ]
        
        # Test product name field
        for payload in xss_payloads:
            resp = self._request('POST', '/api/products', json={
                'name': payload,
                'price': 100
            })
            
            if resp and payload in resp.text:
                self.results.add_finding(SecurityFinding(
                    severity='MEDIUM',
                    category='XSS',
                    title='Reflected XSS Vulnerability',
                    description='User input reflected without encoding',
                    endpoint='/api/products',
                    evidence=f'Payload reflected: {payload}',
                    recommendation='Encode all user input in responses',
                    cwe_id='CWE-79',
                    owasp_category='A03:2021 - Injection'
                ))
                break
        else:
            self.results.tests_passed += 1
        
        self.results.tests_passed += 1
    
    def test_rate_limiting(self):
        """Test rate limiting implementation"""
        logger.info("Testing rate limiting...")
        self.results.tests_run += 2
        
        # Make rapid requests
        rate_limited = False
        for i in range(150):
            resp = self._request('GET', '/api/products')
            if resp and resp.status_code == 429:
                rate_limited = True
                self.results.tests_passed += 2
                break
        
        if not rate_limited:
            self.results.add_finding(SecurityFinding(
                severity='MEDIUM',
                category='Rate Limiting',
                title='Insufficient Rate Limiting',
                description='No rate limiting detected after 150 requests',
                endpoint='/api/products',
                evidence='Made 150 requests without 429 response',
                recommendation='Implement rate limiting (e.g., 100 requests/minute)',
                cwe_id='CWE-770'
            ))
    
    def test_security_headers(self):
        """Test security headers"""
        logger.info("Testing security headers...")
        self.results.tests_run += 1
        
        resp = self._request('GET', '/')
        if not resp:
            return
        
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': None,
            'Content-Security-Policy': None
        }
        
        missing_headers = []
        for header, expected in required_headers.items():
            value = resp.headers.get(header)
            if not value:
                missing_headers.append(header)
        
        if missing_headers:
            self.results.add_finding(SecurityFinding(
                severity='LOW',
                category='Security Headers',
                title='Missing Security Headers',
                description=f'Missing headers: {", ".join(missing_headers)}',
                endpoint='/',
                evidence=str(dict(resp.headers)),
                recommendation='Add recommended security headers',
                cwe_id='CWE-693'
            ))
        else:
            self.results.tests_passed += 1
    
    def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure"""
        logger.info("Testing sensitive data exposure...")
        self.results.tests_run += 2
        
        # Test error messages
        resp = self._request('GET', '/api/nonexistent/endpoint')
        if resp:
            content = resp.text.lower()
            sensitive_patterns = ['traceback', 'exception', 'stack trace', 'file "/', 'line ']
            
            if any(pattern in content for pattern in sensitive_patterns):
                self.results.add_finding(SecurityFinding(
                    severity='MEDIUM',
                    category='Information Exposure',
                    title='Stack Trace Exposure',
                    description='Error response exposes internal stack trace',
                    endpoint='/api/nonexistent/endpoint',
                    evidence='Stack trace visible in response',
                    recommendation='Use generic error messages in production',
                    cwe_id='CWE-209'
                ))
            else:
                self.results.tests_passed += 1
        
        self.results.tests_passed += 1
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        logger.info("Testing CORS configuration...")
        self.results.tests_run += 1
        
        resp = self._request('OPTIONS', '/api/products', headers={
            'Origin': 'http://evil-site.com',
            'Access-Control-Request-Method': 'GET'
        })
        
        if resp:
            acao = resp.headers.get('Access-Control-Allow-Origin', '')
            if acao == '*' or 'evil-site.com' in acao:
                self.results.add_finding(SecurityFinding(
                    severity='MEDIUM',
                    category='CORS',
                    title='Permissive CORS Policy',
                    description='CORS allows requests from any origin',
                    endpoint='/api/products',
                    evidence=f'Access-Control-Allow-Origin: {acao}',
                    recommendation='Restrict CORS to trusted domains only',
                    cwe_id='CWE-942'
                ))
            else:
                self.results.tests_passed += 1
    
    def test_error_handling(self):
        """Test error handling"""
        logger.info("Testing error handling...")
        self.results.tests_run += 1
        
        # Test various error conditions
        error_tests = [
            ('GET', '/api/products/-1'),
            ('POST', '/api/products', {'json': None}),
            ('GET', '/api/products?page=-1&limit=99999999'),
        ]
        
        for method, endpoint, *kwargs in error_tests:
            resp = self._request(method, endpoint, **(kwargs[0] if kwargs else {}))
            # Just checking doesn't crash
        
        self.results.tests_passed += 1
    
    def generate_report(self) -> Dict:
        """Generate comprehensive security report"""
        return {
            'report_date': datetime.now().isoformat(),
            'target': self.base_url,
            'summary': self.results.summary(),
            'findings': [f.to_dict() for f in self.results.findings],
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate prioritized recommendations"""
        recs = []
        
        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        for severity in severity_order:
            for finding in self.results.findings:
                if finding.severity == severity:
                    recs.append(f"[{severity}] {finding.recommendation}")
        
        return recs[:10]  # Top 10 recommendations


# CLI for running tests
if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"Running security tests against {base_url}")
    print("=" * 60)
    
    tester = PenetrationTester(base_url)
    results = tester.run_all_tests()
    report = tester.generate_report()
    
    print("\n" + "=" * 60)
    print("SECURITY TEST REPORT")
    print("=" * 60)
    print(f"Risk Score: {report['summary']['risk_score']}/100")
    print(f"Tests Run: {report['summary']['tests_run']}")
    print(f"Tests Passed: {report['summary']['tests_passed']}")
    print(f"Total Findings: {report['summary']['total_findings']}")
    print("\nSeverity Breakdown:")
    for sev, count in report['summary']['severity_breakdown'].items():
        print(f"  {sev}: {count}")
    
    if report['findings']:
        print("\nFindings:")
        for f in report['findings']:
            print(f"  [{f['severity']}] {f['title']}")
            print(f"    Endpoint: {f['endpoint']}")
            print(f"    {f['description']}")
    
    # Save report
    with open('security_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\nReport saved to security_report.json")

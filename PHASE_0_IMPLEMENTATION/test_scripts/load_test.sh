#!/usr/bin/env python3
"""
Load Testing Script using Apache Bench
Tests API endpoints under load: 100 concurrent users, 10,000 requests
"""

import subprocess
import sys
import os
from datetime import datetime

BASE_URL = os.getenv("API_URL", "http://localhost:8000")
ENDPOINTS = [
    "/api/v1/inventory/list",
    "/api/v1/sales/list",
    "/api/v1/customers/list",
]

CONCURRENT_USERS = 100
TOTAL_REQUESTS = 10000

def run_load_test(endpoint: str) -> dict:
    """Run Apache Bench on an endpoint"""
    
    print(f"\n📊 Testing: {endpoint}")
    print("-" * 60)
    
    url = f"{BASE_URL}{endpoint}"
    cmd = [
        "ab",
        "-n", str(TOTAL_REQUESTS),
        "-c", str(CONCURRENT_USERS),
        "-g", f"results_{endpoint.replace('/', '_')}.tsv",
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse output
        output = result.stdout
        
        # Extract key metrics
        metrics = {
            'endpoint': endpoint,
            'timestamp': datetime.now().isoformat(),
            'requests': TOTAL_REQUESTS,
            'concurrent': CONCURRENT_USERS,
        }
        
        # Parse metrics from output
        for line in output.split('\n'):
            if 'Requests per second' in line:
                metrics['rps'] = line.split(':')[1].strip()
            elif 'Time per request' in line and '[ms]' in line and '(mean)' in line:
                metrics['mean_response_time'] = line.split(':')[1].strip()
            elif 'Failed requests' in line:
                metrics['failed'] = line.split(':')[1].strip()
            elif 'Complete requests' in line:
                metrics['complete'] = line.split(':')[1].strip()
        
        print(output)
        return metrics
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

def main():
    """Run all load tests"""
    
    print("\n" + "=" * 60)
    print("🚀 LOAD TESTING - Enterprise Retail Intelligence")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Concurrent Users: {CONCURRENT_USERS}")
    print(f"Total Requests: {TOTAL_REQUESTS}")
    
    # Check if Apache Bench is installed
    try:
        subprocess.run(["ab", "-h"], capture_output=True)
    except FileNotFoundError:
        print("\n❌ Apache Bench not found. Install with:")
        print("   Ubuntu/Debian: sudo apt-get install apache2-utils")
        print("   macOS: brew install httpd")
        print("   Windows: Download from http://httpd.apache.org/")
        sys.exit(1)
    
    results = []
    
    # Run tests
    for endpoint in ENDPOINTS:
        metrics = run_load_test(endpoint)
        results.append(metrics)
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 LOAD TEST SUMMARY")
    print("=" * 60)
    
    for result in results:
        if result:
            print(f"\n{result['endpoint']}")
            print(f"  Requests/sec: {result.get('rps', 'N/A')}")
            print(f"  Mean response time: {result.get('mean_response_time', 'N/A')}")
            print(f"  Failed requests: {result.get('failed', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ Load testing complete")
    print("=" * 60)

if __name__ == "__main__":
    main()

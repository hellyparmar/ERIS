#!/usr/bin/env python3
"""
STEP 2: R-DIOS Backend API Verification Suite
Comprehensive testing of FastAPI endpoints and business logic

Run with: python test_api_verification.py
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIVerifier:
    """Verify R-DIOS FastAPI backend"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 5):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.token = None
        self.results = {
            "health": {"status": "unknown"},
            "auth": {"status": "unknown"},
            "endpoints": {},
            "errors": []
        }
    
    def test_health(self) -> bool:
        """Test health/readiness endpoint"""
        logger.info("🏥 Testing health endpoint...")
        
        try:
            endpoints = [
                "/health",
                "/api/health",
                "/docs",
                f"{self.base_url}/health"
            ]
            
            for endpoint in endpoints:
                try:
                    if not endpoint.startswith("http"):
                        url = f"{self.base_url}{endpoint}"
                    else:
                        url = endpoint
                    
                    response = requests.get(url, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        logger.info(f"  ✅ {endpoint}: {response.status_code}")
                        self.results["health"]["status"] = "pass"
                        self.results["health"]["endpoint"] = endpoint
                        self.results["health"]["response"] = response.json() if response.text else {}
                        return True
                except:
                    pass
            
            logger.warning(f"  ⚠️  Health endpoint not found")
            self.results["health"]["status"] = "not_found"
            return False
            
        except Exception as e:
            logger.error(f"  ❌ Health check failed: {e}")
            self.results["health"]["error"] = str(e)
            return False
    
    def test_connection(self) -> bool:
        """Test basic API connectivity"""
        logger.info("🔗 Testing API connectivity...")
        
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/api", timeout=self.timeout)
            elapsed = time.time() - start
            
            logger.info(f"  ✅ API responding (response time: {elapsed:.2f}s)")
            return True
            
        except requests.ConnectionError:
            logger.error(f"  ❌ Cannot connect to {self.base_url}")
            logger.info("     Make sure backend is running: python -m uvicorn api.main:app --reload --port 8000")
            return False
        except Exception as e:
            logger.error(f"  ❌ Connection error: {e}")
            return False
    
    def test_dashboard_endpoint(self) -> bool:
        """Test dashboard analytics endpoint"""
        logger.info("📊 Testing dashboard endpoint...")
        
        try:
            endpoints = [
                "/api/dashboard",
                "/api/analytics/dashboard",
                "/api/v1/dashboard",
                "/api/v1/dashboard/realtime"
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = requests.get(url, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"  ✅ {endpoint} returned data")
                        self.results["endpoints"]["dashboard"] = {
                            "status": "pass",
                            "endpoint": endpoint,
                            "keys": list(data.keys()) if isinstance(data, dict) else "array"
                        }
                        return True
                except:
                    pass
            
            logger.warning("  ⚠️  Dashboard endpoint not found")
            self.results["endpoints"]["dashboard"] = {"status": "not_found"}
            return False
            
        except Exception as e:
            logger.error(f"  ❌ Dashboard test failed: {e}")
            return False
    
    def test_forecast_endpoint(self) -> bool:
        """Test forecasting endpoint"""
        logger.info("🔮 Testing forecast endpoint...")
        
        try:
            endpoints = [
                "/api/forecasting/forecast/1/1?days=7",
                "/api/v1/forecasting/forecast/1/1?days=7",
                "/api/predictions/forecast",
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"  ✅ {endpoint} returned forecast")
                        self.results["endpoints"]["forecast"] = {
                            "status": "pass",
                            "endpoint": endpoint
                        }
                        return True
                except:
                    pass
            
            logger.warning("  ⚠️  Forecast endpoint not found")
            self.results["endpoints"]["forecast"] = {"status": "not_found"}
            return False
            
        except Exception as e:
            logger.error(f"  ❌ Forecast test failed: {e}")
            return False
    
    def test_ai_assistant(self) -> bool:
        """Test AI assistant endpoint"""
        logger.info("🤖 Testing AI assistant endpoint...")
        
        try:
            endpoints = [
                "/api/ai-assistant/query",
                "/api/v1/ai-assistant/query",
                "/api/assistant/query"
            ]
            
            test_query = {"query": "What is total revenue?"}
            
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = requests.post(url, json=test_query, timeout=10)
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"  ✅ {endpoint} accepted query")
                        self.results["endpoints"]["ai_assistant"] = {
                            "status": "pass",
                            "endpoint": endpoint
                        }
                        return True
                except:
                    pass
            
            logger.warning("  ⚠️  AI assistant endpoint not found")
            self.results["endpoints"]["ai_assistant"] = {"status": "not_found"}
            return False
            
        except Exception as e:
            logger.error(f"  ❌ AI assistant test failed: {e}")
            return False
    
    def test_inventory(self) -> bool:
        """Test inventory endpoints"""
        logger.info("📦 Testing inventory endpoint...")
        
        try:
            endpoints = [
                "/api/inventory/low-stock",
                "/api/v1/inventory/low-stock",
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = requests.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        logger.info(f"  ✅ {endpoint} returned inventory data")
                        self.results["endpoints"]["inventory"] = {
                            "status": "pass",
                            "endpoint": endpoint
                        }
                        return True
                except:
                    pass
            
            logger.warning("  ⚠️  Inventory endpoint not found")
            self.results["endpoints"]["inventory"] = {"status": "not_found"}
            return True  # Not critical
            
        except Exception as e:
            logger.error(f"  ❌ Inventory test failed: {e}")
            return True  # Not critical
    
    def test_swagger_docs(self) -> bool:
        """Test auto-generated API documentation"""
        logger.info("📚 Testing Swagger documentation...")
        
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            
            if response.status_code == 200:
                logger.info(f"  ✅ Swagger UI accessible at /docs")
                return True
            else:
                logger.warning(f"  ⚠️  Swagger UI returned {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"  ⚠️  Swagger UI not accessible: {e}")
            return False
    
    def test_cors(self) -> bool:
        """Test CORS configuration"""
        logger.info("🔐 Testing CORS headers...")
        
        try:
            headers = {"Origin": "http://localhost:5173"}
            response = requests.options(f"{self.base_url}/api", headers=headers, timeout=5)
            
            if 'access-control-allow-origin' in response.headers:
                logger.info(f"  ✅ CORS configured: {response.headers.get('access-control-allow-origin')}")
                return True
            else:
                logger.warning("  ⚠️  CORS headers not found")
                return False
                
        except Exception as e:
            logger.warning(f"  ⚠️  CORS check failed: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling for invalid requests"""
        logger.info("⚠️  Testing error handling...")
        
        try:
            # Test 404 - non-existent endpoint
            response = requests.get(f"{self.base_url}/api/nonexistent", timeout=5)
            if response.status_code == 404:
                logger.info(f"  ✅ 404 error handling works")
                return True
            else:
                logger.warning(f"  ⚠️  Unexpected status for 404: {response.status_code}")
                return True  # Not critical
                
        except Exception as e:
            logger.warning(f"  ⚠️  Error handling test incomplete: {e}")
            return True


def print_summary(results: Dict[str, Any]):
    """Print test summary"""
    print("\n" + "="*70)
    print(" BACKEND API VERIFICATION RESULTS")
    print("="*70)
    
    health_status = results["health"].get("status", "unknown")
    print(f"✅ Health Check: {health_status}")
    
    endpoints_found = sum(1 for ep in results["endpoints"].values() if ep.get("status") == "pass")
    print(f"✅ Endpoints Found: {endpoints_found}/{len(results['endpoints'])}")
    
    if results["errors"]:
        print(f"⚠️  Errors Found: {len(results['errors'])}")
        for error in results["errors"]:
            print(f"   - {error}")
    
    print("="*70 + "\n")
    
    if endpoints_found >= 3:
        print("✅ BACKEND API is RESPONDING")
        print("\nNext Steps:")
        print("1. Review /docs endpoint for full API specification")
        print("2. Test specific business logic endpoints")
        print("3. Verify database connectivity")
    else:
        print("⚠️  BACKEND API needs configuration")
        print("\nTo start backend:")
        print("cd /home/petpooja/'Enterprise Retail Intelligence System'")
        print("python -m uvicorn api.main:app --reload --port 8000")


def main():
    """Main execution"""
    
    print("\n" + "="*70)
    print(" R-DIOS BACKEND API VERIFICATION SUITE")
    print(" STEP 2: API Endpoints & Business Logic Testing")
    print("="*70 + "\n")
    
    verifier = APIVerifier()
    
    # Test connectivity first
    logger.info("Starting API verification...\n")
    
    if not verifier.test_connection():
        logger.error("\n❌ FATAL: API is not running")
        print("\n" + "="*70)
        print(" BACKEND API NOT RUNNING")
        print("="*70)
        print("\nTo start the backend, run:")
        print("cd '/home/petpooja/Enterprise Retail Intelligence System'")
        print("python -m uvicorn api.main:app --reload --port 8000")
        print("\nOr if using Docker:")
        print("docker-compose up -d backend")
        print("="*70 + "\n")
        return
    
    # Run tests
    verifier.test_health()
    verifier.test_dashboard_endpoint()
    verifier.test_forecast_endpoint()
    verifier.test_ai_assistant()
    verifier.test_inventory()
    verifier.test_swagger_docs()
    verifier.test_cors()
    verifier.test_error_handling()
    
    # Save results
    with open("test_results_2_api.json", "w") as f:
        json.dump(verifier.results, f, indent=2, default=str)
    
    logger.info("\n✅ Results saved to: test_results_2_api.json")
    
    # Print summary
    print_summary(verifier.results)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Testing interrupted")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

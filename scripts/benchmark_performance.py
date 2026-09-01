"""
Performance Benchmarking Suite
Measures response times, throughput, and resource usage
"""

import time
import statistics
import asyncio
import aiohttp
import json
import sys
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class BenchmarkResult:
    """Benchmark test result"""
    test_name: str
    endpoint: str
    method: str
    iterations: int
    response_times: List[float]
    status_codes: List[int]
    errors: int
    
    @property
    def min_time(self) -> float:
        return min(self.response_times) if self.response_times else 0
    
    @property
    def max_time(self) -> float:
        return max(self.response_times) if self.response_times else 0
    
    @property
    def avg_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0
    
    @property
    def median_time(self) -> float:
        return statistics.median(self.response_times) if self.response_times else 0
    
    @property
    def p95_time(self) -> float:
        if len(self.response_times) < 20:
            return self.max_time
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx]
    
    @property
    def p99_time(self) -> float:
        if len(self.response_times) < 100:
            return self.max_time
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[idx]
    
    @property
    def success_rate(self) -> float:
        total = self.iterations
        return ((total - self.errors) / total * 100) if total > 0 else 0
    
    @property
    def throughput(self) -> float:
        """Requests per second"""
        total_time = sum(self.response_times)
        return self.iterations / total_time if total_time > 0 else 0

class PerfBenchmark:
    """Performance benchmarking suite"""
    
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: str = None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.results: List[BenchmarkResult] = []
    
    async def benchmark_endpoint(
        self,
        test_name: str,
        method: str,
        endpoint: str,
        iterations: int = 100,
        payload: Dict = None,
        headers: Dict = None
    ) -> BenchmarkResult:
        """
        Benchmark a single endpoint
        
        Args:
            test_name: Name of the test
            method: HTTP method (GET, POST, etc)
            endpoint: API endpoint path
            iterations: Number of iterations
            payload: Request body for POST/PUT
            headers: Custom headers
        """
        
        print(f"\n📊 Benchmarking: {test_name}")
        print(f"   {method} {endpoint} ({iterations} iterations)")
        
        response_times = []
        status_codes = []
        errors = 0
        
        default_headers = {
            "Content-Type": "application/json"
        }
        
        if self.auth_token:
            default_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if headers:
            default_headers.update(headers)
        
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            for i in range(iterations):
                try:
                    start = time.time()
                    
                    if method.upper() == "GET":
                        async with session.get(url, headers=default_headers, timeout=30) as resp:
                            await resp.read()
                            status_codes.append(resp.status)
                    
                    elif method.upper() == "POST":
                        async with session.post(
                            url,
                            headers=default_headers,
                            json=payload,
                            timeout=30
                        ) as resp:
                            await resp.read()
                            status_codes.append(resp.status)
                    
                    elif method.upper() == "PUT":
                        async with session.put(
                            url,
                            headers=default_headers,
                            json=payload,
                            timeout=30
                        ) as resp:
                            await resp.read()
                            status_codes.append(resp.status)
                    
                    elapsed = time.time() - start
                    response_times.append(elapsed)
                    
                    if (i + 1) % max(1, iterations // 10) == 0:
                        print(f"   Progress: {i+1}/{iterations} ({(i+1)/iterations*100:.0f}%)")
                
                except asyncio.TimeoutError:
                    errors += 1
                    status_codes.append(0)
                    print(f"   ⚠️  Timeout on iteration {i+1}")
                
                except Exception as e:
                    errors += 1
                    status_codes.append(0)
                    print(f"   ⚠️  Error on iteration {i+1}: {e}")
        
        result = BenchmarkResult(
            test_name=test_name,
            endpoint=endpoint,
            method=method,
            iterations=iterations,
            response_times=response_times,
            status_codes=status_codes,
            errors=errors
        )
        
        self.results.append(result)
        self._print_result(result)
        
        return result
    
    def _print_result(self, result: BenchmarkResult):
        """Print benchmark result"""
        print(f"\n   ✅ Results:")
        print(f"      Min: {result.min_time*1000:.2f}ms")
        print(f"      Avg: {result.avg_time*1000:.2f}ms")
        print(f"      Med: {result.median_time*1000:.2f}ms")
        print(f"      P95: {result.p95_time*1000:.2f}ms")
        print(f"      P99: {result.p99_time*1000:.2f}ms")
        print(f"      Max: {result.max_time*1000:.2f}ms")
        print(f"      Throughput: {result.throughput:.1f} req/s")
        print(f"      Success: {result.success_rate:.1f}%")
    
    async def run_full_benchmark(self):
        """Run full benchmark suite"""
        
        print("\n" + "="*80)
        print("ENTERPRISE RETAIL POS - PERFORMANCE BENCHMARKING")
        print("="*80)
        
        # 1. Authentication endpoints
        await self.benchmark_endpoint(
            "Manager Login",
            "POST",
            "/api/v1/auth/login",
            iterations=50,
            payload={"username": "manager", "password": "password"}
        )
        
        await self.benchmark_endpoint(
            "Cashier Login",
            "POST",
            "/api/v1/auth/pos-login",
            iterations=50,
            payload={"employee_id": 1, "pin": "1234"}
        )
        
        # 2. Manager override endpoints
        await self.benchmark_endpoint(
            "Get Override Config",
            "GET",
            "/api/v1/pos/override/config",
            iterations=100
        )
        
        # 3. Day operations
        await self.benchmark_endpoint(
            "Get Day Status",
            "GET",
            "/api/v1/pos/day/status",
            iterations=100
        )
        
        # 4. Inventory endpoints
        await self.benchmark_endpoint(
            "List Inventory (Paginated)",
            "GET",
            "/api/v1/inventory?page=1&per_page=50",
            iterations=100
        )
        
        # 5. Product endpoints
        await self.benchmark_endpoint(
            "List Products",
            "GET",
            "/api/v1/products",
            iterations=100
        )
        
        # 6. Health check
        await self.benchmark_endpoint(
            "Health Check",
            "GET",
            "/health",
            iterations=200
        )
        
        # 7. Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print benchmark summary"""
        
        print("\n" + "="*80)
        print("BENCHMARK SUMMARY")
        print("="*80)
        
        print("\n📊 Performance Metrics:")
        print("-" * 80)
        
        headers = ["Test Name", "Avg (ms)", "P95 (ms)", "P99 (ms)", "Throughput", "Success"]
        print(f"{headers[0]:<25} {headers[1]:>12} {headers[2]:>12} {headers[3]:>12} {headers[4]:>12} {headers[5]:>10}")
        print("-" * 80)
        
        for result in self.results:
            print(
                f"{result.test_name:<25} "
                f"{result.avg_time*1000:>11.2f}ms "
                f"{result.p95_time*1000:>11.2f}ms "
                f"{result.p99_time*1000:>11.2f}ms "
                f"{result.throughput:>11.1f}req/s "
                f"{result.success_rate:>9.1f}%"
            )
        
        # Overall statistics
        all_times = [t for r in self.results for t in r.response_times]
        all_errors = sum(r.errors for r in self.results)
        total_requests = sum(r.iterations for r in self.results)
        
        print("\n" + "-" * 80)
        print("Overall Statistics:")
        print(f"  Total Requests: {total_requests}")
        print(f"  Total Errors: {all_errors}")
        print(f"  Overall Success Rate: {(total_requests - all_errors) / total_requests * 100:.1f}%")
        print(f"  Avg Response Time: {statistics.mean(all_times)*1000:.2f}ms")
        print(f"  Median Response Time: {statistics.median(all_times)*1000:.2f}ms")
        print(f"  P95 Response Time: {sorted(all_times)[int(len(all_times)*0.95)]*1000:.2f}ms")
        print(f"  Total Throughput: {total_requests / sum(sum(r.response_times) for r in self.results) if any(r.response_times for r in self.results) else 0:.1f} req/s")
        
        # Recommendations
        print("\n📝 Recommendations:")
        for result in self.results:
            if result.avg_time > 0.5:
                print(f"  ⚠️  {result.test_name}: Average response time > 500ms")
            if result.success_rate < 99:
                print(f"  ⚠️  {result.test_name}: Success rate < 99%")
            if result.p99_time > 1.0:
                print(f"  ⚠️  {result.test_name}: P99 response time > 1000ms")
        
        # Save results
        self._save_results()
    
    def _save_results(self):
        """Save results to JSON"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "test_name": r.test_name,
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "iterations": r.iterations,
                    "min_time_ms": r.min_time * 1000,
                    "avg_time_ms": r.avg_time * 1000,
                    "median_time_ms": r.median_time * 1000,
                    "p95_time_ms": r.p95_time * 1000,
                    "p99_time_ms": r.p99_time * 1000,
                    "max_time_ms": r.max_time * 1000,
                    "throughput": r.throughput,
                    "success_rate": r.success_rate,
                    "errors": r.errors
                }
                for r in self.results
            ]
        }
        
        with open("benchmark_results.json", "w") as f:
            json.dump(results_data, f, indent=2)
        
        print("\n✅ Results saved to benchmark_results.json")

async def main():
    """Run benchmarking"""
    
    benchmark = PerfBenchmark(base_url="http://localhost:8000")
    
    try:
        await benchmark.run_full_benchmark()
    except Exception as e:
        print(f"\n❌ Benchmarking failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

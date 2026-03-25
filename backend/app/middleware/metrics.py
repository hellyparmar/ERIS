import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Metrics definitions
REQUEST_COUNT = Counter(
    "api_requests_total", 
    "Total number of API requests", 
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "api_request_duration_seconds", 
    "API request latency in seconds", 
    ["method", "endpoint"]
)

ERROR_COUNT = Counter(
    "api_errors_total",
    "Total number of API errors",
    ["method", "endpoint", "status"]
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip metrics for internal/health endpoints if desired
        if request.url.path in ["/metrics", "/api/v1/health"]:
            return await call_next(request)
            
        method = request.method
        endpoint = request.url.path
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status = str(response.status_code)
            
            # Record metrics
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
            
            if response.status_code >= 400:
                ERROR_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
                
            return response
        except Exception as e:
            # Handle unhandled exceptions that break the middleware chain
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status="500").inc()
            ERROR_COUNT.labels(method=method, endpoint=endpoint, status="500").inc()
            raise e

def metrics_endpoint():
    """FastAPI endpoint to export Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

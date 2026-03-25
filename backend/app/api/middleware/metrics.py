"""
Prometheus Metrics Middleware for FastAPI
Tracks request counts, durations, error rates, and custom business metrics.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge
import time

# ---------------------------------------------------------------------------
# Core HTTP Metrics
# ---------------------------------------------------------------------------
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

HTTP_EXCEPTIONS_TOTAL = Counter(
    "http_exceptions_total",
    "Total number of uncaught exceptions",
    ["method", "endpoint", "exception_type"]
)

# ---------------------------------------------------------------------------
# Business & Domain Metrics
# ---------------------------------------------------------------------------
DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"]
)

ML_INFERENCE_DURATION_SECONDS = Histogram(
    "ml_inference_duration_seconds",
    "ML model inference duration in seconds",
    ["model_name"]
)

ACTIVE_USERS_GAUGE = Gauge(
    "active_users_current",
    "Number of currently active users"
)

BACKGROUND_JOBS_TOTAL = Counter(
    "background_jobs_total",
    "Total background jobs executed",
    ["job_name", "status"]
)

# ---------------------------------------------------------------------------
# Middleware Implementation
# ---------------------------------------------------------------------------
class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically collects standard HTTP metrics for Prometheus.
    """
    def __init__(self, app, exclude_paths=None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/metrics", "/health", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip paths we don't want to pollute metrics with
        if any(path.startswith(ex) for ex in self.exclude_paths):
            return await call_next(request)

        # Normalize path for generic graphing (e.g. /api/users/123 -> /api/users/{id})
        # This is basic normalizer; normally you extract exact route from router
        route_path = request.scope.get("route", None)
        endpoint = route_path.path if route_path else path

        # Add generic normalization to keep cardinality low
        if len(endpoint.split("/")) > 4:
            parts = endpoint.split("/")
            if parts[-1].isdigit():
                parts[-1] = "{id}"
                endpoint = "/".join(parts)

        method = request.method
        start_time = time.time()

        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            HTTP_EXCEPTIONS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                exception_type=type(e).__name__
            ).inc()
            raise e
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()
            
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

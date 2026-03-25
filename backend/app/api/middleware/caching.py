"""
Caching Middleware for FastAPI

Automatically adds caching headers to responses and handles cache invalidation
"""

import logging
from typing import Optional, Callable
from datetime import datetime, timedelta
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from app.api.cache.redis_cache import get_cache_manager
    from app.api.optimization.response_optimization import get_response_analyzer, CacheHeaderManager
except ImportError:
    # Fallback if modules don't exist
    get_cache_manager = lambda: None
    get_response_analyzer = lambda: None
    CacheHeaderManager = None

logger = logging.getLogger(__name__)


class CachingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that manages HTTP caching headers
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get the response first
        response = await call_next(request)
        
        # Add cache headers based on endpoint for GET requests
        if request.method == "GET":
            path = request.url.path
            
            # Determine cache strategy based on path
            cache_type = self._get_cache_type(path)
            if cache_type and CacheHeaderManager:
                try:
                    headers = CacheHeaderManager.get_cache_headers(cache_type)
                    for header_name, header_value in headers.items():
                        response.headers[header_name] = header_value
                except Exception as e:
                    logger.debug(f"Could not add cache headers: {e}")
        
        return response
    
    def _get_cache_type(self, path: str) -> Optional[str]:
        """Determine cache type based on endpoint path"""
        if '/products' in path and '/search' not in path:
            return 'products'
        elif '/gst' in path or '/tax' in path:
            return 'gst_rates'
        elif '/loyalty' in path:
            return 'user_profile'
        elif '/inventory' in path:
            return 'inventory'
        elif '/sales' in path and '/analytics' not in path:
            return 'sales'
        elif '/dashboard' in path:
            return 'sales'
        
        return None

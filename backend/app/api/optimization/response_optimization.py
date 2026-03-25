"""
API Response Optimization Module

Optimizes API responses for network efficiency:
- Response compression (gzip, brotli)
- Selective field loading (partial responses)
- Response pagination
- Field filtering
- Automatic serialization optimization
"""

import gzip
import io
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from functools import wraps
import json

logger = logging.getLogger(__name__)


# ============================================================================
# Response Compression
# ============================================================================

class ResponseCompressor:
    """
    Handles response compression for bandwidth optimization
    """
    
    @staticmethod
    def should_compress(response_size_bytes: int, min_size: int = 1000) -> bool:
        """Determine if response should be compressed"""
        return response_size_bytes > min_size
    
    @staticmethod
    def gzip_compress(data: str, compression_level: int = 6) -> bytes:
        """
        Compress response using gzip
        
        Args:
            data: Response data to compress
            compression_level: 1-9, 6 is standard balance
        
        Returns:
            Compressed bytes
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        buffer = io.BytesIO()
        with gzip.GzipFile(
            fileobj=buffer,
            mode='wb',
            compresslevel=compression_level
        ) as f:
            f.write(data)
        
        return buffer.getvalue()
    
    @staticmethod
    def get_compression_info(
        original_size: int,
        compressed_size: int
    ) -> Dict[str, Any]:
        """Get compression statistics"""
        if original_size == 0:
            return {"ratio": 0, "savings_percent": 0}
        
        ratio = original_size / compressed_size if compressed_size > 0 else 0
        savings = ((original_size - compressed_size) / original_size) * 100
        
        return {
            "original_size_bytes": original_size,
            "compressed_size_bytes": compressed_size,
            "compression_ratio": round(ratio, 2),
            "savings_percent": round(savings, 2)
        }


# ============================================================================
# Selective Field Loading (Sparse Fieldsets)
# ============================================================================

class FieldSelector:
    """
    Implements sparse fieldsets - allows clients to request only needed fields
    
    Reduces response payload and improves performance
    """
    
    @staticmethod
    def filter_fields(
        data: Dict[str, Any],
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Filter object to include only specified fields
        
        Usage:
            # Client requests: /api/products?fields=id,name,price
            filtered = FieldSelector.filter_fields(product, ['id', 'name', 'price'])
        """
        if not fields:
            return data
        
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k in fields}
        
        return data
    
    @staticmethod
    def filter_collection(
        items: List[Dict[str, Any]],
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Filter collection of objects"""
        if not fields:
            return items
        
        return [FieldSelector.filter_fields(item, fields) for item in items]
    
    @staticmethod
    def extract_fields_from_query(query_params: Dict[str, str]) -> Optional[List[str]]:
        """
        Extract fields parameter from query string
        
        Usage:
            # From request: GET /api/products?fields=id,name,price
            fields = FieldSelector.extract_fields_from_query(request.query_params)
        """
        if 'fields' in query_params:
            return [f.strip() for f in query_params['fields'].split(',')]
        
        return None


# ============================================================================
# Response Serialization Optimization
# ============================================================================

class SerializationOptimizer:
    """
    Optimizes model serialization for performance
    """
    
    @staticmethod
    def model_to_dict_optimized(
        model_instance,
        exclude_fields: Optional[List[str]] = None,
        include_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Convert model to dict with selective field inclusion
        
        More efficient than loading all fields
        """
        if exclude_fields is None:
            exclude_fields = []
        
        result = {}
        
        for key, value in model_instance.__dict__.items():
            # Skip private attributes
            if key.startswith('_'):
                continue
            
            # Skip excluded fields
            if key in exclude_fields:
                continue
            
            # Include only specified fields if provided
            if include_fields and key not in include_fields:
                continue
            
            # Handle datetime serialization
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            # Handle nested models (avoid recursive serialization overhead)
            elif hasattr(value, '__dict__') and not isinstance(value, (str, int, float, bool)):
                continue  # Skip complex objects
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def collection_to_list_optimized(
        items,
        exclude_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Convert collection of models to list of dicts"""
        return [
            SerializationOptimizer.model_to_dict_optimized(
                item,
                exclude_fields=exclude_fields
            )
            for item in items
        ]


# ============================================================================
# Batch Response Operations
# ============================================================================

class BatchResponseOptimizer:
    """
    Optimizes responses for batch operations
    """
    
    @staticmethod
    def batch_get_response(
        items: List[Dict[str, Any]],
        requested_fields: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Create optimized batch response
        
        Includes pagination, field filtering, and metadata
        """
        # Filter fields if requested
        if requested_fields:
            items = FieldSelector.filter_collection(items, requested_fields)
        
        # Paginate
        total = len(items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = items[start_idx:end_idx]
        
        return {
            "data": paginated_items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            },
            "requested_fields": requested_fields,
            "count": len(paginated_items)
        }
    
    @staticmethod
    def batch_delete_response(
        deleted_ids: List[str],
        errors: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Response for batch delete operations"""
        return {
            "deleted": len(deleted_ids),
            "deleted_ids": deleted_ids,
            "errors": errors or [],
            "error_count": len(errors) if errors else 0,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# Cache Headers Configuration
# ============================================================================

class CacheHeaderManager:
    """
    Manages HTTP cache headers for client-side caching
    """
    
    CACHE_CONTROL_STRATEGIES = {
        "products": {
            "max_age": 3600,  # 1 hour
            "public": True,
            "description": "Product catalog - changes infrequently"
        },
        "gst_rates": {
            "max_age": 86400,  # 24 hours
            "public": True,
            "immutable": True,
            "description": "GST rates - never change within day"
        },
        "sales": {
            "max_age": 0,  # No caching
            "private": True,
            "must_revalidate": True,
            "description": "Sales data - must always be fresh"
        },
        "inventory": {
            "max_age": 600,  # 10 minutes
            "private": True,
            "description": "Inventory levels - moderate cache"
        },
        "user_profile": {
            "max_age": 1800,  # 30 minutes
            "private": True,
            "description": "User data - sensitive, client-side cache only"
        }
    }
    
    @staticmethod
    def get_cache_headers(
        resource_type: str
    ) -> Dict[str, str]:
        """
        Get recommended cache headers for resource type
        
        Usage:
            headers = CacheHeaderManager.get_cache_headers("products")
            return JSONResponse(data, headers=headers)
        """
        config = CacheHeaderManager.CACHE_CONTROL_STRATEGIES.get(
            resource_type,
            {"max_age": 0, "private": True}
        )
        
        directives = []
        
        if config.get("public"):
            directives.append("public")
        if config.get("private"):
            directives.append("private")
        
        directives.append(f"max-age={config['max_age']}")
        
        if config.get("must_revalidate"):
            directives.append("must-revalidate")
        if config.get("immutable"):
            directives.append("immutable")
        
        return {
            "Cache-Control": ", ".join(directives),
            "Vary": "Accept-Encoding"
        }
    
    @staticmethod
    def get_etag(data: str) -> str:
        """Generate ETag for response validation"""
        import hashlib
        return hashlib.md5(data.encode()).hexdigest()


# ============================================================================
# Response Size Analysis
# ============================================================================

class ResponseSizeAnalyzer:
    """
    Analyzes response sizes to identify optimization opportunities
    """
    
    def __init__(self):
        self.response_sizes = []
        self.response_counts = {}
    
    def record_response(
        self,
        endpoint: str,
        size_bytes: int,
        response_time_ms: float
    ) -> None:
        """Record response size and metrics"""
        self.response_sizes.append({
            "endpoint": endpoint,
            "size_bytes": size_bytes,
            "response_time_ms": response_time_ms,
            "timestamp": datetime.now()
        })
        
        if endpoint not in self.response_counts:
            self.response_counts[endpoint] = {
                "count": 0,
                "total_bytes": 0,
                "avg_bytes": 0
            }
        
        stats = self.response_counts[endpoint]
        stats["count"] += 1
        stats["total_bytes"] += size_bytes
        stats["avg_bytes"] = stats["total_bytes"] / stats["count"]
    
    def get_largest_responses(self, limit: int = 10) -> List[Dict]:
        """Get endpoints with largest responses"""
        sorted_responses = sorted(
            self.response_sizes,
            key=lambda x: x["size_bytes"],
            reverse=True
        )
        return sorted_responses[:limit]
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get recommendations for response optimization"""
        recommendations = []
        
        # Find large responses
        large_responses = [
            r for r in self.response_sizes
            if r["size_bytes"] > 100000  # > 100KB
        ]
        
        if large_responses:
            endpoints = set(r["endpoint"] for r in large_responses)
            recommendations.append(
                f"Consider pagination or field filtering for: {', '.join(endpoints)}"
            )
        
        # Find slow responses
        slow_responses = [
            r for r in self.response_sizes
            if r["response_time_ms"] > 1000  # > 1s
        ]
        
        if slow_responses:
            endpoints = set(r["endpoint"] for r in slow_responses)
            recommendations.append(
                f"Optimize query performance for: {', '.join(endpoints)}"
            )
        
        return recommendations


# ============================================================================
# Global Instance
# ============================================================================

_response_analyzer = None

def init_response_analyzer() -> ResponseSizeAnalyzer:
    """Initialize global response analyzer"""
    global _response_analyzer
    _response_analyzer = ResponseSizeAnalyzer()
    return _response_analyzer

def get_response_analyzer() -> Optional[ResponseSizeAnalyzer]:
    """Get global response analyzer"""
    return _response_analyzer

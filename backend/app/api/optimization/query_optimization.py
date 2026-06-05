"""
Database Query Optimization Module

Implements performance optimizations:
- N+1 query detection and prevention
- Batch loading strategies
- Eager loading patterns
- Query result caching
- Index recommendations
"""

import logging
from typing import Dict, List, Any, Set
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
import time

logger = logging.getLogger(__name__)


# ============================================================================
# Query Performance Monitor
# ============================================================================

class QueryPerformanceMonitor:
    """
    Monitors and logs slow queries
    
    Helps identify performance bottlenecks and query optimization opportunities
    """
    
    def __init__(self, slow_query_threshold_ms: float = 100):
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.slow_queries = []
        self.query_stats = {}
    
    def record_query(
        self,
        query_text: str,
        execution_time_ms: float,
        row_count: int = 0
    ) -> None:
        """Record query execution time"""
        if execution_time_ms > self.slow_query_threshold_ms:
            self.slow_queries.append({
                "query": query_text[:100],  # First 100 chars
                "time_ms": round(execution_time_ms, 2),
                "timestamp": datetime.now(),
                "rows": row_count
            })
            
            logger.warning(
                f"Slow query detected ({execution_time_ms:.2f}ms): {query_text[:80]}"
            )
        
        # Track query statistics
        query_hash = hash(query_text)
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                "count": 0,
                "total_time_ms": 0,
                "avg_time_ms": 0,
                "max_time_ms": 0,
                "min_time_ms": float('inf')
            }
        
        stats = self.query_stats[query_hash]
        stats["count"] += 1
        stats["total_time_ms"] += execution_time_ms
        stats["avg_time_ms"] = stats["total_time_ms"] / stats["count"]
        stats["max_time_ms"] = max(stats["max_time_ms"], execution_time_ms)
        stats["min_time_ms"] = min(stats["min_time_ms"], execution_time_ms)
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """Get list of slow queries"""
        return sorted(
            self.slow_queries[-limit:],
            key=lambda x: x["time_ms"],
            reverse=True
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get query statistics"""
        if not self.query_stats:
            return {"total_queries": 0}
        
        total_queries = sum(s["count"] for s in self.query_stats.values())
        total_time = sum(s["total_time_ms"] for s in self.query_stats.values())
        
        return {
            "total_queries": total_queries,
            "total_time_ms": round(total_time, 2),
            "avg_time_per_query_ms": round(total_time / total_queries, 2),
            "unique_queries": len(self.query_stats),
            "slow_queries_count": len(self.slow_queries)
        }
    
    def reset(self) -> None:
        """Reset statistics"""
        self.slow_queries.clear()
        self.query_stats.clear()


# ============================================================================
# Query Optimization Patterns
# ============================================================================

class QueryOptimizer:
    """
    Provides optimized query patterns
    
    Handles:
    - Eager loading to prevent N+1 queries
    - Batch operations
    - Pagination
    - Selective field loading
    """
    
    @staticmethod
    def eager_load_products(session: Session, product_ids: List[str]):
        """
        Eager load products with inventory and pricing
        
        Prevents N+1 queries when loading product details
        """
        from app.api.db.database import Product, Inventory, PricingRule
        from sqlalchemy.orm import joinedload
        
        return session.query(Product).filter(
            Product.id.in_(product_ids)
        ).options(
            joinedload(Product.inventory),
            joinedload(Product.pricing_rules)
        ).all()
    
    @staticmethod
    def get_products_by_tenant_with_inventory(
        session: Session,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0
    ):
        """
        Get products with inventory for a tenant
        
        Uses eager loading to prevent N+1 queries
        """
        from app.api.db.database import Product
        from sqlalchemy.orm import joinedload
        from uuid import UUID
        
        return session.query(Product).filter(
            Product.tenant_id == UUID(tenant_id)
        ).options(
            joinedload(Product.inventory)
        ).limit(limit).offset(offset).all()
    
    @staticmethod
    def batch_get_customer_loyalty_info(
        session: Session,
        customer_ids: List[str],
        tenant_id: str
    ) -> Dict[str, Dict]:
        """
        Batch load loyalty information for multiple customers
        
        Single query instead of N queries
        """
        from app.api.db.database import Customer, LoyaltyPoints
        from sqlalchemy.orm import joinedload
        from uuid import UUID
        
        customers = session.query(Customer).filter(
            Customer.tenant_id == UUID(tenant_id),
            Customer.id.in_([UUID(cid) for cid in customer_ids])
        ).options(
            joinedload(Customer.loyalty_points)
        ).all()
        
        return {
            str(c.id): {
                "name": c.name,
                "email": c.email,
                "loyalty_points": c.loyalty_points.points if c.loyalty_points else 0,
                "tier": c.loyalty_tier
            }
            for c in customers
        }
    
    @staticmethod
    def get_sales_with_details(
        session: Session,
        sale_ids: List[str],
        tenant_id: str
    ):
        """
        Get sales with all related details
        
        Prevents N+1 queries on sale items, customer, and payment info
        """
        from app.api.db.database import Sale, SaleItem
        from sqlalchemy.orm import joinedload
        from uuid import UUID
        
        return session.query(Sale).filter(
            Sale.tenant_id == UUID(tenant_id),
            Sale.id.in_([UUID(sid) for sid in sale_ids])
        ).options(
            joinedload(Sale.items),
            joinedload(Sale.customer),
            joinedload(Sale.payment_info)
        ).all()


# ============================================================================
# Database Indexes Recommendations
# ============================================================================

class IndexRecommendations:
    """
    Recommends database indexes for improved query performance
    """
    
    # Recommended indexes for common queries
    RECOMMENDED_INDEXES = [
        # Tenant-based queries
        {
            "table": "products",
            "columns": ["tenant_id", "category"],
            "reason": "Frequent filtering by tenant and category"
        },
        {
            "table": "sales",
            "columns": ["tenant_id", "created_at"],
            "reason": "Common filtering by tenant and date range"
        },
        {
            "table": "customers",
            "columns": ["tenant_id", "email"],
            "reason": "Email lookup and tenant filtering"
        },
        {
            "table": "inventory",
            "columns": ["tenant_id", "product_id"],
            "reason": "Product inventory queries"
        },
        {
            "table": "sales",
            "columns": ["customer_id"],
            "reason": "Customer sales history"
        },
        {
            "table": "sale_items",
            "columns": ["sale_id"],
            "reason": "Sale details retrieval"
        },
        {
            "table": "loyalty_points",
            "columns": ["customer_id"],
            "reason": "Loyalty points lookup"
        },
        {
            "table": "barcode_lookup",
            "columns": ["barcode"],
            "reason": "Product barcode scanning"
        },
        {
            "table": "audit_logs",
            "columns": ["tenant_id", "timestamp"],
            "reason": "Audit log filtering and time-range queries"
        }
    ]
    
    @staticmethod
    def get_recommendations() -> List[Dict[str, Any]]:
        """Get list of recommended indexes"""
        return IndexRecommendations.RECOMMENDED_INDEXES
    
    @staticmethod
    def generate_index_sql() -> str:
        """Generate SQL to create recommended indexes"""
        sql_statements = []
        
        for index in IndexRecommendations.RECOMMENDED_INDEXES:
            table = index["table"]
            columns = ", ".join(index["columns"])
            index_name = f"idx_{table}_{'_'.join(index['columns'])}"
            
            sql = f"""
CREATE INDEX IF NOT EXISTS {index_name}
ON {table} ({columns});
-- Reason: {index['reason']}
            """
            sql_statements.append(sql)
        
        return "\n".join(sql_statements)


# ============================================================================
# Query Execution Timing Decorator
# ============================================================================

query_monitor = QueryPerformanceMonitor(slow_query_threshold_ms=100)

def monitor_query(func):
    """
    Decorator to monitor query execution time
    
    Usage:
        @monitor_query
        def get_products(db: Session):
            result = await db.execute(select(Product))
            return result.scalars().all()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Get row count if result is iterable
        row_count = len(result) if hasattr(result, '__len__') else 0
        
        query_monitor.record_query(
            query_text=f"{func.__module__}.{func.__name__}",
            execution_time_ms=execution_time_ms,
            row_count=row_count
        )
        
        return result
    
    return wrapper


def get_query_monitor() -> QueryPerformanceMonitor:
    """Get global query monitor"""
    return query_monitor


# ============================================================================
# Pagination Helper
# ============================================================================

class PaginationHelper:
    """
    Helper for efficient pagination
    
    Reduces memory usage by fetching only needed records
    """
    
    @staticmethod
    def paginate_query(
        query,
        page: int = 1,
        page_size: int = 50,
        max_page_size: int = 100
    ) -> tuple:
        """
        Paginate query results
        
        Returns: (items, total_count, has_next)
        """
        # Enforce maximum page size
        page_size = min(page_size, max_page_size)
        page = max(page, 1)
        
        # Get total count (can be expensive)
        total_count = query.count()
        
        # Fetch paginated results
        items = query.limit(page_size).offset(
            (page - 1) * page_size
        ).all()
        
        has_next = (page * page_size) < total_count
        
        return items, total_count, has_next
    
    @staticmethod
    def get_pagination_metadata(
        total_count: int,
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """Generate pagination metadata"""
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "current_page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }


# ============================================================================
# Connection Pooling Configuration
# ============================================================================

class ConnectionPoolConfig:
    """
    Recommended connection pool settings for optimal performance
    """
    
    @staticmethod
    def get_recommended_pool_settings() -> Dict[str, Any]:
        """
        Get recommended SQLAlchemy connection pool settings
        """
        return {
            "pool_size": 20,  # Number of connections to keep in pool
            "max_overflow": 40,  # Maximum overflow connections
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "pool_pre_ping": True,  # Test connections before use
            "echo": False,  # Don't log SQL (too verbose)
            "connect_args": {
                "connect_timeout": 10
            }
        }
    
    @staticmethod
    def get_pool_info() -> str:
        """Get human-readable pool configuration info"""
        settings = ConnectionPoolConfig.get_recommended_pool_settings()
        return f"""
Connection Pool Configuration:
- Pool Size: {settings['pool_size']} connections
- Max Overflow: {settings['max_overflow']} additional connections
- Pool Recycle: {settings['pool_recycle']} seconds (prevents stale connections)
- Pool Pre-ping: {settings['pool_pre_ping']} (prevents connection loss errors)

This configuration ensures:
1. Sufficient connections for concurrent requests
2. Overflow handling for traffic spikes
3. Automatic connection refresh to prevent timeout issues
4. Pre-flight checks to catch connection problems early
        """

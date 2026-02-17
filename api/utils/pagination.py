"""
Pagination utility for R-DIOS API
Prevents crashes from loading massive datasets
"""

from typing import TypeVar, Generic, List, Any, Optional
from pydantic import BaseModel
from fastapi import Query

T = TypeVar('T')

class PaginationParams:
    """Standard pagination query parameters"""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        per_page: int = Query(50, ge=1, le=500, description="Items per page (max 500)")
    ):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page

class PagedResponse(BaseModel, Generic[T]):
    """Standard paginated response"""
    success: bool = True
    data: List[T]
    pagination: dict

def create_paged_response(
    items: List[T],
    page: int,
    per_page: int,
    total: int
) -> dict:
    """Create standard paginated response"""
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    return {
        "success": True,
        "data": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

def paginate_query(query, page: int, per_page: int):
    """Apply pagination to SQLAlchemy query"""
    offset = (page - 1) * per_page
    return query.offset(offset).limit(per_page)

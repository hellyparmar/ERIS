"""
Backend Pagination Service
Handles pagination logic for API endpoints
"""

from typing import TypeVar, Generic, List, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
import time
from datetime import datetime

T = TypeVar('T')

class PaginationMetadata(BaseModel):
    total: int
    limit: int
    offset: int
    page: int
    pages: int
    hasMore: bool
    hasPrevious: bool

class PaginationResponse(BaseModel):
    data: List[Any]
    pagination: PaginationMetadata
    meta: Dict[str, Any]

def paginate(
    query,
    model_class,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    order: str = "desc"
) -> PaginationResponse:
    """
    Paginate query results with metadata
    
    Args:
        query: SQLAlchemy query object
        model_class: Model class being queried
        limit: Items per page (1-250)
        offset: Number of items to skip
        sort_by: Column to sort by
        order: Sort order (asc, desc)
    
    Returns:
        PaginationResponse with data and metadata
    """
    
    start_time = time.time()
    
    # Validate and constrain limit
    limit = min(int(limit), 250)
    limit = max(limit, 1)
    offset = max(int(offset), 0)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting
    if hasattr(model_class, sort_by):
        sort_column = getattr(model_class, sort_by)
        if order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    
    # Apply pagination
    items = query.limit(limit).offset(offset).all()
    
    # Calculate metadata
    total_pages = (total + limit - 1) // limit
    current_page = (offset // limit) + 1
    has_more = offset + limit < total
    has_previous = offset > 0
    
    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000
    
    return PaginationResponse(
        data=items,
        pagination=PaginationMetadata(
            total=total,
            limit=limit,
            offset=offset,
            page=current_page,
            pages=total_pages,
            hasMore=has_more,
            hasPrevious=has_previous,
        ),
        meta={
            "responseTime": f"{response_time_ms:.1f}ms",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )

# Example usage in FastAPI endpoint:
"""
from fastapi import FastAPI, Query, Depends
from sqlalchemy.orm import Session

app = FastAPI()

@app.get("/api/v1/inventory/list")
def get_inventory(
    session: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=250),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", regex="^(created_at|price|product_name)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
):
    from models import Inventory
    
    query = session.query(Inventory)
    result = paginate(query, Inventory, limit, offset, sort_by, order)
    
    return {
        "data": [item.to_dict() for item in result.data],
        "pagination": result.pagination.dict(),
        "meta": result.meta
    }
"""

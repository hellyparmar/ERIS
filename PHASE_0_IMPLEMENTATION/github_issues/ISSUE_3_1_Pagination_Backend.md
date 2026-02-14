# Task 3.1: Pagination Implementation - Backend
**Owner:** Backend Lead  
**Duration:** 5 hours  
**Deadline:** Feb 19, 9:00 AM IST  
**Priority:** 🟡 HIGH (Blocks inventory loading)  
**Phase:** Phase 0 - Critical Blockers  
**Depends On:** #1.4 API Testing, #2.1 Environment Config

---

## Description

Implement server-side pagination for inventory endpoint. Currently system crashes when trying to load all 26K products at once. Implement `limit` and `offset` parameters with proper sorting and metadata.

## Acceptance Criteria

- [ ] Endpoint: `GET /api/v1/inventory/list?limit=50&offset=0`
- [ ] Returns paginated results with metadata (total, page, hasMore)
- [ ] Default limit: 50, max limit: 250
- [ ] Supports sorting: by name, by stock level, by price
- [ ] All 528 pages load successfully (26.4K products ÷ 50)
- [ ] Response time < 200ms per page
- [ ] Tested with load: 100 concurrent requests
- [ ] Database indexes optimized
- [ ] API documentation updated

## Endpoint Specification

### Request
```
GET /api/v1/inventory/list?limit=50&offset=0&sort=name&order=asc
```

### Response
```json
{
  "data": [
    {
      "id": 1,
      "product_name": "Product A",
      "sku": "SKU001",
      "current_stock": 100,
      "status": "active",
      "price": 299.99,
      "last_updated": "2024-02-14T10:00:00Z"
    },
    // ... 49 more items
  ],
  "pagination": {
    "total": 26420,
    "limit": 50,
    "offset": 0,
    "page": 1,
    "pages": 529,
    "hasMore": true,
    "hasPrevious": false
  },
  "meta": {
    "responseTime": "45ms",
    "timestamp": "2024-02-14T10:00:00Z"
  }
}
```

## Implementation

### Step 1: Update Database Schema
```sql
-- Create composite indexes for pagination
CREATE INDEX idx_inventory_product_status 
ON inventory(product_id, status, stock_level);

CREATE INDEX idx_inventory_created 
ON inventory(created_at DESC);

CREATE INDEX idx_inventory_price 
ON inventory(price DESC);

-- Verify indexes created
SELECT * FROM pg_stat_user_indexes WHERE relname LIKE 'idx_inventory%';
```

### Step 2: Update SQLAlchemy Model
```python
# In models.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, index=True)
    product_name = Column(String(255), index=True)
    sku = Column(String(50), unique=True)
    current_stock = Column(Integer)
    status = Column(String(50), index=True)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### Step 3: Create Pagination Service
```python
# In services/pagination.py
from typing import Generic, TypeVar, List
from pydantic import BaseModel
from sqlalchemy.orm import Session

T = TypeVar('T')

class PaginationResponse(BaseModel):
    data: List[T]
    pagination: dict
    meta: dict

def paginate(
    query,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    order: str = "desc"
) -> dict:
    """
    Paginate query results with metadata
    """
    import time
    start_time = time.time()
    
    # Validate limit
    limit = min(int(limit), 250)
    limit = max(limit, 1)
    offset = max(int(offset), 0)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    if order.lower() == "desc":
        query = query.order_by(getattr(Inventory, sort_by).desc())
    else:
        query = query.order_by(getattr(Inventory, sort_by).asc())
    
    # Apply pagination
    items = query.limit(limit).offset(offset).all()
    
    # Calculate pagination metadata
    total_pages = (total + limit - 1) // limit
    current_page = (offset // limit) + 1
    has_more = offset + limit < total
    has_previous = offset > 0
    
    response_time = f"{(time.time() - start_time) * 1000:.1f}ms"
    
    return {
        "data": items,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "page": current_page,
            "pages": total_pages,
            "hasMore": has_more,
            "hasPrevious": has_previous,
        },
        "meta": {
            "responseTime": response_time,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
```

### Step 4: Create API Endpoint
```python
# In main.py or routes/inventory.py
from fastapi import FastAPI, Query
from sqlalchemy.orm import Session

app = FastAPI()

@app.get("/api/v1/inventory/list")
def get_inventory(
    session: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=250),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", regex="^(created_at|price|product_name|current_stock)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    status: str = Query(None)  # Optional filter
):
    """
    List inventory with pagination
    
    - **limit**: Items per page (1-250, default 50)
    - **offset**: Number of items to skip (default 0)
    - **sort_by**: Sort column (created_at, price, product_name, current_stock)
    - **order**: Sort order (asc, desc)
    - **status**: Filter by status (active, inactive)
    """
    
    query = session.query(Inventory)
    
    # Apply optional filters
    if status:
        query = query.filter(Inventory.status == status)
    
    # Paginate and return
    result = paginate(query, limit, offset, sort_by, order)
    
    return {
        "data": [item.to_dict() for item in result["data"]],
        "pagination": result["pagination"],
        "meta": result["meta"]
    }
```

### Step 5: Add Serialization
```python
# In models.py
class Inventory(Base):
    # ... existing fields ...
    
    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "sku": self.sku,
            "current_stock": self.current_stock,
            "status": self.status,
            "price": self.price,
            "last_updated": self.updated_at.isoformat() + "Z" if self.updated_at else None
        }
```

## Testing Pagination

### Test All 528 Pages
```bash
#!/bin/bash
# test_all_pages.sh

FAILED=0
TOTAL=0

for page in {0..527}; do
    OFFSET=$((page * 50))
    RESPONSE=$(curl -s "http://localhost:8000/api/v1/inventory/list?limit=50&offset=$OFFSET")
    
    # Check if response is valid JSON
    if ! echo "$RESPONSE" | jq . > /dev/null 2>&1; then
        echo "❌ Page $page: Invalid JSON"
        ((FAILED++))
    fi
    
    # Check if has data
    DATA_LENGTH=$(echo "$RESPONSE" | jq '.data | length')
    if [ "$DATA_LENGTH" -eq 0 ]; then
        echo "❌ Page $page: Empty data"
        ((FAILED++))
    fi
    
    ((TOTAL++))
    
    if [ $((TOTAL % 100)) -eq 0 ]; then
        echo "✅ Tested $TOTAL/528 pages"
    fi
done

echo ""
echo "Test Results:"
echo "✅ Passed: $((TOTAL - FAILED))"
echo "❌ Failed: $FAILED"
```

### Load Test
```bash
# Apache Bench: test pagination under load
ab -n 10000 -c 100 "http://localhost:8000/api/v1/inventory/list?limit=50&offset=0"

# Expected output:
# Requests per second: 1000+
# Failed requests: 0
# Time per request: <200ms (mean across concurrent requests)
```

## Related Issues
- #1.4 API Testing
- #2.1 Backend Environment Config
- #3.2 Pagination Implementation - Frontend

## Performance Targets

| Metric | Target | Method to Test |
|--------|--------|-----------------|
| Single page load | < 200ms | ab -n 100 |
| p95 response | < 250ms | ab -n 1000 |
| 100 concurrent | < 500ms | ab -n 1000 -c 100 |
| Database query | < 50ms | profile with time.time() |

## Definition of Done
✅ Endpoint returns paginated results with metadata  
✅ All 528 pages load successfully  
✅ Response time < 200ms per page  
✅ Handles 100 concurrent users  
✅ Indexed for performance  
✅ Documented in API specs

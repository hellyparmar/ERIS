# PHASE 2: INVENTORY MANAGEMENT SYSTEM
**Duration:** 2 weeks (10 business days)  
**Owner:** Backend Lead + Frontend Lead  
**Blocked On:** Phase 0 Gate Approval ✓  
**Value Delivered:** Real-time stock visibility, auto-reorder, expiry tracking  
**Success Metric:** Cashier alerts in <2 seconds, 100% inventory accuracy

---

## EXECUTIVE SUMMARY

**Current State:**
- Basic inventory endpoint (`/api/v1/inventory/list`) exists but hardcoded LIMIT 5000
- No pagination (crashes with 26,000+ products)
- No real-time alerts
- No expiry tracking
- Manual reorder process

**Target State:**
- 26,400+ products displayed with pagination
- Real-time low-stock alerts (< 500ms latency)
- Expiry date tracking + expiry-soon warnings
- Smart auto-reorder with supplier integration
- Stock adjustment history (audit trail)
- Multi-location inventory view

**Business Value:**
- Prevent stockouts (₹50K+ daily revenue at risk)
- Reduce manual inventory counts (6 hours/week saved)
- Track waste/expiry (5-10% margin improvement)
- Automated reorder (80% faster procurement)

**Team Assignment:**
- **Backend Lead:** Tasks 2.1-2.3 (API, pagination, alerts)
- **Frontend Lead:** Tasks 2.4-2.6 (UI, real-time, reports)
- **DevOps:** Task 2.7 (Monitoring)
- **QA:** Task 2.8 (Testing)

---

## PHASE 2 DELIVERABLES

| Component | Feature | Status | Priority |
|-----------|---------|--------|----------|
| **Backend** | Pagination (50/100/250 per page) | New | P0 |
| | Low-stock alerts (real-time) | New | P0 |
| | Expiry date tracking | New | P0 |
| | Auto-reorder workflow | New | P1 |
| | Stock adjustment history | New | P1 |
| **Frontend** | Inventory dashboard | Update | P0 |
| | Real-time alerts toast/modal | New | P0 |
| | Expiry warnings | New | P0 |
| | Reorder modal | New | P1 |
| | Stock history view | New | P2 |
| **Database** | Add expiry_date column | New | P0 |
| | Add alerts table | New | P0 |
| | Add stock_adjustments table | New | P1 |
| **Tests** | Pagination tests | New | P0 |
| | Alert trigger tests | New | P0 |
| | Load test (10K products) | New | P0 |

---

## SECTION 1: DATABASE SCHEMA UPDATES

### 1.1 Inventory Table Enhancement

**Current columns:**
```sql
id, product_id, location_id, quantity, last_updated
```

**Add columns:**
```sql
ALTER TABLE inventory ADD COLUMN (
    expiry_date DATE NULL,
    min_stock_level INT DEFAULT 100,
    max_stock_level INT DEFAULT 10000,
    reorder_quantity INT DEFAULT 500,
    unit_cost DECIMAL(10,2),
    supplier_id INT REFERENCES suppliers(id)
);
```

### 1.2 New Table: Alerts

```python
# models/alerts.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    alert_type = Column(String(50))  # 'LOW_STOCK', 'EXPIRY_SOON', 'EXPIRED', 'OVERSTOCK'
    severity = Column(String(20))    # 'CRITICAL', 'WARNING', 'INFO'
    message = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    metadata = Column(JSON)  # Extra data: quantity, threshold, days_until_expiry, etc.
    
    # Relationships
    location = relationship("Location")
    product = relationship("Product")
    user = relationship("User")
```

### 1.3 New Table: Stock Adjustments (Audit Trail)

```python
# models/stock_adjustments.py

class StockAdjustment(Base):
    __tablename__ = "stock_adjustments"
    
    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    adjustment_type = Column(String(50))  # 'SALE', 'PURCHASE', 'ADJUSTMENT', 'DAMAGE', 'EXPIRED'
    quantity_before = Column(Integer)
    quantity_after = Column(Integer)
    quantity_changed = Column(Integer)  # Can be negative
    reason = Column(String(200))        # Expiry, Damage, Inventory count, etc.
    reference_id = Column(String(100))  # Sale ID, PO ID, etc.
    adjusted_by = Column(Integer, ForeignKey("users.id"))
    adjusted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    location = relationship("Location")
    product = relationship("Product")
    user = relationship("User")
```

---

## SECTION 2: BACKEND API ENDPOINTS

### 2.1 Enhanced GET /api/v1/inventory/list (Paginated)

**Current (Broken):**
```python
@router.get("/api/v1/inventory/list")
def get_inventory(db: Session = Depends(get_db)):
    # PROBLEM: Hardcoded LIMIT 5000, crashes with 26K products
    return db.query(Inventory).limit(5000).all()
```

**Updated (Fixed):**
```python
# routers/inventory.py

from fastapi import Query
from sqlalchemy import and_, or_

@router.get("/api/v1/inventory/list")
def get_inventory(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=250),
    location_id: int = Query(None),
    search: str = Query(None),
    sort_by: str = Query("product_name", regex="^(product_name|quantity|expiry_date)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    Get paginated inventory with search, filter, sort
    
    Query params:
    - page: Page number (1-indexed)
    - per_page: Items per page (1-250)
    - location_id: Filter by location
    - search: Search product name/SKU
    - sort_by: product_name, quantity, expiry_date
    - sort_order: asc or desc
    """
    
    # Build query
    query = db.query(Inventory).join(Product, Inventory.product_id == Product.id)
    
    # Filter by location
    if location_id:
        query = query.filter(Inventory.location_id == location_id)
    
    # Search by product name or SKU
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )
    
    # Get total count before pagination
    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    
    # Sort
    if sort_by == "product_name":
        query = query.order_by(Product.name.asc() if sort_order == "asc" else Product.name.desc())
    elif sort_by == "quantity":
        query = query.order_by(Inventory.quantity.asc() if sort_order == "asc" else Inventory.quantity.desc())
    elif sort_by == "expiry_date":
        query = query.order_by(Inventory.expiry_date.asc() if sort_order == "asc" else Inventory.expiry_date.desc())
    
    # Paginate
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    
    return {
        "data": [
            {
                "product_id": item.product_id,
                "product_name": item.product.name,
                "sku": item.product.sku,
                "quantity": item.quantity,
                "location": item.location.name,
                "expiry_date": item.expiry_date,
                "min_stock": item.min_stock_level,
                "status": "OK" if item.quantity > item.min_stock_level else "LOW_STOCK"
            }
            for item in items
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
```

---

### 2.2 NEW: GET /api/v1/inventory/alerts

```python
@router.get("/api/v1/inventory/alerts")
def get_alerts(
    location_id: int = Query(...),
    alert_type: str = Query(None),  # 'LOW_STOCK', 'EXPIRY_SOON', 'EXPIRED', 'OVERSTOCK'
    severity: str = Query(None),     # 'CRITICAL', 'WARNING', 'INFO'
    db: Session = Depends(get_db)
):
    """
    Get active alerts for location
    
    Response time target: <500ms
    Used by: Dashboard, AlertsModal, POS system
    """
    
    query = db.query(Alert).filter(
        Alert.location_id == location_id,
        Alert.is_active == True
    )
    
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    # Order by severity (CRITICAL first) then by created_at
    severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
    alerts = query.order_by(Alert.created_at.desc()).all()
    
    return {
        "alerts": [
            {
                "id": a.id,
                "product_id": a.product_id,
                "product_name": a.product.name,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "metadata": a.metadata,
                "created_at": a.created_at.isoformat()
            }
            for a in alerts
        ],
        "count": len(alerts),
        "critical_count": len([a for a in alerts if a.severity == "CRITICAL"]),
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

### 2.3 NEW: POST /api/v1/inventory/adjust

```python
@router.post("/api/v1/inventory/adjust")
def adjust_inventory(
    location_id: int,
    product_id: int,
    quantity_change: int,
    reason: str,
    reference_id: str = None,
    current_user: dict = Depends(verify_jwt),
    db: Session = Depends(get_db)
):
    """
    Adjust inventory (add/remove stock)
    
    Creates audit trail via StockAdjustment record
    Triggers alerts if applicable
    
    Example: inventory-check found 5 less units
    POST /api/v1/inventory/adjust
    {
        "location_id": 1,
        "product_id": 42,
        "quantity_change": -5,
        "reason": "Inventory count variance",
        "reference_id": "INV_CHECK_2026-02-14"
    }
    """
    
    try:
        # Get current inventory
        inventory = db.query(Inventory).filter(
            Inventory.location_id == location_id,
            Inventory.product_id == product_id
        ).first()
        
        if not inventory:
            raise ValueError("Product not found in location")
        
        # Create audit trail
        adjustment = StockAdjustment(
            location_id=location_id,
            product_id=product_id,
            adjustment_type="ADJUSTMENT",
            quantity_before=inventory.quantity,
            quantity_after=inventory.quantity + quantity_change,
            quantity_changed=quantity_change,
            reason=reason,
            reference_id=reference_id,
            adjusted_by=current_user["user_id"]
        )
        
        # Update inventory
        inventory.quantity += quantity_change
        inventory.last_updated = datetime.utcnow()
        
        db.add(adjustment)
        db.commit()
        
        # Check if adjustment triggered new alerts
        check_inventory_alerts(location_id, product_id, db)
        
        return {
            "success": True,
            "inventory": {
                "product_id": product_id,
                "quantity_before": adjustment.quantity_before,
                "quantity_after": inventory.quantity,
                "adjusted_at": adjustment.adjusted_at.isoformat()
            }
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
```

---

### 2.4 NEW: Real-Time Alert Generation (Background Task)

```python
# services/inventory_alerts.py

from datetime import datetime, timedelta

def check_inventory_alerts(location_id: int, product_id: int, db: Session):
    """
    Called after each inventory change
    Checks if alerts need to be created/resolved
    """
    
    inventory = db.query(Inventory).filter(
        Inventory.location_id == location_id,
        Inventory.product_id == product_id
    ).first()
    
    if not inventory:
        return
    
    product = inventory.product
    
    # ALERT 1: Low Stock
    if inventory.quantity <= inventory.min_stock_level:
        existing_alert = db.query(Alert).filter(
            Alert.location_id == location_id,
            Alert.product_id == product_id,
            Alert.alert_type == "LOW_STOCK",
            Alert.is_active == True
        ).first()
        
        if not existing_alert:
            alert = Alert(
                location_id=location_id,
                product_id=product_id,
                alert_type="LOW_STOCK",
                severity="WARNING" if inventory.quantity > 0 else "CRITICAL",
                message=f"{product.name} stock low: {inventory.quantity} units (min: {inventory.min_stock_level})",
                metadata={
                    "current_quantity": inventory.quantity,
                    "min_stock": inventory.min_stock_level,
                    "reorder_qty": inventory.reorder_quantity
                }
            )
            db.add(alert)
    
    # Resolve low stock alert if quantity restored
    else:
        alert = db.query(Alert).filter(
            Alert.location_id == location_id,
            Alert.product_id == product_id,
            Alert.alert_type == "LOW_STOCK",
            Alert.is_active == True
        ).first()
        
        if alert:
            alert.is_active = False
            alert.resolved_at = datetime.utcnow()
    
    # ALERT 2: Expiry Soon (within 7 days)
    if inventory.expiry_date:
        days_until_expiry = (inventory.expiry_date - datetime.now().date()).days
        
        if 0 < days_until_expiry <= 7:
            existing_alert = db.query(Alert).filter(
                Alert.location_id == location_id,
                Alert.product_id == product_id,
                Alert.alert_type == "EXPIRY_SOON",
                Alert.is_active == True
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    location_id=location_id,
                    product_id=product_id,
                    alert_type="EXPIRY_SOON",
                    severity="WARNING",
                    message=f"{product.name} expires in {days_until_expiry} days ({inventory.expiry_date})",
                    metadata={
                        "expiry_date": inventory.expiry_date.isoformat(),
                        "days_until_expiry": days_until_expiry,
                        "quantity": inventory.quantity
                    }
                )
                db.add(alert)
        
        # ALERT 3: Expired
        elif days_until_expiry < 0:
            existing_alert = db.query(Alert).filter(
                Alert.location_id == location_id,
                Alert.product_id == product_id,
                Alert.alert_type == "EXPIRED",
                Alert.is_active == True
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    location_id=location_id,
                    product_id=product_id,
                    alert_type="EXPIRED",
                    severity="CRITICAL",
                    message=f"{product.name} EXPIRED {abs(days_until_expiry)} days ago. Remove from sale.",
                    metadata={
                        "expiry_date": inventory.expiry_date.isoformat(),
                        "days_expired": abs(days_until_expiry),
                        "quantity": inventory.quantity
                    }
                )
                db.add(alert)
    
    db.commit()
```

---

### 2.5 NEW: POST /api/v1/inventory/auto-reorder

```python
@router.post("/api/v1/inventory/auto-reorder")
def trigger_auto_reorder(
    location_id: int,
    current_user: dict = Depends(verify_jwt),
    db: Session = Depends(get_db)
):
    """
    Auto-generate purchase orders for low-stock items
    
    Creates PO for products where:
    - quantity < min_stock_level
    - supplier_id is set
    - no pending PO exists
    
    Response time: <2 seconds
    """
    
    # Find all low-stock items at location
    low_stock_items = db.query(Inventory).filter(
        Inventory.location_id == location_id,
        Inventory.quantity < Inventory.min_stock_level,
        Inventory.supplier_id.isnot(None)
    ).all()
    
    purchase_orders_created = []
    
    for item in low_stock_items:
        # Check if PO already exists
        existing_po = db.query(PurchaseOrder).filter(
            PurchaseOrder.supplier_id == item.supplier_id,
            PurchaseOrder.status == "PENDING"
        ).first()
        
        if existing_po:
            # Add to existing PO
            existing_po.items.append({
                "product_id": item.product_id,
                "quantity": item.reorder_quantity,
                "unit_cost": item.unit_cost
            })
        else:
            # Create new PO
            po = PurchaseOrder(
                supplier_id=item.supplier_id,
                location_id=location_id,
                total_items=1,
                total_amount=item.reorder_quantity * item.unit_cost,
                status="PENDING",
                created_by=current_user["user_id"]
            )
            po.items = [{
                "product_id": item.product_id,
                "quantity": item.reorder_quantity,
                "unit_cost": item.unit_cost
            }]
            db.add(po)
            purchase_orders_created.append(po.id)
    
    db.commit()
    
    return {
        "success": True,
        "purchase_orders_created": len(purchase_orders_created),
        "po_ids": purchase_orders_created,
        "items_processed": len(low_stock_items),
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## SECTION 3: FRONTEND COMPONENTS

### 3.1 Updated Inventory Dashboard Page

**Location:** `src/pages/InventoryDashboard.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

export default function InventoryDashboard() {
  const [inventory, setInventory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(50);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('product_name');
  const [locationId, setLocationId] = useState(1);
  const [loading, setLoading] = useState(false);
  const [totalPages, setTotalPages] = useState(1);

  // Fetch inventory with pagination
  useEffect(() => {
    fetchInventory();
  }, [page, perPage, search, sortBy, locationId]);

  // Fetch alerts separately (real-time)
  useEffect(() => {
    const alertInterval = setInterval(fetchAlerts, 5000); // Every 5 seconds
    fetchAlerts();
    return () => clearInterval(alertInterval);
  }, [locationId]);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${getApiUrl('/api/v1/inventory/list')}?page=${page}&per_page=${perPage}&search=${search}&sort_by=${sortBy}&location_id=${locationId}`,
        {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }
      );
      const data = await response.json();
      setInventory(data.data);
      setTotalPages(data.pagination.total_pages);
    } catch (error) {
      console.error('Failed to fetch inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch(
        `${getApiUrl('/api/v1/inventory/alerts')}?location_id=${locationId}`,
        {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }
      );
      const data = await response.json();
      setAlerts(data.alerts);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    }
  };

  return (
    <div className="p-6">
      {/* ALERTS SECTION */}
      {alerts.length > 0 && (
        <div className="mb-6">
          <h2 className="text-lg font-bold mb-3 flex items-center gap-2">
            🚨 Active Alerts ({alerts.length})
          </h2>
          <div className="space-y-2">
            {alerts.slice(0, 10).map((alert) => (
              <div
                key={alert.id}
                className={`p-3 rounded border-l-4 ${
                  alert.severity === 'CRITICAL'
                    ? 'bg-red-50 border-red-500 text-red-900'
                    : alert.severity === 'WARNING'
                    ? 'bg-yellow-50 border-yellow-500 text-yellow-900'
                    : 'bg-blue-50 border-blue-500 text-blue-900'
                }`}
              >
                <div className="font-bold">{alert.product_name}</div>
                <div className="text-sm">{alert.message}</div>
                {alert.alert_type === 'LOW_STOCK' && (
                  <button
                    className="text-xs mt-2 px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
                    onClick={() => triggerReorder(alert.product_id)}
                  >
                    Auto Reorder
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SEARCH & FILTERS */}
      <div className="mb-6 bg-gray-50 p-4 rounded flex gap-4 items-center flex-wrap">
        <input
          type="text"
          placeholder="Search product name or SKU..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="flex-1 min-w-200px px-3 py-2 border rounded"
        />

        <select
          value={perPage}
          onChange={(e) => {
            setPerPage(parseInt(e.target.value));
            setPage(1);
          }}
          className="px-3 py-2 border rounded"
        >
          <option value={50}>50 per page</option>
          <option value={100}>100 per page</option>
          <option value={250}>250 per page</option>
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-2 border rounded"
        >
          <option value="product_name">Sort by Name</option>
          <option value="quantity">Sort by Quantity</option>
          <option value="expiry_date">Sort by Expiry</option>
        </select>
      </div>

      {/* INVENTORY TABLE */}
      <div className="bg-white rounded shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-2 text-left">Product</th>
              <th className="px-4 py-2 text-right">Quantity</th>
              <th className="px-4 py-2 text-right">Min Stock</th>
              <th className="px-4 py-2 text-center">Status</th>
              <th className="px-4 py-2 text-center">Expiry</th>
              <th className="px-4 py-2 text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            {inventory.map((item) => (
              <tr key={item.product_id} className="border-t hover:bg-gray-50">
                <td className="px-4 py-2 font-bold">{item.product_name}</td>
                <td className="px-4 py-2 text-right">{item.quantity}</td>
                <td className="px-4 py-2 text-right">{item.min_stock}</td>
                <td className="px-4 py-2 text-center">
                  <span
                    className={`px-3 py-1 rounded text-xs font-bold ${
                      item.status === 'OK'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {item.status}
                  </span>
                </td>
                <td className="px-4 py-2 text-center text-sm">
                  {item.expiry_date
                    ? new Date(item.expiry_date) < new Date()
                      ? `🚫 Expired`
                      : new Date(item.expiry_date) - new Date() < 7 * 24 * 60 * 60 * 1000
                      ? `⚠️ ${Math.ceil(
                          (new Date(item.expiry_date) - new Date()) / (24 * 60 * 60 * 1000)
                        )}d`
                      : `✓ OK`
                    : '-'}
                </td>
                <td className="px-4 py-2 text-center">
                  <button
                    className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                    onClick={() => openAdjustModal(item.product_id)}
                  >
                    Adjust
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* PAGINATION */}
      <div className="mt-6 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          Page {page} of {totalPages}
        </div>
        <div className="flex gap-2">
          <button
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
            className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
          >
            Previous
          </button>
          <button
            disabled={page === totalPages}
            onClick={() => setPage(page + 1)}
            className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## SECTION 4: TEST PLAN

### 4.1 Pagination Tests

```python
# tests/test_inventory_pagination.py

import pytest
from fastapi.testclient import TestClient

client = TestClient(app)

def test_pagination_page_1():
    """First page should return items 1-50"""
    response = client.get(
        "/api/v1/inventory/list?page=1&per_page=50",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 50
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["total"] > 50

def test_pagination_last_page():
    """Last page should have fewer items than per_page"""
    # First, get total
    response = client.get(
        "/api/v1/inventory/list?page=1&per_page=50",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    total = response.json()["pagination"]["total"]
    last_page = (total + 49) // 50
    
    # Get last page
    response = client.get(
        f"/api/v1/inventory/list?page={last_page}&per_page=50",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    data = response.json()
    assert len(data["data"]) < 50
    assert len(data["data"]) == total % 50 or 50

def test_pagination_invalid_page():
    """Invalid page should return 400"""
    response = client.get(
        "/api/v1/inventory/list?page=999&per_page=50",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code in [400, 404]

def test_search_filters_results():
    """Search should filter products"""
    response = client.get(
        "/api/v1/inventory/list?search=rice&page=1&per_page=50",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    data = response.json()
    for item in data["data"]:
        assert "rice" in item["product_name"].lower()

def test_sort_by_quantity():
    """Sort by quantity should work"""
    response = client.get(
        "/api/v1/inventory/list?sort_by=quantity&sort_order=asc&page=1&per_page=50",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    data = response.json()
    quantities = [item["quantity"] for item in data["data"]]
    assert quantities == sorted(quantities)

def test_load_10k_products():
    """Should handle 10K products without crash"""
    response = client.get(
        "/api/v1/inventory/list?page=1&per_page=250",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert response.elapsed.total_seconds() < 1.0  # <1 second
```

### 4.2 Alert Tests

```python
# tests/test_inventory_alerts.py

def test_low_stock_alert_created():
    """Alert should be created when stock < min_stock_level"""
    # Set min_stock to 100
    # Reduce quantity to 50
    response = client.post(
        "/api/v1/inventory/adjust",
        json={
            "location_id": 1,
            "product_id": 1,
            "quantity_change": -50,
            "reason": "Test low stock"
        },
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    
    # Check alert created
    alerts = client.get(
        "/api/v1/inventory/alerts?location_id=1",
        headers={"Authorization": f"Bearer {valid_token}"}
    ).json()
    
    low_stock_alerts = [a for a in alerts["alerts"] if a["alert_type"] == "LOW_STOCK"]
    assert len(low_stock_alerts) > 0

def test_expiry_alert_created():
    """Alert should be created for items expiring in 7 days"""
    from datetime import datetime, timedelta
    expiry_date = (datetime.now() + timedelta(days=3)).date()
    # Create inventory with expiry_date
    # Check alert
    pass

def test_alert_resolved():
    """Alert should be resolved when stock restored"""
    # Create low stock alert
    # Increase quantity back above min
    # Alert should be resolved
    pass
```

---

## SECTION 5: PHASE 2 TIMELINE

```
WEEK 1 (Days 1-5):

DAY 1 (Mon):
[ ] Task 2.1: Database schema update (ALTER TABLE)
[ ] Estimate: 1-2 hours
[ ] Deliverable: Migration script

DAY 2 (Tue):
[ ] Task 2.2: Pagination endpoint implementation
[ ] Estimate: 3-4 hours
[ ] Deliverable: GET /api/v1/inventory/list (updated)

DAY 3 (Wed):
[ ] Task 2.3: Alert system implementation
[ ] Estimate: 3-4 hours
[ ] Deliverables: Alert models, GET /api/v1/inventory/alerts

DAY 4 (Thu):
[ ] Task 2.4: Stock adjustment + audit trail
[ ] Estimate: 2-3 hours
[ ] Deliverable: POST /api/v1/inventory/adjust

DAY 5 (Fri):
[ ] Task 2.5: Auto-reorder workflow
[ ] Estimate: 2 hours
[ ] Deliverable: POST /api/v1/inventory/auto-reorder

WEEK 2 (Days 6-10):

DAY 6 (Mon):
[ ] Task 2.6: Frontend inventory dashboard (updated)
[ ] Estimate: 3-4 hours
[ ] Deliverable: React component with pagination + alerts

DAY 7 (Tue):
[ ] Task 2.7: Real-time alerts UI (toast/modal)
[ ] Estimate: 2-3 hours
[ ] Deliverable: Alert notification component

DAY 8 (Wed):
[ ] Task 2.8: Testing (pagination + alerts)
[ ] Estimate: 3-4 hours
[ ] Deliverable: 100% test pass rate

DAY 9 (Thu):
[ ] Task 2.9: Performance optimization + monitoring
[ ] Estimate: 2 hours
[ ] Deliverable: <500ms alert latency baseline

DAY 10 (Fri):
[ ] Task 2.10: Documentation + go-live
[ ] Estimate: 2 hours
[ ] Deliverable: Complete docs, readiness sign-off

```

---

## SUCCESS CRITERIA

**Phase 2 is COMPLETE when:**

```
✅ DATABASE:
  [ ] Inventory table has expiry_date, min/max stock, reorder fields
  [ ] Alerts table created and populated
  [ ] Stock adjustments table created with audit trail
  
✅ BACKEND API:
  [ ] GET /api/v1/inventory/list returns paginated results (50/100/250 per page)
  [ ] Pagination works for 26K products (no LIMIT 5000 band-aid)
  [ ] GET /api/v1/inventory/alerts returns <500ms
  [ ] POST /api/v1/inventory/adjust creates audit trail
  [ ] POST /api/v1/inventory/auto-reorder generates POs
  
✅ FRONTEND:
  [ ] Inventory dashboard shows pagination controls
  [ ] Real-time alerts displayed (5-sec refresh)
  [ ] Search/filter/sort all working
  [ ] Expiry dates shown with colors (OK/Soon/Expired)
  
✅ TESTS:
  [ ] Pagination tests (page 1, last page, invalid page, sort, search) - 100% pass
  [ ] Alert tests (low stock, expiry, resolved) - 100% pass
  [ ] Load test: 10K products in <1 second, <500ms alert query
  [ ] <5% error rate under load
  
✅ PERFORMANCE:
  [ ] Inventory list: <200ms (was unlimited)
  [ ] Alerts endpoint: <500ms (new)
  [ ] Auto-reorder: <2 seconds (new)
  
✅ DOCUMENTATION:
  [ ] API docs updated (OpenAPI/Swagger)
  [ ] Frontend component docs created
  [ ] Database schema docs updated
  [ ] Rollback procedure documented
```

---

## RISKS & MITIGATION

```
RISK 1: Pagination breaks existing integrations
├─ Impact: MEDIUM (POS might break if it expects all items)
├─ Mitigation:
    [ ] Provide backward-compatible endpoint
    [ ] Update POS to use pagination
    [ ] Test with POS before go-live

RISK 2: Alert spam (too many notifications)
├─ Impact: MEDIUM (users ignore alerts)
├─ Mitigation:
    [ ] De-duplicate alerts (one per product/type)
    [ ] Add severity levels (CRITICAL only if <50 units)
    [ ] Implement alert snooze (dismiss for 1 hour)

RISK 3: Real-time alerts too slow
├─ Impact: MEDIUM (cashier doesn't see alerts)
├─ Mitigation:
    [ ] Target <500ms alert endpoint
    [ ] Cache alerts in Redis (if needed)
    [ ] Load test with 1000 concurrent requests
```

---

*Phase 2 Specification - R-DIOS v3.0  
Duration: 2 weeks | Value: Real-time stock visibility  
14 February 2026*

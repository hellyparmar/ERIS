# Phase 6 - Enterprise Advanced Features Implementation Plan

## Overview
Phase 6 delivers multi-tenant support, admin capabilities, event-driven architecture, and production-grade performance optimization.

**Timeline**: Complete implementation with testing
**Status**: Starting

---

## P6-T1: Admin Panel

### 1.1 Backend API Endpoints

**User Management**
```
POST   /api/v1/admin/users              - Create user
GET    /api/v1/admin/users              - List users with pagination
GET    /api/v1/admin/users/{user_id}    - Get user details
PUT    /api/v1/admin/users/{user_id}    - Update user
DELETE /api/v1/admin/users/{user_id}    - Deactivate user
POST   /api/v1/admin/users/{user_id}/reset-pin - Reset PIN
```

**Device Management**
```
POST   /api/v1/admin/devices            - Register device
GET    /api/v1/admin/devices            - List devices
PUT    /api/v1/admin/devices/{device_id} - Update device
DELETE /api/v1/admin/devices/{device_id} - Deregister device
```

**GST Configuration**
```
GET    /api/v1/admin/gst-rates          - Get all GST rates
POST   /api/v1/admin/gst-rates          - Create GST rate
PUT    /api/v1/admin/gst-rates/{rate_id} - Update GST rate
DELETE /api/v1/admin/gst-rates/{rate_id} - Delete GST rate
```

### 1.2 Frontend Components
- AdminDashboard.jsx
- UserManagement.jsx (Create/Edit/Delete/ResetPIN)
- DeviceRegistry.jsx (Register/Edit/Deregister)
- GSTConfiguration.jsx (Add/Edit/Delete rates)

---

## P6-T2: Multi-tenancy

### 2.1 Database Schema Changes
Add to ALL tables:
```sql
ALTER TABLE users ADD COLUMN tenant_id UUID REFERENCES tenants(id);
ALTER TABLE products ADD COLUMN tenant_id UUID REFERENCES tenants(id);
ALTER TABLE inventory ADD COLUMN tenant_id UUID REFERENCES tenants(id);
ALTER TABLE sales ADD COLUMN tenant_id UUID REFERENCES tenants(id);
ALTER TABLE bills ADD COLUMN tenant_id UUID REFERENCES tenants(id);
ALTER TABLE devices ADD COLUMN tenant_id UUID REFERENCES tenants(id);
-- ... continue for all tables
```

### 2.2 Tenants Table
```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50),
    max_users INTEGER,
    max_devices INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2.3 Row-Level Security
```python
# Apply to all queries
def apply_tenant_filter(query, tenant_id):
    return query.filter(Model.tenant_id == tenant_id)
```

### 2.4 Tenant Context
- Extract from JWT token
- Verify in all endpoints
- Isolate data completely

---

## P6-T3: Module Integration (Event-Driven Architecture)

### 3.1 Post-Sale Event Chain
```
Sale Created
  ├─> Deduct Inventory
  ├─> Update Customer Loyalty
  ├─> Trigger Reorder Alerts
  ├─> Update Forecasts
  ├─> Log Anomalies
  └─> Update Analytics
```

### 3.2 Event System
```python
class SaleCreatedEvent:
    sale_id: str
    customer_id: str
    items: List[dict]
    amount: float
    timestamp: datetime

# Event handlers
def handle_sale_created(event):
    inventory_service.deduct_stock(event.items)
    loyalty_service.award_points(event.customer_id, event.amount)
    reorder_service.check_alerts()
    forecast_service.update_forecasts()
    anomaly_service.detect_anomalies(event)
```

### 3.3 Integration Points
- **Inventory**: Deduct stock automatically
- **Loyalty**: Award points based on purchase
- **Reorder**: Check and alert if stock below reorder point
- **Forecasts**: Update demand predictions
- **Anomalies**: Detect unusual patterns

---

## P6-T4: Security Hardening

### 4.1 Tamper-Evident Logs
```python
class TamperEvidentLog(Base):
    id = Column(String, primary_key=True)
    event_type = Column(String)
    user_id = Column(String)
    action = Column(String)
    data = Column(JSON)
    hash = Column(String)  # SHA256 of previous record + current data
    previous_hash = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def compute_hash(self):
        content = f"{self.previous_hash}:{self.event_type}:{self.action}:{self.data}"
        return hashlib.sha256(content.encode()).hexdigest()
```

### 4.2 Device Whitelisting
```python
class WhitelistedDevice(Base):
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    device_uuid = Column(String, unique=True)
    device_name = Column(String)
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime)
    
    # Only allow whitelisted devices to access sensitive endpoints
```

### 4.3 Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/sales", tags=["POS"])
@limiter.limit("10/minute")
async def create_sale(sale: SaleCreate):
    # 10 sales per minute per IP
    pass
```

### 4.4 RPO/RTO Targets
- **RPO (Recovery Point Objective) = 0**: Real-time replication
- **RTO (Recovery Time Objective) < 30s**: Failover within 30 seconds
- Strategy: Master-slave replication, hot standby

---

## P6-T5: Performance Optimization

### 5.1 Frontend Performance
- **First Paint < 1s**: Code splitting, lazy loading
- **Dashboard Load < 2s**: Server-side pagination
- **Remove Framer Motion**: Replace with CSS animations
- **CSS-in-JS Optimization**: Critical CSS inlining

### 5.2 Backend Performance
- **POS Transaction < 500ms**: Async processing
- **Redis Caching**: Cache frequently accessed data
  - Product catalog
  - GST rates
  - Customer loyalty info
  - Inventory levels

### 5.3 Caching Strategy
```python
@router.get("/products")
async def get_products(cache=Depends(get_cache)):
    key = "products:all"
    
    # Try cache first
    cached = await cache.get(key)
    if cached:
        return cached
    
    # Query database
    products = db.query(Product).all()
    
    # Cache for 5 minutes
    await cache.set(key, products, expire=300)
    return products
```

### 5.4 Optimization Techniques
- Database indexing on frequently queried columns
- Query optimization (joins, aggregations)
- Batch operations for inventory updates
- Async/await for I/O operations
- Connection pooling

---

## Implementation Order

1. **Phase 6-T1**: Admin Panel (Days 1-2)
   - User management CRUD
   - PIN reset functionality
   - Device registration
   - GST rate management

2. **Phase 6-T2**: Multi-tenancy (Days 2-3)
   - Schema migration
   - Tenant context management
   - Row-level security

3. **Phase 6-T3**: Event Integration (Days 3-4)
   - Event system setup
   - Post-sale event chain
   - Service integrations

4. **Phase 6-T4**: Security (Days 4-5)
   - Tamper-evident logging
   - Device whitelisting
   - Rate limiting

5. **Phase 6-T5**: Performance (Days 5-6)
   - Redis setup
   - Caching implementation
   - Frontend optimization
   - Remove Framer Motion

---

## Success Criteria

✅ Admin panel fully functional  
✅ Multi-tenant isolation verified  
✅ Event chain working end-to-end  
✅ All security features implemented  
✅ Performance targets met:
  - First paint < 1s
  - POS transaction < 500ms
  - Dashboard load < 2s

---

## Testing Strategy

- Unit tests for each service
- Integration tests for event chain
- Multi-tenant isolation tests
- Security tests (tamper detection, whitelisting)
- Performance benchmarks
- Load testing (100+ concurrent users)

---

## Deployment Strategy

1. Feature flags for gradual rollout
2. Canary deployment (10% → 50% → 100%)
3. Monitor metrics closely
4. Rollback plan if needed
5. User communication for new features


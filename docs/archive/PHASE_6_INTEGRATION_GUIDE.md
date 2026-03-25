"""
Phase 6 - Integration Guide
Instructions for integrating P6-T1, P6-T2, P6-T3 components into existing endpoints
"""

# =============================================================================
# INTEGRATION CHECKLIST FOR PHASE 6
# =============================================================================

"""
This file provides step-by-step instructions for integrating Phase 6 components
into the existing R-DIOS system. Each section can be completed independently
but should be done in the recommended order.

RECOMMENDED ORDER:
1. P6-T1: Admin Panel (✅ DONE)
2. P6-T2: Multi-tenancy (⏳ IN PROGRESS)
3. P6-T3: Event-Driven Architecture (⏳ IN PROGRESS)
4. P6-T4: Security Hardening (❌ PENDING)
5. P6-T5: Performance Optimization (❌ PENDING)
"""

# =============================================================================
# PART 1: REGISTER EVENT HANDLERS IN APPLICATION STARTUP
# =============================================================================

"""
FILE: /api/main.py
LOCATION: Add after app initialization, around line 65-70

CURRENT CODE:
```python
# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Scheduler
    scheduler = start_scheduler()
    yield
    # Shutdown: Stop Scheduler
    scheduler.shutdown()
```

UPDATED CODE:
```python
from api.events import register_event_handlers, get_event_bus

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Scheduler and Event Bus
    scheduler = start_scheduler()
    event_bus = get_event_bus()
    register_event_handlers(event_bus)
    logger.info("Event handlers registered successfully")
    
    yield
    
    # Shutdown: Stop Scheduler
    scheduler.shutdown()
    logger.info("Event bus and scheduler shut down")
```

RESULT: Event handlers will be registered on application startup
TESTING: Check logs for "Event handlers registered successfully"
"""


# =============================================================================
# PART 2: INTEGRATE TENANT CONTEXT IN ENDPOINTS
# =============================================================================

"""
FILE: /api/routers/pos_sales.py (or similar sales endpoint)
LOCATION: In each endpoint that needs tenant filtering

STEP 1: Add imports at the top
```python
from api.db.tenant_context import TenantContextManager, get_tenant_context
from fastapi import Depends, Request
```

STEP 2: Add tenant context to endpoint signature
BEFORE:
```python
@router.post("/api/v1/pos/sales")
async def create_sale(sale_data: SaleCreate):
    session = SessionLocal()
    # ... create sale ...
```

AFTER:
```python
@router.post("/api/v1/pos/sales")
async def create_sale(
    sale_data: SaleCreate,
    request: Request,
    tenant = Depends(get_tenant_context)
):
    session = SessionLocal()
    # Get tenant_id from context
    tenant_id = tenant.get('tenant_id')
    user_id = tenant.get('user_id')
    
    # Create sale with tenant_id
    sale = Sale(
        **sale_data.dict(),
        tenant_id=tenant_id,
        user_id=user_id
    )
    session.add(sale)
    session.commit()
    # ... rest of logic ...
```

STEP 3: Update all queries to include tenant filter
BEFORE:
```python
existing_sale = session.query(Sale).filter(Sale.id == sale_id).first()
```

AFTER:
```python
tenant_id = TenantContextManager.get_tenant_id(request)
existing_sale = session.query(Sale).filter(
    Sale.id == sale_id,
    Sale.tenant_id == tenant_id
).first()
```

AFFECTED ENDPOINTS (estimate 15-20 files):
- /api/routers/pos_sales.py
- /api/routers/inventory_control.py
- /api/routers/customers.py
- /api/routers/loyalty.py
- /api/routers/invoicing_v2.py
- /api/routers/bill_management.py
- And all other business logic routers
"""


# =============================================================================
# PART 3: CONNECT SALES TO EVENT SYSTEM
# =============================================================================

"""
FILE: /api/routers/pos_sales.py (create_sale endpoint)
LOCATION: After sale is successfully created and committed

STEP 1: Import event classes
```python
from api.events import SaleCreatedEvent, get_event_bus
import uuid
```

STEP 2: Add event publishing after sale creation
```python
@router.post("/api/v1/pos/sales")
async def create_sale(
    sale_data: SaleCreate,
    request: Request,
    tenant = Depends(get_tenant_context)
):
    session = SessionLocal()
    tenant_id = uuid.UUID(tenant['tenant_id'])
    user_id = uuid.UUID(tenant['user_id'])
    
    try:
        # Create and save sale
        sale = Sale(
            **sale_data.dict(),
            tenant_id=tenant_id
        )
        session.add(sale)
        session.commit()
        sale_id = sale.id
        
        # ✨ NEW: Publish SALE_CREATED event to trigger event chain
        event = SaleCreatedEvent(
            aggregate_id=uuid.UUID(str(sale_id)),
            tenant_id=tenant_id,
            user_id=user_id,
            data={
                'sale_id': str(sale_id),
                'items': [
                    {
                        'product_id': str(item.product_id),
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                    }
                    for item in sale.items
                ],
                'total_amount': float(sale.total_amount),
                'customer_id': str(sale.customer_id) if sale.customer_id else None,
                'store_id': str(sale.store_id) if sale.store_id else None,
                'payment_method': sale.payment_method,
            }
        )
        
        # Publish event - triggers:
        # 1. Inventory deduction
        # 2. Loyalty points award
        # 3. Reorder alerts
        # 4. Forecast updates
        # 5. Anomaly detection
        event_bus = get_event_bus()
        await event_bus.publish(event)
        
        logger.info(f"Sale {sale_id} created and event published")
        
        return {"sale_id": sale_id, "status": "success"}
        
    except Exception as e:
        session.rollback()
        logger.error(f"Sale creation failed: {e}")
        raise HTTPException(status_code=500, detail="Sale creation failed")
    finally:
        session.close()
```

RESULT: Creating a sale will automatically:
- Deduct inventory
- Award loyalty points
- Check reorder points
- Update forecasts
- Detect anomalies
"""


# =============================================================================
# PART 4: UPDATE DATABASE SCHEMA WITH TENANT_ID
# =============================================================================

"""
STEP 1: Run the migration script

```bash
cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System
python -m api.db.P6T2_add_tenant_id
```

EXPECTED OUTPUT:
```
======================================================================
PHASE 6 - TASK 2: MULTI-TENANCY MIGRATION
======================================================================

Adding tenant_id to all tables for data isolation...

✓ Successfully added tenant_id to users table
✓ Successfully added tenant_id to products table
✓ Successfully added tenant_id to inventory table
✓ Successfully added tenant_id to sales table
✓ Successfully added tenant_id to customers table
✓ Successfully added tenant_id to invoices table
✓ Successfully added tenant_id to bills table
✓ Successfully added tenant_id to devices table

======================================================================
✓ MIGRATION COMPLETE!
======================================================================
```

STEP 2: Verify in database
```sql
-- Check tenant_id column was added
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'tenant_id';

-- Check foreign key constraint
SELECT constraint_name FROM information_schema.table_constraints 
WHERE table_name = 'users' AND constraint_type = 'FOREIGN KEY';

-- Verify index
SELECT indexname FROM pg_indexes 
WHERE tablename = 'users' AND indexname LIKE '%tenant_id%';
```

STEP 3: Backup before migration
```bash
pg_dump petpooja_retail_db > backup_before_p6.sql
```
"""


# =============================================================================
# PART 5: EXAMPLE - UPDATE AN ENDPOINT WITH TENANT FILTERING
# =============================================================================

"""
Example: Updating the Inventory endpoint to support multi-tenancy

FILE: /api/routers/inventory_control.py

BEFORE (No Tenant Filtering):
```python
@router.get("/api/v1/inventory/summary")
async def get_inventory_summary():
    session = SessionLocal()
    try:
        items = session.query(Inventory).all()  # Gets ALL tenants' inventory!
        return {
            "total_items": len(items),
            "low_stock": sum(1 for item in items if item.quantity_available < item.reorder_point),
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product.name,
                    "quantity": item.quantity_available,
                    "status": "low" if item.quantity_available < item.reorder_point else "ok"
                }
                for item in items
            ]
        }
    finally:
        session.close()
```

AFTER (With Tenant Filtering):
```python
from api.db.tenant_context import get_tenant_context, TenantAwareQuery
from fastapi import Depends
import uuid

@router.get("/api/v1/inventory/summary")
async def get_inventory_summary(
    request: Request,
    tenant = Depends(get_tenant_context)
):
    session = SessionLocal()
    try:
        tenant_id = uuid.UUID(tenant['tenant_id'])
        
        # Use tenant-aware query to ensure data isolation
        items = session.query(Inventory).filter(
            Inventory.tenant_id == tenant_id
        ).all()
        
        return {
            "tenant_id": str(tenant_id),
            "total_items": len(items),
            "low_stock": sum(1 for item in items if item.quantity_available < item.reorder_point),
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product.name,
                    "quantity": item.quantity_available,
                    "status": "low" if item.quantity_available < item.reorder_point else "ok"
                }
                for item in items
            ]
        }
    finally:
        session.close()
```

KEY CHANGES:
1. Added get_tenant_context dependency
2. Added Depends(get_tenant_context) to function signature
3. Filter all queries by tenant_id
4. Include tenant_id in response for verification
"""


# =============================================================================
# PART 6: HANDLING TENANT CONTEXT IN ASYNC OPERATIONS
# =============================================================================

"""
For background tasks that need tenant context:

```python
from api.db.tenant_context import TenantContext
from api.db.session import SessionLocal

async def background_task_example(tenant_context: TenantContext):
    '''Background task that needs tenant context'''
    session = SessionLocal()
    try:
        # Use tenant context from parameter
        records = session.query(Product).filter(
            Product.tenant_id == tenant_context.tenant_id
        ).all()
        
        # Do work...
        logger.info(f"Processed {len(records)} products for tenant {tenant_context.tenant_id}")
        
    finally:
        session.close()


# When triggering background task, pass tenant context
@router.post("/api/v1/bulk-operation")
async def trigger_bulk_operation(
    request: Request,
    tenant = Depends(get_tenant_context)
):
    # Extract full tenant context
    tenant_context = TenantContextManager.get_from_request(request)
    
    # Trigger background task with context
    import asyncio
    asyncio.create_task(background_task_example(tenant_context))
    
    return {"status": "processing"}
```
"""


# =============================================================================
# TESTING THE INTEGRATION
# =============================================================================

"""
STEP 1: Create a test JWT token with tenant_id

```python
import jwt
import json
from datetime import datetime, timedelta

jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key")

payload = {
    "tenant_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "manager",
    "store_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "exp": datetime.utcnow() + timedelta(hours=24)
}

token = jwt.encode(payload, jwt_secret, algorithm="HS256")
print(f"Test Token: {token}")
```

STEP 2: Test endpoint with token

```bash
curl -X POST http://localhost:8000/api/v1/pos/sales \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "items": [
      {"product_id": "550e8400-e29b-41d4-a716-446655440000", "quantity": 2}
    ],
    "total_amount": 500.0
  }'
```

STEP 3: Verify tenant isolation

```bash
# Sale should only appear for the tenant in the token
curl -X GET http://localhost:8000/api/v1/pos/sales \\
  -H "Authorization: Bearer $TOKEN_TENANT_1"

# Different token = different tenant = no sales
curl -X GET http://localhost:8000/api/v1/pos/sales \\
  -H "Authorization: Bearer $TOKEN_TENANT_2"
```

STEP 4: Check event logs

```bash
# Monitor logs for event processing
docker logs -f rdios_backend

# Expected output:
# Publishing event: sale_created (event_id)
# Handler InventoryDeductionHandler completed
# Handler LoyaltyPointsHandler completed
# Handler AnomalyDetectionHandler completed
# Event sale_created completed successfully
```
"""


# =============================================================================
# TROUBLESHOOTING GUIDE
# =============================================================================

"""
ISSUE: "Tenant context not found"
CAUSE: Endpoint not decorated with Depends(get_tenant_context)
FIX: Add the dependency to the endpoint

ISSUE: "Invalid UUID format in token"
CAUSE: tenant_id in JWT is not a valid UUID
FIX: Ensure JWT payload has valid UUID for tenant_id

ISSUE: Events not being triggered
CAUSE: Event handlers not registered in startup
FIX: Ensure register_event_handlers() called in lifespan

ISSUE: "You do not have access to this resource" (403)
CAUSE: Requesting resource from different tenant
FIX: This is correct behavior - tokens cannot access other tenants' data

ISSUE: Migration script fails
CAUSE: Column already exists or database connection issue
FIX: Check if tenant_id column already added, verify DB connection

ISSUE: Query returns empty results after migration
CAUSE: tenant_id is NULL for existing records
FIX: Run migration with default tenant_id value, or backfill manually
"""


# =============================================================================
# DEPLOYMENT CHECKLIST
# =============================================================================

"""
Before deploying Phase 6 to production:

PREPARATION:
[ ] Backup production database
[ ] Test migration script on staging
[ ] Review all endpoint changes for tenant filtering
[ ] Verify event handlers don't break existing logic
[ ] Load test with multiple tenants

EXECUTION:
[ ] Run P6T2 migration script
[ ] Update endpoints with tenant filtering (15-20 files)
[ ] Register event handlers in main.py
[ ] Connect POS sales to event system
[ ] Deploy to staging environment
[ ] Run full integration tests
[ ] Performance testing
[ ] Security audit

VALIDATION:
[ ] Multi-tenant data isolation verified
[ ] Event chain executes correctly
[ ] Admin panel functional
[ ] No data leakage between tenants
[ ] API response times acceptable
[ ] Logging captures all events

ROLLBACK:
[ ] Keep database backup
[ ] Git branch ready for revert
[ ] Rollback procedure documented
[ ] Team notified of deployment
"""

print(__doc__)

"""
Supplier & Purchase Order Router
REST API for vendor management and procurement workflows
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.supplier_service import SupplierService
from app.schemas.supplier import (
    SupplierCreate, SupplierUpdate, PurchaseOrderCreate, ReceiveGoodsRequest, UpdatePOStatusRequest
)
from app.api.deps import get_current_active_user
from app.models.users import User

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

# ==================== SUPPLIERS ====================

@router.post("/", status_code=201)
async def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new supplier"""
    try:
        svc = SupplierService(db)
        s = svc.create_supplier(data.dict())
        return {"success": True, "data": svc._supplier_dict(s), "message": "Supplier created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
@router.get("/")
async def list_suppliers(
    search: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    is_active: bool = Query(True),
    page: int = Query(1, ge=1),
    per_page: Optional[int] = Query(None, ge=1, le=100),
    limit: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all suppliers with optional filters and pagination"""
    try:
        svc = SupplierService(db)
        search_val = search if isinstance(search, str) else None
        city_val = city if isinstance(city, str) else None
        is_active_val = is_active if isinstance(is_active, bool) else True
        page_num = page if isinstance(page, int) else 1
        effective_limit = (per_page if isinstance(per_page, int) else None) or (limit if isinstance(limit, int) else None) or 20
        res = svc.list_suppliers(search=search_val, city=city_val, is_active=is_active_val, page=page_num, limit=effective_limit)
        res["per_page"] = effective_limit
        res["limit"] = effective_limit
        res["total_pages"] = (res.get("total", 0) + effective_limit - 1) // effective_limit if effective_limit > 0 else 1
        res["suppliers"] = res.get("items", [])
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{supplier_id}")
async def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Get supplier details"""
    svc = SupplierService(db)
    s = svc.get_supplier(supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"success": True, "data": svc._supplier_dict(s)}


@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update supplier information"""
    try:
        svc = SupplierService(db)
        s = svc.update_supplier(supplier_id, data.dict(exclude_unset=True))
        if not s:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return {"success": True, "data": svc._supplier_dict(s), "message": "Supplier updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deactivate a supplier"""
    svc = SupplierService(db)
    if not svc.delete_supplier(supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"success": True, "message": "Supplier deactivated"}


@router.get("/{supplier_id}/products")
async def get_supplier_products(supplier_id: int, db: Session = Depends(get_db)):
    """Get all products supplied by this vendor"""
    try:
        svc = SupplierService(db)
        return {"success": True, "data": svc.get_supplier_products(supplier_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{supplier_id}/performance")
async def get_supplier_performance(supplier_id: int, db: Session = Depends(get_db)):
    """Get performance metrics for a supplier"""
    try:
        svc = SupplierService(db)
        return {"success": True, "data": svc.get_supplier_performance(supplier_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PURCHASE ORDERS ====================

@router.post("/{supplier_id}/purchase-order", status_code=201)
async def create_purchase_order(
    supplier_id: int,
    data: PurchaseOrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a purchase order for a supplier"""
    try:
        svc = SupplierService(db, current_user)
        payload = data.dict()
        payload["supplier_id"] = supplier_id
        po = svc.create_purchase_order(payload)
        return {"success": True, "data": svc._po_dict(po), "message": f"Purchase order {po.po_number} created"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/purchase-orders/all")
async def list_all_purchase_orders(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: Optional[int] = Query(None, ge=1, le=100),
    limit: Optional[int] = Query(None, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all purchase orders across all suppliers"""
    try:
        svc = SupplierService(db, current_user)
        status_val = status if isinstance(status, str) else None
        page_num = page if isinstance(page, int) else 1
        effective_limit = (per_page if isinstance(per_page, int) else None) or (limit if isinstance(limit, int) else None) or 20
        res = svc.list_purchase_orders(status=status_val, page=page_num, limit=effective_limit)
        res["per_page"] = effective_limit
        res["limit"] = effective_limit
        res["total_pages"] = (res.get("total", 0) + effective_limit - 1) // effective_limit if effective_limit > 0 else 1
        res["purchase_orders"] = res.get("items", [])
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/purchase-orders/{po_id}")
async def get_purchase_order(
    po_id: int, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get purchase order details"""
    svc = SupplierService(db, current_user)
    po = svc.get_purchase_order(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {"success": True, "data": svc._po_dict(po)}


@router.put("/purchase-orders/{po_id}/status")
async def update_po_status(
    po_id: int,
    data: UpdatePOStatusRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update purchase order status (sent, confirmed, paid, cancelled)"""
    try:
        svc = SupplierService(db, current_user)
        po = svc.update_po_status(po_id, data.status, data.notes)
        return {"success": True, "data": svc._po_dict(po), "message": f"Status updated to {data.status}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/purchase-orders/{po_id}/receive")
async def receive_goods(
    po_id: int,
    data: ReceiveGoodsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark goods as received and update inventory stock levels"""
    try:
        svc = SupplierService(db, current_user)
        po = svc.receive_goods(po_id, data.items, data.notes)
        return {
            "success": True,
            "data": svc._po_dict(po),
            "message": f"Goods received for PO {po.po_number}. Inventory updated."
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}/price-comparison")
async def compare_prices(product_id: int, db: Session = Depends(get_db)):
    """Compare prices for a product across all suppliers"""
    try:
        svc = SupplierService(db)
        return {"success": True, "data": svc.compare_supplier_prices(product_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

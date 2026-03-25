"""
Pydantic schemas for Supplier and Purchase Order management
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# ==================== SUPPLIER ====================

class SupplierCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gst_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    payment_terms_days: int = Field(default=30, ge=0, le=365)
    organization_id: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gst_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    payment_terms_days: Optional[int] = None
    is_active: Optional[bool] = None


class SupplierResponse(BaseModel):
    id: int
    supplier_code: Optional[str]
    name: str
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    gst_number: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    payment_terms_days: int
    is_active: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== PURCHASE ORDER ====================

class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    quantity_ordered: int = Field(..., gt=0)
    unit_cost: float = Field(..., gt=0)
    gst_rate: float = Field(default=18.0, ge=0, le=100)


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None
    items: List[PurchaseOrderItemCreate] = Field(..., min_items=1)


class PurchaseOrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity_ordered: int
    quantity_received: int
    unit_cost: float
    gst_rate: float
    line_total: float

    class Config:
        from_attributes = True


class PurchaseOrderResponse(BaseModel):
    id: int
    po_number: str
    supplier_id: int
    order_date: Optional[date]
    expected_delivery_date: Optional[date]
    actual_delivery_date: Optional[date]
    subtotal: float
    gst_amount: float
    total_amount: float
    status: str
    notes: Optional[str]
    created_at: Optional[datetime]
    items: List[PurchaseOrderItemResponse] = []

    class Config:
        from_attributes = True


class ReceiveGoodsRequest(BaseModel):
    items: List[dict]  # [{product_id, quantity_received}]
    notes: Optional[str] = None


class UpdatePOStatusRequest(BaseModel):
    status: str = Field(..., description="draft, sent, confirmed, received, paid, cancelled")
    notes: Optional[str] = None

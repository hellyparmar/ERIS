"""
backend/app/schemas/inventory.py
Pydantic V2 schemas for the Inventory Management API.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: Optional[str] = None
    is_active: bool = True

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Beverages",
                "slug": "beverages",
                "is_active": True,
            }
        },
    }


# ── Product ───────────────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100, description="Unique product SKU")
    barcode: Optional[str] = Field(None, max_length=100)
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = None
    category_id: Optional[int] = None
    price: Decimal = Field(..., gt=0, description="Selling price (INR)")
    cost: Decimal = Field(..., ge=0, description="Purchase / COGS price (INR)")
    tax_rate: float = Field(18.0, ge=0, le=100, description="GST percentage")
    reorder_level: int = Field(10, ge=0, description="Stock alert threshold")
    max_stock: Optional[int] = Field(None, ge=0)
    unit: str = Field("pcs", max_length=20)
    is_perishable: bool = False
    expiry_days: Optional[int] = Field(None, ge=1)


class ProductCreate(ProductBase):
    initial_stock: int = Field(0, ge=0, description="Starting stock quantity")
    store_id: Optional[UUID] = Field(None, description="Store for initial stock placement")

    model_config = {
        "json_schema_extra": {
            "example": {
                "sku": "COF-AR-001",
                "name": "Arabica Coffee Beans",
                "category_id": 1,
                "price": 45.50,
                "cost": 30.00,
                "tax_rate": 5.0,
                "reorder_level": 20,
                "unit": "kg",
                "initial_stock": 100,
            }
        }
    }

    @field_validator("cost")
    @classmethod
    def cost_less_than_price(cls, v: Decimal) -> Decimal:
        return v  # price / cost cross-validation handled in model_validator

    @model_validator(mode="after")
    def validate_margin(self) -> "ProductCreate":
        if self.cost > self.price:
            raise ValueError("Cost price cannot exceed the selling price.")
        return self


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[Decimal] = Field(None, gt=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    reorder_level: Optional[int] = Field(None, ge=0)
    max_stock: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=20)
    is_perishable: Optional[bool] = None
    expiry_days: Optional[int] = Field(None, ge=1)
    status: Optional[str] = Field(None, pattern="^(active|inactive|discontinued)$")
    is_active: Optional[bool] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "price": 49.99,
                "reorder_level": 15,
                "is_active": True,
            }
        }
    }


class ProductResponse(BaseModel):
    id: int
    sku: str
    barcode: Optional[str] = None
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    price: Decimal
    cost: Decimal
    tax_rate: float
    reorder_level: int
    stock: int = 0            # aggregate org-level stock
    status: str
    is_active: bool
    unit: str
    is_perishable: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Computed
    is_low_stock: bool = False
    margin_pct: float = 0.0

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 101,
                "sku": "COF-AR-001",
                "name": "Arabica Coffee Beans",
                "price": 45.50,
                "cost": 30.00,
                "tax_rate": 5.0,
                "stock": 85,
                "reorder_level": 20,
                "status": "active",
                "is_active": True,
                "unit": "kg",
                "is_perishable": False,
                "is_low_stock": False,
                "margin_pct": 33.85,
                "created_at": "2026-03-26T10:00:00",
            }
        },
    }


# ── Pagination wrapper ────────────────────────────────────────────────────────

class PaginatedProducts(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[ProductResponse]

    model_config = {"from_attributes": True}


# ── Low-stock alert ───────────────────────────────────────────────────────────

class LowStockResponse(BaseModel):
    product_id: int
    sku: str
    name: str
    stock: int
    reorder_level: int
    shortage: int                       # reorder_level - stock
    unit: str = "pcs"
    store_id: Optional[UUID] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "product_id": 101,
                "sku": "COF-AR-001",
                "name": "Arabica Coffee Beans",
                "stock": 5,
                "reorder_level": 20,
                "shortage": 15,
                "unit": "kg",
            }
        },
    }


# ── Stock adjustment ──────────────────────────────────────────────────────────

class StockAdjustmentReason(str):
    pass


class StockAdjustmentRequest(BaseModel):
    product_id: int = Field(..., description="Product to adjust")
    delta: int = Field(..., description="Positive = add stock, Negative = remove stock")
    reason: str = Field(..., min_length=3, max_length=255, description="Reason for adjustment")
    store_id: Optional[UUID] = Field(None, description="Store-level adjustment (optional)")
    reference: Optional[str] = Field(None, max_length=100, description="PO number, adjustment code, etc.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": 101,
                "delta": 50,
                "reason": "New stock received from PO-2026-043",
                "store_id": None,
                "reference": "PO-2026-043",
            }
        }
    }


class StockAdjustmentResponse(BaseModel):
    product_id: int
    product_name: str
    sku: str
    previous_stock: int
    delta: int
    new_stock: int
    reason: str
    adjusted_by: str         # user email or name
    adjusted_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": 101,
                "product_name": "Arabica Coffee Beans",
                "sku": "COF-AR-001",
                "previous_stock": 35,
                "delta": 50,
                "new_stock": 85,
                "reason": "New stock from PO-2026-043",
                "adjusted_by": "admin@example.com",
                "adjusted_at": "2026-03-26T11:00:00",
            }
        }
    }


# ── Store (for listing) ───────────────────────────────────────────────────────

class StoreResponse(BaseModel):
    id: UUID
    name: str
    code: Optional[str] = None
    store_type: str = "branch"
    city: Optional[str] = None
    is_active: bool = True

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Downtown Outlet",
                "code": "DT-01",
                "store_type": "branch",
                "city": "Mumbai",
                "is_active": True,
            }
        },
    }

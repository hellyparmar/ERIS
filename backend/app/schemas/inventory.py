from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from uuid import UUID

class ProductBase(BaseModel):
    sku: str
    name: str
    category: str
    subcategory: Optional[str] = None
    unit_price: Decimal
    cost_price: Optional[Decimal] = None
    hsn_code: Optional[str] = None
    gst_rate: Optional[float] = 18.0
    description: Optional[str] = None

class ProductCreate(ProductBase):
    organization_id: UUID = Field(..., description="Organization ID owning the product")
    initial_stock: int = Field(0, description="Initial stock quantity to be added")
    store_id: UUID = Field(..., description="Store ID where initial stock is located")

    model_config = {
        "json_schema_extra": {
            "example": {
                "sku": "COF-AR-001",
                "name": "Arabica Coffee Beans",
                "category": "Beverages",
                "subcategory": "Coffee",
                "unit_price": 45.50,
                "cost_price": 30.00,
                "hsn_code": "0901",
                "gst_rate": 5.0,
                "initial_stock": 100,
                "store_id": "550e8400-e29b-41d4-a716-446655440001",
                "organization_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    }

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[Decimal] = None
    gst_rate: Optional[float] = None
    is_dead_stock: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    is_dead_stock: bool
    created_at: datetime
    current_stock: Optional[int] = 0

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 101,
                "sku": "COF-AR-001",
                "name": "Arabica Coffee Beans",
                "category": "Beverages",
                "unit_price": 45.50,
                "is_dead_stock": False,
                "created_at": "2024-03-24T10:00:00",
                "current_stock": 85
            }
        }
    }

class LowStockResponse(BaseModel):
    product_id: int
    sku: str
    name: str
    current_stock: int
    reorder_point: int
    store_id: UUID

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "product_id": 101,
                "sku": "COF-AR-001",
                "name": "Arabica Coffee Beans",
                "current_stock": 5,
                "reorder_point": 10,
                "store_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        }
    }

class StoreResponse(BaseModel):
    id: UUID
    name: str
    code: Optional[str] = None
    store_type: str = "retail"
    is_active: bool = True

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Downtown Outlet",
                "code": "DT-01",
                "store_type": "retail",
                "is_active": True
            }
        }
    }

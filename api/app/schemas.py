"""Request bodies (responses are plain dicts built by the routers)."""
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class LoginIn(BaseModel):
    email: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ProfileIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)


class RefreshIn(BaseModel):
    refresh_token: str


class UserIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    role: str = Field(pattern="^(admin|manager|staff|viewer)$")
    outlet_ids: list[int] = Field(default_factory=list)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    role: str | None = Field(default=None, pattern="^(admin|manager|staff|viewer)$")
    outlet_ids: list[int] | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class OrganizationIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    industry: str | None = Field(default=None, max_length=80)
    currency: str = Field(default="INR", max_length=8)
    currency_symbol: str = Field(default="₹", max_length=4)
    timezone: str = Field(default="Asia/Kolkata", max_length=64)
    email: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = Field(default=None, max_length=255)
    tax_id: str | None = Field(default=None, max_length=32)
    state: str | None = Field(default=None, max_length=40)
    state_code: str | None = Field(default=None, pattern=r"^\d{2}$")
    low_stock_cover_days: int = Field(default=7, ge=1, le=60)

    @field_validator("tax_id")
    @classmethod
    def valid_gstin(cls, v: str | None) -> str | None:
        from app.services.gst import is_valid_gstin

        if not v or not v.strip():
            return None
        v = v.strip().upper()
        if not is_valid_gstin(v):
            raise ValueError("GSTIN is not valid (15 characters: state code, PAN, entity, Z, check digit)")
        return v

    @field_validator("timezone")
    @classmethod
    def valid_tz(cls, v: str) -> str:
        from zoneinfo import ZoneInfo

        try:
            ZoneInfo(v)
        except Exception:
            raise ValueError("Unknown time zone - use an IANA name such as Asia/Kolkata") from None
        return v


class OutletIn(BaseModel):
    code: str = Field(min_length=2, max_length=16, pattern=r"^[A-Za-z0-9-]+$")
    name: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=80)
    state: str | None = Field(default=None, max_length=40)
    state_code: str | None = Field(default=None, pattern=r"^\d{2}$")
    address: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    manager_name: str | None = Field(default=None, max_length=120)
    opened_on: date | None = None
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()


class CategoryIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class ProductIn(BaseModel):
    sku: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    name: str = Field(min_length=2, max_length=160)
    category_id: int
    supplier_id: int | None = None
    unit: str = Field(default="pcs", max_length=16)
    cost_price: float = Field(ge=0)
    selling_price: float = Field(gt=0)
    tax_rate: float = Field(default=5, ge=0, le=40)
    reorder_level: float = Field(default=10, ge=0)
    hsn_code: str | None = Field(default=None, pattern=r"^\d{4,8}$")
    is_active: bool = True

    @field_validator("sku")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode="after")
    def price_covers_cost(self) -> "ProductIn":
        # same rule as the CSV importer; temporary discounts belong in promotions, not in the base price
        if self.selling_price < self.cost_price:
            raise ValueError("selling_price is below cost_price")
        return self


class SupplierIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    contact_person: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=80)
    lead_time_days: int = Field(default=3, ge=0, le=90)
    payment_terms: str | None = Field(default=None, max_length=60)
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool = True


class CustomerIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=80)
    customer_type: str = Field(default="retail", pattern="^(retail|business)$")
    gstin: str | None = Field(default=None, max_length=15)
    state_code: str | None = Field(default=None, pattern=r"^\d{2}$")
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("gstin")
    @classmethod
    def valid_gstin(cls, v: str | None) -> str | None:
        from app.services.gst import is_valid_gstin

        if not v:
            return None
        v = v.strip().upper()
        if not is_valid_gstin(v):
            raise ValueError("GSTIN is not valid (15 characters with a correct check digit)")
        return v


class SaleLineIn(BaseModel):
    product_id: int
    quantity: float = Field(gt=0, le=100000)
    unit_price: float | None = Field(default=None, ge=0)
    discount: float = Field(default=0, ge=0)


class SaleIn(BaseModel):
    outlet_id: int
    items: list[SaleLineIn] = Field(min_length=1, max_length=200)
    sold_at: datetime | None = None
    payment_method: str = "cash"
    channel: str = "in_store"
    customer_id: int | None = None
    customer_phone: str | None = None
    customer_name: str | None = None
    bill_discount: float = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=255)


class VoidIn(BaseModel):
    reason: str = Field(min_length=3, max_length=200)


class StockAdjustIn(BaseModel):
    outlet_id: int
    product_id: int
    mode: str = Field(pattern="^(set|add|remove)$")
    quantity: float = Field(ge=0)
    reason: str = Field(default="adjustment", pattern="^(adjustment|damage|purchase)$")
    note: str | None = Field(default=None, max_length=255)


class TransferIn(BaseModel):
    from_outlet_id: int
    to_outlet_id: int
    product_id: int
    quantity: float = Field(gt=0)
    note: str | None = Field(default=None, max_length=255)


class ReorderLevelIn(BaseModel):
    reorder_level: float = Field(ge=0)


class POLineIn(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    unit_cost: float | None = Field(default=None, ge=0)


class PurchaseOrderIn(BaseModel):
    supplier_id: int
    outlet_id: int
    items: list[POLineIn] = Field(min_length=1, max_length=300)
    expected_date: date | None = None
    notes: str | None = Field(default=None, max_length=255)


class ReceiveLineIn(BaseModel):
    product_id: int
    quantity: float = Field(ge=0)


class ReceiveIn(BaseModel):
    items: list[ReceiveLineIn] | None = None  # None = receive everything as ordered


class ReorderCreateIn(BaseModel):
    lines: list[dict] = Field(min_length=1)  # rows from reorder suggestions: outlet_id, product_id, quantity


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=500)

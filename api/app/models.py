"""ORM models.

ERIS manages a single organization (a retail business) that runs several outlets.
Money values are stored as floats rounded to 2 decimals; selling prices are tax-inclusive (MRP style),
and the tax portion of a line is derived from the product's tax rate.
"""
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import clock
from app.db import Base

# admin: everything · manager: operations for assigned outlets · staff: billing & stock lookup ·
# viewer: read-only dashboards, forecasts, analytics and AI questions
ROLES = ("admin", "manager", "staff", "viewer")
MAX_OUTLETS = 7
OPEN_PO_STATUSES = ("ordered", "partial")  # partial = some goods received, the rest still expected
SALE_SOURCES = ("synthetic", "manual", "import")
PAYMENT_METHODS = ("cash", "upi", "card", "credit")
CHANNELS = ("in_store", "delivery")
SALE_STATUSES = ("completed", "void")
PO_STATUSES = ("ordered", "received", "cancelled")
MOVEMENT_REASONS = (
    "sale",
    "sale_void",
    "purchase",
    "adjustment",
    "damage",
    "transfer_in",
    "transfer_out",
    "import",
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now, server_default=func.now())


class Organization(TimestampMixin, Base):
    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    industry: Mapped[str] = mapped_column(String(80), default="Food & Beverage Retail")
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    currency_symbol: Mapped[str] = mapped_column(String(4), default="₹")
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata")
    email: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(32))
    address: Mapped[str | None] = mapped_column(String(255))
    tax_id: Mapped[str | None] = mapped_column(String(32))  # GSTIN
    tax_id_is_demo: Mapped[bool] = mapped_column(Boolean, default=False)  # synthetic GSTIN, never for filing
    state: Mapped[str | None] = mapped_column(String(40))
    state_code: Mapped[str | None] = mapped_column(String(2))  # GST state code, e.g. 27 = Maharashtra
    # An item is "low stock" when it covers fewer days of demand than this (or is below its reorder level).
    low_stock_cover_days: Mapped[int] = mapped_column(Integer, default=7)


class Outlet(TimestampMixin, Base):
    __tablename__ = "outlets"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str | None] = mapped_column(String(40))
    state_code: Mapped[str | None] = mapped_column(String(2))
    address: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32))
    manager_name: Mapped[str | None] = mapped_column(String(120))
    opened_on: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


user_outlets = Table(
    "user_outlets", Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("outlet_id", ForeignKey("outlets.id", ondelete="CASCADE"), primary_key=True),
)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="staff")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    # Bumped on password change / sign-out everywhere to invalidate refresh tokens.
    token_version: Mapped[int] = mapped_column(Integer, default=0)

    # Admins see every outlet; everyone else only the outlets assigned here.
    outlets: Mapped[list[Outlet]] = relationship(secondary=user_outlets, order_by="Outlet.id")

    @property
    def outlet_ids(self) -> list[int]:
        return [o.id for o in self.outlets]


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)


class Supplier(TimestampMixin, Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    contact_person: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(160))
    city: Mapped[str | None] = mapped_column(String(80))
    lead_time_days: Mapped[int] = mapped_column(Integer, default=3)
    payment_terms: Mapped[str | None] = mapped_column(String(60))
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"))
    unit: Mapped[str] = mapped_column(String(16), default="pcs")
    cost_price: Mapped[float] = mapped_column(Float)
    selling_price: Mapped[float] = mapped_column(Float)  # tax inclusive
    tax_rate: Mapped[float] = mapped_column(Float, default=5.0)  # percent
    reorder_level: Mapped[float] = mapped_column(Float, default=10)  # default per outlet
    hsn_code: Mapped[str | None] = mapped_column(String(8))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped[Category] = relationship()
    supplier: Mapped[Supplier | None] = relationship()


class InventoryItem(Base):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("outlet_id", "product_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    outlet_id: Mapped[int] = mapped_column(ForeignKey("outlets.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[float] = mapped_column(Float, default=0)
    reorder_level: Mapped[float] = mapped_column(Float, default=10)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now, server_default=func.now(), onupdate=clock.now)

    outlet: Mapped[Outlet] = relationship()
    product: Mapped[Product] = relationship()


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (Index("ix_movements_outlet_product", "outlet_id", "product_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    outlet_id: Mapped[int] = mapped_column(ForeignKey("outlets.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    change: Mapped[float] = mapped_column(Float)
    balance_after: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String(20))
    reference: Mapped[str | None] = mapped_column(String(64))
    note: Mapped[str | None] = mapped_column(String(255))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now, server_default=func.now(), index=True)

    product: Mapped[Product] = relationship()
    outlet: Mapped[Outlet] = relationship()
    user: Mapped[User | None] = relationship()


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    email: Mapped[str | None] = mapped_column(String(160))
    city: Mapped[str | None] = mapped_column(String(80))
    customer_type: Mapped[str] = mapped_column(String(16), default="retail")  # retail | business
    gstin: Mapped[str | None] = mapped_column(String(15))
    state_code: Mapped[str | None] = mapped_column(String(2))
    notes: Mapped[str | None] = mapped_column(Text)


class Sale(TimestampMixin, Base):
    __tablename__ = "sales"
    __table_args__ = (
        Index("ix_sales_outlet_date", "outlet_id", "sale_date"),
        Index("ix_sales_status_date", "status", "sale_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_no: Mapped[str] = mapped_column(String(32), unique=True)
    outlet_id: Mapped[int] = mapped_column(ForeignKey("outlets.id"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), index=True)
    sold_at: Mapped[datetime] = mapped_column(DateTime)
    sale_date: Mapped[date] = mapped_column(Date, index=True)
    channel: Mapped[str] = mapped_column(String(16), default="in_store")
    payment_method: Mapped[str] = mapped_column(String(16), default="cash")
    subtotal: Mapped[float] = mapped_column(Float)  # before discount, tax inclusive
    discount: Mapped[float] = mapped_column(Float, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float)  # amount paid
    items_count: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(12), default="completed")
    source: Mapped[str] = mapped_column(String(12), default="manual")  # synthetic | manual | import
    dataset_id: Mapped[int | None] = mapped_column(ForeignKey("dataset_info.id", ondelete="SET NULL"))
    import_id: Mapped[int | None] = mapped_column(ForeignKey("import_jobs.id", ondelete="SET NULL"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    notes: Mapped[str | None] = mapped_column(String(255))

    outlet: Mapped[Outlet] = relationship()
    customer: Mapped[Customer | None] = relationship()
    items: Mapped[list["SaleItem"]] = relationship(back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"
    __table_args__ = (
        Index("ix_sale_items_product_date", "product_id", "sale_date"),
        Index("ix_sale_items_outlet_date", "outlet_id", "sale_date"),
        Index("ix_sale_items_date", "sale_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    # Denormalised from the sale header so product-level analytics avoid a join.
    outlet_id: Mapped[int] = mapped_column(ForeignKey("outlets.id"))
    sale_date: Mapped[date] = mapped_column(Date)
    quantity: Mapped[float] = mapped_column(Float)
    unit_price: Mapped[float] = mapped_column(Float)
    list_price: Mapped[float | None] = mapped_column(Float)  # regular price when a promotion applied
    promotion_id: Mapped[int | None] = mapped_column(ForeignKey("promotions.id", ondelete="SET NULL"))
    discount: Mapped[float] = mapped_column(Float, default=0)
    line_total: Mapped[float] = mapped_column(Float)  # after discount, tax inclusive
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    cost_amount: Mapped[float] = mapped_column(Float, default=0)  # cost snapshot for margin analysis

    sale: Mapped[Sale] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    po_number: Mapped[str] = mapped_column(String(32), unique=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    outlet_id: Mapped[int] = mapped_column(ForeignKey("outlets.id"))
    status: Mapped[str] = mapped_column(String(12), default="ordered")
    order_date: Mapped[date] = mapped_column(Date)
    expected_date: Mapped[date | None] = mapped_column(Date)
    received_date: Mapped[date | None] = mapped_column(Date)
    total_cost: Mapped[float] = mapped_column(Float, default=0)
    notes: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    supplier: Mapped[Supplier] = relationship()
    outlet: Mapped[Outlet] = relationship()
    items: Mapped[list["PurchaseOrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Float)  # ordered
    received_quantity: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    unit_cost: Mapped[float] = mapped_column(Float)

    order: Mapped[PurchaseOrder] = relationship(back_populates="items")

    @property
    def outstanding(self) -> float:
        return max(0.0, round(self.quantity - (self.received_quantity or 0.0), 3))
    product: Mapped[Product] = relationship()


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(12))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now, server_default=func.now())


# --------------------------------------------------------------------------------------------- provenance
class DatasetInfo(Base):
    """One row per generated dataset - every synthetic sale points here (provenance)."""
    __tablename__ = "dataset_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_source: Mapped[str] = mapped_column(String(20), default="synthetic")
    generator_version: Mapped[str] = mapped_column(String(20))
    random_seed: Mapped[int] = mapped_column(Integer)
    generated_at: Mapped[datetime] = mapped_column(DateTime)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    parameters: Mapped[dict | None] = mapped_column(JSON)
    row_counts: Mapped[dict | None] = mapped_column(JSON)


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    filename: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16))  # committed | rejected | validated
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    mapping: Mapped[dict | None] = mapped_column(JSON)
    errors: Mapped[list | None] = mapped_column(JSON)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now, server_default=func.now(), index=True)

    user: Mapped[User | None] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(40), index=True)  # e.g. sale.create, stock.adjust, import.commit
    entity: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str | None] = mapped_column(String(40))
    outlet_id: Mapped[int | None] = mapped_column(ForeignKey("outlets.id", ondelete="SET NULL"))
    summary: Mapped[str] = mapped_column(String(255))
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now, server_default=func.now(), index=True)

    user: Mapped[User | None] = relationship()


# --------------------------------------------------------------------------------------------- demand drivers
class Promotion(TimestampMixin, Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    outlet_id: Mapped[int | None] = mapped_column(ForeignKey("outlets.id", ondelete="CASCADE"))  # None = all
    discount_pct: Mapped[float] = mapped_column(Float)
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date, index=True)

    category: Mapped[Category | None] = relationship()
    product: Mapped[Product | None] = relationship()
    outlet: Mapped[Outlet | None] = relationship()


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    effective_from: Mapped[date] = mapped_column(Date)
    selling_price: Mapped[float] = mapped_column(Float)
    cost_price: Mapped[float] = mapped_column(Float)


class WeatherDaily(Base):
    __tablename__ = "weather_daily"
    __table_args__ = (UniqueConstraint("city", "day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column(String(80))
    day: Mapped[date] = mapped_column(Date, index=True)
    temp_max_c: Mapped[float] = mapped_column(Float)
    rain_mm: Mapped[float] = mapped_column(Float)
    is_forecast: Mapped[bool] = mapped_column(Boolean, default=False)  # climatology for future days


class StockoutEvent(Base):
    __tablename__ = "stockout_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    outlet_id: Mapped[int] = mapped_column(ForeignKey("outlets.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    substitute_product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))


class AnomalyLabel(Base):
    """Ground truth for anomalies deliberately injected by the generator (used to score the detector)."""
    __tablename__ = "anomaly_labels"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    outlet_id: Mapped[int] = mapped_column(ForeignKey("outlets.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(30))  # pos_outage | bulk_order | entry_error | local_event
    direction: Mapped[str] = mapped_column(String(4))  # up | down
    description: Mapped[str] = mapped_column(String(255))
    magnitude: Mapped[float] = mapped_column(Float)  # multiplicative effect on the day's revenue

    outlet: Mapped[Outlet] = relationship()


# --------------------------------------------------------------------------------------------- forecasting
class ForecastRun(Base):
    __tablename__ = "forecast_runs"
    __table_args__ = (Index("ix_forecast_runs_lookup", "scope", "target", "data_end", "fingerprint"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    run_type: Mapped[str] = mapped_column(String(16), default="forecast")  # forecast | evaluation
    scope: Mapped[str] = mapped_column(String(16))
    target: Mapped[str] = mapped_column(String(16))
    series_label: Mapped[str] = mapped_column(String(160))
    outlet_ids: Mapped[list | None] = mapped_column(JSON)
    category_id: Mapped[int | None] = mapped_column(Integer)
    product_id: Mapped[int | None] = mapped_column(Integer)
    horizon: Mapped[int] = mapped_column(Integer)
    data_start: Mapped[date | None] = mapped_column(Date)
    data_end: Mapped[date | None] = mapped_column(Date)
    selected_model: Mapped[str | None] = mapped_column(String(40))
    model_version: Mapped[str] = mapped_column(String(20))
    features: Mapped[list | None] = mapped_column(JSON)
    parameters: Mapped[dict | None] = mapped_column(JSON)
    metrics: Mapped[list | None] = mapped_column(JSON)  # per-model back-test metrics
    status: Mapped[str] = mapped_column(String(12), default="ok")  # ok | failed | running
    error: Mapped[str | None] = mapped_column(String(500))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now, server_default=func.now(), index=True)
    # compact, date-free result + input fingerprint: an identical request is answered without refitting
    core: Mapped[dict | None] = mapped_column(JSON)
    fingerprint: Mapped[str | None] = mapped_column(String(64))

    results: Mapped[list["ForecastResult"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class ResponseCache(Base):
    """Analytics answers kept per user, request and data version (see app/services/response_cache.py)."""
    __tablename__ = "response_cache"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    version: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now, server_default=func.now())


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("forecast_runs.id", ondelete="CASCADE"), index=True)
    day: Mapped[date] = mapped_column(Date)
    yhat: Mapped[float] = mapped_column(Float)
    lower: Mapped[float] = mapped_column(Float)
    upper: Mapped[float] = mapped_column(Float)

    run: Mapped[ForecastRun] = relationship(back_populates="results")


# --------------------------------------------------------------------------------------------- GST demo invoices
class Invoice(Base):
    """Demo GST tax invoice for a sale. Uses a synthetic GSTIN - never for real tax filing or IRN."""
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(32), unique=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime)
    seller_gstin: Mapped[str | None] = mapped_column(String(15))
    buyer_name: Mapped[str | None] = mapped_column(String(120))
    buyer_gstin: Mapped[str | None] = mapped_column(String(15))
    place_of_supply: Mapped[str | None] = mapped_column(String(2))  # state code
    supply_type: Mapped[str] = mapped_column(String(12))  # intra_state | inter_state
    taxable_value: Mapped[float] = mapped_column(Float)
    cgst: Mapped[float] = mapped_column(Float, default=0)
    sgst: Mapped[float] = mapped_column(Float, default=0)
    igst: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    sale: Mapped[Sale] = relationship()

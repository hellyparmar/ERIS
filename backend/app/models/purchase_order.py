"""
Purchase Order Models
"""

from sqlalchemy import String, Integer, Float, Date, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
import enum

class PurchaseOrderStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    confirmed = "confirmed"
    delivered = "delivered"
    cancelled = "cancelled"

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    outlet_id: Mapped[int] = mapped_column(Integer, ForeignKey("outlets.id"), nullable=False)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    status: Mapped[PurchaseOrderStatus] = mapped_column(Enum(PurchaseOrderStatus), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    expected_delivery_date: Mapped[Date] = mapped_column(Date, nullable=True)
    actual_delivery_date: Mapped[Date] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
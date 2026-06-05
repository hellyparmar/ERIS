"""
Sales Models
"""

from sqlalchemy import Integer, ForeignKey, Float, String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class SaleTransaction(Base):
    __tablename__ = "sales_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    outlet_id: Mapped[int] = mapped_column(Integer, ForeignKey("outlets.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    gst_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    transaction_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    cashier_id: Mapped[int] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_sales_outlet_transaction_at", "outlet_id", "transaction_at"),
        Index("idx_sales_product_id", "product_id"),
    )
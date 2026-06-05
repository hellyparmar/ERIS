"""
Invoice Models
"""

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    outlet_id: Mapped[int] = mapped_column(Integer, ForeignKey("outlets.id"), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    invoice_type: Mapped[str] = mapped_column(String(20), nullable=False)
    customer_gstin: Mapped[str] = mapped_column(String(20), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=True)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    cgst_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sgst_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    igst_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    pdf_path: Mapped[str] = mapped_column(String(500), nullable=True)
    issued_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    sales: Mapped[list["Sale"]] = relationship("Sale", back_populates="invoice")
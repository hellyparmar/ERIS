"""
Inventory Models
"""

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, default=1)
    outlet_id = Column(Integer, ForeignKey("outlets.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    current_stock = Column(Integer, default=0, nullable=False)
    reserved_stock = Column(Integer, default=0, nullable=False)
    last_restocked_at = Column(DateTime(timezone=True), nullable=True)
    next_expiry_date = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_inventory_outlet_product", "outlet_id", "product_id"),
        UniqueConstraint("outlet_id", "product_id", name="uq_inventory_outlet_product"),
    )

    product = relationship("Product")

    @property
    def available_stock(self) -> int:
        return self.current_stock - self.reserved_stock

    @property
    def reorder_point(self) -> int:
        if self.product:
            return self.product.reorder_level
        return 10

    @property
    def stock_status(self) -> str:
        return getattr(self, "_stock_status", "high")

    @stock_status.setter
    def stock_status(self, value):
        self._stock_status = value

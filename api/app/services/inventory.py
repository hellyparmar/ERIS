"""Stock bookkeeping. Every change to a stock level goes through `change_stock`, which records a movement."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InventoryItem, Product, StockMovement


def stock_status(quantity: float, reorder_level: float) -> str:
    if quantity <= 0:
        return "out_of_stock" if reorder_level > 0 else "no_stock"
    if quantity <= reorder_level:
        return "low"
    return "ok"


def get_or_create_item(db: Session, outlet_id: int, product_id: int) -> InventoryItem:
    item = db.scalar(select(InventoryItem).where(InventoryItem.outlet_id == outlet_id,
                                                 InventoryItem.product_id == product_id))
    if item is None:
        product = db.get(Product, product_id)
        item = InventoryItem(outlet_id=outlet_id, product_id=product_id, quantity=0,
                             reorder_level=product.reorder_level if product else 10)
        db.add(item)
        db.flush()
    return item


def change_stock(db: Session, outlet_id: int, product_id: int, change: float, reason: str, user_id: int | None,
                 reference: str | None = None, note: str | None = None, allow_negative: bool = False) -> InventoryItem:
    item = get_or_create_item(db, outlet_id, product_id)
    new_qty = round(item.quantity + change, 3)
    if new_qty < 0 and not allow_negative:
        product = db.get(Product, product_id)
        raise HTTPException(
            400, f"Not enough stock for {product.name if product else product_id}: "
                 f"{item.quantity:g} available, {abs(change):g} requested")
    item.quantity = new_qty
    db.add(StockMovement(outlet_id=outlet_id, product_id=product_id, change=change, balance_after=new_qty,
                         reason=reason, reference=reference, note=note, user_id=user_id))
    return item


def set_stock(db: Session, outlet_id: int, product_id: int, quantity: float, user_id: int | None,
              reason: str = "adjustment", reference: str | None = None, note: str | None = None) -> InventoryItem:
    if quantity < 0:
        raise HTTPException(400, "Stock quantity cannot be negative")
    item = get_or_create_item(db, outlet_id, product_id)
    return change_stock(db, outlet_id, product_id, quantity - item.quantity, reason, user_id, reference, note)

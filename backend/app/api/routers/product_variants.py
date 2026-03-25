"""
Phase 2 — Product Variants Router
Handles product variant management (size, color, unit).
Endpoint: /api/v1/inventory/variants
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import logging

from app.api.db import get_db

router = APIRouter(prefix="/api/v1/inventory", tags=["Product Variants"])
logger = logging.getLogger(__name__)

# ── Schema ─────────────────────────────────────────────────────────────────────

class VariantCreate(BaseModel):
    product_id: int
    variant_name: str          # e.g. "500ml", "Red/Large"
    size: Optional[str] = None
    color: Optional[str] = None
    unit: Optional[str] = None  # "kg", "litre", "piece"
    price_modifier: float = 0.0  # +/- from base price
    sku_suffix: Optional[str] = None   # appended to parent SKU
    stock: int = 0

class VariantUpdate(BaseModel):
    variant_name: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    unit: Optional[str] = None
    price_modifier: Optional[float] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None


# ── Ensure Table Exists ────────────────────────────────────────────────────────

def ensure_variants_table(db: Session):
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS product_variants (
            id               SERIAL PRIMARY KEY,
            product_id       INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            variant_name     VARCHAR(100) NOT NULL,
            size             VARCHAR(50),
            color            VARCHAR(50),
            unit             VARCHAR(20),
            price_modifier   NUMERIC(10,2) DEFAULT 0,
            sku_suffix       VARCHAR(50),
            stock            INTEGER DEFAULT 0,
            is_active        BOOLEAN DEFAULT TRUE,
            created_at       TIMESTAMP DEFAULT NOW(),
            updated_at       TIMESTAMP DEFAULT NOW()
        )
    """))
    db.commit()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/variants")
async def list_variants(
    product_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List product variants, optionally filtered by product_id."""
    ensure_variants_table(db)
    try:
        where = "WHERE pv.product_id = :pid" if product_id else ""
        rows = db.execute(text(f"""
            SELECT pv.id, pv.product_id, p.name as product_name, p.sku as base_sku,
                   pv.variant_name, pv.size, pv.color, pv.unit,
                   pv.price_modifier, pv.sku_suffix, pv.stock, pv.is_active,
                   p.unit_price,
                   (p.unit_price + COALESCE(pv.price_modifier, 0)) as variant_price
            FROM product_variants pv
            JOIN products p ON p.id = pv.product_id
            {where}
            ORDER BY pv.product_id, pv.id
        """), {"pid": product_id} if product_id else {}).fetchall()

        return {
            "success": True,
            "count": len(rows),
            "data": [
                {
                    "id": r[0],
                    "product_id": r[1],
                    "product_name": r[2],
                    "base_sku": r[3],
                    "variant_name": r[4],
                    "size": r[5],
                    "color": r[6],
                    "unit": r[7],
                    "price_modifier": float(r[8] or 0),
                    "sku_suffix": r[9],
                    "stock": r[10],
                    "is_active": r[11],
                    "base_price": float(r[12] or 0),
                    "variant_price": float(r[13] or 0),
                }
                for r in rows
            ]
        }
    except Exception as e:
        logger.error(f"List variants error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/variants", status_code=201)
async def create_variant(variant: VariantCreate, db: Session = Depends(get_db)):
    """Create a new product variant."""
    ensure_variants_table(db)
    # Verify product exists
    prod = db.execute(text("SELECT id FROM products WHERE id = :pid"), {"pid": variant.product_id}).fetchone()
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product {variant.product_id} not found")

    row = db.execute(text("""
        INSERT INTO product_variants
            (product_id, variant_name, size, color, unit, price_modifier, sku_suffix, stock)
        VALUES
            (:product_id, :variant_name, :size, :color, :unit, :price_modifier, :sku_suffix, :stock)
        RETURNING id
    """), {
        "product_id": variant.product_id,
        "variant_name": variant.variant_name,
        "size": variant.size,
        "color": variant.color,
        "unit": variant.unit,
        "price_modifier": variant.price_modifier,
        "sku_suffix": variant.sku_suffix,
        "stock": variant.stock,
    }).fetchone()
    db.commit()
    return {"success": True, "variant_id": row[0], "message": "Variant created"}


@router.patch("/variants/{variant_id}")
async def update_variant(variant_id: int, update: VariantUpdate, db: Session = Depends(get_db)):
    """Update a product variant."""
    ensure_variants_table(db)
    fields = {k: v for k, v in update.dict().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    fields["vid"] = variant_id
    result = db.execute(text(f"UPDATE product_variants SET {set_clause}, updated_at=NOW() WHERE id = :vid"), fields)
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Variant {variant_id} not found")
    return {"success": True, "message": "Variant updated"}


@router.delete("/variants/{variant_id}")
async def delete_variant(variant_id: int, db: Session = Depends(get_db)):
    """Soft-delete a variant (set is_active=False)."""
    ensure_variants_table(db)
    result = db.execute(
        text("UPDATE product_variants SET is_active=FALSE, updated_at=NOW() WHERE id = :vid"),
        {"vid": variant_id}
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Variant {variant_id} not found")
    return {"success": True, "message": "Variant deactivated"}

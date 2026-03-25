"""
Configurable GST Rates - P3-T5
Business type selection, pre-loaded GST slabs, per-category rates
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/gst-config", tags=["GST Configuration"])

from app.api.db import get_db

# ═══════════════════════════════════════════════════════
# PRE-LOADED GST SLABS  (India 2024-25)
# ═══════════════════════════════════════════════════════

GST_SLABS = {
    "0": {"rate": 0, "description": "Exempt", "examples": ["fresh food", "books", "vegetables"]},
    "5": {"rate": 5, "description": "Reduced Rate", "examples": ["edible oils", "tea", "coffee", "coal"]},
    "12": {"rate": 12, "description": "Standard Rate (Lower)", "examples": ["processed food", "business class flights", "mobile phones"]},
    "18": {"rate": 18, "description": "Standard Rate", "examples": ["electronics", "furniture", "AC", "computers", "services"]},
    "28": {"rate": 28, "description": "Luxury / Demerit Rate", "examples": ["automobiles", "tobacco", "luxury goods", "aerated drinks"]}
}

# Default rates per common retail categories
DEFAULT_CATEGORY_GST = {
    "food": 5,
    "beverages": 12,
    "dairy": 5,
    "snacks": 12,
    "groceries": 0,
    "vegetables": 0,
    "fruits": 0,
    "electronics": 18,
    "mobile": 18,
    "clothing": 12,
    "footwear": 12,
    "furniture": 18,
    "pharma": 12,
    "toys": 12,
    "stationery": 12,
    "cleaning": 18,
    "luxury": 28,
    "tobacco": 28,
    "default": 18
}

BUSINESS_TYPES = {
    "grocery": {"name": "Grocery / Kirana Store", "default_category": "groceries", "typical_gst": 0},
    "restaurant": {"name": "Restaurant / Food Service", "default_category": "food", "typical_gst": 5},
    "pharmacy": {"name": "Pharmacy / Medical", "default_category": "pharma", "typical_gst": 12},
    "electronics": {"name": "Electronics / Mobile Shop", "default_category": "electronics", "typical_gst": 18},
    "clothing": {"name": "Clothing / Apparel", "default_category": "clothing", "typical_gst": 12},
    "general": {"name": "General Merchandise", "default_category": "default", "typical_gst": 18}
}

# ═══════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════

class GSTRateUpdate(BaseModel):
    category: str
    gst_rate: float
    hsn_code: Optional[str] = None
    description: Optional[str] = None

class BusinessTypeConfig(BaseModel):
    business_type: str
    store_id: Optional[int] = 1

# ═══════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════

@router.get("/slabs")
async def get_gst_slabs():
    """Get all available GST slabs with examples"""
    return {
        "slabs": GST_SLABS,
        "note": "Indian GST rates as per 2024-25 schedule"
    }

@router.get("/business-types")
async def get_business_types():
    """Get all supported business types with recommended GST profile"""
    return {
        "business_types": [
            {
                "id": k,
                "name": v["name"],
                "typical_gst_rate": v["typical_gst"],
                "default_category": v["default_category"]
            }
            for k, v in BUSINESS_TYPES.items()
        ]
    }

@router.get("/category-rates")
async def get_category_rates(db=Depends(get_db)):
    """Get effective GST rates per category (DB overrides or defaults)"""
    try:
        # Get any overrides from DB
        overrides = db.execute(text("""
            SELECT category, gst_rate, hsn_code, description, updated_at
            FROM gst_category_rates
            ORDER BY category
        """)).fetchall()

        db_rates = {r[0]: {"rate": float(r[1]), "hsn": r[2], "description": r[3], "source": "custom", "updated": r[4].isoformat() if r[4] else None} for r in overrides}
    except Exception:
        db_rates = {}

    result = {}
    for cat, default_rate in DEFAULT_CATEGORY_GST.items():
        if cat in db_rates:
            result[cat] = db_rates[cat]
        else:
            result[cat] = {
                "rate": default_rate,
                "hsn": "",
                "description": cat.title(),
                "source": "default",
                "updated": None
            }

    return {"category_rates": result, "total_categories": len(result)}

@router.post("/category-rates")
async def set_category_rate(req: GSTRateUpdate, db=Depends(get_db)):
    """Set or override GST rate for a specific category"""
    if req.gst_rate not in [0, 5, 12, 18, 28]:
        raise HTTPException(status_code=400, detail="GST rate must be one of: 0, 5, 12, 18, 28")

    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS gst_category_rates (
                id SERIAL PRIMARY KEY,
                category VARCHAR(100) UNIQUE NOT NULL,
                gst_rate DECIMAL(5,2) NOT NULL,
                hsn_code VARCHAR(20),
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))

        db.execute(text("""
            INSERT INTO gst_category_rates (category, gst_rate, hsn_code, description)
            VALUES (:cat, :rate, :hsn, :desc)
            ON CONFLICT (category) DO UPDATE
            SET gst_rate = EXCLUDED.gst_rate,
                hsn_code = EXCLUDED.hsn_code,
                description = EXCLUDED.description,
                updated_at = NOW()
        """), {
            "cat": req.category.lower(),
            "rate": req.gst_rate,
            "hsn": req.hsn_code or "",
            "desc": req.description or req.category.title()
        })
        db.commit()

        return {
            "success": True,
            "message": f"GST rate for '{req.category}' set to {req.gst_rate}%",
            "category": req.category,
            "gst_rate": req.gst_rate
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apply-business-type")
async def apply_business_type(req: BusinessTypeConfig, db=Depends(get_db)):
    """Apply a business type profile to pre-populate GST rates"""
    if req.business_type not in BUSINESS_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown business type. Valid: {list(BUSINESS_TYPES.keys())}")

    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS gst_category_rates (
                id SERIAL PRIMARY KEY,
                category VARCHAR(100) UNIQUE NOT NULL,
                gst_rate DECIMAL(5,2) NOT NULL,
                hsn_code VARCHAR(20),
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))

        btype = BUSINESS_TYPES[req.business_type]
        default_rate = btype["typical_gst"]

        # Bulk insert defaults for this business type
        applied = 0
        for cat, rate in DEFAULT_CATEGORY_GST.items():
            if cat == "default":
                continue
            db.execute(text("""
                INSERT INTO gst_category_rates (category, gst_rate, description)
                VALUES (:cat, :rate, :desc)
                ON CONFLICT (category) DO UPDATE SET gst_rate = EXCLUDED.gst_rate, updated_at=NOW()
            """), {"cat": cat, "rate": rate, "desc": f"{cat.title()} - {req.business_type} profile"})
            applied += 1

        db.commit()

        return {
            "success": True,
            "business_type": req.business_type,
            "business_name": btype["name"],
            "rates_applied": applied,
            "message": f"Applied {btype['name']} GST profile successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/product-gst/{product_id}")
async def get_product_gst(product_id: int, db=Depends(get_db)):
    """Get effective GST rate for a specific product"""
    try:
        product = db.execute(text("""
            SELECT id, name, category, gst_rate, hsn_code FROM products WHERE id = :pid
        """), {"pid": product_id}).fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Check for custom override
        try:
            override = db.execute(text("""
                SELECT gst_rate FROM gst_category_rates WHERE category = LOWER(:cat)
            """), {"cat": product[2] or "default"}).scalar()
        except Exception:
            override = None

        effective_rate = float(override) if override else float(product[3] or 18)

        return {
            "product_id": product[0],
            "product_name": product[1],
            "category": product[2],
            "hsn_code": product[4] or "9999",
            "gst_rate_on_product": float(product[3] or 18),
            "override_rate": float(override) if override else None,
            "effective_gst_rate": effective_rate,
            "cgst": effective_rate / 2,
            "sgst": effective_rate / 2
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

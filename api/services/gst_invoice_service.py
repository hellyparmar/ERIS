"""
GST Invoice Service
Generate GST-compliant invoice data with CGST/SGST/IGST breakdown
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# GST rate lookup by category
GST_RATES_BY_CATEGORY = {
    "electronics": 18,
    "clothing": 12,
    "food": 5,
    "pharma": 12,
    "luxury": 28,
    "essentials": 0,
    "default": 18,
}

SELLER_STATE_CODE = "29"  # Karnataka (default — from business config)


def is_interstate(buyer_state_code: Optional[str]) -> bool:
    """Determine if sale is interstate (IGST) or intra-state (CGST+SGST)"""
    if not buyer_state_code:
        return False
    return buyer_state_code != SELLER_STATE_CODE


def calculate_line_item_gst(
    unit_price: float,
    quantity: int,
    gst_rate: float,
    discount_pct: float = 0.0,
    inter_state: bool = False
) -> Dict[str, float]:
    """
    Calculate GST for a single line item.
    Returns detailed breakdown: taxable_value, cgst, sgst, igst, total.
    """
    subtotal = unit_price * quantity
    discount = subtotal * (discount_pct / 100)
    taxable = subtotal - discount
    total_gst = taxable * (gst_rate / 100)

    if inter_state:
        return {
            "subtotal": round(subtotal, 2),
            "discount": round(discount, 2),
            "taxable_value": round(taxable, 2),
            "cgst_rate": 0.0,
            "sgst_rate": 0.0,
            "igst_rate": gst_rate,
            "cgst_amount": 0.0,
            "sgst_amount": 0.0,
            "igst_amount": round(total_gst, 2),
            "total_gst": round(total_gst, 2),
            "line_total": round(taxable + total_gst, 2),
        }
    else:
        half = gst_rate / 2
        return {
            "subtotal": round(subtotal, 2),
            "discount": round(discount, 2),
            "taxable_value": round(taxable, 2),
            "cgst_rate": half,
            "sgst_rate": half,
            "igst_rate": 0.0,
            "cgst_amount": round(total_gst / 2, 2),
            "sgst_amount": round(total_gst / 2, 2),
            "igst_amount": 0.0,
            "total_gst": round(total_gst, 2),
            "line_total": round(taxable + total_gst, 2),
        }


def generate_invoice_for_sale(
    db: Session,
    sale_id: int,
    buyer_state_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate full GST invoice data for a completed sale.
    Fetches sale + line items, calculates GST breakdown.
    """
    # Fetch sale
    # Use a safe query — gstin may or may not exist on the customers table
    try:
        sale = db.execute(text("""
            SELECT s.id, s.transaction_id, s.customer_id, s.total_amount,
                   s.tax, s.discount, s.payment_method, s.transaction_date,
                   c.name as customer_name, c.phone as customer_phone,
                   COALESCE(c.gstin, '') as customer_gstin
            FROM sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            WHERE s.id = :sale_id
        """), {"sale_id": sale_id}).fetchone()
    except Exception:
        # Fallback: query without gstin if column not yet present
        sale = db.execute(text("""
            SELECT s.id, s.transaction_id, s.customer_id, s.total_amount,
                   s.tax, s.discount, s.payment_method, s.transaction_date,
                   c.name as customer_name, c.phone as customer_phone,
                   '' as customer_gstin
            FROM sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            WHERE s.id = :sale_id
        """), {"sale_id": sale_id}).fetchone()

    if not sale:
        raise ValueError(f"Sale {sale_id} not found")

    # Fetch line items
    items = db.execute(text("""
        SELECT si.id, si.quantity, si.unit_price, si.line_total,
               p.name, p.category, p.hsn_code
        FROM sale_items si
        JOIN products p ON p.id = si.product_id
        WHERE si.sale_id = :sale_id
    """), {"sale_id": sale_id}).fetchall()

    inter_state = is_interstate(buyer_state_code)
    line_items = []
    totals = {"taxable": 0.0, "cgst": 0.0, "sgst": 0.0, "igst": 0.0, "total_gst": 0.0}

    for item in items:
        category = (item[5] or "default").lower()
        gst_rate = GST_RATES_BY_CATEGORY.get(category, GST_RATES_BY_CATEGORY["default"])
        breakdown = calculate_line_item_gst(
            unit_price=float(item[2]),
            quantity=int(item[1]),
            gst_rate=gst_rate,
            inter_state=inter_state
        )
        line_items.append({
            "item_id": item[0],
            "product_name": item[4],
            "hsn_code": item[6] or "9999",
            "quantity": item[1],
            "unit_price": float(item[2]),
            **breakdown,
        })
        totals["taxable"] += breakdown["taxable_value"]
        totals["cgst"] += breakdown["cgst_amount"]
        totals["sgst"] += breakdown["sgst_amount"]
        totals["igst"] += breakdown["igst_amount"]
        totals["total_gst"] += breakdown["total_gst"]

    grand_total = totals["taxable"] + totals["total_gst"]

    return {
        "invoice_number": f"INV/{datetime.utcnow().year}/{sale[0]:06d}",
        "sale_id": sale[0],
        "transaction_id": sale[1],
        "invoice_date": sale[7].isoformat() if sale[7] else datetime.utcnow().isoformat(),
        "seller": {
            "name": "R-DIOS Enterprise Store",
            "gstin": "29ABCDE1234F1Z5",
            "state_code": SELLER_STATE_CODE,
            "address": "Enterprise Park, Bangalore, Karnataka - 560001",
        },
        "buyer": {
            "customer_id": sale[2],
            "name": sale[8] or "Cash Customer",
            "phone": sale[9] or "",
            "gstin": sale[10] or "",
            "state_code": buyer_state_code or SELLER_STATE_CODE,
        },
        "is_interstate": inter_state,
        "transaction_type": "IGST" if inter_state else "CGST+SGST",
        "line_items": line_items,
        "totals": {
            "subtotal": round(totals["taxable"], 2),
            "cgst": round(totals["cgst"], 2),
            "sgst": round(totals["sgst"], 2),
            "igst": round(totals["igst"], 2),
            "total_gst": round(totals["total_gst"], 2),
            "grand_total": round(grand_total, 2),
        },
        "payment_method": sale[3] if len(sale) > 3 else "cash",
    }


def get_invoice_list(
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
) -> Dict[str, Any]:
    """Get paginated list of invoices (sales) with GST summary"""
    where = []
    params: Dict[str, Any] = {"offset": (page - 1) * per_page, "limit": per_page}

    if start_date:
        where.append("s.transaction_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where.append("s.transaction_date < :end_date")
        params["end_date"] = end_date

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    total = db.execute(text(f"SELECT COUNT(*) FROM sales s {where_sql}"), params).scalar()
    rows = db.execute(text(f"""
        SELECT s.id, s.transaction_id, s.total_amount, s.tax, s.transaction_date,
               s.payment_method, c.name as customer_name
        FROM sales s
        LEFT JOIN customers c ON c.id = s.customer_id
        {where_sql}
        ORDER BY s.transaction_date DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    return {
        "data": [
            {
                "sale_id": r[0],
                "invoice_number": f"INV/{r[4].year if r[4] else 2026}/{r[0]:06d}",
                "transaction_id": r[1],
                "taxable_amount": float(r[2] or 0),
                "gst_amount": float(r[3] or 0),
                "grand_total": float((r[2] or 0) + (r[3] or 0)),
                "cgst": round(float(r[3] or 0) / 2, 2),
                "sgst": round(float(r[3] or 0) / 2, 2),
                "igst": 0.0,
                "date": r[4].isoformat() if r[4] else None,
                "payment_method": r[5],
                "customer_name": r[6] or "Cash Customer",
            }
            for r in rows
        ],
        "total": int(total or 0),
        "page": page,
        "per_page": per_page,
    }

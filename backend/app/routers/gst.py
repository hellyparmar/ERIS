"""
GST API Endpoints
Routes: /api/v1/gst/*
"""

from __future__ import annotations
from typing import Dict, List, Any
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import Response
from app.middleware.auth import get_current_user
from app.models.multitenant_models import User

from app.api.gst.calculator import GSTCalculator
from app.api.gst.invoice_generator import GSTInvoiceGenerator
from app.api.gst.gstr1_generator import GSTR1Generator
from app.api.gst.gstr3b_generator import GSTR3BGenerator

router = APIRouter(
    prefix="/api/v1/gst",
    tags=["GST Operations (India)"],
)

# ─── Mocks & Helpers ─────────────────────────────────────────────────────────────

# In a real system, these would be loaded from the DB and config tables.
MOCK_COMPANY_CONFIG = {
    "name": "R-DIOS Technologies Pt Ltd",
    "address": "123 Tech Park, 4th Floor, Mumbai",
    "gstin": "27AAACR1234A1Z5",
    "state_code": "27",
    "bank_name": "HDFC Bank Ltd",
    "bank_ac": "12345678901234",
    "bank_ifsc": "HDFC0001234"
}

def _get_mock_sale(sale_id: str) -> Dict:
    """Mock database lookup for a sale + items."""
    return {
        "invoice_number": f"INV/26-27/{sale_id}",
        "date": datetime.today().strftime('%Y-%m-%d'),
        "customer": {
            "name": "Acme Corp",
            "address": "456 Business Lane, Delhi",
            "gstin": "07AABBAC1234A1Z",
            "state_code": "07"
        },
        "items": [
            {"name": "POS Software License", "hsn": "997331", "qty": 1, "rate": 5000, "gst_rate": 18},
            {"name": "Hardware Scanner", "hsn": "847190", "qty": 2, "rate": 1500, "gst_rate": 18}
        ]
    }

def _calculate_sale_tax(sale: Dict, seller_gstin: str) -> Dict:
    """Run GST calculator over a raw sale to populate tax amounts."""
    buyer_gstin = sale.get("customer", {}).get("gstin", "")
    is_interstate = GSTCalculator.is_same_state(seller_gstin, buyer_gstin) is False

    taxable_total = Decimal("0")
    cgst_total = Decimal("0")
    sgst_total = Decimal("0")
    igst_total = Decimal("0")
    grand_total = Decimal("0")
    
    processed_items = []
    
    for item in sale.get("items", []):
        qty = Decimal(str(item.get("qty", 1)))
        rate = Decimal(str(item.get("rate", 0)))
        base_amt = qty * rate
        
        tax_res = GSTCalculator.calculate_forward_tax(
            taxable_value=base_amt,
            gst_rate=item.get("gst_rate", 0),
            is_interstate=is_interstate
        )
        
        proc_item = item.copy()
        proc_item.update({
            "amount": float(tax_res.taxable_value),
            "cgst": float(tax_res.cgst_amount),
            "sgst": float(tax_res.sgst_amount),
            "igst": float(tax_res.igst_amount),
            "total": float(tax_res.grand_total)
        })
        processed_items.append(proc_item)
        
        taxable_total += tax_res.taxable_value
        cgst_total += tax_res.cgst_amount
        sgst_total += tax_res.sgst_amount
        igst_total += tax_res.igst_amount
        grand_total += tax_res.grand_total

    sale["is_interstate"] = is_interstate
    sale["items"] = processed_items
    sale["totals"] = {
        "taxable": float(taxable_total),
        "cgst": float(cgst_total),
        "sgst": float(sgst_total),
        "igst": float(igst_total),
        "grand_total": float(grand_total),
        "amount_in_words": f"Rupees {int(grand_total)} Only" # Simple mock
    }
    
    # Required flat fields for GSTR generators
    sale["taxable_amount"] = float(taxable_total)
    sale["cgst_amount"] = float(cgst_total)
    sale["sgst_amount"] = float(sgst_total)
    sale["igst_amount"] = float(igst_total)
    sale["grand_total"] = float(grand_total)
    
    return sale


# ─── Endpoints ───────────────────────────────────────────────────────────────────

@router.get("/invoice/{sale_id}", summary="Download GST Tax Invoice (PDF)")
async def generate_gst_invoice(sale_id: str, current_user: User = Depends(get_current_user)):
    """
    Computes tax splits for a specific sale and returns an official 
    GST Tax Invoice PDF (B2B/B2C).
    """
    raw_sale = _get_mock_sale(sale_id)
    if not raw_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
        
    calc_sale = _calculate_sale_tax(raw_sale, MOCK_COMPANY_CONFIG["gstin"])
    
    try:
        generator = GSTInvoiceGenerator(MOCK_COMPANY_CONFIG)
        pdf_bytes = generator.generate_pdf(calc_sale)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="Invoice_{sale_id}.pdf"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF Generation Failed: {str(e)}")


@router.get("/gstr1", summary="Generate GSTR-1 Report (JSON)")
async def generate_gstr1(period: str = Query("052026", description="MMYYYY format"), current_user: User = Depends(get_current_user)):
    """
    Returns the compiled GSTR-1 outward supply JSON structure 
    ready for upload via the GSTN portal offline utility.
    """
    # In a real app, query sales where invoice_date is in `period`
    s1 = _calculate_sale_tax(_get_mock_sale("1001"), MOCK_COMPANY_CONFIG["gstin"])
    s2 = _calculate_sale_tax(_get_mock_sale("1002"), MOCK_COMPANY_CONFIG["gstin"])
    
    # Alter s2 to be an intra-state B2C Small sale
    s2["customer"] = {"name": "Walkin", "state_code": "27"} # Same as seller 27
    s2 = _calculate_sale_tax(s2, MOCK_COMPANY_CONFIG["gstin"])
    
    payload = GSTR1Generator.generate_report(
        period=period,
        gstin=MOCK_COMPANY_CONFIG["gstin"],
        gross_turnover=15000000.0, # 1.5Cr
        sales=[s1, s2]
    )
    return payload


@router.get("/gstr3b", summary="Generate GSTR-3B Summary (JSON)")
async def generate_gstr3b(period: str = Query("052026", description="MMYYYY format"), current_user: User = Depends(get_current_user)):
    """
    Returns the compiled monthly GSTR-3B summary (Totals and ITC).
    """
    s1 = _calculate_sale_tax(_get_mock_sale("1001"), MOCK_COMPANY_CONFIG["gstin"])
    
    # Mock some inward purchases (ITC)
    purchases = [
        {"invoice_number": "P1", "taxable_amount": 2000, "igst_amount": 360, "cgst_amount": 0, "sgst_amount": 0},
        {"invoice_number": "P2", "taxable_amount": 1000, "igst_amount": 0, "cgst_amount": 90, "sgst_amount": 90},
    ]

    payload = GSTR3BGenerator.generate_report(
        period=period,
        gstin=MOCK_COMPANY_CONFIG["gstin"],
        legal_name=MOCK_COMPANY_CONFIG["name"],
        sales=[s1],
        purchases=purchases
    )
    return payload

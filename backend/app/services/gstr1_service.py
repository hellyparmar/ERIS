"""Read-only GSTR-1 preparation from recorded GST invoices."""

from calendar import monthrange
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.invoicing import Invoice
from app.models.invoicing import InvoiceLineItem
from app.models.commerce import Product
from app.models.organization import Organization


def _period(month: int, year: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    last_day = monthrange(year, month)[1]
    end = datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=timezone.utc)
    return start, end


def _invoice_query(db: Session, month: int, year: int, organization_id: int, outlet_ids: list[int]):
    start, end = _period(month, year)
    query = db.query(Invoice).filter(
        Invoice.organization_id == organization_id,
        Invoice.invoice_date >= start,
        Invoice.invoice_date <= end,
        Invoice.is_voided.is_(False),
    )
    return query.filter(Invoice.outlet_id.in_(outlet_ids)) if outlet_ids else query.filter(False)


def validate_gstr1(
    db: Session,
    month: int,
    year: int,
    organization_id: int,
    outlet_ids: list[int],
) -> Dict[str, Any]:
    issues = []
    invoices = _invoice_query(db, month, year, organization_id, outlet_ids).all()
    missing_tax = sum(1 for invoice in invoices if Decimal(invoice.tax_amount or 0) <= 0)
    if missing_tax:
        issues.append(
            {
                "severity": "warning",
                "code": "MISSING_TAX",
                "message": f"{missing_tax} invoice(s) have no GST recorded",
                "action": "Review zero-rated and exempt transactions before filing",
            }
        )
    missing_hsn = (
        db.query(Product)
        .filter(
            Product.organization_id == organization_id,
            Product.is_deleted.is_(False),
            (Product.hsn_code.is_(None)) | (Product.hsn_code == ""),
        )
        .count()
    )
    if missing_hsn:
        issues.append(
            {
                "severity": "info",
                "code": "MISSING_HSN",
                "message": f"{missing_hsn} active product(s) have no HSN code",
                "action": "Assign HSN codes for an accurate HSN summary",
            }
        )
    return {
        "is_valid": not any(issue["severity"] == "error" for issue in issues),
        "issues": issues,
        "period": f"{month:02d}/{year}",
    }


def generate_gstr1_report(
    db: Session,
    month: int,
    year: int,
    organization_id: int,
    outlet_ids: list[int],
) -> Dict[str, Any]:
    invoices = _invoice_query(db, month, year, organization_id, outlet_ids).all()
    b2b = [invoice for invoice in invoices if invoice.billed_to_gstin]
    b2c = [invoice for invoice in invoices if not invoice.billed_to_gstin]

    def totals(records: list[Invoice]) -> dict:
        taxable = sum(
            (Decimal(record.subtotal or 0) - Decimal(record.discount or 0) for record in records), Decimal("0")
        )
        cgst = sum((Decimal(record.cgst_amount or 0) for record in records), Decimal("0"))
        sgst = sum((Decimal(record.sgst_amount or 0) for record in records), Decimal("0"))
        igst = sum((Decimal(record.igst_amount or 0) for record in records), Decimal("0"))
        return {
            "invoice_count": len(records),
            "taxable_value": float(taxable),
            "cgst": float(cgst),
            "sgst": float(sgst),
            "igst": float(igst),
            "total_gst": float(cgst + sgst + igst),
        }

    invoice_ids = [invoice.id for invoice in invoices]
    hsn_rows: dict[str, dict] = {}
    if invoice_ids:
        rows = (
            db.query(InvoiceLineItem, Product)
            .outerjoin(Product, Product.id == InvoiceLineItem.product_id)
            .filter(InvoiceLineItem.invoice_id.in_(invoice_ids))
            .all()
        )
        for line, product in rows:
            hsn = (product.hsn_code if product else None) or "UNASSIGNED"
            bucket = hsn_rows.setdefault(
                hsn,
                {
                    "hsn_code": hsn,
                    "description": product.name if product else line.product_name or line.description,
                    "uqc": "NOS",
                    "total_quantity": 0.0,
                    "taxable_value": 0.0,
                    "gst_amount": 0.0,
                },
            )
            bucket["total_quantity"] += float(line.quantity or 0)
            bucket["taxable_value"] += float(line.line_total or 0)
            bucket["gst_amount"] += float(line.gst_amount or 0)

    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    b2c_totals = totals(b2c)
    all_totals = totals(invoices)
    return {
        "period": f"{month:02d}/{year}",
        "gstin": organization.tax_id if organization else None,
        "return_type": "GSTR-1 preparation",
        "disclaimer": "Review with a tax professional before filing; ERIS does not submit returns.",
        "b2c_summary": b2c_totals,
        "b2b_invoices": [
            {
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date.date().isoformat(),
                "buyer_gstin": invoice.billed_to_gstin,
                "taxable_value": float(Decimal(invoice.subtotal or 0) - Decimal(invoice.discount or 0)),
                "tax_amount": float(invoice.tax_amount or 0),
                "total_amount": float(invoice.total_amount or 0),
            }
            for invoice in b2b
        ],
        "hsn_summary": list(hsn_rows.values()),
        "total_liability": all_totals,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

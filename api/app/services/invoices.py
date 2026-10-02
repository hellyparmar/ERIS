"""Demo GST tax invoices.

An invoice is issued from a completed sale and frozen at issue time (number, GSTINs, place of supply, tax split).
Rules implemented:
- Seller GSTIN: GST registration is per state, so each outlet uses the organisation's PAN with its own state code
  (derived from the organisation GSTIN, checksum recomputed).
- Place of supply: the buyer's GSTIN state, else the customer's state, else the outlet's state (counter sale).
- Same state as the outlet -> intra-state: CGST + SGST (half each). Different state -> inter-state: IGST.
- Numbering: <outlet code>/<financial year>/<sequence>, e.g. MUMAND/2627/0001, consecutive per outlet and
  financial year (16 characters, the GST limit).

Everything is marked as a demo: GSTINs are synthetic, there is no IRN / e-invoice registration and the PDF carries
a "DEMO - NOT FOR TAX FILING" watermark.
"""
from __future__ import annotations

import io
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import clock
from app.models import Invoice, Organization, Outlet, Sale, User
from app.services.gst import STATES, gstin_checksum, is_valid_gstin, split_tax

WATERMARK = "DEMO - NOT FOR TAX FILING"


def financial_year(d: datetime) -> str:
    start = d.year if d.month >= 4 else d.year - 1
    return f"{start % 100:02d}{(start + 1) % 100:02d}"


def outlet_gstin(org: Organization | None, outlet: Outlet) -> str | None:
    base = org.tax_id if org else None
    if not base or not is_valid_gstin(base):
        return None
    code = outlet.state_code or base[:2]
    first14 = f"{code}{base[2:14]}"
    return first14 + gstin_checksum(first14)


def _next_number(db: Session, outlet: Outlet, when: datetime) -> str:
    prefix = f"{outlet.code.replace('-', '')[:6]}/{financial_year(when)}/"
    last = db.scalar(select(func.max(Invoice.number)).where(Invoice.number.like(f"{prefix}%")))
    seq = int(last.rsplit("/", 1)[1]) + 1 if last else 1
    return f"{prefix}{seq:04d}"  # 16 characters, the GST limit, up to 9,999 invoices per outlet and year


def create_invoice(db: Session, sale: Sale, user: User | None, buyer_gstin: str | None = None) -> tuple[Invoice, bool]:
    """Issue (or return the existing) invoice for a sale. Returns (invoice, created)."""
    existing = db.scalar(select(Invoice).where(Invoice.sale_id == sale.id))
    if existing:
        return existing, False
    if sale.status != "completed":
        raise HTTPException(400, "Invoices can only be issued for completed sales")
    org = db.scalar(select(Organization))
    outlet = sale.outlet
    cust = sale.customer
    buyer_gstin = (buyer_gstin or (cust.gstin if cust else None) or "").strip().upper() or None
    if buyer_gstin and not is_valid_gstin(buyer_gstin):
        raise HTTPException(422, f"{buyer_gstin} is not a valid GSTIN")
    seller_state = outlet.state_code or (org.state_code if org else None)
    pos = buyer_gstin[:2] if buyer_gstin else ((cust.state_code if cust and cust.state_code else None) or seller_state)
    intra = pos == seller_state
    tax = round(sum(i.tax_amount for i in sale.items), 2)
    cgst, sgst, igst = split_tax(tax, intra)
    now = clock.now()
    inv = Invoice(number=_next_number(db, outlet, sale.sold_at), sale_id=sale.id, issued_at=now,
                  seller_gstin=outlet_gstin(org, outlet), buyer_name=cust.name if cust else None,
                  buyer_gstin=buyer_gstin, place_of_supply=pos, supply_type="intra_state" if intra else "inter_state",
                  taxable_value=round(sale.total - tax, 2), cgst=cgst, sgst=sgst, igst=igst, total=round(sale.total, 2),
                  is_demo=True, created_by=user.id if user else None)
    for attempt in range(6):
        try:
            with db.begin_nested():
                db.add(inv)
                db.flush()
            break
        except IntegrityError:
            # the same sale was invoiced at the same moment (return that invoice), or the number was taken
            existing = db.scalar(select(Invoice).where(Invoice.sale_id == sale.id))
            if existing:
                db.commit()
                return existing, False
            if attempt == 5:
                raise HTTPException(409, "Could not allocate an invoice number, please retry") from None
            inv.number = _next_number(db, outlet, sale.sold_at)
    db.commit()
    db.refresh(inv)
    return inv, True


def lines(sale: Sale) -> list[dict]:
    out = []
    for i in sale.items:
        p = i.product
        taxable = round(i.line_total - i.tax_amount, 2)
        out.append({"product": p.name, "sku": p.sku, "hsn_code": p.hsn_code, "quantity": i.quantity, "unit": p.unit,
                    "unit_price": i.unit_price, "discount": i.discount, "tax_rate": p.tax_rate,
                    "taxable_value": taxable, "tax": round(i.tax_amount, 2), "total": round(i.line_total, 2)})
    return out


def tax_summary(inv: Invoice, items: list[dict]) -> list[dict]:
    by_rate: dict[float, dict] = {}
    for it in items:
        r = by_rate.setdefault(it["tax_rate"], {"rate": it["tax_rate"], "taxable_value": 0.0, "tax": 0.0})
        r["taxable_value"] += it["taxable_value"]
        r["tax"] += it["tax"]
    out = []
    for r in sorted(by_rate.values(), key=lambda r: r["rate"]):
        cgst, sgst, igst = split_tax(r["tax"], inv.supply_type == "intra_state")
        out.append({"rate": r["rate"], "taxable_value": round(r["taxable_value"], 2), "cgst": cgst, "sgst": sgst,
                    "igst": igst})
    return out


def invoice_dict(inv: Invoice, detail: bool = False) -> dict:
    s = inv.sale
    d = {"id": inv.id, "number": inv.number, "sale_id": inv.sale_id, "invoice_no": s.invoice_no,
         "issued_at": inv.issued_at.isoformat(), "outlet": s.outlet.name, "outlet_id": s.outlet_id,
         "buyer_name": inv.buyer_name, "buyer_gstin": inv.buyer_gstin, "seller_gstin": inv.seller_gstin,
         "place_of_supply": inv.place_of_supply, "place_of_supply_name": STATES.get(inv.place_of_supply or ""),
         "supply_type": inv.supply_type, "taxable_value": inv.taxable_value, "cgst": inv.cgst, "sgst": inv.sgst,
         "igst": inv.igst, "total": inv.total, "is_demo": inv.is_demo, "sale_status": s.status,
         "watermark": WATERMARK}
    if detail:
        items = lines(s)
        d.update(items=items, tax_summary=tax_summary(inv, items), sold_at=s.sold_at.isoformat(),
                 payment_method=s.payment_method, amount_in_words=amount_in_words(inv.total))
    return d


_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
         "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _words(n: int) -> str:
    if n < 20:
        return _ONES[n]
    if n < 100:
        return (_TENS[n // 10] + " " + _ONES[n % 10]).strip()
    if n < 1000:
        return (_ONES[n // 100] + " Hundred " + _words(n % 100)).strip()
    for div, name in ((10_000_000, "Crore"), (100_000, "Lakh"), (1000, "Thousand")):
        if n >= div:
            return (_words(n // div) + f" {name} " + _words(n % div)).strip()
    return ""


def amount_in_words(amount: float) -> str:
    """Indian numbering: 1,23,456.50 -> 'Rupees One Lakh Twenty Three Thousand Four Hundred Fifty Six and Fifty
    Paise Only'."""
    rupees, paise = int(amount), int(round((amount - int(amount)) * 100))
    text = "Rupees " + (_words(rupees) or "Zero")
    if paise:
        text += f" and {_words(paise)} Paise"
    return text + " Only"


def invoice_pdf(db: Session, inv: Invoice) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    org = db.scalar(select(Organization))
    d = invoice_dict(inv, detail=True)
    sale = inv.sale
    outlet = sale.outlet
    styles = getSampleStyleSheet()
    small = styles["BodyText"].clone("small", fontSize=8, leading=10)
    buf = io.BytesIO()
    cancelled = sale.status != "completed"

    def watermark(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 38)
        canvas.setFillColor(colors.Color(0.85, 0.1, 0.1, alpha=0.15))
        canvas.translate(A4[0] / 2, A4[1] / 2)
        canvas.rotate(35)
        canvas.drawCentredString(0, 0, "CANCELLED - " + WATERMARK if cancelled else WATERMARK)
        canvas.restoreState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.grey)
        canvas.drawString(15 * mm, 10 * mm, "Generated by ERIS on synthetic demo data. Synthetic GSTINs; no IRN; "
                                            "not valid for input tax credit or filing.")
        canvas.drawRightString(A4[0] - 15 * mm, 10 * mm, f"Page {doc.page}")

    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm,
                            bottomMargin=18 * mm, title=f"Invoice {inv.number}", author=org.name if org else "ERIS")
    money = lambda v: f"{v:,.2f}"  # noqa: E731
    story = [
        Paragraph(f"<b>{org.name if org else 'ERIS'}</b> - {outlet.name}", styles["Title"]),
        Paragraph(f"TAX INVOICE (DEMO){' - CANCELLED' if cancelled else ''}", styles["Heading2"]),
        Spacer(1, 4),
    ]
    seller = (f"<b>Seller</b><br/>{org.name if org else ''}, {outlet.name}<br/>{outlet.address or outlet.city}<br/>"
              f"State: {outlet.state or ''} ({outlet.state_code or ''})<br/>GSTIN: {inv.seller_gstin or 'not set'} (demo)")
    buyer = (f"<b>Buyer</b><br/>{inv.buyer_name or 'Walk-in customer'}<br/>GSTIN: {inv.buyer_gstin or 'Unregistered'}"
             f"<br/>Place of supply: {d['place_of_supply_name'] or ''} ({inv.place_of_supply or ''})")
    meta = (f"<b>Invoice no:</b> {inv.number}<br/><b>Invoice date:</b> {inv.issued_at:%d-%m-%Y}<br/>"
            f"<b>Bill no:</b> {sale.invoice_no} ({sale.sold_at:%d-%m-%Y %H:%M})<br/>"
            f"<b>Supply:</b> {'Intra-state (CGST + SGST)' if inv.supply_type == 'intra_state' else 'Inter-state (IGST)'}"
            f"<br/><b>Payment:</b> {sale.payment_method.upper()}")
    head = Table([[Paragraph(seller, small), Paragraph(buyer, small), Paragraph(meta, small)]],
                 colWidths=[62 * mm, 58 * mm, 60 * mm])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                              ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    story += [head, Spacer(1, 8)]

    rows = [["#", "Item", "HSN", "Qty", "Rate", "Disc.", "Taxable", "GST %", "Tax", "Amount"]]
    for n, it in enumerate(d["items"], start=1):
        rows.append([n, Paragraph(it["product"], small), it["hsn_code"] or "", f"{it['quantity']:g}",
                     money(it["unit_price"]), money(it["discount"]), money(it["taxable_value"]), f"{it['tax_rate']:g}",
                     money(it["tax"]), money(it["total"])])
    rows.append(["", "Total", "", "", "", "", money(inv.taxable_value), "", money(inv.cgst + inv.sgst + inv.igst),
                 money(inv.total)])
    t = Table(rows, colWidths=[7 * mm, 52 * mm, 15 * mm, 11 * mm, 16 * mm, 14 * mm, 19 * mm, 12 * mm, 16 * mm, 20 * mm],
              repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 8), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
        ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 8), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story += [t, Spacer(1, 8)]

    tax_rows = [["GST %", "Taxable value", "CGST", "SGST", "IGST"]]
    for r in d["tax_summary"]:
        tax_rows.append([f"{r['rate']:g}", money(r["taxable_value"]), money(r["cgst"]), money(r["sgst"]), money(r["igst"])])
    tax_rows.append(["Total", money(inv.taxable_value), money(inv.cgst), money(inv.sgst), money(inv.igst)])
    tt = Table(tax_rows, colWidths=[20 * mm, 30 * mm, 25 * mm, 25 * mm, 25 * mm])
    tt.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "Helvetica", 8), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
                            ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 8), ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5"))]))
    story += [tt, Spacer(1, 6),
              Paragraph(f"<b>Amount payable:</b> Rs {money(inv.total)} ({d['amount_in_words']})", small),
              Spacer(1, 10),
              Paragraph("This is a demonstration invoice produced from synthetic data. It is not registered on the "
                        "Invoice Registration Portal (no IRN / QR code) and must not be used for tax filing.", small)]
    doc.build(story, onFirstPage=watermark, onLaterPages=watermark)
    return buf.getvalue()

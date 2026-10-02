"""Reports & exports, demo GST invoices and the audit log."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditLog, Invoice, Sale, User
from app.routers.common import get_or_404, page_response, paginate
from app.security import ensure_outlet_access, get_current_user, require_admin, require_writer, scoped_outlet_ids
from app.services import analytics as A
from app.services import invoices as INV
from app.services import reports as R

router = APIRouter(prefix="/api", tags=["reports, invoices & audit"])


# ------------------------------------------------------------------------------------------ reports
@router.get("/reports")
def list_reports(user: User = Depends(get_current_user)):
    return [{"key": r.key, "title": r.title, "description": r.description, "uses_period": r.uses_period,
             "columns": [h for _, h in r.columns]} for r in R.available(user.role)]


def _report(key: str, user: User) -> R.Report:
    rep = R.REPORTS.get(key)
    if not rep:
        raise HTTPException(404, "Unknown report")
    if rep not in R.available(user.role):
        raise HTTPException(403, "This report needs a manager or admin account")
    return rep


@router.get("/reports/{key}")
def report_preview(key: str, period: str = "30d", start: date | None = None, end: date | None = None,
                   outlet_id: int | None = None, limit: int = Query(50, ge=1, le=500),
                   user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rep = _report(key, user)
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    rng = A.resolve_period(db, period, start, end)
    rows = R.build(db, rep, rng, outlet_ids)
    return {"key": rep.key, "title": rep.title, "columns": [h for _, h in rep.columns], "rows": rows[:limit],
            "total_rows": len(rows), "about": dict(R.provenance(db, rep, rng, outlet_ids))}


@router.get("/reports/{key}/export")
def report_export(key: str, format: str = Query("csv", pattern="^(csv|xlsx)$"), period: str = "30d",
                  start: date | None = None, end: date | None = None, outlet_id: int | None = None,
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rep = _report(key, user)
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    rng = A.resolve_period(db, period, start, end)
    rows = R.build(db, rep, rng, outlet_ids)
    stamp = f"{rng.start:%Y%m%d}-{rng.end:%Y%m%d}" if rep.uses_period else date.today().strftime("%Y%m%d")
    name = f"eris_{rep.key}_{stamp}.{format}"
    headers = {"Content-Disposition": f'attachment; filename="{name}"'}
    if format == "xlsx":
        body = R.to_xlsx(rep, rows, R.provenance(db, rep, rng, outlet_ids))
        return Response(body, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers=headers)
    return Response(R.to_csv(rep, rows), media_type="text/csv", headers=headers)


# ------------------------------------------------------------------------------------------ invoices
class InvoiceIn(BaseModel):
    sale_id: int
    buyer_gstin: str | None = None


def _invoice_for(db: Session, user: User, invoice_id: int) -> Invoice:
    inv = get_or_404(db, Invoice, invoice_id, "Invoice")
    ensure_outlet_access(user, inv.sale.outlet_id)
    return inv


@router.get("/invoices")
def list_invoices(q: str | None = None, outlet_id: int | None = None, page: int = Query(1, ge=1),
                  page_size: int = Query(25, ge=1, le=200), user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    query = select(Invoice).join(Sale, Sale.id == Invoice.sale_id).order_by(Invoice.id.desc())
    if outlet_ids:
        query = query.where(Sale.outlet_id.in_(outlet_ids))
    if q:
        like = f"%{q.strip()}%"
        query = query.where(or_(Invoice.number.ilike(like), Sale.invoice_no.ilike(like), Invoice.buyer_name.ilike(like),
                                Invoice.buyer_gstin.ilike(like)))
    rows, total = paginate(db, query, page, page_size)
    return page_response([INV.invoice_dict(r[0]) for r in rows], total, page, page_size)


@router.post("/invoices", status_code=201)
def issue_invoice(data: InvoiceIn, response: Response, user: User = Depends(require_writer),
                  db: Session = Depends(get_db)):
    sale = get_or_404(db, Sale, data.sale_id, "Sale")
    ensure_outlet_access(user, sale.outlet_id)
    inv, created = INV.create_invoice(db, sale, user, data.buyer_gstin)
    if not created:
        response.status_code = 200  # the sale already had an invoice: return it unchanged
    return {**INV.invoice_dict(inv, detail=True), "created": created}


@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return INV.invoice_dict(_invoice_for(db, user, invoice_id), detail=True)


@router.get("/invoices/{invoice_id}/pdf")
def invoice_pdf(invoice_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    inv = _invoice_for(db, user, invoice_id)
    body = INV.invoice_pdf(db, inv)
    return Response(body, media_type="application/pdf", headers={
        "Content-Disposition": f'inline; filename="invoice_{inv.number.replace("/", "-")}_DEMO.pdf"'})


# ------------------------------------------------------------------------------------------ audit log
@router.get("/audit")
def audit_log(entity: str | None = None, action: str | None = None, user_id: int | None = None,
              outlet_id: int | None = None, start: date | None = None, end: date | None = None, q: str | None = None,
              page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
              _: User = Depends(require_admin), db: Session = Depends(get_db)):
    query = select(AuditLog).order_by(AuditLog.id.desc())
    if entity:
        query = query.where(AuditLog.entity == entity)
    if action:
        query = query.where(AuditLog.action.like(f"%{action}%"))
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if outlet_id:
        query = query.where(AuditLog.outlet_id == outlet_id)
    if start:
        query = query.where(AuditLog.created_at >= start)
    if end:
        query = query.where(AuditLog.created_at < end + timedelta(days=1))
    if q:
        query = query.where(AuditLog.summary.ilike(f"%{q.strip()}%"))
    rows, total = paginate(db, query, page, page_size)
    items = [{"id": a.id, "at": a.created_at.isoformat() if a.created_at else None, "user": a.user.full_name if a.user
              else "system", "user_id": a.user_id, "action": a.action, "entity": a.entity, "entity_id": a.entity_id,
              "outlet_id": a.outlet_id, "summary": a.summary, "details": a.details} for (a,) in rows]
    return page_response(items, total, page, page_size)


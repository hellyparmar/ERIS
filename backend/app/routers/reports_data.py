"""Authenticated report downloads, exports, and persistent CSV imports."""

from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_outlet_scope, require_role
from app.api.schemas import DataSource, DataSourcesResponse, UploadResponse
from app.database import get_db_sync_dependency
from app.models import Customer, Inventory, Invoice, Sale, User
from app.services.data_service import DataService
from app.services.export_service import ExportService
from app.services.reporting_service import ReportingService


router = APIRouter(prefix="/reports", tags=["Reports"])
data_router = APIRouter(prefix="/data", tags=["Data imports"])
data_service = DataService()
export_service = ExportService()


class ExportRequest(BaseModel):
    format: Literal["pdf", "excel", "csv"] = "pdf"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    filters: Optional[dict] = None


def _outlet_ids(current_user: User, db: Session) -> list[int]:
    return get_outlet_scope(current_user, db)


def _download(content: bytes, media_type: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _export_response(content: bytes, export_format: str, stem: str) -> Response:
    media_types = {
        "pdf": "application/pdf",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv; charset=utf-8",
    }
    extensions = {"pdf": "pdf", "excel": "xlsx", "csv": "csv"}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _download(content, media_types[export_format], f"{stem}_{timestamp}.{extensions[export_format]}")


@router.get("/sales/download")
async def download_sales_report(
    format: Literal["xlsx", "pdf"] = Query("xlsx"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(get_current_active_user),
):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    rows = ReportingService.get_sales_rows(start_date, end_date, db, _outlet_ids(current_user, db))
    if format == "pdf":
        content = ReportingService.generate_pdf_report(
            rows, f"Sales Report ({start_date.date()} to {end_date.date()})"
        ).getvalue()
        return _download(content, "application/pdf", f"sales_report_{end_date:%Y%m%d}.pdf")
    content = ReportingService.generate_excel_report(
        rows, f"Sales Report ({start_date.date()} to {end_date.date()})"
    ).getvalue()
    return _download(
        content,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        f"sales_report_{end_date:%Y%m%d}.xlsx",
    )


@router.get("/inventory/download")
async def download_inventory_report(
    format: Literal["xlsx", "pdf"] = Query("xlsx"),
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(get_current_active_user),
):
    rows = ReportingService.get_inventory_rows(db, _outlet_ids(current_user, db))
    if format == "pdf":
        content = ReportingService.generate_pdf_report(rows, "Inventory Status Report").getvalue()
        return _download(content, "application/pdf", f"inventory_report_{datetime.now():%Y%m%d}.pdf")
    content = ReportingService.generate_excel_report(rows, "Inventory Status Report").getvalue()
    return _download(
        content,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        f"inventory_report_{datetime.now():%Y%m%d}.xlsx",
    )


@router.post("/export/sales")
async def export_sales(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    end = request.end_date or datetime.now()
    start = request.start_date or end - timedelta(days=30)
    rows = ReportingService.get_sales_rows(start, end, db, _outlet_ids(current_user, db))
    content = export_service.export_sales_report(
        rows, format=request.format, date_range=f"{start.date()} to {end.date()}"
    )
    return _export_response(content, request.format, "sales_report")


@router.post("/export/inventory")
async def export_inventory(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    rows = ReportingService.get_inventory_rows(db, _outlet_ids(current_user, db))
    content = export_service.export_inventory_report(rows, format=request.format)
    return _export_response(content, request.format, "inventory_report")


@router.post("/export/invoices")
async def export_invoices(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    outlet_ids = _outlet_ids(current_user, db)
    query = db.query(Invoice).filter(Invoice.organization_id == current_user.organization_id)
    query = query.filter(Invoice.outlet_id.in_(outlet_ids)) if outlet_ids else query.filter(False)
    if request.start_date:
        query = query.filter(Invoice.invoice_date >= request.start_date)
    if request.end_date:
        query = query.filter(Invoice.invoice_date <= request.end_date)
    rows = [
        {
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else "",
            "customer_id": invoice.customer_id or "",
            "total_amount": float(invoice.total_amount or 0),
            "amount_paid": float(invoice.amount_paid or 0),
            "amount_due": float(invoice.amount_due or 0),
            "payment_status": invoice.payment_status or "",
            "due_date": invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "",
        }
        for invoice in query.order_by(Invoice.invoice_date.desc()).all()
    ]
    content = export_service.export_invoice_report(rows, format=request.format)
    return _export_response(content, request.format, "invoices_report")


@router.post("/export/customers")
async def export_customers(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_sync_dependency),
):
    customers = (
        db.query(Customer)
        .filter(
            Customer.organization_id == current_user.organization_id,
            Customer.is_deleted.is_(False),
        )
        .order_by(Customer.created_at.desc())
        .all()
    )
    rows = [
        {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email or "",
            "phone": customer.phone or "",
            "city": customer.city or "",
            "state": customer.state or "",
            "total_spent": float(customer.total_purchases or 0),
            "transactions": customer.total_transactions or 0,
        }
        for customer in customers
    ]
    if request.format == "pdf":
        content = export_service.export_to_pdf(rows, "Customer Report")
    elif request.format == "excel":
        content = export_service.export_to_excel(rows, "Customers", "Customer Report")
    else:
        content = export_service.export_to_csv(rows)
    return _export_response(content, request.format, "customers_report")


async def _csv_bytes(file: UploadFile) -> bytes:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must use the .csv extension")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    return content


@data_router.post("/upload/sales", response_model=UploadResponse)
async def upload_sales_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(require_role("admin", "manager")),
):
    return data_service.process_sales_upload(
        await _csv_bytes(file), db, current_user.organization_id, _outlet_ids(current_user, db), current_user.id
    )


@data_router.post("/upload/inventory", response_model=UploadResponse)
async def upload_inventory_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(require_role("admin", "manager")),
):
    return data_service.process_inventory_upload(
        await _csv_bytes(file), db, current_user.organization_id, _outlet_ids(current_user, db), current_user.id
    )


@data_router.get("/sources", response_model=DataSourcesResponse)
async def get_data_sources(
    db: Session = Depends(get_db_sync_dependency),
    current_user: User = Depends(get_current_active_user),
):
    outlet_ids = _outlet_ids(current_user, db)
    sales_query = db.query(func.count(Sale.id), func.max(Sale.updated_at)).filter(
        Sale.organization_id == current_user.organization_id
    )
    inventory_query = db.query(func.count(Inventory.id), func.max(Inventory.last_restocked_at)).filter(
        Inventory.organization_id == current_user.organization_id
    )
    if outlet_ids:
        sales_query = sales_query.filter(Sale.outlet_id.in_(outlet_ids))
        inventory_query = inventory_query.filter(Inventory.outlet_id.in_(outlet_ids))
    else:
        sales_query = sales_query.filter(False)
        inventory_query = inventory_query.filter(False)
    sales_count, sales_updated = sales_query.one()
    inventory_count, inventory_updated = inventory_query.one()
    return DataSourcesResponse(
        sources=[
            DataSource(name="Recorded sales", type="sales", last_updated=sales_updated, row_count=sales_count or 0),
            DataSource(
                name="Current inventory",
                type="inventory",
                last_updated=inventory_updated,
                row_count=inventory_count or 0,
            ),
        ]
    )

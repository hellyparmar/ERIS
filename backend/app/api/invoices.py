"""
Invoices Management API Router
"""

from datetime import datetime, timedelta, date
from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_, and_, select, select
from uuid import UUID

from app.database import get_db
from app.models import User, Outlet, Invoice
from app.api.deps import get_current_active_user
from app.core.data_isolation import OutletDataAccess
from app.api.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    InvoiceListResponse, OverdueInvoicesListResponse,
    InvoiceSummaryResponse, OverdueInvoiceResponse
)

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


@router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    status_filter: Optional[str] = Query(None, alias="status"),
    contact_id: Optional[UUID] = None,
    outlet_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Paginated invoice list with filters.
    Status: paid, pending, overdue
    """
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user, db)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    # Build query with contact relationship
    query = db.query(Invoice).options(joinedload(Invoice.contact))

    # Apply outlet filter
    if outlet_id:
        if outlet_id not in allowed_outlet_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this outlet"
            )
        query = query.filter(Invoice.outlet_id == outlet_id)
    else:
        query = query.filter(Invoice.outlet_id.in_(allowed_outlet_ids))

    # Apply other filters
    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    if contact_id:
        query = query.filter(Invoice.contact_id == contact_id)

    if date_from:
        query = query.filter(Invoice.issue_date >= date_from)

    if date_to:
        query = query.filter(Invoice.issue_date <= date_to)

    # Get total count
    total = query.count()
    total_pages = (total + per_page - 1) // per_page

    # Apply pagination and ordering
    invoices = query.order_by(desc(Invoice.created_at)).offset((page - 1) * per_page).limit(per_page).all()

    # Build response with contact data
    items = []
    for invoice in invoices:
        invoice_dict = InvoiceResponse.from_orm(invoice)
        if invoice.contact:
            invoice_dict.contact = {
                "contact_id": invoice.contact.contact_id,
                "company_name": invoice.contact.company_name,
                "contact_person": invoice.contact.contact_person,
                "email": invoice.contact.email,
                "phone": invoice.contact.phone
            }
        items.append(invoice_dict)

    return InvoiceListResponse(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        items=items
    )


@router.post("/", response_model=InvoiceResponse)
async def create_invoice(
    invoice_data: InvoiceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new invoice.
    Validate that contact_id exists.
    """
    if not OutletDataAccess.can_access_outlet(invoice_data.outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this outlet"
        )

    # Validate contact exists
    result = await db.execute(select(BusinessContact).where(BusinessContact.contact_id == invoice_data.contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Validate outlet exists
    result = await db.execute(select(Outlet).where(Outlet.outlet_id == invoice_data.outlet_id))
    outlet = result.scalar_one_or_none()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    # Create invoice
    invoice = Invoice(
        contact_id=invoice_data.contact_id,
        outlet_id=invoice_data.outlet_id,
        total_amount=invoice_data.total_amount,
        tax_amount=invoice_data.tax_amount,
        items=invoice_data.items,
        issue_date=invoice_data.issue_date,
        due_date=invoice_data.due_date,
        notes=invoice_data.notes
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return InvoiceResponse.from_orm(invoice)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get single invoice with full contact details"""
    result = await db.execute(select(Invoice).options(joinedload(Invoice.contact)).where(Invoice.invoice_id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check outlet access
    if not OutletDataAccess.can_access_outlet(invoice.outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this invoice"
        )

    response = InvoiceResponse.from_orm(invoice)
    if invoice.contact:
        response.contact = {
            "contact_id": invoice.contact.contact_id,
            "company_name": invoice.contact.company_name,
            "contact_person": invoice.contact.contact_person,
            "email": invoice.contact.email,
            "phone": invoice.contact.phone,
            "address": invoice.contact.address,
            "city": invoice.contact.city
        }

    return response


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update invoice (status, paid_date, notes)"""
    result = await db.execute(select(Invoice).where(Invoice.invoice_id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check outlet access
    if not OutletDataAccess.can_access_outlet(invoice.outlet_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this invoice"
        )

    # Update fields
    update_data = invoice_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    invoice.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(invoice)

    return InvoiceResponse.from_orm(invoice)


@router.get("/overdue/list", response_model=OverdueInvoicesListResponse)
async def list_overdue_invoices(
    outlet_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns all overdue invoices sorted by days overdue.
    Includes contact details.
    """
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user, db)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    today = date.today()

    # Build query
    query = db.query(Invoice).options(joinedload(Invoice.contact)).filter(
        Invoice.status == "pending",
        Invoice.due_date < today
    )

    if outlet_id:
        if outlet_id not in allowed_outlet_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this outlet"
            )
        query = query.filter(Invoice.outlet_id == outlet_id)
    else:
        query = query.filter(Invoice.outlet_id.in_(allowed_outlet_ids))

    overdue_invoices = query.order_by(desc(Invoice.due_date)).all()

    items = []
    total_amount = 0.0

    for invoice in overdue_invoices:
        days_overdue = (today - invoice.due_date).days
        total_amount += invoice.total_amount

        items.append(OverdueInvoiceResponse(
            invoice_id=invoice.invoice_id,
            contact_id=invoice.contact_id,
            outlet_id=invoice.outlet_id,
            contact_name=invoice.contact.contact_person if invoice.contact else "Unknown",
            contact_company=invoice.contact.company_name if invoice.contact else "Unknown",
            total_amount=invoice.total_amount,
            due_date=invoice.due_date,
            days_overdue=days_overdue,
            status=invoice.status
        ))

    return OverdueInvoicesListResponse(
        total_overdue=len(items),
        total_amount=total_amount,
        items=items
    )


@router.get("/summary", response_model=InvoiceSummaryResponse)
async def get_invoices_summary(
    outlet_id: Optional[UUID] = None,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns summary: paid_amount, pending_amount, overdue_amount for the period.
    """
    allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(current_user, db)
    if not allowed_outlet_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No outlets accessible"
        )

    date_from = date.today() - timedelta(days=days)

    # Build base query
    base_query = db.query(Invoice).filter(Invoice.issue_date >= date_from)

    if outlet_id:
        if outlet_id not in allowed_outlet_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this outlet"
            )
        base_query = base_query.filter(Invoice.outlet_id == outlet_id)
    else:
        base_query = base_query.filter(Invoice.outlet_id.in_(allowed_outlet_ids))

    # Calculate summaries
    paid_amount = db.query(func.sum(Invoice.total_amount)).filter(
        base_query.whereclause,
        Invoice.status == "paid"
    ).scalar() or 0

    pending_amount = db.query(func.sum(Invoice.total_amount)).filter(
        base_query.whereclause,
        Invoice.status == "pending"
    ).scalar() or 0

    overdue_amount = db.query(func.sum(Invoice.total_amount)).filter(
        base_query.whereclause,
        Invoice.status == "overdue"
    ).scalar() or 0

    total_amount = paid_amount + pending_amount + overdue_amount
    invoice_count = base_query.count()

    return InvoiceSummaryResponse(
        period_days=days,
        paid_amount=float(paid_amount),
        pending_amount=float(pending_amount),
        overdue_amount=float(overdue_amount),
        total_amount=float(total_amount),
        invoice_count=invoice_count
    )

"""
Business Contacts Management API Router
"""

from datetime import datetime
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, or_, select, case
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_active_user
from app.models.users import User
from app.models.business_contact import BusinessContact
from app.models.invoicing import Invoice
from app.schemas.contact import (
    BusinessContactCreate, BusinessContactUpdate, BusinessContactResponse,
    BusinessContactListResponse, InvoiceHistorySummary
)

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=BusinessContactListResponse)
async def list_contacts(
    search: Optional[str] = None,
    contact_type: Optional[str] = None,
    city: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Paginated list of business contacts with search and filtering.
    Search by company name, contact person, email, or phone.
    """
    # Build query
    stmt = select(BusinessContact)

    # Apply filters
    if search:
        stmt = stmt.where(
            or_(
                BusinessContact.company_name.ilike(f"%{search}%"),
                BusinessContact.contact_person.ilike(f"%{search}%"),
                BusinessContact.email.ilike(f"%{search}%"),
                BusinessContact.phone.ilike(f"%{search}%")
            )
        )

    if contact_type:
        stmt = stmt.where(BusinessContact.contact_type == contact_type)

    if city:
        stmt = stmt.where(BusinessContact.city.ilike(f"%{city}%"))

    if is_active is not None:
        stmt = stmt.where(BusinessContact.is_active == is_active)

    # Get total count
    count_stmt = select(func.count()).select_from(BusinessContact)
    
    if search:
        count_stmt = count_stmt.where(or_(
            BusinessContact.company_name.ilike(f"%{search}%"),
            BusinessContact.contact_person.ilike(f"%{search}%"),
            BusinessContact.email.ilike(f"%{search}%"),
            BusinessContact.phone.ilike(f"%{search}%")
        ))
    
    if contact_type:
        count_stmt = count_stmt.where(BusinessContact.contact_type == contact_type)
    
    if city:
        count_stmt = count_stmt.where(BusinessContact.city.ilike(f"%{city}%"))
    
    if is_active is not None:
        count_stmt = count_stmt.where(BusinessContact.is_active == is_active)
    
    result = await db.execute(count_stmt)
    total = result.scalar_one()
    total_pages = (total + per_page - 1) // per_page

    # Apply pagination
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    contacts = result.scalars().all()

    return BusinessContactListResponse(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        items=[BusinessContactResponse.from_orm(contact) for contact in contacts]
    )


@router.post("/", response_model=BusinessContactResponse)
async def create_contact(
    contact_data: BusinessContactCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create new business contact"""
    # Check for duplicate email
    result = await db.execute(select(BusinessContact).where(BusinessContact.email == contact_data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Contact with this email already exists")

    # Create contact
    contact = BusinessContact(
        company_name=contact_data.company_name,
        contact_person=contact_data.contact_person,
        phone=contact_data.phone,
        email=contact_data.email,
        gst_number=contact_data.gst_number,
        address=contact_data.address,
        city=contact_data.city,
        contact_type=contact_data.contact_type,
        product_categories=contact_data.product_categories
    )

    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    return BusinessContactResponse.from_orm(contact)


@router.get("/{contact_id}", response_model=BusinessContactResponse)
async def get_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get contact details with their invoice history summary.
    """
    result = await db.execute(select(BusinessContact).where(BusinessContact.contact_id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Get invoice history summary
    result = await db.execute(
        select(
            func.count(Invoice.invoice_id).label("total_invoices"),
            func.sum(Invoice.total_amount).label("total_amount"),
            func.sum(
                case(
                    (Invoice.status == "paid", Invoice.total_amount),
                    else_=None
                )
            ).label("paid_amount"),
            func.sum(
                case(
                    (Invoice.status == "pending", Invoice.total_amount),
                    else_=None
                )
            ).label("pending_amount"),
            func.sum(
                case(
                    (Invoice.status == "overdue", Invoice.total_amount),
                    else_=None
                )
            ).label("overdue_amount")
        ).where(Invoice.contact_id == contact_id)
    )
    invoice_stats = result.first()

    # Get last invoice date
    result = await db.execute(
        select(Invoice.created_at).where(
            Invoice.contact_id == contact_id
        ).order_by(desc(Invoice.created_at))
    )
    last_invoice = result.scalar_one_or_none()

    response = BusinessContactResponse.from_orm(contact)
    response.invoice_history = InvoiceHistorySummary(
        total_invoices=invoice_stats.total_invoices or 0,
        total_amount=float(invoice_stats.total_amount or 0),
        paid_amount=float(invoice_stats.paid_amount or 0),
        pending_amount=float(invoice_stats.pending_amount or 0),
        overdue_amount=float(invoice_stats.overdue_amount or 0),
        last_invoice_date=last_invoice if last_invoice else None
    )

    return response


@router.put("/{contact_id}", response_model=BusinessContactResponse)
async def update_contact(
    contact_id: UUID,
    contact_data: BusinessContactUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update contact information"""
    result = await db.execute(select(BusinessContact).where(BusinessContact.contact_id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Check for duplicate email if email is being updated
    if contact_data.email and contact_data.email != contact.email:
        result = await db.execute(select(BusinessContact).where(BusinessContact.email == contact_data.email))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Contact with this email already exists")

    # Update fields
    update_data = contact_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)

    contact.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(contact)

    return BusinessContactResponse.from_orm(contact)


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Soft delete a contact"""
    result = await db.execute(select(BusinessContact).where(BusinessContact.contact_id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact.is_active = False
    contact.updated_at = datetime.utcnow()

    await db.commit()

    return {
        "contact_id": contact_id,
        "message": "Contact deactivated successfully"
    }

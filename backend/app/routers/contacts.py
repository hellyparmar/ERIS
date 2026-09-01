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
@router.get("", response_model=BusinessContactListResponse)
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
    Search by company name, contact person, or phone.
    """
    # Build query
    stmt = select(BusinessContact)

    # Apply filters
    if search:
        stmt = stmt.where(
            or_(
                BusinessContact.company_name.ilike(f"%{search}%"),
                BusinessContact.contact_person.ilike(f"%{search}%"),
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
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    # Apply pagination and sorting
    stmt = stmt.order_by(BusinessContact.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    contacts = result.scalars().all()

    return BusinessContactListResponse(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        items=[
            BusinessContactResponse(
                contact_id=contact.contact_id,
                company_name=contact.company_name,
                contact_person=contact.contact_person,
                phone=contact.phone,
                gst_number=contact.gst_number,
                address=contact.address,
                city=contact.city,
                contact_type=contact.contact_type.value if hasattr(contact.contact_type, 'value') else str(contact.contact_type),
                product_categories=contact.product_categories or [],
                is_active=contact.is_active,
                created_at=contact.created_at,
                updated_at=contact.updated_at
            )
            for contact in contacts
        ]
    )


@router.post("/", response_model=BusinessContactResponse)
@router.post("", response_model=BusinessContactResponse)
async def create_contact(
    contact_data: BusinessContactCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create new business contact"""
    # Check for duplicate phone
    result = await db.execute(select(BusinessContact).where(BusinessContact.phone == contact_data.phone))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Contact with this phone number already exists")

    # Create contact
    contact = BusinessContact(
        company_name=contact_data.company_name,
        contact_person=contact_data.contact_person,
        phone=contact_data.phone,
        gst_number=contact_data.gst_number,
        address=contact_data.address,
        city=contact_data.city,
        contact_type=contact_data.contact_type,
        product_categories=contact_data.product_categories
    )

    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    return BusinessContactResponse(
        contact_id=contact.contact_id,
        company_name=contact.company_name,
        contact_person=contact.contact_person,
        phone=contact.phone,
        gst_number=contact.gst_number,
        address=contact.address,
        city=contact.city,
        contact_type=contact.contact_type.value if hasattr(contact.contact_type, 'value') else str(contact.contact_type),
        product_categories=contact.product_categories or [],
        is_active=contact.is_active,
        created_at=contact.created_at,
        updated_at=contact.updated_at
    )


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
            func.count(Invoice.id).label("total_invoices"),
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

    response = BusinessContactResponse(
        contact_id=contact.contact_id,
        company_name=contact.company_name,
        contact_person=contact.contact_person,
        phone=contact.phone,
        gst_number=contact.gst_number,
        address=contact.address,
        city=contact.city,
        contact_type=contact.contact_type.value if hasattr(contact.contact_type, 'value') else str(contact.contact_type),
        product_categories=contact.product_categories or [],
        is_active=contact.is_active,
        created_at=contact.created_at,
        updated_at=contact.updated_at
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

    # Check for duplicate phone if phone is being updated
    if contact_data.phone and contact_data.phone != contact.phone:
        result = await db.execute(select(BusinessContact).where(BusinessContact.phone == contact_data.phone))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Contact with this phone number already exists")

    # Update fields
    update_data = contact_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)

    contact.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(contact)

    return BusinessContactResponse(
        contact_id=contact.contact_id,
        company_name=contact.company_name,
        contact_person=contact.contact_person,
        phone=contact.phone,
        gst_number=contact.gst_number,
        address=contact.address,
        city=contact.city,
        contact_type=contact.contact_type.value if hasattr(contact.contact_type, 'value') else str(contact.contact_type),
        product_categories=contact.product_categories or [],
        is_active=contact.is_active,
        created_at=contact.created_at,
        updated_at=contact.updated_at
    )


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Soft delete / deactivate a contact"""
    result = await db.execute(select(BusinessContact).where(BusinessContact.contact_id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact.is_active = False
    contact.updated_at = datetime.utcnow()

    await db.commit()

    return {
        "contact_id": str(contact_id),
        "message": "Contact deactivated successfully"
    }

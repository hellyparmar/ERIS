"""
Messages Router - Communication Hub API Endpoints
Unified inbox for customer support, supplier POs, and internal chat
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.api.db import get_db
from app.api.db.models import MessageChannel, User
from app.api.services.message_service import MessageService
from app.api.auth.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/api/messages", tags=["messages"])

# ==================== REQUEST/RESPONSE MODELS ====================

class SendMessageRequest(BaseModel):
    sender_type: str = Field(..., description="customer, supplier, staff, system")
    sender_id: int
    recipient_type: str
    recipient_id: int
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    channel: str = Field(default="in_app", description="whatsapp, email, sms, in_app")
    related_entity_type: Optional[str] = Field(None, description="invoice, order, product")
    related_entity_id: Optional[int] = None
    thread_id: Optional[str] = None
    attachments: Optional[List[dict]] = None

class MessageResponse(BaseModel):
    id: int
    thread_id: str
    sender_type: str
    sender_id: int
    recipient_type: str
    recipient_id: int
    channel: str
    subject: str
    body: str
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    status: str
    sent_at: datetime
    read_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class InvoiceInquiryRequest(BaseModel):
    customer_id: int
    invoice_id: int
    message: str = Field(..., min_length=1)

class SupplierPORequest(BaseModel):
    staff_id: int
    supplier_id: int
    product_ids: List[int] = Field(..., min_items=1)
    quantities: List[int] = Field(..., min_items=1)
    notes: str = ""

# ==================== ENDPOINTS ====================

@router.post("/send", response_model=MessageResponse, status_code=201)
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send a message through unified inbox
    
    - Supports customer support, supplier communication, internal chat
    - Can be linked to invoices, orders, or products (contextual)
    - Automatically groups into conversation threads
    """
    try:
        service = MessageService(db)
        
        # Convert channel string to enum
        channel_enum = MessageChannel[request.channel.upper()]
        
        message = service.send_message(
            sender_type=request.sender_type,
            sender_id=request.sender_id,
            recipient_type=request.recipient_type,
            recipient_id=request.recipient_id,
            subject=request.subject,
            body=request.body,
            channel=channel_enum,
            related_entity_type=request.related_entity_type,
            related_entity_id=request.related_entity_id,
            thread_id=request.thread_id,
            attachments=request.attachments
        )
        
        return message
        
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid channel: {request.channel}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@router.get("/inbox", response_model=List[MessageResponse])
async def get_inbox(
    user_type: str = Query(..., description="staff, customer, supplier"),
    user_id: int = Query(...),
    unread_only: bool = Query(False),
    channel: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get messages in user's inbox
    
    - Filter by unread status
    - Filter by channel (whatsapp, email, sms, in_app)
    - Pagination support
    """
    service = MessageService(db)
    
    channel_enum = None
    if channel:
        try:
            channel_enum = MessageChannel[channel.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid channel: {channel}")
    
    messages = service.get_inbox(
        user_type=user_type,
        user_id=user_id,
        unread_only=unread_only,
        channel=channel_enum,
        limit=limit,
        offset=offset
    )
    
    return messages

@router.get("/sent", response_model=List[MessageResponse])
async def get_sent_messages(
    user_type: str = Query(...),
    user_id: int = Query(...),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get messages sent by user"""
    service = MessageService(db)
    return service.get_sent_messages(user_type, user_id, limit)

@router.get("/thread/{thread_id}", response_model=List[MessageResponse])
async def get_thread(
    thread_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all messages in a conversation thread"""
    service = MessageService(db)
    return service.get_thread(thread_id, limit)

@router.get("/contextual/{entity_type}/{entity_id}", response_model=List[MessageResponse])
async def get_contextual_messages(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all messages related to an invoice, order, or product
    
    **Use Cases:**
    - View all customer inquiries about a specific invoice
    - See communication history for a purchase order
    - Track support tickets for a product
    """
    service = MessageService(db)
    return service.get_contextual_messages(entity_type, entity_id)

@router.post("/{message_id}/mark-read", response_model=MessageResponse)
async def mark_as_read(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a message as read"""
    try:
        service = MessageService(db)
        return service.mark_as_read(message_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/thread/{thread_id}/mark-read")
async def mark_thread_as_read(
    thread_id: str,
    user_type: str = Query(...),
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Mark all messages in a thread as read for the user"""
    service = MessageService(db)
    count = service.mark_thread_as_read(thread_id, user_type, user_id)
    return {"marked_read": count, "thread_id": thread_id}

@router.get("/unread-count")
async def get_unread_count(
    user_type: str = Query(...),
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Get count of unread messages"""
    service = MessageService(db)
    total = service.get_unread_count(user_type, user_id)
    by_channel = service.get_unread_by_channel(user_type, user_id)
    
    return {
        "total_unread": total,
        "by_channel": by_channel
    }

@router.get("/search")
async def search_messages(
    user_type: str = Query(...),
    user_id: int = Query(...),
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Search messages by subject or body"""
    service = MessageService(db)
    return service.search_messages(user_type, user_id, q, limit)

@router.get("/inbox/summary")
async def get_inbox_summary(
    user_type: str = Query(...),
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Get inbox summary with statistics and recent threads"""
    service = MessageService(db)
    return service.get_inbox_summary(user_type, user_id)

# ==================== CONTEXTUAL MESSAGING SHORTCUTS ====================

@router.post("/invoice-inquiry", response_model=MessageResponse, status_code=201)
async def send_invoice_inquiry(
    request: InvoiceInquiryRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send customer inquiry about an invoice
    (Automatically links message to invoice)
    """
    try:
        service = MessageService(db)
        return service.send_invoice_inquiry(
            customer_id=request.customer_id,
            invoice_id=request.invoice_id,
            message_body=request.message
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/supplier-po", response_model=MessageResponse, status_code=201)
async def send_supplier_po(
    request: SupplierPORequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send purchase order to supplier
    (Automatically formats PO and links to products)
    """
    if len(request.product_ids) != len(request.quantities):
        raise HTTPException(
            status_code=400,
            detail="product_ids and quantities must have same length"
        )
    
    service = MessageService(db)
    return service.send_supplier_po(
        staff_id=request.staff_id,
        supplier_id=request.supplier_id,
        product_ids=request.product_ids,
        quantities=request.quantities,
        notes=request.notes
    )

@router.get("/stats/overview")
async def get_messaging_stats(db: Session = Depends(get_db)):
    """Get overall messaging platform statistics"""
    from app.api.db.models import Message
    
    total_messages = db.query(Message).count()
    by_channel = db.query(
        Message.channel,
        func.count(Message.id)
    ).group_by(Message.channel).all()
    
    by_status = db.query(
        Message.status,
        func.count(Message.id)
    ).group_by(Message.status).all()
    
    contextual_count = db.query(Message).filter(
        Message.related_entity_type.isnot(None)
    ).count()
    
    return {
        "total_messages": total_messages,
        "by_channel": {str(ch.value): count for ch, count in by_channel},
        "by_status": {status: count for status, count in by_status},
        "contextual_messages": contextual_count,
        "contextual_percentage": (contextual_count / total_messages * 100) if total_messages > 0 else 0
    }

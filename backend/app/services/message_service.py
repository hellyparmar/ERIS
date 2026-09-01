"""
Message Service - Communication Hub Core
Unified inbox for customer support, supplier communication, and internal chat
"""

from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models import Message, Invoice, MessageChannel

class MessageService:
    """Service for unified communication management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def send_message(
        self,
        sender_type: str,
        sender_id: int,
        recipient_type: str,
        recipient_id: int,
        subject: str,
        body: str,
        channel: MessageChannel = MessageChannel.IN_APP,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[int] = None,
        thread_id: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Message:
        """
        Send a message through unified inbox
        
        Args:
            sender_type: 'customer', 'supplier', 'staff', 'system'
            sender_id: ID of sender
            recipient_type: Type of recipient
            recipient_id: ID of recipient
            subject: Message subject
            body: Message content
            channel: Communication channel (email, sms, in_app)
            related_entity_type: Link to 'invoice', 'order', 'product'
            related_entity_id: ID of related entity
            thread_id: Group related messages
            attachments: List of attachment dicts
        
        Returns:
            Created message
        """
        # Generate thread_id if not provided
        if not thread_id:
            thread_id = self._generate_thread_id(
                sender_type, sender_id, recipient_type, recipient_id,
                related_entity_type, related_entity_id
            )
        
        message = Message(
            thread_id=thread_id,
            sender_type=sender_type,
            sender_id=sender_id,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            channel=channel,
            subject=subject,
            body=body,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            attachments=attachments,
            status="sent"
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def _generate_thread_id(
        self, 
        sender_type: str, 
        sender_id: int,
        recipient_type: str,
        recipient_id: int,
        related_entity_type: Optional[str],
        related_entity_id: Optional[int]
    ) -> str:
        """Generate unique thread ID for conversation"""
        if related_entity_type and related_entity_id:
            # Contextual thread (linked to invoice/order)
            return f"{related_entity_type}_{related_entity_id}_{sender_type}_{sender_id}"
        else:
            # Direct conversation thread
            participants = sorted([f"{sender_type}_{sender_id}", f"{recipient_type}_{recipient_id}"])
            return f"chat_{'_'.join(participants)}"
    
    def get_inbox(
        self,
        user_type: str,
        user_id: int,
        unread_only: bool = False,
        channel: Optional[MessageChannel] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """
        Get messages for a user's inbox
        
        Args:
            user_type: Type of user ('staff', 'customer', 'supplier')
            user_id: User ID
            unread_only: Show only unread messages
            channel: Filter by channel
            limit: Max messages to return
            offset: Pagination offset
        
        Returns:
            List of messages
        """
        query = self.db.query(Message).filter(
            and_(
                Message.recipient_type == user_type,
                Message.recipient_id == user_id
            )
        )
        
        if unread_only:
            query = query.filter(Message.read_at.is_(None))
        
        if channel:
            query = query.filter(Message.channel == channel)
        
        return query.order_by(Message.sent_at.desc()).limit(limit).offset(offset).all()
    
    def get_sent_messages(
        self,
        user_type: str,
        user_id: int,
        limit: int = 50
    ) -> List[Message]:
        """Get messages sent by a user"""
        return self.db.query(Message).filter(
            and_(
                Message.sender_type == user_type,
                Message.sender_id == user_id
            )
        ).order_by(Message.sent_at.desc()).limit(limit).all()
    
    def get_thread(
        self,
        thread_id: str,
        limit: int = 100
    ) -> List[Message]:
        """Get all messages in a conversation thread"""
        return self.db.query(Message).filter(
            Message.thread_id == thread_id
        ).order_by(Message.sent_at.asc()).limit(limit).all()
    
    def get_contextual_messages(
        self,
        entity_type: str,
        entity_id: int
    ) -> List[Message]:
        """
        Get all messages related to a specific entity
        
        Args:
            entity_type: 'invoice', 'order', 'product'
            entity_id: Entity ID
        
        Returns:
            Messages linked to this entity
        """
        return self.db.query(Message).filter(
            and_(
                Message.related_entity_type == entity_type,
                Message.related_entity_id == entity_id
            )
        ).order_by(Message.sent_at.asc()).all()
    
    def mark_as_read(self, message_id: int) -> Message:
        """Mark a message as read"""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise ValueError(f"Message {message_id} not found")
        
        if not message.read_at:
            message.read_at = datetime.now()
            message.status = "read"
            self.db.commit()
            self.db.refresh(message)
        
        return message
    
    def mark_thread_as_read(self, thread_id: str, user_type: str, user_id: int):
        """Mark all messages in a thread as read for a specific user"""
        messages = self.db.query(Message).filter(
            and_(
                Message.thread_id == thread_id,
                Message.recipient_type == user_type,
                Message.recipient_id == user_id,
                Message.read_at.is_(None)
            )
        ).all()
        
        for msg in messages:
            msg.read_at = datetime.now()
            msg.status = "read"
        
        self.db.commit()
        return len(messages)
    
    def get_unread_count(self, user_type: str, user_id: int) -> int:
        """Get count of unread messages"""
        return self.db.query(Message).filter(
            and_(
                Message.recipient_type == user_type,
                Message.recipient_id == user_id,
                Message.read_at.is_(None)
            )
        ).count()
    
    def get_unread_by_channel(self, user_type: str, user_id: int) -> Dict[str, int]:
        """Get unread count grouped by channel"""
        results = self.db.query(
            Message.channel,
            func.count(Message.id)
        ).filter(
            and_(
                Message.recipient_type == user_type,
                Message.recipient_id == user_id,
                Message.read_at.is_(None)
            )
        ).group_by(Message.channel).all()
        
        return {str(channel.value): count for channel, count in results}
    
    def search_messages(
        self,
        user_type: str,
        user_id: int,
        search_term: str,
        limit: int = 50
    ) -> List[Message]:
        """Search messages by subject or body"""
        return self.db.query(Message).filter(
            and_(
                or_(
                    Message.recipient_type == user_type,
                    Message.sender_type == user_type
                ),
                or_(
                    Message.recipient_id == user_id,
                    Message.sender_id == user_id
                ),
                or_(
                    Message.subject.ilike(f"%{search_term}%"),
                    Message.body.ilike(f"%{search_term}%")
                )
            )
        ).order_by(Message.sent_at.desc()).limit(limit).all()
    
    def send_invoice_inquiry(
        self,
        customer_id: int,
        invoice_id: int,
        message_body: str
    ) -> Message:
        """
        Send customer inquiry about an invoice
        (Contextual messaging - linked to invoice)
        """
        # Get invoice to validate
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        return self.send_message(
            sender_type="customer",
            sender_id=customer_id,
            recipient_type="staff",
            recipient_id=1,  # Admin/support staff
            subject=f"Inquiry about Invoice {invoice.invoice_number}",
            body=message_body,
            channel=MessageChannel.IN_APP,
            related_entity_type="invoice",
            related_entity_id=invoice_id
        )
    
    def send_supplier_po(
        self,
        staff_id: int,
        supplier_id: int,
        product_ids: List[int],
        quantities: List[int],
        notes: str
    ) -> Message:
        """
        Send purchase order to supplier
        (Contextual messaging - linked to products)
        """
        po_details = []
        for product_id, qty in zip(product_ids, quantities):
            po_details.append(f"Product ID {product_id}: {qty} units")
        
        body = f"Purchase Order Request:\n\n" + "\n".join(po_details) + f"\n\nNotes: {notes}"
        
        return self.send_message(
            sender_type="staff",
            sender_id=staff_id,
            recipient_type="supplier",
            recipient_id=supplier_id,
            subject="Purchase Order Request",
            body=body,
            channel=MessageChannel.SMS,
            related_entity_type="product",
            related_entity_id=product_ids[0] if product_ids else None
        )
    
    def get_inbox_summary(self, user_type: str, user_id: int) -> Dict:
        """Get inbox summary with statistics"""
        total_unread = self.get_unread_count(user_type, user_id)
        by_channel = self.get_unread_by_channel(user_type, user_id)
        
        # Get recent threads
        recent_threads = self.db.query(
            Message.thread_id,
            func.max(Message.sent_at).label('last_message'),
            func.count(Message.id).label('message_count')
        ).filter(
            or_(
                and_(Message.recipient_type == user_type, Message.recipient_id == user_id),
                and_(Message.sender_type == user_type, Message.sender_id == user_id)
            )
        ).group_by(Message.thread_id).order_by(func.max(Message.sent_at).desc()).limit(10).all()
        
        return {
            "total_unread": total_unread,
            "unread_by_channel": by_channel,
            "recent_threads": [
                {
                    "thread_id": t.thread_id,
                    "last_message": t.last_message.isoformat(),
                    "message_count": t.message_count
                }
                for t in recent_threads
            ]
        }
    
    def auto_respond_invoice_paid(self, invoice_id: int) -> Message:
        """
        Automatically send confirmation when invoice is paid
        (System-generated contextual message)
        """
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        return self.send_message(
            sender_type="system",
            sender_id=0,
            recipient_type="customer",
            recipient_id=invoice.customer_id,
            subject=f"Payment Confirmed - {invoice.invoice_number}",
            body=f"Thank you! Your payment of ₹{invoice.total_amount:,.2f} has been received and processed. Invoice {invoice.invoice_number} is now marked as PAID.",
            channel=MessageChannel.SMS,
            related_entity_type="invoice",
            related_entity_id=invoice_id
        )

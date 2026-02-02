"""
Loyalty Service - Next-Gen Loyalty Module
Full referral management, credit analytics, and smart reminders
"""

import random
import string
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from decimal import Decimal

from api.db.models import (
    Referral, Customer, CustomerCredit, Invoice, 
    PaymentStatus, Message, MessageChannel
)

logger = logging.getLogger(__name__)


class LoyaltyService:
    """Service for managing loyalty program, referrals, and credit (udhaar)"""
    
    REFERRAL_REWARD_AMOUNT = Decimal("100.00")  # ₹100 reward for successful referral
    
    def __init__(self, db: Session):
        self.db = db

    # ==================================================
    # REFERRAL CODE MANAGEMENT
    # ==================================================
    
    def generate_referral_code(self, length: int = 8) -> str:
        """Generate a unique referral code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            # Check if code already exists
            existing = self.db.query(Customer).filter(Customer.referral_code == code).first()
            if not existing:
                return code

    def ensure_customer_has_referral_code(self, customer_id: int) -> str:
        """Ensure customer has a referral code, generate if missing"""
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        if not customer.referral_code:
            customer.referral_code = self.generate_referral_code()
            self.db.commit()
        
        return customer.referral_code

    # ==================================================
    # REFERRAL MANAGEMENT
    # ==================================================
    
    def create_referral(
        self, 
        referrer_id: int, 
        referee_name: str, 
        referee_email: str = None,
        referee_phone: str = None
    ) -> Referral:
        """Create a new referral invite"""
        # Verify referrer exists
        referrer = self.db.query(Customer).filter(Customer.id == referrer_id).first()
        if not referrer:
            raise ValueError(f"Referrer customer {referrer_id} not found")
        
        referral = Referral(
            referrer_id=referrer_id,
            referee_name=referee_name,
            referee_email=referee_email,
            referee_phone=referee_phone,
            status="pending"
        )
        self.db.add(referral)
        self.db.commit()
        self.db.refresh(referral)
        
        logger.info(f"Created referral {referral.id} by customer {referrer_id}")
        return referral

    def get_customer_referrals(self, customer_id: int) -> List[Referral]:
        """Get all referrals made by a customer"""
        return self.db.query(Referral).filter(
            Referral.referrer_id == customer_id
        ).order_by(desc(Referral.created_at)).all()

    def get_all_referrals(
        self, 
        status: str = None, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all referrals with referrer info"""
        query = self.db.query(Referral).join(
            Customer, Customer.id == Referral.referrer_id
        )
        
        if status:
            query = query.filter(Referral.status == status)
        
        referrals = query.order_by(desc(Referral.created_at)).limit(limit).all()
        
        result = []
        for ref in referrals:
            referrer = self.db.query(Customer).filter(Customer.id == ref.referrer_id).first()
            result.append({
                "id": ref.id,
                "referrer_id": ref.referrer_id,
                "referrer_name": referrer.name if referrer else "Unknown",
                "referee_name": ref.referee_name,
                "referee_email": ref.referee_email,
                "referee_phone": ref.referee_phone,
                "status": ref.status,
                "reward_amount": float(ref.reward_amount or 0),
                "created_at": ref.created_at.isoformat() if ref.created_at else None,
                "converted_at": ref.converted_at.isoformat() if ref.converted_at else None
            })
        
        return result

    def convert_referral(self, referral_id: int, new_customer_id: int = None) -> Referral:
        """Mark a referral as converted and process reward"""
        referral = self.db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise ValueError(f"Referral {referral_id} not found")
        
        if referral.status != "pending":
            raise ValueError(f"Referral {referral_id} is already {referral.status}")
        
        referral.status = "converted"
        referral.converted_at = datetime.now()
        
        # Award loyalty points to the referrer
        referrer = self.db.query(Customer).filter(Customer.id == referral.referrer_id).first()
        if referrer:
            referrer.loyalty_points = (referrer.loyalty_points or 0) + 100  # 100 points per referral
            referral.reward_amount = self.REFERRAL_REWARD_AMOUNT
        
        self.db.commit()
        self.db.refresh(referral)
        
        logger.info(f"Referral {referral_id} converted, rewarded customer {referral.referrer_id}")
        return referral

    def get_top_referrers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top customers by successful referrals"""
        query = self.db.query(
            Customer.id,
            Customer.name,
            func.count(Referral.id).label('referral_count'),
            func.sum(Referral.reward_amount).label('total_earned')
        ).join(
            Referral, Referral.referrer_id == Customer.id
        ).filter(
            Referral.status == "converted"
        ).group_by(
            Customer.id, Customer.name
        ).order_by(
            desc('referral_count')
        ).limit(limit)
        
        return [
            {
                "customer_id": row.id,
                "name": row.name,
                "referral_count": row.referral_count,
                "total_earned": float(row.total_earned or 0)
            }
            for row in query.all()
        ]

    # ==================================================
    # CREDIT (UDHAAR) MANAGEMENT
    # ==================================================
    
    def get_customer_credit(self, customer_id: int) -> CustomerCredit:
        """Get or create customer credit account"""
        credit = self.db.query(CustomerCredit).filter(
            CustomerCredit.customer_id == customer_id
        ).first()
        
        if not credit:
            credit = CustomerCredit(
                customer_id=customer_id,
                credit_limit=Decimal("5000.00"),
                current_balance=Decimal("0.00"),
                credit_score=750
            )
            self.db.add(credit)
            self.db.commit()
            self.db.refresh(credit)
        
        return credit

    def get_all_credit_customers(
        self, 
        min_balance: float = 0,
        risk_level: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all customers with credit accounts and outstanding balance"""
        
        # Get customers with credit accounts
        query = self.db.query(CustomerCredit).join(
            Customer, Customer.id == CustomerCredit.customer_id
        ).filter(
            CustomerCredit.current_balance > min_balance
        )
        
        credit_accounts = query.order_by(
            desc(CustomerCredit.current_balance)
        ).limit(limit).all()
        
        result = []
        for credit in credit_accounts:
            customer = self.db.query(Customer).filter(Customer.id == credit.customer_id).first()
            
            # Calculate risk status
            utilization = float(credit.current_balance) / float(credit.credit_limit) * 100 if credit.credit_limit else 0
            if utilization >= 90:
                status = "critical"
            elif utilization >= 70:
                status = "warning"
            else:
                status = "good"
            
            # Skip if risk filter applied
            if risk_level and status != risk_level:
                continue
            
            # Get last payment date
            last_payment = credit.last_payment_date
            
            result.append({
                "id": credit.id,
                "customer_id": credit.customer_id,
                "customer_name": customer.name if customer else "Unknown",
                "phone": customer.phone if customer else None,
                "whatsapp": customer.whatsapp_number if customer else None,
                "balance": float(credit.current_balance),
                "credit_limit": float(credit.credit_limit),
                "utilization": round(utilization, 1),
                "credit_score": credit.credit_score,
                "status": status,
                "last_payment_date": last_payment.strftime("%d %b") if last_payment else None
            })
        
        return result

    def get_at_risk_customers(self, min_utilization: float = 80) -> List[Dict[str, Any]]:
        """Get customers at high credit risk"""
        return self.get_all_credit_customers(min_balance=0, risk_level=None)

    def calculate_credit_risk(self, customer_id: int) -> Dict[str, Any]:
        """Calculate credit risk score for a customer"""
        credit = self.get_customer_credit(customer_id)
        
        # Get payment history from invoices
        invoices = self.db.query(Invoice).filter(
            Invoice.customer_id == customer_id
        ).all()
        
        total_invoices = len(invoices)
        overdue_count = sum(1 for inv in invoices if inv.payment_status == PaymentStatus.OVERDUE)
        on_time_count = sum(1 for inv in invoices if inv.payment_status == PaymentStatus.PAID)
        
        # Calculate score factors
        utilization_factor = 100 - (float(credit.current_balance) / float(credit.credit_limit or 1) * 100)
        payment_history_factor = (on_time_count / max(total_invoices, 1)) * 100
        
        # Base score
        risk_score = int((utilization_factor * 0.4 + payment_history_factor * 0.6))
        risk_score = max(300, min(850, risk_score + 500))  # CIBIL-like range
        
        return {
            "customer_id": customer_id,
            "credit_score": risk_score,
            "utilization_percent": round(100 - utilization_factor, 1),
            "total_invoices": total_invoices,
            "overdue_invoices": overdue_count,
            "on_time_payments": on_time_count,
            "recommendation": "Increase limit" if risk_score > 750 else "Monitor closely" if risk_score < 600 else "Stable"
        }

    # ==================================================
    # DASHBOARD STATISTICS
    # ==================================================
    
    def get_loyalty_stats(self) -> Dict[str, Any]:
        """Get overall loyalty program statistics"""
        
        # Referral stats
        total_referrals = self.db.query(func.count(Referral.id)).scalar() or 0
        converted_referrals = self.db.query(func.count(Referral.id)).filter(
            Referral.status == "converted"
        ).scalar() or 0
        pending_referrals = self.db.query(func.count(Referral.id)).filter(
            Referral.status == "pending"
        ).scalar() or 0
        
        # Total rewards earned
        total_rewards = self.db.query(func.sum(Referral.reward_amount)).filter(
            Referral.status == "converted"
        ).scalar() or 0
        
        # Pending rewards (converted but not yet claimed)
        pending_rewards = self.db.query(func.sum(Referral.reward_amount)).filter(
            Referral.status == "converted"
        ).scalar() or 0
        
        # Credit stats
        total_credit_outstanding = self.db.query(
            func.sum(CustomerCredit.current_balance)
        ).scalar() or 0
        
        credit_customer_count = self.db.query(
            func.count(CustomerCredit.id)
        ).filter(CustomerCredit.current_balance > 0).scalar() or 0
        
        # At-risk customers (>80% utilization)
        at_risk_count = 0
        all_credits = self.db.query(CustomerCredit).filter(
            CustomerCredit.current_balance > 0
        ).all()
        for c in all_credits:
            if c.credit_limit and float(c.current_balance) / float(c.credit_limit) > 0.8:
                at_risk_count += 1
        
        return {
            "referrals": {
                "total": total_referrals,
                "converted": converted_referrals,
                "pending": pending_referrals,
                "conversion_rate": round(converted_referrals / max(total_referrals, 1) * 100, 1)
            },
            "rewards": {
                "total_earned": float(total_rewards),
                "pending": float(pending_rewards)
            },
            "credit": {
                "total_outstanding": float(total_credit_outstanding),
                "formatted": self._format_inr(float(total_credit_outstanding)),
                "customer_count": credit_customer_count,
                "at_risk_count": at_risk_count
            }
        }

    def _format_inr(self, amount: float) -> str:
        """Format amount in INR style (L for lakhs)"""
        if amount >= 100000:
            return f"₹{amount/100000:.1f}L"
        elif amount >= 1000:
            return f"₹{amount/1000:.1f}K"
        else:
            return f"₹{amount:,.0f}"

    # ==================================================
    # REMINDER MANAGEMENT
    # ==================================================
    
    def get_reminder_queue(
        self, 
        min_days_overdue: int = 1,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get prioritized list of customers needing reminders"""
        
        # Get overdue invoices
        overdue_invoices = self.db.query(Invoice).filter(
            Invoice.payment_status.in_([PaymentStatus.OVERDUE, PaymentStatus.PENDING]),
            Invoice.amount_due > 0
        ).all()
        
        reminder_queue = []
        seen_customers = set()
        
        for invoice in overdue_invoices:
            if invoice.customer_id in seen_customers:
                continue
            
            customer = invoice.customer
            if not customer:
                continue
            
            days_overdue = 0
            if invoice.due_date:
                days_overdue = (datetime.now() - invoice.due_date).days
            
            if days_overdue < min_days_overdue:
                continue
            
            # Determine urgency
            if days_overdue > 60:
                urgency = "final"
            elif days_overdue > 30:
                urgency = "urgent"
            else:
                urgency = "friendly"
            
            reminder_queue.append({
                "customer_id": customer.id,
                "customer_name": customer.name,
                "phone": customer.phone,
                "whatsapp": customer.whatsapp_number,
                "email": customer.email,
                "invoice_number": invoice.invoice_number,
                "amount_due": float(invoice.amount_due),
                "days_overdue": max(0, days_overdue),
                "urgency": urgency
            })
            
            seen_customers.add(customer.id)
        
        # Sort by days overdue (most urgent first)
        reminder_queue.sort(key=lambda x: x['days_overdue'], reverse=True)
        
        return reminder_queue[:limit]

    def record_reminder_sent(
        self, 
        customer_id: int, 
        invoice_id: int,
        channel: str = "whatsapp"
    ) -> Message:
        """Record that a reminder was sent"""
        
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not customer or not invoice:
            logger.warning(f"Cannot record reminder: customer={customer_id}, invoice={invoice_id}")
            return None
        
        message = Message(
            sender_type="system",
            sender_id=0,
            recipient_type="customer",
            recipient_id=customer_id,
            channel=MessageChannel[channel.upper()],
            subject="Payment Reminder",
            body=f"Payment reminder sent for Invoice #{invoice.invoice_number}",
            related_entity_type="invoice",
            related_entity_id=invoice_id,
            status="sent"
        )
        
        self.db.add(message)
        self.db.commit()
        
        return message

    def get_reminder_history(
        self, 
        customer_id: int = None,
        days: int = 30,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get history of reminders sent"""
        
        query = self.db.query(Message).filter(
            Message.sender_type == "system",
            Message.subject.ilike("%reminder%"),
            Message.sent_at >= datetime.now() - timedelta(days=days)
        )
        
        if customer_id:
            query = query.filter(Message.recipient_id == customer_id)
        
        messages = query.order_by(desc(Message.sent_at)).limit(limit).all()
        
        return [
            {
                "id": msg.id,
                "customer_id": msg.recipient_id,
                "channel": msg.channel.value if msg.channel else "unknown",
                "subject": msg.subject,
                "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
                "status": msg.status,
                "related_invoice_id": msg.related_entity_id
            }
            for msg in messages
        ]

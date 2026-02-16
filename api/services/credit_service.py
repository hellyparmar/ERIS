"""
Enterprise Retail Intelligence System v3.0
Credit Service - Customer credit management and payment tracking
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, List
from api.models.customer import Customer
from api.models.credit_payment import CreditPayment


class CreditService:
    """Service for customer credit management"""
    
    @staticmethod
    def assign_credit_limit(db: Session, customer_id: int, limit: Decimal) -> Dict:
        """Assign or update credit limit for a customer"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        old_limit = customer.credit_limit
        customer.credit_limit = limit
        
        db.commit()
        
        return {
            'success': True,
            'customer_id': customer_id,
            'old_limit': float(old_limit) if old_limit else 0,
            'new_limit': float(limit),
            'available_credit': float(limit - (customer.outstanding_balance or Decimal('0')))
        }
    
    @staticmethod
    def record_credit_sale(db: Session, customer_id: int, amount: Decimal) -> Dict:
        """Record a credit sale (increases outstanding balance)"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Check credit limit
        new_balance = (customer.outstanding_balance or Decimal('0')) + amount
        
        if new_balance > customer.credit_limit:
            return {
                'success': False,
                'message': f'Credit limit exceeded. Limit: ₹{customer.credit_limit}, New balance would be: ₹{new_balance}'
            }
        
        customer.outstanding_balance = new_balance
        
        db.commit()
        
        return {
            'success': True,
            'amount': float(amount),
            'outstanding_balance': float(new_balance),
            'available_credit': float(customer.credit_limit - new_balance)
        }
    
    @staticmethod
    def record_payment(
        db: Session,
        customer_id: int,
        amount: Decimal,
        payment_method: str,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> Dict:
        """Record a credit payment"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        if amount <= 0:
            return {
                'success': False,
                'message': 'Payment amount must be greater than zero'
            }
        
        if amount > customer.outstanding_balance:
            return {
                'success': False,
                'message': f'Payment amount (₹{amount}) exceeds outstanding balance (₹{customer.outstanding_balance})'
            }
        
        # Create payment record
        payment = CreditPayment(
            customer_id=customer_id,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        
        db.add(payment)
        
        # Update outstanding balance
        customer.outstanding_balance -= amount
        
        db.commit()
        db.refresh(payment)
        
        return {
            'success': True,
            'payment_id': payment.id,
            'amount_paid': float(amount),
            'remaining_balance': float(customer.outstanding_balance),
            'available_credit': float(customer.credit_limit - customer.outstanding_balance)
        }
    
    @staticmethod
    def get_credit_status(db: Session, customer_id: int) -> Dict:
        """Get customer's credit status"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        credit_limit = customer.credit_limit or Decimal('0')
        outstanding_balance = customer.outstanding_balance or Decimal('0')
        available_credit = credit_limit - outstanding_balance
        
        utilization = (outstanding_balance / credit_limit * 100) if credit_limit > 0 else 0
        
        return {
            'customer_id': customer_id,
            'customer_name': customer.name,
            'credit_limit': float(credit_limit),
            'outstanding_balance': float(outstanding_balance),
            'available_credit': float(available_credit),
            'utilization_percentage': round(float(utilization), 2),
            'status': 'overdue' if outstanding_balance > credit_limit else 'good'
        }
    
    @staticmethod
    def get_payment_history(
        db: Session,
        customer_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """Get payment history for a customer"""
        payments = db.query(CreditPayment).filter(
            CreditPayment.customer_id == customer_id
        ).order_by(desc(CreditPayment.created_at)).limit(limit).all()
        
        return [p.to_dict() for p in payments]
    
    @staticmethod
    def get_overdue_customers(db: Session) -> List[Dict]:
        """Get customers with outstanding balance exceeding credit limit"""
        customers = db.query(Customer).filter(
            Customer.outstanding_balance > Customer.credit_limit
        ).all()
        
        return [
            {
                'customer_id': c.id,
                'name': c.name,
                'phone': c.phone,
                'credit_limit': float(c.credit_limit),
                'outstanding_balance': float(c.outstanding_balance),
                'overdue_amount': float(c.outstanding_balance - c.credit_limit)
            }
            for c in customers
        ]
    
    @staticmethod
    def get_credit_stats(db: Session) -> Dict:
        """Get overall credit statistics"""
        from sqlalchemy import func
        
        total_credit_issued = db.query(func.sum(Customer.credit_limit)).scalar() or Decimal('0')
        total_outstanding = db.query(func.sum(Customer.outstanding_balance)).scalar() or Decimal('0')
        
        customers_with_credit = db.query(func.count(Customer.id)).filter(
            Customer.credit_limit > 0
        ).scalar()
        
        overdue_count = db.query(func.count(Customer.id)).filter(
            Customer.outstanding_balance > Customer.credit_limit
        ).scalar()
        
        return {
            'total_credit_issued': float(total_credit_issued),
            'total_outstanding': float(total_outstanding),
            'customers_with_credit': customers_with_credit,
            'overdue_customers': overdue_count,
            'collection_rate': round((1 - float(total_outstanding / total_credit_issued)) * 100, 2) if total_credit_issued > 0 else 100
        }

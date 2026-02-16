"""
Enterprise Retail Intelligence System v3.0
Customer Service - Customer profile management and segmentation
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from api.models.customer import Customer


class CustomerService:
    """Service for customer profile management"""
    
    # Segmentation thresholds
    VIP_THRESHOLD = Decimal('50000')  # ₹50,000 lifetime value
    REGULAR_THRESHOLD = Decimal('10000')  # ₹10,000 lifetime value
    
    @staticmethod
    def create_customer(db: Session, data: Dict) -> Customer:
        """Create a new customer"""
        customer = Customer(
            name=data['name'],
            phone=data['phone'],
            email=data.get('email'),
            address=data.get('address'),
            segment='New',
            created_at=datetime.utcnow()
        )
        
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
        return customer
    
    @staticmethod
    def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
        """Get customer by ID"""
        return db.query(Customer).filter(Customer.id == customer_id).first()
    
    @staticmethod
    def get_customer_by_phone(db: Session, phone: str) -> Optional[Customer]:
        """Get customer by phone number"""
        return db.query(Customer).filter(Customer.phone == phone).first()
    
    @staticmethod
    def update_customer(db: Session, customer_id: int, data: Dict) -> Optional[Customer]:
        """Update customer information"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            return None
        
        # Update allowed fields
        for field in ['name', 'email', 'address']:
            if field in data:
                setattr(customer, field, data[field])
        
        customer.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(customer)
        
        return customer
    
    @staticmethod
    def delete_customer(db: Session, customer_id: int) -> bool:
        """Delete a customer"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            return False
        
        db.delete(customer)
        db.commit()
        
        return True
    
    @staticmethod
    def list_customers(
        db: Session,
        segment: Optional[str] = None,
        tier: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """List customers with filters and pagination"""
        query = db.query(Customer)
        
        # Apply filters
        if segment:
            query = query.filter(Customer.segment == segment)
        
        if tier:
            query = query.filter(Customer.loyalty_tier == tier)
        
        if search:
            query = query.filter(
                (Customer.name.ilike(f'%{search}%')) |
                (Customer.phone.ilike(f'%{search}%')) |
                (Customer.email.ilike(f'%{search}%'))
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        customers = query.order_by(desc(Customer.created_at)).offset(offset).limit(per_page).all()
        
        return {
            'customers': [c.to_dict() for c in customers],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    
    @staticmethod
    def update_purchase_stats(db: Session, customer_id: int, sale_amount: Decimal):
        """Update customer purchase statistics"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            return
        
        # Update stats
        customer.total_purchases += 1
        customer.lifetime_value = (customer.lifetime_value or Decimal('0')) + sale_amount
        customer.last_purchase_at = datetime.utcnow()
        
        if not customer.first_purchase_at:
            customer.first_purchase_at = datetime.utcnow()
        
        # Update segment
        customer.segment = CustomerService._calculate_segment(customer.lifetime_value)
        
        db.commit()
    
    @staticmethod
    def _calculate_segment(lifetime_value: Decimal) -> str:
        """Calculate customer segment based on lifetime value"""
        if lifetime_value >= CustomerService.VIP_THRESHOLD:
            return 'VIP'
        elif lifetime_value >= CustomerService.REGULAR_THRESHOLD:
            return 'Regular'
        else:
            return 'New'
    
    @staticmethod
    def get_top_customers(db: Session, limit: int = 10) -> List[Customer]:
        """Get top customers by lifetime value"""
        return db.query(Customer).order_by(desc(Customer.lifetime_value)).limit(limit).all()
    
    @staticmethod
    def get_customer_stats(db: Session) -> Dict:
        """Get overall customer statistics"""
        total_customers = db.query(func.count(Customer.id)).scalar()
        
        vip_count = db.query(func.count(Customer.id)).filter(Customer.segment == 'VIP').scalar()
        regular_count = db.query(func.count(Customer.id)).filter(Customer.segment == 'Regular').scalar()
        new_count = db.query(func.count(Customer.id)).filter(Customer.segment == 'New').scalar()
        
        total_ltv = db.query(func.sum(Customer.lifetime_value)).scalar() or Decimal('0')
        avg_ltv = db.query(func.avg(Customer.lifetime_value)).scalar() or Decimal('0')
        
        return {
            'total_customers': total_customers,
            'vip_customers': vip_count,
            'regular_customers': regular_count,
            'new_customers': new_count,
            'total_lifetime_value': float(total_ltv),
            'average_lifetime_value': float(avg_ltv)
        }

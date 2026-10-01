"""
Enterprise Retail Intelligence System v3.0
Customer Service - Customer profile management and segmentation
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
from app.models.customers import Customer


class CustomerService:
    """Service for customer profile management"""

    # Segmentation thresholds
    VIP_THRESHOLD = Decimal("50000")  # ₹50,000 lifetime value
    REGULAR_THRESHOLD = Decimal("10000")  # ₹10,000 lifetime value

    @staticmethod
    def create_customer(db: Session, data: Dict, organization_id: int) -> Customer:
        """Create a new customer"""
        customer = Customer(
            name=data["name"],
            phone=data["phone"],
            email=data.get("email"),
            address=data.get("address"),
            organization_id=organization_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        return customer

    @staticmethod
    def get_customer(db: Session, customer_id: int, organization_id: int) -> Optional[Customer]:
        """Get customer by ID"""
        return (
            db.query(Customer)
            .filter(
                Customer.id == customer_id, Customer.organization_id == organization_id, Customer.is_deleted.is_(False)
            )
            .first()
        )

    @staticmethod
    def get_customer_by_phone(db: Session, phone: str, organization_id: int) -> Optional[Customer]:
        """Get customer by phone number"""
        return (
            db.query(Customer)
            .filter(
                Customer.phone == phone, Customer.organization_id == organization_id, Customer.is_deleted.is_(False)
            )
            .first()
        )

    @staticmethod
    def update_customer(db: Session, customer_id: int, organization_id: int, data: Dict) -> Optional[Customer]:
        """Update customer information"""
        customer = CustomerService.get_customer(db, customer_id, organization_id)

        if not customer:
            return None

        # Update allowed fields
        for field in ["name", "email", "address"]:
            if field in data:
                setattr(customer, field, data[field])

        customer.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(customer)

        return customer

    @staticmethod
    def delete_customer(db: Session, customer_id: int, organization_id: int) -> bool:
        """Delete a customer"""
        customer = CustomerService.get_customer(db, customer_id, organization_id)

        if not customer:
            return False

        customer.is_deleted = True
        customer.is_active = False
        db.commit()

        return True

    @staticmethod
    def list_customers(
        db: Session,
        segment: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        organization_id: int = 1,
    ) -> Dict:
        """List customers with filters and pagination"""
        query = db.query(Customer).filter(Customer.organization_id == organization_id, Customer.is_deleted.is_(False))

        # Apply filters
        if segment:
            threshold = CustomerService.VIP_THRESHOLD if segment == "VIP" else CustomerService.REGULAR_THRESHOLD
            if segment == "VIP":
                query = query.filter(Customer.total_purchases >= threshold)
            elif segment == "Regular":
                query = query.filter(
                    Customer.total_purchases >= threshold, Customer.total_purchases < CustomerService.VIP_THRESHOLD
                )
            else:
                query = query.filter(Customer.total_purchases < CustomerService.REGULAR_THRESHOLD)

        if search:
            query = query.filter(
                (Customer.first_name.ilike(f"%{search}%"))
                | (Customer.last_name.ilike(f"%{search}%"))
                | (Customer.phone.ilike(f"%{search}%"))
                | (Customer.email.ilike(f"%{search}%"))
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        customers = query.order_by(desc(Customer.created_at)).offset(offset).limit(per_page).all()

        return {
            "customers": [c.to_dict() for c in customers],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }

    @staticmethod
    def get_customer_stats(db: Session, organization_id: int) -> Dict:
        """Get overall customer statistics"""
        base = [Customer.organization_id == organization_id, Customer.is_deleted.is_(False)]
        total_customers = db.query(func.count(Customer.id)).filter(*base).scalar()

        vip_count = (
            db.query(func.count(Customer.id))
            .filter(*base, Customer.total_purchases >= CustomerService.VIP_THRESHOLD)
            .scalar()
        )
        regular_count = (
            db.query(func.count(Customer.id))
            .filter(
                *base,
                Customer.total_purchases >= CustomerService.REGULAR_THRESHOLD,
                Customer.total_purchases < CustomerService.VIP_THRESHOLD,
            )
            .scalar()
        )
        new_count = (
            db.query(func.count(Customer.id))
            .filter(*base, Customer.total_purchases < CustomerService.REGULAR_THRESHOLD)
            .scalar()
        )

        total_ltv = db.query(func.sum(Customer.total_purchases)).filter(*base).scalar() or Decimal("0")
        avg_ltv = db.query(func.avg(Customer.total_purchases)).filter(*base).scalar() or Decimal("0")

        return {
            "total_customers": total_customers,
            "vip_customers": vip_count,
            "regular_customers": regular_count,
            "new_customers": new_count,
            "total_lifetime_value": float(total_ltv),
            "average_lifetime_value": float(avg_ltv),
        }

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app.models.multitenant_models import Customer, User
from app.schemas.customers import CustomerCreate, CustomerResponse, PurchaseHistoryItem
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])

@router.get("/", response_model=List[CustomerResponse])
def get_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all customers registered under the organization.
    """
    customers = db.query(Customer).filter(
        Customer.organization_id == current_user.organization_id
    ).all()
    return customers

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve details for a specific customer by ID.
    """
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.organization_id == current_user.organization_id
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enroll a new customer into the organization's database.
    
    - **phone**: Must be unique within the organization.
    - **customer_code**: Generated automatically.
    """
    # Check if phone already exists for this organization
    if customer_in.phone and db.query(Customer).filter(
        Customer.phone == customer_in.phone,
        Customer.organization_id == current_user.organization_id
    ).first():
        raise HTTPException(status_code=400, detail="Customer with this phone number already exists")
    
    # Create Customer
    uid = uuid.uuid4().hex
    new_customer = Customer(
        **customer_in.model_dump(),
        customer_code=f"CUST-{uid[0:6].upper()}"
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer

@router.get("/{customer_id}/purchase-history", response_model=List[PurchaseHistoryItem])
def get_purchase_history(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve the transaction history for a specific customer.
    """
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.organization_id == current_user.organization_id
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    history = []
    for sale in customer.sales:
        history.append({
            "sale_id": sale.id,
            "transaction_date": sale.transaction_date,
            "total_amount": sale.total_amount,
            "items_count": len(sale.items)
        })
        
    return history

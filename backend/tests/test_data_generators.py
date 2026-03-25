import uuid
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.multitenant_models import Product, Inventory, Customer, User
from app.models.models import Sale, SaleItem, PaymentStatus
from decimal import Decimal

def create_test_product(db: Session, organization_id, store_id, initial_stock: int = 100):
    uid = uuid.uuid4().hex[0:6].upper()
    product = Product(
        sku=f"SKU-{uid}",
        name=f"Product {uid}",
        category="Test Category",
        unit_price=Decimal("100.0"),
        cost_price=Decimal("50.0"),
        organization_id=organization_id
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    
    inventory = Inventory(
        product_id=product.id,
        store_id=store_id,
        current_stock=initial_stock,
        available_stock=initial_stock,
        reorder_point=10
    )
    db.add(inventory)
    db.commit()
    
    return product

def create_test_customer(db: Session, organization_id):
    uid = uuid.uuid4().hex[0:6].upper()
    customer = Customer(
        name=f"Test Customer {uid}",
        email=f"customer_{uid.lower()}@example.com",
        phone=f"+91{random.randint(6000000000, 9999999999)}",
        organization_id=organization_id,
        customer_code=f"CUST-{uid}"
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

def generate_historical_sales(db: Session, organization_id: int, store_id: int, product_id: int, days: int = 30):
    sales = []
    base_date = datetime.utcnow() - timedelta(days=days)
    
    for i in range(days):
        date = base_date + timedelta(days=i)
        # Random number of sales per day (0 to 5)
        num_sales = random.randint(1, 5)
        for _ in range(num_sales):
            sale_uid = uuid.uuid4().hex[0:8].upper()
            qty = random.randint(1, 3)
            unit_price = 100.0
            total = qty * unit_price
            
            sale = Sale(
                transaction_id=f"TRX-{sale_uid}",
                store_id=store_id,
                transaction_date=date,
                total_amount=Decimal(str(total)),
                payment_method="cash",
                payment_status=PaymentStatus.PAID,
                items=[
                    SaleItem(
                        product_id=product_id,
                        quantity=qty,
                        unit_price=Decimal(str(unit_price)),
                        line_total=Decimal(str(total))
                    )
                ]
            )
            db.add(sale)
            sales.append(sale)
            
    db.commit()
    return sales

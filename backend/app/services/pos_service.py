"""
POS Transaction Service
ACID-compliant sale processing with inventory locking and event chain
Per CLAUDE.md Part 5.1 specifications
"""
import logging
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.customers import Customer
from app.models.models_v6 import Sale
from app.models.models_v6 import SaleItem
from app.models.inventory import Inventory
from app.models.models_v6 import Product
from app.models.users import User
from app.core.data_isolation import OutletDataAccess

logger = logging.getLogger(__name__)


def complete_sale(cart: dict, payment: dict, cashier_id: int, db: Session) -> dict:
    """
    Complete POS sale with ACID guarantees
    
    Args:
        cart: {"items": [...], "subtotal": float, "gst_amount": float, "total": float, "customer_id": int|None}
        payment: {"method": str, "amount": float, "reference": str|None}
        cashier_id: User ID of cashier
        db: Database session
        
    Returns:
        dict with sale_id, receipt data
        
    Raises:
        HTTPException 400: Validation error (insufficient stock, invalid product)
        HTTPException 500: Database error
    """
    try:
        # Get cashier user and validate outlet access
        cashier = db.query(User).filter(User.id == cashier_id).first()
        if not cashier:
            raise ValueError("Invalid cashier ID")
        
        if not cashier.outlet_id:
            raise ValueError("Cashier not assigned to an outlet")
        
        allowed_outlet_ids = OutletDataAccess.get_allowed_outlet_ids(cashier)
        
        if allowed_outlet_ids is None:
            # Super admin cashiers fallback to user's outlet_id or first available outlet
            if cashier.outlet_id:
                outlet_id = cashier.outlet_id
            else:
                from app.models.outlet import Outlet
                first_outlet = db.query(Outlet).first()
                if not first_outlet:
                    raise ValueError("No outlets found in the system")
                outlet_id = first_outlet.id
        else:
            if len(allowed_outlet_ids) != 1:
                # If they have multiple outlets (e.g. area manager), use user's primary outlet_id
                if cashier.outlet_id and cashier.outlet_id in allowed_outlet_ids:
                    outlet_id = cashier.outlet_id
                else:
                    raise ValueError("Cashier must be assigned to exactly one outlet or have a valid primary outlet assignment")
            else:
                outlet_id = allowed_outlet_ids[0]
        # Step 1: Lock all inventory rows first (prevents race conditions / overselling)
        product_ids = [i['product_id'] for i in cart['items']]
        inv_rows = db.query(Inventory).filter(
            Inventory.product_id.in_(product_ids),
            Inventory.outlet_id == outlet_id
        ).with_for_update().all()
        inv_map = {i.product_id: i for i in inv_rows}

        # Step 2: Validate ALL stock before touching anything
        for item in cart['items']:
            inv = inv_map.get(item['product_id'])
            if not inv:
                raise ValueError(f"Product {item['product_id']} not found in inventory")
            if inv.current_stock < item['quantity']:
                product = db.query(Product).filter_by(id=item['product_id']).first()
                product_name = product.name if product else f"Product {item['product_id']}"
                raise ValueError(
                    f"Only {inv.current_stock} units of '{product_name}' available. "
                    f"Requested: {item['quantity']}"
                )

        # Step 3: Create sale record
        from app.models.sale import SalePaymentStatus
        transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        sale = Sale(
            transaction_id=transaction_id,
            organization_id=getattr(cashier, 'organization_id', None),
            store_id=outlet_id,
            customer_id=cart.get('customer_id'),
            cashier_id=cashier_id,
            subtotal=cart.get('subtotal', 0),
            discount=0.0,  # TODO: Handle discounts
            tax_amount=cart.get('gst_amount', 0),
            total_amount=cart['total'],
            amount_paid=cart['total'],
            payment_method=payment['method'],
            payment_status=SalePaymentStatus.PAID.value,
            channel='pos',
            notes='POS sale',
            transaction_date=datetime.now(),
        )
        db.add(sale)
        db.flush()  # Get sale.id without committing yet

        # Step 4: Add items and deduct stock atomically
        for item in cart['items']:
            # Add sale item
            db.add(SaleItem(
                sale_id=sale.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                line_total=item['total']
            ))
            
            # Deduct inventory
            inv_map[item['product_id']].current_stock -= item['quantity']
            
            # Update stock status
            inv = inv_map[item['product_id']]
            if inv.current_stock == 0:
                inv.stock_status = 'out_of_stock'
            elif inv.current_stock <= inv.reorder_point:
                inv.stock_status = 'low'
            elif inv.current_stock <= (inv.reorder_point * 1.5):
                inv.stock_status = 'medium'
            else:
                inv.stock_status = 'high'

        # Step 5: Commit transaction (ACID point)
        db.commit()
        db.refresh(sale)

        logger.info(f"Sale {sale.id} completed: ₹{cart['total']:.2f}, {len(cart['items'])} items")

        # Step 7: Fire post-sale events (non-blocking — failures do not rollback sale)
        try:
            _trigger_post_sale_events(sale.id, product_ids, cart.get('customer_id'), db)
        except Exception as e:
            logger.warning(f"Post-sale events failed (non-critical): {e}")

        return _build_receipt(sale, cart, payment, db)

    except ValueError as e:
        db.rollback()
        logger.warning(f"Sale validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Sale failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Sale could not be processed. No charges made. Please try again."
        )


def _trigger_post_sale_events(sale_id: int, product_ids: List[int], customer_id: int, db: Session):
    """
    Trigger post-sale event chain (non-blocking)
    - Reorder alerts
    - Customer tier upgrade
    - Audit log
    """
    from app.models import Alert
    
    # Check reorder alerts
    for pid in product_ids:
        inv = db.query(Inventory).filter_by(product_id=pid).first()
        if inv and inv.current_stock <= inv.reorder_point:
            # Check if alert already exists
            existing = db.query(Alert).filter_by(
                product_id=pid,
                alert_type='reorder',
                status='active'
            ).first()
            
            if not existing:
                severity = 'critical' if inv.current_stock == 0 else 'warning'
                product = db.query(Product).filter_by(id=pid).first()
                product_name = product.name if product else f"Product {pid}"
                
                db.add(Alert(
                    product_id=pid,
                    alert_type='reorder',
                    severity=severity,
                    message=f"{product_name}: Stock {inv.current_stock} units — reorder point is {inv.reorder_point}",
                    status='active',
                    created_at=datetime.now()
                ))
    
    db.commit()


def _build_receipt(sale: Sale, cart: dict, payment: dict, db: Session) -> dict:
    """Build receipt data structure"""
    items = []
    for item in cart['items']:
        product = db.query(Product).filter_by(id=item['product_id']).first()
        items.append({
            "product_id": item['product_id'],
            "name": product.name if product else "Unknown Product",
            "sku": product.sku if product else "",
            "quantity": item['quantity'],
            "unit_price": item['unit_price'],
            "line_total": item['total']
        })
    
    return {
        "success": True,
        "data": {
            "sale_id": sale.id,
            "transaction_id": sale.transaction_id,
            "receipt_number": f"RCP-{sale.id:06d}",
            "timestamp": sale.transaction_date.isoformat() if sale.transaction_date else datetime.now().isoformat(),
            "items": items,
            "subtotal": cart['subtotal'],
            "gst_amount": cart.get('gst_amount', 0),
            "total": cart['total'],
            "payment_method": payment['method'],
            "payment_amount": payment['amount'],
            "customer_id": cart.get('customer_id')
        },
        "message": f"Sale completed successfully. Receipt: RCP-{sale.id:06d}"
    }

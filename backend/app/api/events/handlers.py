"""
Phase 6 - Task 3: Event Handlers
Post-sale event chain handlers:
1. Deduct inventory
2. Award loyalty points
3. Check reorder alerts
4. Update forecasts
5. Log anomalies
"""

from app.api.events.events import (
    Event, EventBus, EventType, EventStatus,
    SaleCreatedEvent, InventoryDeductedEvent, LoyaltyPointsAwardedEvent,
    ReorderAlertEvent, ForecastUpdatedEvent, AnomalyDetectedEvent,
    get_event_bus
)
from app.api.db.database import SessionLocal
from app.api.db.multitenant_models import Inventory, Product, Customer, Invoice
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from decimal import Decimal

logger = logging.getLogger(__name__)


class InventoryDeductionHandler:
    """
    Handles inventory deduction after sale is created
    
    Reduces product stock by quantity sold
    Creates InventoryDeductedEvent
    """
    
    @staticmethod
    async def handle(event: SaleCreatedEvent) -> bool:
        """
        Deduct inventory for all items in the sale
        """
        session = SessionLocal()
        try:
            deductions = []
            event_bus = get_event_bus()
            
            for item in event.items:
                product_id = uuid.UUID(item['product_id'])
                quantity = item['quantity']
                
                # Find inventory record
                inventory = session.query(Inventory).filter(
                    Inventory.product_id == product_id,
                    Inventory.tenant_id == event.tenant_id
                ).first()
                
                if not inventory:
                    logger.error(f"Inventory not found for product {product_id}")
                    return False
                
                # Record previous stock
                previous_stock = inventory.quantity_available
                
                # Deduct inventory
                inventory.quantity_available -= quantity
                inventory.quantity_reserved = inventory.quantity_reserved or 0
                inventory.updated_at = datetime.utcnow()
                
                session.add(inventory)
                
                # Log deduction
                deductions.append({
                    "product_id": str(product_id),
                    "quantity": quantity,
                    "previous_stock": previous_stock,
                    "new_stock": inventory.quantity_available,
                    "product_name": inventory.product.name if inventory.product else "Unknown"
                })
                
                logger.info(
                    f"Deducted {quantity} units of {product_id} "
                    f"({previous_stock} -> {inventory.quantity_available})"
                )
            
            session.commit()
            
            # Publish InventoryDeductedEvent
            deducted_event = InventoryDeductedEvent(
                aggregate_id=event.sale_id,
                tenant_id=event.tenant_id,
                user_id=event.user_id,
                data={
                    "sale_id": str(event.sale_id),
                    "deductions": deductions
                }
            )
            
            await event_bus.publish(deducted_event)
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Inventory deduction failed: {e}")
            return False
        finally:
            session.close()


class LoyaltyPointsHandler:
    """
    Awards loyalty points to customer based on purchase amount
    
    Point calculation rules:
    - Base rate: 1 point per ₹100 (configurable per tenant)
    - Premium customers: 1.5x multiplier
    - Occasional customers: 0.5x multiplier
    """
    
    @staticmethod
    async def handle(event: SaleCreatedEvent) -> bool:
        """
        Award loyalty points based on sale amount
        """
        session = SessionLocal()
        try:
            customer_id = event.customer_id
            
            if not customer_id:
                logger.info(f"Sale {event.sale_id} has no customer, skipping loyalty points")
                return True
            
            # Get customer
            customer = session.query(Customer).filter(
                Customer.id == customer_id,
                Customer.tenant_id == event.tenant_id
            ).first()
            
            if not customer:
                logger.error(f"Customer {customer_id} not found")
                return False
            
            # Calculate points: 1 point per ₹100
            base_points = int(event.total_amount / 100)
            
            # Apply multiplier based on customer segment
            multiplier = 1.0
            if customer.customer_segment == 'premium':
                multiplier = 1.5
            elif customer.customer_segment == 'occasional':
                multiplier = 0.5
            
            points_awarded = int(base_points * multiplier)
            
            # Update customer loyalty points
            customer.loyalty_points = (customer.loyalty_points or 0) + points_awarded
            session.add(customer)
            session.commit()
            
            logger.info(f"Awarded {points_awarded} loyalty points to customer {customer_id}")
            
            # Publish LoyaltyPointsAwardedEvent
            event_bus = get_event_bus()
            loyalty_event = LoyaltyPointsAwardedEvent(
                aggregate_id=customer_id,
                tenant_id=event.tenant_id,
                user_id=event.user_id,
                data={
                    "customer_id": str(customer_id),
                    "sale_id": str(event.sale_id),
                    "sale_amount": float(event.total_amount),
                    "points_awarded": points_awarded,
                    "total_points": customer.loyalty_points,
                    "multiplier": multiplier
                }
            )
            
            await event_bus.publish(loyalty_event)
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Loyalty points handler failed: {e}")
            return False
        finally:
            session.close()


class ReorderAlertHandler:
    """
    Checks if inventory has fallen below reorder point
    Creates purchase orders automatically if configured
    """
    
    @staticmethod
    async def handle(event: InventoryDeductedEvent) -> bool:
        """
        Check reorder points for deducted items
        """
        session = SessionLocal()
        try:
            event_bus = get_event_bus()
            reorder_alerts = []
            
            for deduction in event.deductions:
                product_id = uuid.UUID(deduction['product_id'])
                new_stock = deduction['new_stock']
                
                # Get product with reorder settings
                product = session.query(Product).filter(
                    Product.id == product_id,
                    Product.tenant_id == event.tenant_id
                ).first()
                
                if not product:
                    continue
                
                reorder_point = product.reorder_point or 0
                reorder_quantity = product.reorder_quantity or 0
                
                # Check if below reorder point
                if new_stock <= reorder_point:
                    logger.warning(
                        f"Product {product_id} below reorder point "
                        f"({new_stock} <= {reorder_point})"
                    )
                    
                    reorder_alerts.append({
                        "product_id": str(product_id),
                        "product_name": product.name,
                        "current_stock": new_stock,
                        "reorder_point": reorder_point,
                        "reorder_quantity": reorder_quantity
                    })
                    
                    # Create ReorderAlertEvent
                    alert_event = ReorderAlertEvent(
                        aggregate_id=product_id,
                        tenant_id=event.tenant_id,
                        user_id=event.user_id,
                        data={
                            "product_id": str(product_id),
                            "product_name": product.name,
                            "current_stock": new_stock,
                            "reorder_point": reorder_point,
                            "reorder_quantity": reorder_quantity,
                            "supplier_id": str(product.supplier_id) if product.supplier_id else None
                        }
                    )
                    
                    await event_bus.publish(alert_event)
            
            if not reorder_alerts:
                logger.info("No reorder alerts needed")
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Reorder alert handler failed: {e}")
            return False
        finally:
            session.close()


class ForecastUpdateHandler:
    """
    Updates demand forecasts with new sale data
    Uses ARIMA or similar statistical models
    
    Note: Forecast model not currently in database schema
    This handler is a placeholder for future ML-based forecasting
    """
    
    @staticmethod
    async def handle(event: SaleCreatedEvent) -> bool:
        """
        Update forecasts for products sold
        Currently a no-op placeholder
        """
        try:
            event_bus = get_event_bus()
            
            logger.info(f"Forecast update triggered for {len(event.items)} products")
            
            # TODO: Implement ML-based forecasting when Forecast model is added
            # For now, just log and return success
            
            forecast_event = ForecastUpdatedEvent(
                aggregate_id=event.sale_id,
                tenant_id=event.tenant_id,
                user_id=event.user_id,
                data={
                    "sale_id": str(event.sale_id),
                    "items_count": len(event.items),
                    "status": "forecast_updated_placeholder"
                }
            )
            
            await event_bus.publish(forecast_event)
            
            return True
            
        except Exception as e:
            logger.error(f"Forecast update handler failed: {e}")
            return False


class AnomalyDetectionHandler:
    """
    Detects anomalies in sales patterns, inventory, and customer behavior
    
    Anomaly types:
    - High sales volume spike
    - Suspicious pricing
    - Unusual purchase patterns
    - Inventory discrepancies
    """
    
    @staticmethod
    async def handle(event: SaleCreatedEvent) -> bool:
        """
        Detect anomalies in the sale data
        """
        session = SessionLocal()
        try:
            event_bus = get_event_bus()
            
            # Check for high-value transactions
            if event.total_amount > 50000:  # Above ₹50,000
                logger.warning(f"High-value transaction detected: ₹{event.total_amount}")
                
                anomaly = AnomalyDetectedEvent(
                    aggregate_id=event.sale_id,
                    tenant_id=event.tenant_id,
                    user_id=event.user_id,
                    data={
                        "anomaly_type": "high_value_transaction",
                        "sale_id": str(event.sale_id),
                        "amount": float(event.total_amount),
                        "anomaly_score": min(1.0, event.total_amount / 100000),
                        "details": {
                            "transaction_amount": float(event.total_amount),
                            "threshold": 50000,
                            "item_count": len(event.items)
                        },
                        "recommendation": "Review transaction for potential fraud"
                    }
                )
                
                await event_bus.publish(anomaly)
            
            # Check for bulk quantity purchases
            for item in event.items:
                if item.get('quantity', 0) > 100:
                    logger.warning(f"Bulk purchase detected: {item['quantity']} units")
                    
                    anomaly = AnomalyDetectedEvent(
                        aggregate_id=event.sale_id,
                        tenant_id=event.tenant_id,
                        user_id=event.user_id,
                        data={
                            "anomaly_type": "bulk_purchase",
                            "product_id": item['product_id'],
                            "quantity": item['quantity'],
                            "anomaly_score": min(1.0, item['quantity'] / 200),
                            "details": {
                                "quantity": item['quantity'],
                                "threshold": 100
                            },
                            "recommendation": "Verify bulk purchase legitimacy"
                        }
                    )
                    
                    await event_bus.publish(anomaly)
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Anomaly detection handler failed: {e}")
            return False
        finally:
            session.close()


def register_event_handlers(event_bus: EventBus):
    """
    Register all event handlers with the event bus
    Called during application startup
    """
    logger.info("Registering event handlers...")
    
    # Sale created event handlers
    event_bus.subscribe(EventType.SALE_CREATED, InventoryDeductionHandler.handle)
    event_bus.subscribe(EventType.SALE_CREATED, LoyaltyPointsHandler.handle)
    event_bus.subscribe(EventType.SALE_CREATED, AnomalyDetectionHandler.handle)
    
    # Inventory deducted handlers
    event_bus.subscribe(EventType.INVENTORY_DEDUCTED, ReorderAlertHandler.handle)
    event_bus.subscribe(EventType.INVENTORY_DEDUCTED, ForecastUpdateHandler.handle)
    
    logger.info("✓ All event handlers registered")

"""
Phase 2-T5: Dead Stock Identification Service
Identifies slow-moving and dead stock items

Dead Stock: Items not sold in 90+ days
Slow-Moving: Items not sold in 30-90 days
"""

from typing import List, Dict
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.api.db.models_v6 import Product, Sale, SaleItem


class DeadStockService:
    """Service for identifying dead stock and slow-moving items"""
    
    DEAD_STOCK_DAYS = 90  # Days without sale to be considered dead stock
    SLOW_MOVING_DAYS = 30  # Days without sale to be considered slow-moving
    
    def identify_dead_stock(self, db: Session, days: int = DEAD_STOCK_DAYS) -> Dict:
        """
        Identify dead stock items
        
        Args:
            db: Database session
            days: Period to check (default: 90 days)
        
        Returns:
            Dict with dead stock items and recommendations
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get products with no sales in the period
        products_with_sales = db.query(Product.id).join(
            SaleItem, Product.id == SaleItem.product_id
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).filter(
            Sale.sale_date >= cutoff_date
        ).distinct().all()
        
        products_with_sales_ids = [p[0] for p in products_with_sales]
        
        # Get all active products without recent sales
        dead_stock_products = db.query(Product).filter(
            and_(
                Product.is_active == True,
                Product.id.notin_(products_with_sales_ids) if products_with_sales_ids else True
            )
        ).all()
        
        # Enrich data
        dead_stock_data = []
        for product in dead_stock_products:
            if product.stock_level > 0:  # Only items that have stock
                stock_value = (
                    Decimal(str(product.stock_level)) * 
                    Decimal(str(product.cost_price))
                )
                
                # Calculate suggested discount
                suggested_discount = self._calculate_discount(product)
                
                dead_stock_data.append({
                    "product_id": product.id,
                    "name": product.name,
                    "sku": product.sku,
                    "barcode": product.barcode,
                    "category": product.category.name if product.category else "Unknown",
                    "current_stock": product.stock_level,
                    "cost_price": float(product.cost_price),
                    "selling_price": float(product.selling_price),
                    "stock_value": float(stock_value),
                    "last_sale_date": product.last_sale_date.isoformat() if product.last_sale_date else "Never",
                    "days_since_last_sale": (datetime.utcnow().date() - product.last_sale_date).days if product.last_sale_date else 999999,
                    "suggested_discount_percentage": suggested_discount,
                    "suggested_clearance_price": float(
                        Decimal(str(product.selling_price)) * 
                        (1 - Decimal(str(suggested_discount)) / 100)
                    ),
                    "total_recovery_amount": float(
                        Decimal(str(product.stock_level)) * 
                        Decimal(str(product.selling_price)) * 
                        (1 - Decimal(str(suggested_discount)) / 100)
                    )
                })
        
        # Sort by stock value descending
        dead_stock_data.sort(key=lambda x: x["stock_value"], reverse=True)
        
        # Calculate metrics
        total_dead_stock_value = sum(item["stock_value"] for item in dead_stock_data)
        total_items = sum(item["current_stock"] for item in dead_stock_data)
        
        return {
            "status": "success",
            "analysis_date": datetime.utcnow().isoformat(),
            "period_days": days,
            "dead_stock_items": dead_stock_data,
            "summary": {
                "total_dead_stock_items": len(dead_stock_data),
                "total_units": total_items,
                "total_value": total_dead_stock_value,
                "potential_recovery": float(
                    Decimal(str(total_dead_stock_value)) * Decimal("0.70")  # Conservative 70% recovery
                ),
                "average_discount_needed": sum(
                    item["suggested_discount_percentage"] for item in dead_stock_data
                ) / len(dead_stock_data) if dead_stock_data else 0
            },
            "recommendations": self._generate_disposal_recommendations(dead_stock_data)
        }
    
    def identify_slow_moving(self, db: Session, days: int = SLOW_MOVING_DAYS) -> Dict:
        """
        Identify slow-moving items
        
        Args:
            db: Database session
            days: Period to check (default: 30 days)
        
        Returns:
            Dict with slow-moving items
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get products with sales in the extended period
        products_with_recent_sales = db.query(Product.id).join(
            SaleItem, Product.id == SaleItem.product_id
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).filter(
            Sale.sale_date >= cutoff_date
        ).distinct().all()
        
        recent_sales_ids = [p[0] for p in products_with_recent_sales]
        
        # Get products with sales older than cutoff
        old_cutoff = datetime.utcnow() - timedelta(days=days * 3)
        products_with_old_sales = db.query(Product.id).join(
            SaleItem, Product.id == SaleItem.product_id
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).filter(
            Sale.sale_date >= old_cutoff,
            Sale.sale_date < cutoff_date
        ).distinct().all()
        
        old_sales_ids = [p[0] for p in products_with_old_sales]
        
        slow_moving_products = db.query(Product).filter(
            Product.id.in_(old_sales_ids) if old_sales_ids else False,
            Product.is_active == True
        ).all()
        
        # Enrich data
        slow_moving_data = []
        for product in slow_moving_products:
            # Calculate sales velocity
            total_units = db.query(
                func.sum(SaleItem.quantity)
            ).join(
                Sale, SaleItem.sale_id == Sale.id
            ).filter(
                and_(
                    SaleItem.product_id == product.id,
                    Sale.sale_date >= old_cutoff
                )
            ).scalar() or 0
            
            velocity = total_units / (days * 3) if total_units > 0 else 0
            
            slow_moving_data.append({
                "product_id": product.id,
                "name": product.name,
                "sku": product.sku,
                "current_stock": product.stock_level,
                "cost_price": float(product.cost_price),
                "selling_price": float(product.selling_price),
                "last_sale_date": product.last_sale_date.isoformat() if product.last_sale_date else "Never",
                "days_since_last_sale": (datetime.utcnow().date() - product.last_sale_date).days if product.last_sale_date else 999999,
                "units_sold_90_days": int(total_units),
                "daily_velocity": float(velocity),
                "stock_coverage_days": int(product.stock_level / velocity) if velocity > 0 else 999999,
                "recommendation": self._get_slow_moving_recommendation(velocity, product.stock_level)
            })
        
        return {
            "status": "success",
            "analysis_date": datetime.utcnow().isoformat(),
            "period_days": days,
            "slow_moving_items": slow_moving_data,
            "summary": {
                "total_slow_moving_items": len(slow_moving_data),
                "total_units_in_stock": sum(item["current_stock"] for item in slow_moving_data),
                "average_velocity": sum(item["daily_velocity"] for item in slow_moving_data) / len(slow_moving_data) if slow_moving_data else 0
            }
        }
    
    def _calculate_discount(self, product: Product) -> float:
        """
        Calculate suggested discount to move dead stock
        Based on days without sale and stock quantity
        """
        days_without_sale = (
            (datetime.utcnow().date() - product.last_sale_date).days
            if product.last_sale_date
            else 999
        )
        
        # Base discount calculation
        if days_without_sale < 90:
            base_discount = 10
        elif days_without_sale < 180:
            base_discount = 20
        elif days_without_sale < 365:
            base_discount = 30
        else:
            base_discount = 50
        
        # Adjust for stock quantity
        if product.stock_level > 1000:
            base_discount += 10
        elif product.stock_level > 500:
            base_discount += 5
        
        # Cap at 80% (don't go below 20% of selling price)
        return min(base_discount, 80)
    
    def _get_slow_moving_recommendation(self, velocity: float, current_stock: int) -> str:
        """Generate recommendation based on velocity"""
        if velocity == 0:
            return "Stop ordering - no recent sales"
        elif velocity < 0.1:
            return "Reduce order quantity - very slow moving"
        elif velocity < 0.5:
            return "Monitor closely - below target velocity"
        elif current_stock / velocity > 90:
            return "Consider discount promotion"
        else:
            return "Monitor inventory levels"
    
    def _generate_disposal_recommendations(self, dead_stock_items: List[Dict]) -> Dict:
        """Generate disposal strategies for dead stock"""
        
        # Group by value
        high_value = [item for item in dead_stock_items if item["stock_value"] > 10000]
        medium_value = [item for item in dead_stock_items if 1000 <= item["stock_value"] <= 10000]
        low_value = [item for item in dead_stock_items if item["stock_value"] < 1000]
        
        return {
            "high_value_items": {
                "count": len(high_value),
                "total_value": sum(item["stock_value"] for item in high_value),
                "strategy": "Aggressive promotion + Bundling with fast-movers",
                "actions": [
                    "Run flash sales/clearance events",
                    "Create combo offers with popular items",
                    "Offer employee discounts",
                    "Consider wholesale to other retailers"
                ]
            },
            "medium_value_items": {
                "count": len(medium_value),
                "total_value": sum(item["stock_value"] for item in medium_value),
                "strategy": "Moderate promotion + Liquidation",
                "actions": [
                    "Apply suggested discounts",
                    "Liquidation sales",
                    "Online clearance listings",
                    "Donation (for tax benefit)"
                ]
            },
            "low_value_items": {
                "count": len(low_value),
                "total_value": sum(item["stock_value"] for item in low_value),
                "strategy": "Clearance + Donation",
                "actions": [
                    "Bundle with other items",
                    "Clearance sections",
                    "Donation to NGOs (tax deductible)",
                    "Scrap/Waste disposal"
                ]
            },
            "overall": {
                "priority_items": len(high_value),
                "estimated_timeline": "3-6 months for clearance",
                "success_metrics": [
                    "Reduce dead stock value by 70%",
                    "Improve cash flow",
                    "Free up warehouse space"
                ]
            }
        }
    
    def get_dead_stock_by_category(self, db: Session) -> Dict:
        """Get dead stock breakdown by category"""
        from app.api.db.models_v6 import ProductCategory
        
        categories = db.query(ProductCategory).all()
        category_summary = {}
        
        for category in categories:
            products = db.query(Product).filter(
                and_(
                    Product.category_id == category.id,
                    Product.is_active == True
                )
            ).all()
            
            dead_items = []
            for p in products:
                if p.last_sale_date:
                    days = (datetime.utcnow().date() - p.last_sale_date).days
                    if days >= self.DEAD_STOCK_DAYS and p.stock_level > 0:
                        dead_items.append(p)
            
            if dead_items:
                total_value = sum(
                    Decimal(str(p.stock_level)) * Decimal(str(p.cost_price))
                    for p in dead_items
                )
                
                category_summary[category.name] = {
                    "dead_stock_count": len(dead_items),
                    "total_units": sum(p.stock_level for p in dead_items),
                    "total_value": float(total_value),
                    "percentage_of_category": len(dead_items) / len(products) * 100 if products else 0
                }
        
        return category_summary


# Initialize service
dead_stock_service = DeadStockService()

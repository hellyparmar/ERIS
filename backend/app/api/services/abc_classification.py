"""
Phase 2-T2: ABC Classification Service
Implements ABC analysis for inventory management

ABC Classification:
- A Items: 80% of revenue, ~20% of items (high priority)
- B Items: 15% of revenue, ~30% of items (medium priority)
- C Items: 5% of revenue, ~50% of items (low priority)
"""

from decimal import Decimal
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.api.db.models_v6 import Product, Sale, SaleItem


class ABCClassificationService:
    """Service for ABC analysis and classification"""
    
    def __init__(self):
        self.a_threshold = Decimal("0.80")  # 80% cumulative revenue
        self.b_threshold = Decimal("0.95")  # 95% cumulative revenue
    
    def analyze_inventory(self, db: Session, days: int = 365) -> Dict:
        """
        Perform ABC analysis on products
        
        Args:
            db: Database session
            days: Period to analyze (default: 365 days)
        
        Returns:
            Dict with analysis results and classifications
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all products with sales data
        products_data = []
        
        products = db.query(Product).filter(Product.is_active == True).all()
        
        for product in products:
            # Calculate revenue contribution
            sale_items = db.query(SaleItem).join(
                Sale, SaleItem.sale_id == Sale.id
            ).filter(
                and_(
                    SaleItem.product_id == product.id,
                    Sale.sale_date >= cutoff_date
                )
            ).all()
            
            total_revenue = sum(
                Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
                for item in sale_items
            )
            
            total_quantity = sum(item.quantity for item in sale_items)
            
            if total_revenue > 0 or total_quantity > 0:
                products_data.append({
                    "product_id": product.id,
                    "name": product.name,
                    "sku": product.sku,
                    "revenue": float(total_revenue),
                    "quantity": total_quantity,
                    "selling_price": float(product.selling_price),
                    "cost_price": float(product.cost_price),
                    "current_stock": product.stock_level,
                    "turnover": total_quantity
                })
        
        if not products_data:
            return {
                "status": "success",
                "message": "No sales data available",
                "a_items": [],
                "b_items": [],
                "c_items": [],
                "summary": {
                    "total_products": 0,
                    "a_count": 0,
                    "b_count": 0,
                    "c_count": 0,
                    "total_revenue": 0
                }
            }
        
        # Sort by revenue descending
        products_data.sort(key=lambda x: x["revenue"], reverse=True)
        
        # Calculate cumulative revenue percentage
        total_revenue = sum(p["revenue"] for p in products_data)
        
        if total_revenue == 0:
            return {
                "status": "success",
                "message": "No revenue data",
                "a_items": [],
                "b_items": [],
                "c_items": [],
                "summary": {"total_products": 0}
            }
        
        # Classify items
        cumulative_percentage = Decimal("0")
        a_items = []
        b_items = []
        c_items = []
        
        for item in products_data:
            revenue_percentage = Decimal(str(item["revenue"])) / Decimal(str(total_revenue))
            cumulative_percentage += revenue_percentage
            
            item_with_percent = {
                **item,
                "revenue_percentage": float(revenue_percentage),
                "cumulative_percentage": float(cumulative_percentage)
            }
            
            if cumulative_percentage <= self.a_threshold:
                item_with_percent["classification"] = "A"
                a_items.append(item_with_percent)
            elif cumulative_percentage <= self.b_threshold:
                item_with_percent["classification"] = "B"
                b_items.append(item_with_percent)
            else:
                item_with_percent["classification"] = "C"
                c_items.append(item_with_percent)
        
        # Update database classifications
        self._update_product_classifications(db, a_items, b_items, c_items)
        
        # Calculate metrics
        a_revenue = sum(p["revenue"] for p in a_items)
        b_revenue = sum(p["revenue"] for p in b_items)
        c_revenue = sum(p["revenue"] for p in c_items)
        
        return {
            "status": "success",
            "analysis_date": datetime.utcnow().isoformat(),
            "period_days": days,
            "a_items": a_items,
            "b_items": b_items,
            "c_items": c_items,
            "summary": {
                "total_products": len(products_data),
                "a_count": len(a_items),
                "b_count": len(b_items),
                "c_count": len(c_items),
                "a_percentage": len(a_items) / len(products_data) * 100,
                "b_percentage": len(b_items) / len(products_data) * 100,
                "c_percentage": len(c_items) / len(products_data) * 100,
                "a_revenue": a_revenue,
                "b_revenue": b_revenue,
                "c_revenue": c_revenue,
                "total_revenue": total_revenue,
                "a_revenue_percentage": a_revenue / total_revenue * 100 if total_revenue > 0 else 0,
                "b_revenue_percentage": b_revenue / total_revenue * 100 if total_revenue > 0 else 0,
                "c_revenue_percentage": c_revenue / total_revenue * 100 if total_revenue > 0 else 0
            },
            "recommendations": self._generate_recommendations(a_items, b_items, c_items)
        }
    
    def _update_product_classifications(self, db: Session, a_items: List, b_items: List, c_items: List):
        """Update product ABC classification in database"""
        try:
            # Update A items
            for item in a_items:
                db.query(Product).filter(
                    Product.id == item["product_id"]
                ).update({"abc_classification": "A"})
            
            # Update B items
            for item in b_items:
                db.query(Product).filter(
                    Product.id == item["product_id"]
                ).update({"abc_classification": "B"})
            
            # Update C items
            for item in c_items:
                db.query(Product).filter(
                    Product.id == item["product_id"]
                ).update({"abc_classification": "C"})
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error updating classifications: {str(e)}")
    
    def get_items_by_classification(self, db: Session, classification: str) -> List[Dict]:
        """
        Get all items of a specific classification
        
        Args:
            db: Database session
            classification: 'A', 'B', or 'C'
        
        Returns:
            List of products with that classification
        """
        if classification not in ['A', 'B', 'C']:
            return []
        
        products = db.query(Product).filter(
            and_(
                Product.abc_classification == classification,
                Product.is_active == True
            )
        ).all()
        
        return [
            {
                "product_id": p.id,
                "name": p.name,
                "sku": p.sku,
                "barcode": p.barcode,
                "current_stock": p.stock_level,
                "reorder_point": p.reorder_point,
                "max_stock": p.max_stock_level,
                "selling_price": float(p.selling_price),
                "cost_price": float(p.cost_price),
                "hsn_code": p.hsn_code,
                "gst_rate": float(p.gst_rate)
            }
            for p in products
        ]
    
    def _generate_recommendations(self, a_items: List, b_items: List, c_items: List) -> Dict:
        """Generate inventory management recommendations based on classifications"""
        recommendations = {
            "A_items": {
                "strategy": "Tight inventory control",
                "actions": [
                    "Maintain high safety stock",
                    "Frequent reorder checks (daily/weekly)",
                    "Implement demand forecasting",
                    "Focus on minimizing stockouts",
                    "Negotiate supplier agreements for priority supply"
                ],
                "recommended_safety_stock_multiplier": 1.5
            },
            "B_items": {
                "strategy": "Moderate inventory control",
                "actions": [
                    "Maintain moderate safety stock",
                    "Reorder checks every 2 weeks",
                    "Use standard reorder points",
                    "Monitor for trends",
                    "Adjust stock based on seasonality"
                ],
                "recommended_safety_stock_multiplier": 1.0
            },
            "C_items": {
                "strategy": "Loose inventory control",
                "actions": [
                    "Maintain lower safety stock",
                    "Reorder monthly or less frequently",
                    "Consider dropping slow-moving items",
                    "Use batch ordering to reduce costs",
                    "Review for dead stock regularly"
                ],
                "recommended_safety_stock_multiplier": 0.75
            }
        }
        
        # Add specific metrics
        recommendations["A_items"]["count"] = len(a_items)
        recommendations["A_items"]["revenue_contribution"] = f"{sum(p['revenue'] for p in a_items) / (sum(p['revenue'] for p in a_items + b_items + c_items) or 1) * 100:.1f}%"
        
        recommendations["B_items"]["count"] = len(b_items)
        recommendations["B_items"]["revenue_contribution"] = f"{sum(p['revenue'] for p in b_items) / (sum(p['revenue'] for p in a_items + b_items + c_items) or 1) * 100:.1f}%"
        
        recommendations["C_items"]["count"] = len(c_items)
        recommendations["C_items"]["revenue_contribution"] = f"{sum(p['revenue'] for p in c_items) / (sum(p['revenue'] for p in a_items + b_items + c_items) or 1) * 100:.1f}%"
        
        return recommendations
    
    def get_classification_metrics(self, db: Session) -> Dict:
        """Get current classification metrics from database"""
        total = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0
        
        a_count = db.query(func.count(Product.id)).filter(
            and_(Product.abc_classification == "A", Product.is_active == True)
        ).scalar() or 0
        
        b_count = db.query(func.count(Product.id)).filter(
            and_(Product.abc_classification == "B", Product.is_active == True)
        ).scalar() or 0
        
        c_count = db.query(func.count(Product.id)).filter(
            and_(Product.abc_classification == "C", Product.is_active == True)
        ).scalar() or 0
        
        return {
            "total_products": total,
            "a_items": {
                "count": a_count,
                "percentage": a_count / total * 100 if total > 0 else 0
            },
            "b_items": {
                "count": b_count,
                "percentage": b_count / total * 100 if total > 0 else 0
            },
            "c_items": {
                "count": c_count,
                "percentage": c_count / total * 100 if total > 0 else 0
            }
        }


# Initialize service
abc_service = ABCClassificationService()

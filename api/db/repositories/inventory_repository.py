"""
Inventory Repository
Data access layer for inventory operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from api.db.models import Inventory, Product, AlertSeverity
from typing import List, Dict, Any, Optional
from datetime import datetime

class InventoryRepository:
    """Repository for inventory database operations"""
    
    @staticmethod
    def get_inventory_list(
        db: Session,
        search: Optional[str] = None,
        category: Optional[str] = None,
        stock_status: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> tuple[List[Dict], Dict]:
        """
        Get paginated inventory list with filters
        
        Returns: (items, pagination_info)
        """
        # Base query joining inventory with products
        query = db.query(Inventory, Product).join(
            Product, Inventory.product_id == Product.id
        )
        
        # Apply filters
        filters = []
        
        if search:
            search_term = f"%{search}%"
            filters.append(
                or_(
                    Product.name.ilike(search_term),
                    Product.sku.ilike(search_term)
                )
            )
        
        if category:
            filters.append(Product.category == category)
        
        if stock_status:
            if stock_status == 'out_of_stock':
                filters.append(Inventory.current_stock == 0)
            elif stock_status == 'low':
                filters.append(
                    and_(
                        Inventory.current_stock > 0,
                        Inventory.current_stock < Inventory.reorder_point
                    )
                )
            elif stock_status == 'medium':
                filters.append(
                    and_(
                        Inventory.current_stock >= Inventory.reorder_point,
                        Inventory.current_stock < Inventory.reorder_point * 2
                    )
                )
            elif stock_status == 'high':
                filters.append(Inventory.current_stock >= Inventory.reorder_point * 2)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count
        total_items = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        results = query.offset(offset).limit(per_page).all()
        
        # Transform to dict
        items = []
        for inventory, product in results:
            # Determine stock status
            if inventory.current_stock == 0:
                status = 'out_of_stock'
            elif inventory.current_stock < inventory.reorder_point:
                status = 'low'
            elif inventory.current_stock < inventory.reorder_point * 2:
                status = 'medium'
            else:
                status = 'high'
            
            items.append({
                'id': inventory.id,
                'sku': product.sku,
                'name': product.name,
                'category': product.category,
                'current_stock': inventory.current_stock,
                'reserved_stock': inventory.reserved_stock,
                'available_stock': inventory.available_stock,
                'reorder_point': inventory.reorder_point,
                'reorder_quantity': inventory.reorder_quantity,
                'unit_price': product.unit_price,
                'stock_status': status,
                'last_updated': inventory.updated_at.isoformat() if inventory.updated_at else None,
                'warehouse_location': inventory.warehouse_location
            })
        
        # Pagination info
        pagination = {
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': (total_items + per_page - 1) // per_page,
            'has_next': (page * per_page) < total_items,
            'has_prev': page > 1
        }
        
        return items, pagination
    
    @staticmethod
    def get_reorder_recommendations(db: Session, limit: int = 15) -> List[Dict]:
        """Get products that need reordering"""
        # Query products where stock is below reorder point
        results = db.query(Inventory, Product).join(
            Product, Inventory.product_id == Product.id
        ).filter(
            Inventory.current_stock < Inventory.reorder_point
        ).order_by(
            Inventory.current_stock.asc()
        ).limit(limit).all()
        
        recommendations = []
        for inventory, product in results:
            # Calculate urgency
            if inventory.current_stock == 0:
                urgency = 'critical'
            elif inventory.current_stock < 10:
                urgency = 'high'
            else:
                urgency = 'medium'
            
            # Simple recommendation: reorder_quantity or enough to reach reorder point
            deficit = inventory.reorder_point - inventory.current_stock
            recommended_qty = max(inventory.reorder_quantity, deficit)
            
            recommendations.append({
                'product_id': product.id,
                'sku': product.sku,
                'name': product.name,
                'category': product.category,
                'current_stock': inventory.current_stock,
                'reorder_point': inventory.reorder_point,
                'stock_deficit': deficit,
                'avg_daily_sales': 10,  # TODO: Calculate from sales history
                'lead_time_days': 7,    # TODO: Get from product or vendor data
                'recommended_order_qty': recommended_qty,
                'estimated_cost': round(product.cost_price * recommended_qty, 2) if product.cost_price else 0,
                'urgency': urgency,
                'days_until_stockout': max(0, inventory.current_stock // 10)  # Assuming 10 units/day avg
            })
        
        return recommendations
    
    @staticmethod
    def get_stock_summary(db: Session) -> Dict[str, Any]:
        """Get inventory summary statistics"""
        # Total products
        total_products = db.query(Product).count()
        
        # Stock value (sum of current_stock * unit_price)
        total_value = db.query(
            func.sum(Inventory.current_stock * Product.unit_price)
        ).join(Product).scalar() or 0
        
        # Low stock count
        low_stock = db.query(Inventory).filter(
            and_(
                Inventory.current_stock > 0,
                Inventory.current_stock < Inventory.reorder_point
            )
        ).count()
        
        # Out of stock
        out_of_stock = db.query(Inventory).filter(
            Inventory.current_stock == 0
        ).count()
        
        # Overstocked (more than 3x reorder point)
        overstocked = db.query(Inventory).filter(
            Inventory.current_stock > Inventory.reorder_point * 3
        ).count()
        
        # Category breakdown
        category_counts = db.query(
            Product.category,
            func.count(Product.id)
        ).group_by(Product.category).all()
        
        categories = {cat: count for cat, count in category_counts}
        
        return {
            'total_products': total_products,
            'total_stock_value': round(total_value, 2),
            'low_stock_count': low_stock,
            'out_of_stock_count': out_of_stock,
            'overstocked_count': overstocked,
            'categories': categories
        }


    @staticmethod
    def create_product(db: Session, product_data: Dict, inventory_data: Dict) -> Dict:
        """Create new product and initialize inventory"""
        try:
            # 1. Create Product
            new_product = Product(
                sku=product_data['sku'],
                name=product_data['name'],
                category=product_data.get('category'),
                unit_price=product_data['unit_price'],
                cost_price=product_data.get('cost_price'),
                hsn_code=product_data.get('hsn_code'),
                gst_rate=product_data.get('gst_rate'),
                description=product_data.get('description')
            )
            db.add(new_product)
            db.flush()  # To get product ID

            # 2. Create Inventory Record
            new_inventory = Inventory(
                product_id=new_product.id,
                current_stock=inventory_data.get('current_stock', 0),
                reorder_point=inventory_data.get('reorder_point', 10),
                reorder_quantity=inventory_data.get('reorder_quantity', 50),
                warehouse_location=inventory_data.get('warehouse_location'),
                last_stocked_date=datetime.now() if inventory_data.get('current_stock', 0) > 0 else None
            )
            db.add(new_inventory)
            db.commit()
            
            return {
                "id": new_inventory.id,
                "product_id": new_product.id,
                "name": new_product.name,
                "sku": new_product.sku
            }
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update_product(db: Session, product_id: int, updates: Dict) -> Optional[Dict]:
        """Update product and inventory details"""
        product = db.query(Product).filter(Product.id == product_id).first()
        inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
        
        if not product or not inventory:
            return None
            
        # Update Product Fields
        if 'name' in updates: product.name = updates['name']
        if 'category' in updates: product.category = updates['category']
        if 'unit_price' in updates: product.unit_price = updates['unit_price']
        if 'cost_price' in updates: product.cost_price = updates['cost_price']
        
        # Update Inventory Fields
        if 'current_stock' in updates: 
            inventory.current_stock = updates['current_stock']
            inventory.updated_at = datetime.now()
        if 'reorder_point' in updates: inventory.reorder_point = updates['reorder_point']
        if 'warehouse_location' in updates: inventory.warehouse_location = updates['warehouse_location']
        
        db.commit()
        return {"id": product.id, "name": product.name, "message": "Updated successfully"}

    @staticmethod
    def delete_product(db: Session, product_id: int) -> bool:
        """Delete product and related inventory"""
        try:
            # Delete inventory first (FK constraint usually handles this but being explicit)
            db.query(Inventory).filter(Inventory.product_id == product_id).delete()
            db.query(Product).filter(Product.id == product_id).delete()
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

# Singleton instance
inventory_repository = InventoryRepository()

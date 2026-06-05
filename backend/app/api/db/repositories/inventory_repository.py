"""
Inventory Repository
Handles database operations for inventory management
"""

from sqlalchemy.orm import Session
from app.models import Product, Inventory
from typing import Dict, Any, Optional


class InventoryRepository:
    """Repository for inventory operations"""

    @staticmethod
    def create_product(db: Session, prod_data: Dict[str, Any], inv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product with inventory"""
        try:
            # Create product
            product = Product(
                name=prod_data['name'],
                category=prod_data['category'],
                sku=prod_data['sku'],
                base_price=prod_data.get('cost_price', 0.0),
                selling_price=prod_data['unit_price'],
                gst_rate=prod_data.get('gst_rate', 5),
                unit=prod_data.get('unit', 'piece'),
                brand=prod_data.get('brand'),
                is_active=True
            )
            db.add(product)
            db.flush()  # Get product ID

            # Create inventory record
            inventory = Inventory(
                outlet_id=inv_data.get('outlet_id', 1),  # Default outlet
                product_id=product.id,
                current_stock=inv_data.get('current_stock', 0),
                reorder_level=inv_data.get('reorder_level', 10),
                max_stock=inv_data.get('max_stock', 100)
            )
            db.add(inventory)
            db.commit()
            db.refresh(product)

            return {
                "id": product.id,
                "name": product.name,
                "sku": product.sku,
                "category": product.category,
                "selling_price": product.selling_price,
                "current_stock": inventory.current_stock
            }
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update_product(db: Session, product_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product"""
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError(f"Product with ID {product_id} not found")

            # Update product fields
            for key, value in update_data.items():
                if hasattr(product, key):
                    setattr(product, key, value)

            db.commit()
            db.refresh(product)

            # Get inventory info
            inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()

            return {
                "id": product.id,
                "name": product.name,
                "sku": product.sku,
                "category": product.category,
                "selling_price": product.selling_price,
                "current_stock": inventory.current_stock if inventory else 0
            }
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def delete_product(db: Session, product_id: int) -> bool:
        """Delete a product and its inventory"""
        try:
            # Delete inventory first (foreign key constraint)
            db.query(Inventory).filter(Inventory.product_id == product_id).delete()

            # Delete product
            result = db.query(Product).filter(Product.id == product_id).delete()

            db.commit()
            return result > 0
        except Exception as e:
            db.rollback()
            raise e


# Create singleton instance
inventory_repository = InventoryRepository()
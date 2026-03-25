"""
Inventory Service
Business logic for inventory management
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

class InventoryService:
    """Service for inventory operations"""
    
    @staticmethod
    def get_inventory_list(
        search: Optional[str] = None,
        category: Optional[str] = None,
        stock_status: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        Get paginated inventory list with filters
        
        Args:
            search: Search term for product name/SKU
            category: Filter by category
            stock_status: Filter by stock level (low, medium, high)
            page: Page number (1-indexed)
            per_page: Items per page
            
        Returns:
            Paginated inventory data with totals
        """
        # Mock data - will be replaced with database query
        categories = ['Electronics', 'Groceries', 'Clothing', 'Home & Kitchen', 'Sports', 'Beauty']
        
        all_items = []
        for i in range(1, 151):  # 150 products
            stock = random.randint(0, 500)
            reorder_point = random.randint(20, 50)
            
            # Determine stock status
            if stock == 0:
                status = 'out_of_stock'
            elif stock < reorder_point:
                status = 'low'
            elif stock < reorder_point * 2:
                status = 'medium'
            else:
                status = 'high'
            
            item_category = random.choice(categories)
            
            item = {
                'id': i,
                'sku': f'SKU-{1000 + i}',
                'name': f'Product {i}',
                'category': item_category,
                'current_stock': stock,
                'reserved_stock': random.randint(0, min(stock, 20)),
                'available_stock': max(0, stock - random.randint(0, min(stock, 20))),
                'reorder_point': reorder_point,
                'reorder_quantity': random.randint(50, 200),
                'unit_price': round(random.uniform(10, 1000), 2),
                'stock_status': status,
                'last_updated': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                'warehouse_location': f'W{random.randint(1, 5)}-A{random.randint(1, 10)}'
            }
            
            # Apply filters
            if search and search.lower() not in item['name'].lower() and search.lower() not in item['sku'].lower():
                continue
            if category and item['category'] != category:
                continue
            if stock_status and item['stock_status'] != stock_status:
                continue
                
            all_items.append(item)
        
        # Pagination
        total_items = len(all_items)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        items = all_items[start_idx:end_idx]
        
        return {
            'items': items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_items': total_items,
                'total_pages': (total_items + per_page - 1) // per_page,
                'has_next': end_idx < total_items,
                'has_prev': page > 1
            },
            'filters_applied': {
                'search': search,
                'category': category,
                'stock_status': stock_status
            }
        }
    
    @staticmethod
    def get_reorder_recommendations() -> List[Dict[str, Any]]:
        """
        Get products that need reordering
        
        Returns:
            List of products below reorder point with recommendations
        """
        recommendations = []
        
        # Mock data
        for i in range(1, 16):  # 15 recommendations
            current_stock = random.randint(0, 20)
            reorder_point = random.randint(25, 50)
            avg_daily_sales = random.randint(5, 15)
            lead_time_days = random.randint(3, 14)
            
            # Calculate recommended order quantity
            safety_stock = avg_daily_sales * 7  # 1 week buffer
            recommended_qty = (avg_daily_sales * lead_time_days) + safety_stock - current_stock
            
            recommendations.append({
                'product_id': i,
                'sku': f'SKU-{1000 + i}',
                'name': f'Product {i}',
                'category': random.choice(['Electronics', 'Groceries', 'Clothing']),
                'current_stock': current_stock,
                'reorder_point': reorder_point,
                'stock_deficit': reorder_point - current_stock,
                'avg_daily_sales': avg_daily_sales,
                'lead_time_days': lead_time_days,
                'recommended_order_qty': max(50, recommended_qty),
                'estimated_cost': round(random.uniform(500, 5000), 2),
                'urgency': 'critical' if current_stock == 0 else 'high' if current_stock < 10 else 'medium',
                'days_until_stockout': max(0, current_stock // avg_daily_sales) if avg_daily_sales > 0 else 0
            })
        
        # Sort by urgency and stock deficit
        recommendations.sort(key=lambda x: (
            0 if x['urgency'] == 'critical' else 1 if x['urgency'] == 'high' else 2,
            -x['stock_deficit']
        ))
        
        return recommendations
    
    @staticmethod
    def get_stock_summary() -> Dict[str, Any]:
        """
        Get high-level inventory statistics
        
        Returns:
            Summary statistics for dashboard
        """
        return {
            'total_products': 150,
            'total_stock_value': 1245000,
            'low_stock_count': 23,
            'out_of_stock_count': 5,
            'overstocked_count': 12,
            'categories': {
                'Electronics': 35,
                'Groceries': 42,
                'Clothing': 28,
                'Home & Kitchen': 20,
                'Sports': 15,
                'Beauty': 10
            }
        }

# Singleton
inventory_service = InventoryService()

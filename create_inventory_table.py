"""
Create INVENTORY table with realistic data for Petpooja F&B retail system
Based on product sales volume, category demand, and F&B business patterns
"""

import sqlite3
import random
from datetime import datetime, timedelta
import pandas as pd

def create_inventory_table():
    """Create INVENTORY table schema"""
    conn = sqlite3.connect('api/rdios_dev.db')
    cursor = conn.cursor()
    
    # Drop existing if any
    cursor.execute("DROP TABLE IF EXISTS inventory")
    
    # Create inventory table (matching PRODUCTS table for joins)
    cursor.execute("""
    CREATE TABLE inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL UNIQUE,
        sku TEXT NOT NULL,
        name TEXT NOT NULL,
        current_stock INTEGER NOT NULL DEFAULT 0,
        reorder_point INTEGER NOT NULL DEFAULT 20,
        max_stock INTEGER NOT NULL DEFAULT 100,
        warehouse_location TEXT DEFAULT 'Main Store',
        last_restock_date TEXT,
        stock_status TEXT DEFAULT 'medium',
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
    
    conn.commit()
    print("✓ INVENTORY table created")
    
    # Get all products with their sales volume
    products_df = pd.read_sql("""
        SELECT 
            p.id,
            p.sku,
            p.name,
            p.category,
            p.subcategory,
            COUNT(si.id) as sale_count,
            COALESCE(SUM(si.quantity), 0) as total_sold,
            p.selling_price
        FROM products p
        LEFT JOIN sale_items si ON p.id = si.product_id
        GROUP BY p.id
        ORDER BY total_sold DESC
    """, conn)
    
    print(f"\n✓ Loaded {len(products_df)} products")
    
    # Calculate inventory based on sales velocity
    inventory_data = []
    
    for idx, row in products_df.iterrows():
        product_id = row['id']
        sku = row['sku']
        category = row['category']
        total_sold = row['total_sold']
        
        # Calculate stock levels based on sales velocity
        # High sellers get more stock, low sellers get less
        daily_sales = max(0.1, total_sold / 90)  # Assuming 90 days of sales data
        
        # Base parameters by category (F&B retail with daily turnover)
        if category == 'Beverages':
            # Very high turnover items - need frequent restocking
            base_multiplier = 0.5
            daily_multiple = random.uniform(1.5, 2.5)
        elif category == 'Indian Breads':
            # High turnover - perishable
            base_multiplier = 0.6
            daily_multiple = random.uniform(1.5, 2.5)
        elif category in ['Desserts', 'South Indian', 'Starters & Appetizers']:
            # Medium-high turnover
            base_multiplier = 1.0
            daily_multiple = random.uniform(2, 4)
        else:
            # Lower turnover - main courses, rice
            base_multiplier = 1.5
            daily_multiple = random.uniform(3, 5)
        
        reorder_point = max(3, int(daily_sales * 1.5))
        max_stock = max(15, int(daily_sales * (8 + random.uniform(0, 4))))
        
        # Generate realistic current stock distribution
        rand_val = random.random()
        if rand_val < 0.1:  # 10% out of stock
            current_stock = 0
            stock_status = 'out_of_stock'
        elif rand_val < 0.3:  # 20% low stock
            current_stock = int(reorder_point * random.uniform(0.5, 1.0))
            stock_status = 'low'
        elif rand_val < 0.65:  # 35% medium stock
            current_stock = int(reorder_point + (max_stock - reorder_point) * random.uniform(0.3, 0.7))
            stock_status = 'medium'
        else:  # 35% high stock
            current_stock = int(max_stock * random.uniform(0.75, 1.0))
            stock_status = 'high'
        
        # Determine stock status based on actual levels
        if current_stock == 0:
            stock_status = 'out_of_stock'
        elif current_stock < reorder_point:
            stock_status = 'low'
        elif current_stock >= max_stock * 0.75:
            stock_status = 'high'
        else:
            stock_status = 'medium'
        
        # Last restock date (within last 30 days for realistic data)
        days_ago = random.randint(0, 30)
        last_restock = (datetime.now() - timedelta(days=days_ago)).isoformat()
        
        now = datetime.now().isoformat()
        
        inventory_data.append({
            'product_id': product_id,
            'sku': sku,
            'name': row['name'],
            'current_stock': current_stock,
            'reorder_point': reorder_point,
            'max_stock': max_stock,
            'warehouse_location': 'Main Store',
            'last_restock_date': last_restock,
            'stock_status': stock_status,
            'created_at': now,
            'updated_at': now
        })
    
    # Insert all inventory records
    df_inventory = pd.DataFrame(inventory_data)
    df_inventory.to_sql('inventory', conn, if_exists='append', index=False)
    
    print(f"✓ Inserted {len(df_inventory)} inventory records")
    
    # Print statistics
    stats = pd.read_sql("""
        SELECT 
            stock_status,
            COUNT(*) as count,
            AVG(current_stock) as avg_stock,
            MIN(current_stock) as min_stock,
            MAX(current_stock) as max_stock
        FROM inventory
        GROUP BY stock_status
    """, conn)
    
    print("\n=== INVENTORY STATISTICS ===")
    print(stats.to_string(index=False))
    
    # Low stock items
    low_stock = pd.read_sql("""
        SELECT 
            i.id,
            p.name,
            p.category,
            i.current_stock,
            i.reorder_point,
            i.max_stock
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE i.stock_status = 'low' OR i.stock_status = 'out_of_stock'
        ORDER BY i.current_stock ASC
        LIMIT 10
    """, conn)
    
    print("\n=== LOW STOCK ALERTS (Top 10) ===")
    print(low_stock.to_string(index=False))
    
    # High stock items
    high_stock = pd.read_sql("""
        SELECT 
            i.id,
            p.name,
            p.category,
            i.current_stock,
            i.reorder_point,
            i.max_stock
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE i.stock_status = 'high'
        ORDER BY i.current_stock DESC
        LIMIT 10
    """, conn)
    
    print("\n=== HIGH STOCK ITEMS (Top 10) ===")
    print(high_stock.to_string(index=False))
    
    conn.close()
    print("\n✓ Inventory table created successfully!")

if __name__ == "__main__":
    create_inventory_table()

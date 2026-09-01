
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import api modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db.database import engine

def verify_data():
    print(f"Connecting to database: {engine.url}")
    with engine.connect() as connection:
        tables = ['products', 'customers', 'sales', 'sale_items', 'inventory', 'organizations', 'stores']
        
        print("\n📊 Data counts:")
        for table in tables:
            try:
                result = connection.execute(text(f"SELECT count(*) FROM {table}"))
                count = result.scalar()
                print(f"   {table.ljust(15)}: {count:,}")
            except Exception as e:
                print(f"   {table.ljust(15)}: Error - {e}")

        print("\n🔍 Sample Data Check:")
        # Check a sale and its items
        try:
            sale = connection.execute(text("SELECT id, total_amount, customer_id FROM sales LIMIT 1")).fetchone()
            if sale:
                print(f"   Sale ID {sale[0]}: Amount={sale[1]}, CustomerID={sale[2]}")
                items = connection.execute(text(f"SELECT product_id, quantity, total_price FROM sale_items WHERE sale_id = {sale[0]}")).fetchall()
                print(f"   Items for Sale {sale[0]}: {len(items)} items found")
                for item in items:
                    print(f"     - Product {item[0]}: Qty={item[1]}, Total={item[2]}")
            else:
                print("   No sales found to verify.")
        except Exception as e:
            print(f"   Verification failed: {e}")

if __name__ == "__main__":
    verify_data()

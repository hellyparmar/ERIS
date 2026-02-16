from api.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("🔍 Verifying Supabase Data...")

# Check sales
r = db.execute(text("SELECT id, total_amount FROM sales"))
sales = list(r)
print(f"\n✅ Sales: {len(sales)}")
for s in sales:
    print(f"   Sale {s[0]}: ₹{s[1]}")

# Check inventory
r = db.execute(text("SELECT product_id, current_stock FROM inventory ORDER BY product_id"))
inv = list(r)
print(f"\n✅ Inventory:")
for i in inv:
    print(f"   Product {i[0]}: Stock {i[1]}")

db.close()

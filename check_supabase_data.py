from api.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
r = db.execute(text("SELECT COUNT(*) FROM products"))
products = r.scalar()
r = db.execute(text("SELECT COUNT(*) FROM inventory"))
inventory = r.scalar()
print(f"Products: {products}, Inventory: {inventory}")
db.close()

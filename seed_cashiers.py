"""
Seed Cashier Data for POS Testing
Creates test cashiers with 4-digit PINs
"""
import sys
sys.path.append('/home/petpooja/Enterprise Retail Intelligence System')

from api.db import SessionLocal
from api.models.cashier import Cashier

def seed_cashiers():
    db = SessionLocal()
    
    try:
        # Check if cashiers already exist
        existing = db.query(Cashier).first()
        if existing:
            print("✅ Cashiers already seeded")
            return
        
        # Create test cashiers
        cashiers = [
            {
                "name": "John Doe",
                "pin": "1234",
                "role": "cashier",
                "store_id": 1
            },
            {
                "name": "Jane Manager",
                "pin": "9999",
                "role": "manager",
                "store_id": 1
            }
        ]
        
        for data in cashiers:
            cashier = Cashier(
                name=data["name"],
                role=data["role"],
                store_id=data["store_id"],
                is_active=True
            )
            cashier.set_pin(data["pin"])
            db.add(cashier)
        
        db.commit()
        print(f"✅ Created {len(cashiers)} test cashiers")
        print("   Cashier: John Doe, PIN: 1234")
        print("   Manager: Jane Manager, PIN: 9999")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding cashiers: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_cashiers()

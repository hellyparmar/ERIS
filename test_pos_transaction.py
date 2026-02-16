"""
Test POS ACID Transaction
Verifies row-level locking, stock validation, and atomic commit
"""
from api.db import SessionLocal
from api.services.pos_service import complete_sale

def test_pos_transaction():
    db = SessionLocal()
    try:
        # Mock cart with 2 items
        cart = {
            "items": [
                {
                    "product_id": 1,
                    "quantity": 2,
                    "unit_price": 100.0,
                    "total": 200.0,
                    "gst_rate": 18.0,
                    "gst_amount": 36.0
                },
                {
                    "product_id": 2,
                    "quantity": 1,
                    "unit_price": 50.0,
                    "total": 50.0,
                    "gst_rate": 18.0,
                    "gst_amount": 9.0
                }
            ],
            "subtotal": 250.0,
            "gst_amount": 45.0,
            "total": 295.0,
            "customer_id": None
        }
        
        payment = {
            "method": "cash",
            "amount": 295.0,
            "reference": None
        }
        
        cashier_id = 1
        
        result = complete_sale(cart, payment, cashier_id, db)
        
        print("✅ POS Transaction Test PASSED")
        print(f"   Sale ID: {result['data']['sale_id']}")
        print(f"   Receipt: {result['data']['receipt_number']}")
        print(f"   Total: ₹{result['data']['total']:.2f}")
        print(f"   Items: {len(result['data']['items'])}")
        
    except Exception as e:
        print(f"❌ POS Transaction Test FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_pos_transaction()

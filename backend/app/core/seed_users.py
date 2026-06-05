"""
Creates default system users with hashed passwords.
Run once after database migration.
"""
from app.database import SessionLocal
from app.models import User
from app.core.security import hash_password


DEFAULT_USERS = [
    {
        "email": "admin@rdios.com",
        "name": "System Admin",
        "password": "admin123",
        "role": "admin",
        "outlet_id": None,
    },
    {
        "email": "manager@rdios.com",
        "name": "Store Manager",
        "password": "manager123",
        "role": "manager",
        "outlet_id": 1,
    },
    {
        "email": "analyst@rdios.com",
        "name": "Data Analyst",
        "password": "analyst123",
        "role": "analyst",
        "outlet_id": None,
    },
]


def seed_users():
    db = SessionLocal()
    try:
        for u in DEFAULT_USERS:
            exists = db.query(User).filter(User.email == u["email"]).first()
            if not exists:
                db.add(User(
                    email=u["email"],
                    name=u["name"],
                    hashed_password=hash_password(u["password"]),
                    role=u["role"],
                    outlet_id=u["outlet_id"],
                    is_active=True,
                ))
        db.commit()
        print("✅ Default users seeded")
    except Exception as e:
        db.rollback()
        print(f"❌ User seed failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()

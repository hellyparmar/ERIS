from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.multitenant_models import User, Organization, UserRole
from app.services.auth_service import auth_service
import uuid

def debug_registration():
    db = SessionLocal()
    try:
        # 1. Create Org
        org_name = "Debug Org " + uuid.uuid4().hex[:4]
        print(f"Creating org: {org_name}")
        organization = Organization(name=org_name)
        db.add(organization)
        db.commit()
        db.refresh(organization)
        print(f"Org created: {organization.id}")

        # 2. Create User
        user_email = f"debug_{uuid.uuid4().hex[:4]}@example.com"
        print(f"Creating user: {user_email}")
        new_user = User(
            email=user_email,
            full_name="Debug User",
            hashed_password=auth_service.get_password_hash("password123"),
            role=UserRole.ADMIN,
            organization_id=organization.id
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"User created: {new_user.id}")
        
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_registration()

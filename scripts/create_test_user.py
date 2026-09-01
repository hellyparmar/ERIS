#!/usr/bin/env python3
"""
Create test user for R-DIOS authentication testing
"""
import sys
sys.path.insert(0, '/home/petpooja/Enterprise Retail Intelligence System')

from api.db.database import get_db
from api.db.multitenant_models import User, Organization
from api.auth.password import hash_password
from sqlalchemy.orm import Session
import uuid

def create_test_user():
    db = next(get_db())
    
    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(User.email == "admin@petpooja.com").first()
        
        if existing_user:
            print(f"✅ Test user already exists: {existing_user.email}")
            print(f"   Role: {existing_user.role}")
            return
        
        # Check if organization exists, create if not
        org = db.query(Organization).first()
        if not org:
            org = Organization(
                id=uuid.uuid4(),
                name="Petpooja Test Organization",
                subdomain="petpooja",
                is_active=True
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"✅ Created organization: {org.name}")
        
        # Create test user
        test_user = User(
            email="admin@petpooja.com",
            hashed_password=hash_password("admin123"),
            full_name="Admin User",
            role="admin",
            is_active=True,
            organization_id=org.id,
            assigned_stores=[]
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✅ Created test user:")
        print(f"   Email: {test_user.email}")
        print(f"   Password: admin123")
        print(f"   Role: {test_user.role}")
        print(f"   Organization: {org.name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()

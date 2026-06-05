#!/usr/bin/env python3
"""
Minimal seed script for ERIS restaurant management system
Run from project root: python3 scripts/seed_minimal_final.py
"""
import psycopg2
from psycopg2 import sql
from datetime import datetime
import hashlib
import bcrypt

# Database connection details
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'eris_admin',
    'password': 'JnCSXvJLgIY7V8KtUd2TT26QXkbgvuwv',
    'dbname': 'eris_production'
}

def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("=" * 70)
        print("🌱 Starting Database Seeding for ERIS")
        print("=" * 70)
        
        # Step 1: Check if we already have data
        cur.execute("SELECT COUNT(*) FROM organizations")
        org_count = cur.fetchone()[0]
        
        if org_count > 0:
            print("✓ Database already seeded. Organizations found:", org_count)
            cur.close()
            conn.close()
            return
        
        print("\n[1/7] Inserting Organization...")
        cur.execute("""
            INSERT INTO organizations 
            (name, email, phone, city, is_active, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id, name
        """, ('PetPooja Restaurant Chain', 'contact@petpooja.com', '+91-8080-808-080', 'Bangalore', True))
        org = cur.fetchone()
        org_id = org[0]
        print(f"   ✓ Created organization: {org[1]} (ID: {org_id})")
        
        # Step 2: Insert Roles
        print("\n[2/7] Inserting Roles...")
        roles_data = [
            ('superadmin', 'System Administrator', True, True),
            ('manager', 'Restaurant Manager', False, True),
            ('analyst', 'Data Analyst', False, True),
            ('staff', 'Staff Member', False, True),
        ]
        
        role_ids = {}
        for role_name, role_desc, is_sys, is_active in roles_data:
            cur.execute("""
                INSERT INTO roles 
                (name, description, is_system_role, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id, name
            """, (role_name, role_desc, is_sys, is_active))
            role = cur.fetchone()
            role_ids[role_name] = role[0]
            print(f"   ✓ Created role: {role[1]} (ID: {role[0]})")
        
        # Step 3: Insert Outlets
        print("\n[3/7] Inserting Outlets...")
        outlets_data = [
            ('Koramangala Outlet', '5th Block, Koramangala', 'Bangalore', 'Karnataka', '560034'),
            ('Andheri West Outlet', 'Lokhandwala Complex', 'Mumbai', 'Maharashtra', '400053'),
            ('Connaught Place Outlet', 'Block A, CP', 'New Delhi', 'Delhi', '110001'),
            ('Navrangpura Outlet', 'CG Road', 'Ahmedabad', 'Gujarat', '380009'),
            ('Anna Nagar Outlet', '2nd Avenue', 'Chennai', 'Tamil Nadu', '600040'),
        ]
        
        outlet_ids = []
        for outlet_name, address, city, state, postal_code in outlets_data:
            cur.execute("""
                INSERT INTO outlets 
                (organization_id, name, address, city, state, postal_code, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id, name
            """, (org_id, outlet_name, address, city, state, postal_code, True))
            outlet = cur.fetchone()
            outlet_ids.append(outlet[0])
            print(f"   ✓ Created outlet: {outlet[1]} (ID: {outlet[0]})")
        
        # Step 4: Insert Users
        print("\n[4/7] Inserting Users...")
        users_data = [
            ('admin', 'admin@petpooja.com', 'Admin', 'User', 'admin123', 'superadmin', None),
            ('manager1', 'manager@petpooja.com', 'Manager', 'One', 'manager123', 'manager', outlet_ids[0]),
            ('analyst1', 'analyst@petpooja.com', 'Analyst', 'One', 'analyst123', 'analyst', None),
            ('staff1', 'staff@petpooja.com', 'Staff', 'One', 'staff123', 'staff', outlet_ids[0]),
        ]
        
        user_ids = []
        for username, email, fname, lname, password, role_name, outlet_id in users_data:
            pwd_hash = hash_password(password)
            role_id = role_ids[role_name]
            
            if outlet_id:
                cur.execute("""
                    INSERT INTO users
                    (username, email, first_name, last_name, password_hash, role_id, organization_id, 
                     outlet_id, is_active, email_verified, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id, username
                """, (username, email, fname, lname, pwd_hash, role_id, org_id, outlet_id, True, False))
            else:
                cur.execute("""
                    INSERT INTO users
                    (username, email, first_name, last_name, password_hash, role_id, organization_id,
                     is_active, email_verified, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id, username
                """, (username, email, fname, lname, pwd_hash, role_id, org_id, True, False))
            
            user = cur.fetchone()
            user_ids.append(user[0])
            print(f"   ✓ Created user: {user[1]} (ID: {user[0]}, Role: {role_name})")
        
        conn.commit()
        
        # Step 5: Check counts
        print("\n[5/7] Verifying inserted data...")
        cur.execute("SELECT COUNT(*) FROM organizations WHERE is_deleted = FALSE")
        print(f"   ✓ Organizations: {cur.fetchone()[0]}")
        
        cur.execute("SELECT COUNT(*) FROM outlets WHERE is_deleted = FALSE")
        print(f"   ✓ Outlets: {cur.fetchone()[0]}")
        
        cur.execute("SELECT COUNT(*) FROM roles WHERE is_deleted = FALSE")
        print(f"   ✓ Roles: {cur.fetchone()[0]}")
        
        cur.execute("SELECT COUNT(*) FROM users WHERE is_deleted = FALSE")
        print(f"   ✓ Users: {cur.fetchone()[0]}")
        
        # Step 6: Display foundation data
        print("\n[6/7] Foundation Data Summary:")
        print(f"   Organization ID: {org_id}")
        print(f"   Outlet IDs: {outlet_ids}")
        print(f"   Role IDs: {role_ids}")
        print(f"   User IDs: {user_ids}")
        
        # Step 7: Check all critical tables
        print("\n[7/7] Checking all table row counts...")
        cur.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """)
        
        tables = [row[0] for row in cur.fetchall()]
        print(f"\n   Found {len(tables)} tables in database:")
        
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                status = "✓" if count > 0 else "✗"
                print(f"   {status} {table:30} {count:6} rows")
            except Exception as e:
                print(f"   ? {table:30} (error: {str(e)[:30]})")
        
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✅ Database seeding COMPLETE!")
        print("=" * 70)
        print("\n🎯 Foundation data is ready. System can now function with:")
        print(f"   - 1 organization ({org_id})")
        print(f"   - 5 outlets (IDs: {', '.join(map(str, outlet_ids))})")
        print(f"   - 4 roles (admin, manager, analyst, staff)")
        print(f"   - 4 users (admin, manager, analyst, staff)")
        print("\n📝 Test Login Credentials:")
        print("   Username: admin")
        print("   Email: admin@petpooja.com")
        print("   Password: admin123")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ Database Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)

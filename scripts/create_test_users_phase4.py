import psycopg2
import os
import bcrypt
from dotenv import load_dotenv

load_dotenv("backend/.env")

db_url = os.getenv("DATABASE_URL")
if db_url:
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

def hash_password(password):
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def main():
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Get organization ID
    cur.execute("SELECT id FROM organizations LIMIT 1")
    org_id = cur.fetchone()[0]
    
    # 1. Super Admin Test User
    super_admin_email = "super_admin_test@rdios.com"
    cur.execute("SELECT id FROM users WHERE email = %s", (super_admin_email,))
    if cur.fetchone():
        print(f"User {super_admin_email} already exists. Deleting...")
        cur.execute("DELETE FROM user_outlets WHERE user_id IN (SELECT id FROM users WHERE email = %s)", (super_admin_email,))
        cur.execute("DELETE FROM users WHERE email = %s", (super_admin_email,))
        
    pwd_hash = hash_password("password123")
    cur.execute("""
        INSERT INTO users (username, email, first_name, last_name, password_hash, role_id, organization_id, is_active, email_verified, created_at, updated_at)
        VALUES ('super_admin_test', %s, 'Super', 'Admin Test', %s, 1, %s, True, True, NOW(), NOW())
        RETURNING id
    """, (super_admin_email, pwd_hash, org_id))
    super_admin_id = cur.fetchone()[0]
    print(f"Created Super Admin Test User with ID: {super_admin_id}")
    
    # 2. Area Manager Test User (Assigned to Outlets 1 and 2)
    area_manager_email = "area_manager_test@rdios.com"
    cur.execute("SELECT id FROM users WHERE email = %s", (area_manager_email,))
    if cur.fetchone():
        print(f"User {area_manager_email} already exists. Deleting...")
        cur.execute("DELETE FROM user_outlets WHERE user_id IN (SELECT id FROM users WHERE email = %s)", (area_manager_email,))
        cur.execute("DELETE FROM users WHERE email = %s", (area_manager_email,))
        
    cur.execute("""
        INSERT INTO users (username, email, first_name, last_name, password_hash, role_id, organization_id, outlet_id, is_active, email_verified, created_at, updated_at)
        VALUES ('area_manager_test', %s, 'Area', 'Manager Test', %s, 5, %s, 1, True, True, NOW(), NOW())
        RETURNING id
    """, (area_manager_email, pwd_hash, org_id))
    area_manager_id = cur.fetchone()[0]
    print(f"Created Area Manager Test User with ID: {area_manager_id}")
    
    # Associate Area Manager with Outlet 1 and Outlet 2
    cur.execute("INSERT INTO user_outlets (user_id, outlet_id) VALUES (%s, %s)", (area_manager_id, 1))
    cur.execute("INSERT INTO user_outlets (user_id, outlet_id) VALUES (%s, %s)", (area_manager_id, 2))
    print(f"Associated Area Manager with Outlets 1 and 2")
    
    # 3. Outlet Manager Test User (Assigned to Outlet 1)
    outlet_manager_email = "outlet_manager_test@rdios.com"
    cur.execute("SELECT id FROM users WHERE email = %s", (outlet_manager_email,))
    if cur.fetchone():
        print(f"User {outlet_manager_email} already exists. Deleting...")
        cur.execute("DELETE FROM user_outlets WHERE user_id IN (SELECT id FROM users WHERE email = %s)", (outlet_manager_email,))
        cur.execute("DELETE FROM users WHERE email = %s", (outlet_manager_email,))
        
    cur.execute("""
        INSERT INTO users (username, email, first_name, last_name, password_hash, role_id, organization_id, outlet_id, is_active, email_verified, created_at, updated_at)
        VALUES ('outlet_manager_test', %s, 'Outlet', 'Manager Test', %s, 2, %s, 1, True, True, NOW(), NOW())
        RETURNING id
    """, (outlet_manager_email, pwd_hash, org_id))
    outlet_manager_id = cur.fetchone()[0]
    print(f"Created Outlet Manager Test User with ID: {outlet_manager_id}")
    
    # Associate Outlet Manager with Outlet 1
    cur.execute("INSERT INTO user_outlets (user_id, outlet_id) VALUES (%s, %s)", (outlet_manager_id, 1))
    print(f"Associated Outlet Manager with Outlet 1")
    
    conn.commit()
    cur.close()
    conn.close()
    print("Done seeding Phase 4 test users!")

if __name__ == '__main__':
    main()

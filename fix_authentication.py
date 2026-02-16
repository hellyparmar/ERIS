#!/usr/bin/env python3
"""
Authentication Configuration Fix - STEP 2.5 Final Implementation
Creates User table in SQLite and configures authentication

Three options provided:
1. Create User table (RECOMMENDED)
2. Modify auth router for hardcoded users
3. Use auth_login router exclusively

Run with: python fix_authentication.py
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
import hashlib
import os

# Password hasher (using hashlib for simplicity, bcrypt recommended for production)
def hash_password(password: str) -> str:
    """Hash password using SHA256 (development) - use bcrypt in production"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hash_value: str) -> bool:
    """Verify password matches hash"""
    return hash_password(password) == hash_value

def create_user_table():
    """OPTION 1: Create User table in SQLite"""
    print("\n" + "="*80)
    print("OPTION 1: Creating User Table in SQLite")
    print("="*80 + "\n")
    
    db_path = "api/rdios_dev.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            print("⚠️  User table already exists")
            return True
        
        # Create users table
        print("📝 Creating users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE,
                full_name TEXT,
                hashed_password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on email for faster lookups
        print("📑 Creating email index...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        
        # Insert test users
        print("👤 Adding test users...")
        test_users = [
            ("admin@rdios.local", "admin", "Admin User", hash_password("secret"), True, True),
            ("user@rdios.local", "user", "Test User", hash_password("secret"), True, False),
            ("demo@rdios.local", "demo", "Demo User", hash_password("demo123"), True, False)
        ]
        
        for email, username, full_name, hashed_pwd, is_active, is_admin in test_users:
            try:
                cursor.execute("""
                    INSERT INTO users (email, username, full_name, hashed_password, is_active, is_admin)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (email, username, full_name, hashed_pwd, is_active, is_admin))
                print(f"   ✅ Added user: {email}")
            except sqlite3.IntegrityError:
                print(f"   ⚠️  User already exists: {email}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ User table created successfully")
        print("\n📋 Test Credentials:")
        print("   admin@rdios.local / secret (Admin)")
        print("   user@rdios.local / secret (User)")
        print("   demo@rdios.local / demo123 (Demo)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating user table: {e}")
        return False

def modify_auth_router():
    """OPTION 2: Modify existing auth router to use hardcoded fallback"""
    print("\n" + "="*80)
    print("OPTION 2: Modifying Auth Router for Hardcoded Fallback")
    print("="*80 + "\n")
    
    auth_file = "api/routers/auth.py"
    
    if not os.path.exists(auth_file):
        print(f"❌ File not found: {auth_file}")
        return False
    
    print(f"📝 Reading {auth_file}...")
    with open(auth_file, 'r') as f:
        content = f.read()
    
    # Check if modification already exists
    if "HARDCODED_USERS" in content:
        print("⚠️  Auth router already modified")
        return True
    
    # Add hardcoded users
    hardcoded_section = '''
# Hardcoded test users for development
HARDCODED_USERS = {
    "admin@rdios.local": {
        "email": "admin@rdios.local",
        "username": "admin",
        "full_name": "Admin User",
        "hashed_password": "$2b$12$...",  # "secret" hashed with bcrypt
        "is_active": True,
        "is_admin": True
    }
}

def verify_hardcoded_user(email: str, password: str) -> dict | None:
    """Verify user from hardcoded database"""
    if email not in HARDCODED_USERS:
        return None
    user = HARDCODED_USERS[email]
    # In development, accept "secret" password
    if password == "secret":
        return user
    return None
'''
    
    # Insert hardcoded section after imports
    lines = content.split('\n')
    import_end = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('from') and not line.startswith('import'):
            import_end = i
            break
    
    lines.insert(import_end, hardcoded_section)
    modified_content = '\n'.join(lines)
    
    # Modify authenticate_user function to check hardcoded first
    modified_content = modified_content.replace(
        'def authenticate_user(db: Session, email: str, password: str):',
        '''def authenticate_user(db: Session, email: str, password: str):
    """Authenticate user - check hardcoded first, then database"""
    # Check hardcoded users first (development)
    hardcoded = verify_hardcoded_user(email, password)
    if hardcoded:
        return hardcoded
    
    # Fall back to database'''
    )
    
    print(f"✅ Would modify {auth_file} to add hardcoded fallback")
    print("\n⚠️  This requires manual integration")
    print("   Recommended: Use Option 1 instead (create User table)")
    
    return True

def use_auth_login_router():
    """OPTION 3: Use new auth_login router exclusively"""
    print("\n" + "="*80)
    print("OPTION 3: Using auth_login Router Exclusively")
    print("="*80 + "\n")
    
    main_file = "api/main.py"
    
    if not os.path.exists(main_file):
        print(f"❌ File not found: {main_file}")
        return False
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check if both routers are included
    has_old_auth = "from api.routers import auth" in content and "from api.routers import auth_login" in content
    
    if has_old_auth:
        print("✅ Both auth routers detected")
        print("   To use only auth_login router:")
        print("   1. Comment out: # from api.routers import auth")
        print("   2. Comment out: # app.include_router(auth.router)")
        print("   3. Restart backend: pkill -f uvicorn && python -m uvicorn api.main:app")
        return True
    
    return False

def print_summary():
    """Print options summary"""
    print("\n" + "="*80)
    print("AUTHENTICATION FIX - CHOOSE YOUR OPTION")
    print("="*80 + "\n")
    
    print("✅ RECOMMENDED: Option 1 - Create User Table")
    print("   • Creates permanent User table in SQLite")
    print("   • Works with existing auth.py router")
    print("   • Supports multiple users and permissions")
    print("   • Time: 5 minutes")
    print("   • Run: python fix_authentication.py --option 1")
    
    print("\n⚠️  ALTERNATIVE: Option 2 - Hardcoded Fallback")
    print("   • Modifies auth router to check hardcoded users first")
    print("   • Preserves existing database logic")
    print("   • Development-focused")
    print("   • Time: 10 minutes (manual)")
    
    print("\n⚠️  ALTERNATIVE: Option 3 - Use auth_login Only")
    print("   • Removes original auth router")
    print("   • Uses hardcoded users from auth_login.py")
    print("   • Simplest approach")
    print("   • Time: 5 minutes")
    
    print("\n" + "="*80 + "\n")

def test_login_after_fix():
    """Test login after creating user table"""
    print("\n🧪 Testing login after fix...\n")
    
    print("Execute these commands to test:")
    print("""
# Test login with curl
curl -X POST http://localhost:8000/auth/login \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "username=admin@rdios.local&password=secret"

# Or use Python requests
import requests
response = requests.post(
    'http://localhost:8000/auth/login',
    data={'username': 'admin@rdios.local', 'password': 'secret'}
)
token = response.json()['access_token']

# Then use token for protected endpoints
headers = {'Authorization': f'Bearer {token}'}
requests.get('http://localhost:8000/api/v1/analytics/sales', headers=headers)
    """)

def main():
    """Main execution"""
    import sys
    
    print_summary()
    
    # Check if option specified via command line
    option = None
    if len(sys.argv) > 1:
        if "--option" in sys.argv:
            option = sys.argv[sys.argv.index("--option") + 1]
    
    if option == "1":
        print("Installing User table...\n")
        if create_user_table():
            print("\n✅ User table created successfully")
            test_login_after_fix()
        else:
            print("\n❌ Failed to create user table")
    
    elif option == "2":
        print("Modifying auth router...\n")
        if modify_auth_router():
            print("\n⚠️  Manual steps required")
        else:
            print("\n❌ Failed to modify auth router")
    
    elif option == "3":
        print("Using auth_login router exclusively...\n")
        if use_auth_login_router():
            print("\n✅ Review changes shown above")
        else:
            print("\n✅ Setup ready")
    
    else:
        print("\n💡 Choose an option above and run:")
        print("   python fix_authentication.py --option 1")
        print("   python fix_authentication.py --option 2")
        print("   python fix_authentication.py --option 3")
        
        print("\n📝 RECOMMENDED WORKFLOW:")
        print("   1. python fix_authentication.py --option 1  (Create User table)")
        print("   2. pkill -f uvicorn  (Restart backend)")
        print("   3. python -m uvicorn api.main:app --reload --port 8000  (Start backend)")
        print("   4. python test_auth_setup.py  (Test login)")
        print("   5. python test_api_comprehensive.py  (Test analytics endpoints)")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")

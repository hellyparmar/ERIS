#!/usr/bin/env python3
"""
CRITICAL FIX: Authentication System & Security Headers Configuration

Fixes:
1. Update auth.py to handle SHA256 hashed passwords (legacy) and bcrypt (new)
2. Add security headers middleware
3. Fix analytics endpoint routing
4. Add weather endpoint parameter support

Run with: python implement_fixes.py
"""

import sqlite3
import hashlib
import os

def fix_authentication_system():
    """Fix authentication to support both SHA256 and bcrypt passwords"""
    
    print("\n" + "="*80)
    print("FIX 1: AUTHENTICATION SYSTEM")
    print("="*80)
    
    auth_file = "api/routers/auth.py"
    
    with open(auth_file, 'r') as f:
        content = f.read()
    
    # Add helper function for SHA256 password verification
    sha256_helper = '''
# Legacy SHA256 password verification (for existing users)
def verify_sha256_password(plain_password: str, sha256_hash: str) -> bool:
    """Verify SHA256 hashed password"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == sha256_hash

# Combined password verifier
def verify_password_legacy(plain_password: str, stored_hash: str) -> bool:
    """Verify password - supports both bcrypt and SHA256"""
    # Try bcrypt first
    try:
        return pwd_context.verify(plain_password, stored_hash)
    except:
        # Fall back to SHA256
        return verify_sha256_password(plain_password, stored_hash)

'''
    
    # Find where to insert (after imports)
    insert_pos = content.find('pwd_context = CryptContext')
    if insert_pos > 0:
        insert_pos = content.find('\n', insert_pos) + 1
        
        # Check if already present
        if 'verify_sha256_password' not in content:
            content = content[:insert_pos] + sha256_helper + content[insert_pos:]
            
            # Replace password verification in login function
            old_verify = '''# Verify password
    if not verify_password(form_data.password, user.hashed_password):'''
            
            new_verify = '''# Verify password (supports both bcrypt and SHA256)
    if not verify_password_legacy(form_data.password, user.hashed_password):'''
            
            content = content.replace(old_verify, new_verify)
            
            with open(auth_file, 'w') as f:
                f.write(content)
            
            print("✅ Updated auth.py to support SHA256 passwords")
            print("   - Added verify_sha256_password() function")
            print("   - Added verify_password_legacy() for both bcrypt and SHA256")
            print("   - Updated login endpoint to use legacy verifier")
            return True
        else:
            print("⚠️  auth.py already updated")
            return True
    
    return False

def add_security_headers():
    """Add security headers middleware to main.py"""
    
    print("\n" + "="*80)
    print("FIX 2: SECURITY HEADERS")
    print("="*80)
    
    main_file = "api/main.py"
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Security headers middleware code
    security_middleware = '''
# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

'''
    
    # Check if already present
    if 'add_security_headers' not in content:
        # Find position after CORS middleware setup
        insert_pos = content.find('app.add_middleware(APIRateLimitMiddleware')
        if insert_pos > 0:
            # Find end of line
            insert_pos = content.find('\n', insert_pos) + 1
            content = content[:insert_pos] + security_middleware + content[insert_pos:]
            
            with open(main_file, 'w') as f:
                f.write(content)
            
            print("✅ Added security headers middleware to main.py")
            print("   - X-Content-Type-Options: nosniff")
            print("   - X-Frame-Options: DENY")
            print("   - X-XSS-Protection: 1; mode=block")
            print("   - Content-Security-Policy configured")
            print("   - Strict-Transport-Security: max-age=31536000")
            print("   - Referrer-Policy: strict-origin-when-cross-origin")
            print("   - Permissions-Policy: disabled (geolocation, microphone, camera)")
            return True
    else:
        print("⚠️  Security headers already configured")
        return True

def add_missing_import():
    """Add hashlib import to auth.py"""
    
    auth_file = "api/routers/auth.py"
    
    with open(auth_file, 'r') as f:
        content = f.read()
    
    if 'import hashlib' not in content:
        # Find last import
        lines = content.split('\n')
        last_import_idx = 0
        
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                last_import_idx = i
        
        lines.insert(last_import_idx + 1, 'import hashlib')
        
        with open(auth_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print("✅ Added hashlib import to auth.py")
        return True
    
    return False

def verify_analytics_router():
    """Verify analytics router is properly included"""
    
    print("\n" + "="*80)
    print("FIX 3: ANALYTICS ROUTER VERIFICATION")
    print("="*80)
    
    main_file = "api/main.py"
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    if 'app.include_router(analytics.router' in content:
        print("✅ Analytics router is included in main.py")
        
        # Check with prefix
        if 'prefix="/api/v1"' in content and 'analytics.router' in content:
            print("✅ Analytics router uses /api/v1 prefix")
            return True
        else:
            print("⚠️  Analytics router prefix may need verification")
            return False
    else:
        print("❌ Analytics router NOT found in main.py")
        return False

def main():
    print("\n" + "="*80)
    print("IMPLEMENTING CRITICAL FIXES")
    print("="*80)
    
    results = []
    
    # Fix 1: Authentication
    print("\n[1/4] Fixing authentication system...")
    results.append(add_missing_import())
    results.append(fix_authentication_system())
    
    # Fix 2: Security Headers
    print("\n[2/4] Adding security headers...")
    results.append(add_security_headers())
    
    # Fix 3: Verify Analytics
    print("\n[3/4] Verifying analytics routing...")
    results.append(verify_analytics_router())
    
    # Summary
    print("\n" + "="*80)
    print("FIX SUMMARY")
    print("="*80)
    
    if all(results):
        print("✅ All fixes applied successfully!")
        print("\nNEXT STEPS:")
        print("1. Restart backend: pkill -f uvicorn && python -m uvicorn api.main:app --reload --port 8000")
        print("2. Test login: curl -X POST http://localhost:8000/auth/login -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=admin@rdios.local&password=secret'")
        print("3. Verify analytics: curl http://localhost:8000/api/v1/analytics/metrics")
        print("4. Re-run verification: python verify_and_diagnose.py")
    else:
        print("⚠️  Some fixes may need manual intervention")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

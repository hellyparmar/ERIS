#!/bin/bash
# Security Features Testing Script
# Tests all security hardening features

API_URL="http://localhost:8000/api/v1"
TEST_EMAIL="test@example.com"
TEST_PASSWORD="TestPass123!"  # Valid: 12+ chars, upper, lower, digit, special

echo "=========================================="
echo "Security Features Testing"
echo "=========================================="

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Password Strength Validation
echo -e "\n${YELLOW}Test 1: Password Strength Validation${NC}"
echo "Testing weak password rejection..."

weak_passwords=(
    "short"                # Too short
    "NoDigit!"            # No digit
    "nouppercas3!"        # No uppercase
    "NOLOWERCASE3!"       # No lowercase
    "NoSpecial123"        # No special char
)

# Get admin token first (assuming test user exists)
# This is a placeholder - you'll need to adjust based on your test setup
echo "Note: Requires valid admin token to test registration"

# Test 2: Input Sanitization
echo -e "\n${YELLOW}Test 2: Input Sanitization${NC}"
echo "Testing input validation on email..."

# Test with email containing null bytes (should be rejected)
TEST_RESULT=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "email": "test\x00@example.com",
    "password": "TestPass123!",
    "full_name": "Test User"
  }')

if echo "$TEST_RESULT" | grep -q "invalid"; then
    echo -e "${GREEN}✓ Null byte rejection working${NC}"
else
    echo -e "${RED}✗ Null byte check failed${NC}"
fi

# Test 3: Rate Limiting
echo -e "\n${YELLOW}Test 3: Rate Limiting${NC}"
echo "Testing auth rate limiting (5 requests/minute)..."

RATE_LIMIT_HITS=0
for i in {1..6}; do
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/login" \
      -H "Content-Type: application/json" \
      -d "{\"username\":\"$TEST_EMAIL\",\"password\":\"wrong\"}")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" = "429" ]; then
        echo -e "${GREEN}✓ Rate limit triggered on request $i (HTTP $HTTP_CODE)${NC}"
        ((RATE_LIMIT_HITS++))
    fi
done

if [ "$RATE_LIMIT_HITS" -gt 0 ]; then
    echo -e "${GREEN}✓ Rate limiting working${NC}"
else
    echo -e "${RED}✗ Rate limiting not triggered${NC}"
fi

# Test 4: Brute Force Protection
echo -e "\n${YELLOW}Test 4: Brute Force Protection${NC}"
echo "Testing account lockout after 5 failed attempts..."

FAILED_ATTEMPTS=0
for i in {1..7}; do
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/login" \
      -H "Content-Type: application/json" \
      -d "{\"username\":\"$TEST_EMAIL\",\"password\":\"wrongpass\"}")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n -1)
    
    echo "Attempt $i: HTTP $HTTP_CODE"
    
    # Check for lock message (should happen on 5th attempt)
    if echo "$BODY" | grep -q "Account locked"; then
        echo -e "${GREEN}✓ Account locked after $i attempts${NC}"
        break
    fi
    
    if [ "$HTTP_CODE" = "429" ]; then
        echo -e "${GREEN}✓ Too many requests (HTTP 429) on attempt $i${NC}"
        break
    fi
done

# Test 5: Successful Login (clears brute force counter)
echo -e "\n${YELLOW}Test 5: Successful Login${NC}"
echo "Testing successful login..."

# This requires a valid user to exist
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin@example.com\",\"password\":\"SecurePass123!\"}")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Login successful, received access token${NC}"
    
    # Check for request ID in response headers
    HEADERS=$(curl -s -i -X POST "$API_URL/auth/login" \
      -H "Content-Type: application/json" \
      -d "{\"username\":\"admin@example.com\",\"password\":\"SecurePass123!\"}" 2>&1)
    
    if echo "$HEADERS" | grep -q "X-Request-ID"; then
        echo -e "${GREEN}✓ X-Request-ID header present${NC}"
    else
        echo -e "${RED}✗ X-Request-ID header missing${NC}"
    fi
else
    echo -e "${RED}✗ Login failed${NC}"
fi

# Test 6: Structured Logging
echo -e "\n${YELLOW}Test 6: Structured Logging${NC}"
echo "Check application logs for JSON formatted entries..."
echo "Look for logs containing: timestamp, level, module, function, message"
echo "In production mode, logs should be machine-readable JSON"

# Test 7: GET /me endpoint with auth
echo -e "\n${YELLOW}Test 7: Authentication Token Verification${NC}"
echo "Testing protected endpoint..."

# This requires a valid token
ME_RESPONSE=$(curl -s -X GET "$API_URL/auth/me" \
  -H "Authorization: Bearer VALID_TOKEN_HERE")

if echo "$ME_RESPONSE" | grep -q "email"; then
    echo -e "${GREEN}✓ Protected endpoint accessible with valid token${NC}"
else
    echo -e "${YELLOW}⚠ Provide valid token to test protected endpoint${NC}"
fi

echo -e "\n${GREEN}=========================================="
echo "Testing complete!"
echo "=========================================${NC}"

echo -e "\n${YELLOW}Manual Testing Steps:${NC}"
echo "1. Register new user with weak password:"
echo "   - Should reject with specific requirement message"
echo ""
echo "2. Register new user with strong password:"
echo "   - Should succeed and create user"
echo ""
echo "3. Login with correct password:"
echo "   - Should return access token"
echo "   - Brute force counter should reset"
echo ""
echo "4. Login 5 times with wrong password:"
echo "   - 5th attempt should return 'Account locked'"
echo "   - Should not be able to login for 30 minutes"
echo ""
echo "5. Make 6+ rapid login attempts:"
echo "   - 6th attempt should be rate limited (429)"
echo ""
echo "6. Check logs for security events:"
echo "   - Look for: 'Brute force attempt', 'Account locked'"
echo "   - Look for: JSON formatted logs in production"

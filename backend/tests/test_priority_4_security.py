"""
PRIORITY 4: Security Tests - Token Revocation & Input Validation
Real working tests for security features
"""

import pytest
import logging
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TestTokenRevocation:
    """
    PRIORITY 4: Verify token revocation/blacklist works
    """
    
    def test_token_revocation_basic(self):
        """Verify tokens can be revoked"""
        from api.utils.token_blacklist import revoke_token, is_token_revoked
        
        token = "test_token_12345"
        
        # Token should not be revoked initially
        assert not is_token_revoked(token), "Token should not be revoked initially"
        
        # Revoke the token
        revoke_token(token)
        
        # Token should now be revoked
        assert is_token_revoked(token), "Token should be revoked after revocation"
        
        logger.info("✅ Token revocation test passed")
    
    def test_logout_service(self):
        """Verify logout service revokes token"""
        from api.utils.token_blacklist import LogoutService, is_token_revoked
        
        token = "test_logout_token"
        
        # Logout should revoke token
        result = LogoutService.logout(token)
        
        assert result["status"] == "success"
        assert result["token_revoked"] == True
        assert is_token_revoked(token), "Token should be revoked after logout"
        
        logger.info("✅ Logout service test passed")
    
    def test_token_status_check(self):
        """Verify we can check token status"""
        from api.utils.token_blacklist import LogoutService, revoke_token
        
        active_token = "active_token_123"
        revoked_token = "revoked_token_123"
        
        # Revoke one token
        revoke_token(revoked_token)
        
        # Check status
        active_status = LogoutService.verify_active(active_token)
        revoked_status = LogoutService.verify_active(revoked_token)
        
        assert active_status["token_active"] == True
        assert active_status["token_revoked"] == False
        
        assert revoked_status["token_active"] == False
        assert revoked_status["token_revoked"] == True
        
        logger.info("✅ Token status check test passed")


class TestInputValidation:
    """
    PRIORITY 4: Verify input validation prevents attacks
    """
    
    def test_email_validation(self):
        """Verify email validation works"""
        from api.utils.input_validators import InputValidator, ValidationError
        
        # Valid email
        valid_email = InputValidator.validate_email("test@example.com")
        assert valid_email == "test@example.com"
        
        # Invalid email
        with pytest.raises(ValidationError):
            InputValidator.validate_email("invalid-email")
        
        logger.info("✅ Email validation test passed")
    
    def test_store_id_validation(self):
        """Verify store ID validation"""
        from api.utils.input_validators import InputValidator, ValidationError
        
        # Valid store ID
        store_id = InputValidator.validate_store_id("STORE_001")
        assert store_id == "STORE_001"
        
        # Invalid characters
        with pytest.raises(ValidationError):
            InputValidator.validate_store_id("STORE@001")
        
        logger.info("✅ Store ID validation test passed")
    
    def test_dangerous_characters_rejected(self):
        """Verify dangerous characters are rejected"""
        from api.utils.input_validators import InputValidator, ValidationError
        
        # Test XSS attempt
        xss_attempt = "<script>alert('xss')</script>"
        with pytest.raises(ValidationError):
            InputValidator.validate_string(xss_attempt, "test_field")
        
        # Test quote injection
        quote_attempt = "Test'; DROP TABLE users; --"
        with pytest.raises(ValidationError):
            InputValidator.validate_string(quote_attempt, "test_field")
        
        logger.info("✅ Dangerous characters rejection test passed")
    
    def test_amount_validation(self):
        """Verify decimal/currency validation"""
        from api.utils.input_validators import InputValidator, ValidationError
        
        # Valid amount
        amount = InputValidator.validate_decimal(
            "1000.50",
            "amount",
            Decimal("0.01"),
            Decimal("999999.99")
        )
        assert amount == Decimal("1000.50")
        
        # Negative amount
        with pytest.raises(ValidationError):
            InputValidator.validate_decimal(
                "-100",
                "amount",
                Decimal("0.01"),
                Decimal("999999.99")
            )
        
        # Amount too large
        with pytest.raises(ValidationError):
            InputValidator.validate_decimal(
                "9999999.99",
                "amount",
                Decimal("0.01"),
                Decimal("999999.99")
            )
        
        logger.info("✅ Amount validation test passed")
    
    def test_enum_validation(self):
        """Verify enum/choice validation"""
        from api.utils.input_validators import InputValidator, ValidationError
        
        allowed = ["CASH", "CARD", "CHEQUE"]
        
        # Valid value
        value = InputValidator.validate_enum("CARD", "payment_method", allowed)
        assert value == "CARD"
        
        # Invalid value
        with pytest.raises(ValidationError):
            InputValidator.validate_enum("BITCOIN", "payment_method", allowed)
        
        logger.info("✅ Enum validation test passed")
    
    def test_batch_validation(self):
        """Verify batch validation of multiple fields"""
        from api.utils.input_validators import validate_sale_request
        
        valid_request = {
            "store_id": "STORE_001",
            "customer_name": "John Doe",
            "total_amount": "1500.00",
            "payment_method": "CARD"
        }
        
        result = validate_sale_request(valid_request)
        
        assert result["store_id"] == "STORE_001"
        assert result["customer_name"] == "John Doe"
        assert result["total_amount"] == Decimal("1500.00")
        assert result["payment_method"] == "CARD"
        
        logger.info("✅ Batch validation test passed")


class TestRateLimiting:
    """
    PRIORITY 4: Verify rate limiting prevents abuse
    """
    
    def test_rate_limit_enforcement(self):
        """Verify rate limiting works"""
        from api.middleware.security import RateLimiter
        
        # Create limiter with 5 requests per minute
        limiter = RateLimiter(requests_per_minute=5)
        user = "test_user"
        
        # First 5 requests should be allowed
        for i in range(5):
            allowed = limiter.is_allowed(user)
            assert allowed, f"Request {i+1} should be allowed"
        
        # 6th request should be blocked
        blocked = limiter.is_allowed(user)
        assert not blocked, "6th request should be blocked"
        
        logger.info("✅ Rate limit enforcement test passed")
    
    def test_rate_limit_remaining(self):
        """Verify remaining request count"""
        from api.middleware.security import RateLimiter
        
        limiter = RateLimiter(requests_per_minute=10)
        user = "test_user"
        
        # Make some requests
        for i in range(3):
            limiter.is_allowed(user)
        
        # Check remaining
        remaining = limiter.get_remaining(user)
        assert remaining == 7, f"Should have 7 remaining, got {remaining}"
        
        logger.info("✅ Rate limit remaining test passed")


class TestCSRFProtection:
    """
    PRIORITY 4: Verify CSRF protection works
    """
    
    def test_csrf_token_generation(self):
        """Verify CSRF token generation"""
        from api.middleware.security import CSRFProtection
        
        csrf = CSRFProtection()
        user_id = "user_123"
        
        token = csrf.generate_token(user_id)
        
        assert token is not None
        assert len(token) > 20
        assert isinstance(token, str)
        
        logger.info("✅ CSRF token generation test passed")
    
    def test_csrf_token_verification(self):
        """Verify CSRF token verification"""
        from api.middleware.security import CSRFProtection
        
        csrf = CSRFProtection()
        user_id = "user_123"
        
        # Generate token
        token = csrf.generate_token(user_id)
        
        # Verify correct token
        assert csrf.verify_token(user_id, token)
        
        # Verify wrong token
        assert not csrf.verify_token(user_id, "wrong_token")
        
        # Verify wrong user
        assert not csrf.verify_token("wrong_user", token)
        
        logger.info("✅ CSRF token verification test passed")


class TestInjectionPrevention:
    """
    PRIORITY 4: Verify injection attack prevention
    """
    
    def test_sql_injection_detection(self):
        """Verify SQL injection attempts are detected"""
        from api.middleware.security import RequestValidator
        
        # SQL injection attempts
        sql_injections = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "UNION SELECT * FROM users",
            "1' AND '1'='1"
        ]
        
        for injection in sql_injections:
            assert not RequestValidator.is_safe(injection), \
                f"Should detect SQL injection: {injection}"
        
        logger.info("✅ SQL injection detection test passed")
    
    def test_xss_detection(self):
        """Verify XSS attempts are detected"""
        from api.middleware.security import RequestValidator
        
        # XSS attempts
        xss_attacks = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img onerror=alert('xss')>",
            "<body onload=alert('xss')>"
        ]
        
        for attack in xss_attacks:
            assert not RequestValidator.is_safe(attack), \
                f"Should detect XSS: {attack}"
        
        logger.info("✅ XSS detection test passed")
    
    def test_safe_input_allowed(self):
        """Verify legitimate input is allowed"""
        from api.middleware.security import RequestValidator
        
        # Safe inputs
        safe_inputs = [
            "John Doe",
            "Customer123",
            "123 Main Street",
            "STORE_001"
        ]
        
        for safe_input in safe_inputs:
            assert RequestValidator.is_safe(safe_input), \
                f"Should allow safe input: {safe_input}"
        
        logger.info("✅ Safe input allowance test passed")


class TestSecurityIntegration:
    """
    PRIORITY 4: Integration tests combining multiple security features
    """
    
    def test_logout_and_revocation_flow(self):
        """Verify complete logout and token revocation flow"""
        from api.utils.token_blacklist import (
            LogoutService, is_token_revoked, revoke_token
        )
        
        token = "integration_test_token"
        
        # User is logged in (token is active)
        assert not is_token_revoked(token)
        
        # User clicks logout
        logout_result = LogoutService.logout(token)
        assert logout_result["token_revoked"]
        
        # Token is now revoked
        assert is_token_revoked(token)
        
        # Verify status
        status = LogoutService.verify_active(token)
        assert not status["token_active"]
        assert status["token_revoked"]
        
        logger.info("✅ Logout and revocation flow test passed")
    
    def test_secure_sale_creation(self):
        """Verify secure sale request validation"""
        from api.utils.input_validators import validate_sale_request, ValidationError
        
        # Valid request
        valid_request = {
            "store_id": "STORE_001",
            "customer_name": "John Doe",
            "total_amount": "1500.00",
            "payment_method": "CARD"
        }
        
        result = validate_sale_request(valid_request)
        assert result["store_id"] == "STORE_001"
        
        # Injection attempt
        injection_request = {
            "store_id": "STORE_001",
            "customer_name": "'; DROP TABLE sales; --",
            "total_amount": "1500.00",
            "payment_method": "CARD"
        }
        
        with pytest.raises(ValidationError):
            validate_sale_request(injection_request)
        
        logger.info("✅ Secure sale creation test passed")


class TestSecurityObjectives:
    """
    PRIORITY 4: Validate security objectives are met
    """
    
    def test_token_revocation_implemented(self):
        """Verify token revocation feature exists"""
        from api.utils import token_blacklist
        
        # Check required functions exist
        assert hasattr(token_blacklist, 'revoke_token')
        assert hasattr(token_blacklist, 'is_token_revoked')
        assert hasattr(token_blacklist, 'LogoutService')
        
        logger.info("✅ Token revocation implementation verified")
    
    def test_input_validation_implemented(self):
        """Verify input validation is implemented"""
        from api.utils import input_validators
        
        # Check required classes/functions exist
        assert hasattr(input_validators, 'InputValidator')
        assert hasattr(input_validators, 'ValidationError')
        assert hasattr(input_validators, 'validate_sale_request')
        assert hasattr(input_validators, 'validate_inventory_request')
        assert hasattr(input_validators, 'validate_customer_request')
        
        logger.info("✅ Input validation implementation verified")
    
    def test_security_middleware_implemented(self):
        """Verify security middleware is implemented"""
        from api.middleware import security
        
        # Check required classes exist
        assert hasattr(security, 'SecurityMiddleware')
        assert hasattr(security, 'RateLimitMiddleware')
        assert hasattr(security, 'CSRFProtection')
        assert hasattr(security, 'RequestValidator')
        
        logger.info("✅ Security middleware implementation verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

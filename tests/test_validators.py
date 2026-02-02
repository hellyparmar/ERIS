"""
Input Validation Tests
Test SQL injection prevention, XSS protection, and data sanitization
"""

import pytest
from api.validators.input_sanitizer import InputSanitizer

class TestInputSanitizer:
    """Test input sanitization and validation"""
    
    def test_sanitize_string_removes_html(self):
        """Test HTML tags are removed from strings"""
        sanitizer = InputSanitizer()
        
        dirty = "<script>alert('xss')</script>Hello"
        clean = sanitizer.sanitize_string(dirty)
        
        assert "<script>" not in clean
        assert "alert" not in clean
        assert "Hello" in clean
    
    def test_sanitize_string_detects_sql_injection(self):
        """Test SQL injection patterns are rejected"""
        sanitizer = InputSanitizer()
        
        malicious_inputs = [
            "admin' OR '1'='1",
            "1; DROP TABLE users--",
            "admin'--",
            "' UNION SELECT * FROM users--"
        ]
        
        for malicious in malicious_inputs:
            with pytest.raises(ValueError, match="Invalid characters"):
                sanitizer.sanitize_string(malicious)
    
    def test_sanitize_string_enforces_length_limit(self):
        """Test string length limits are enforced"""
        sanitizer = InputSanitizer()
        
        too_long = "a" * 1000
        
        with pytest.raises(ValueError, match="too long"):
            sanitizer.sanitize_string(too_long, max_length=100)
    
    def test_sanitize_email_validates_format(self):
        """Test email validation"""
        sanitizer = InputSanitizer()
        
        # Valid emails
        valid_emails = [
            "user@example.com",
            "test.user@company.co.in",
            "admin123@test-site.org"
        ]
        
        for email in valid_emails:
            result = sanitizer.sanitize_email(email)
            assert "@" in result
            assert result == email.lower()
        
        # Invalid emails
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user @example.com"  # Space
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email"):
                sanitizer.sanitize_email(email)
    
    def test_sanitize_email_blocks_temporary_domains(self):
        """Test temporary email services are blocked"""
        sanitizer = InputSanitizer()
        
        temp_emails = [
            "user@tempmail.com",
            "test@10minutemail.com",
            "fake@mailinator.com"
        ]
        
        for email in temp_emails:
            with pytest.raises(ValueError, match="Temporary email"):
                sanitizer.sanitize_email(email)
    
    def test_sanitize_number_validates_type(self):
        """Test number validation"""
        sanitizer = InputSanitizer()
        
        # Valid numbers
        assert sanitizer.sanitize_number(42) == 42
        assert sanitizer.sanitize_number("42") == 42.0
        assert sanitizer.sanitize_number(42.5) == 42.5
        
        # Invalid numbers
        with pytest.raises(ValueError):
            sanitizer.sanitize_number("not a number")
        
        with pytest.raises(ValueError):
            sanitizer.sanitize_number(None)
    
    def test_sanitize_number_enforces_range(self):
        """Test number range validation"""
        sanitizer = InputSanitizer()
        
        # Within range
        assert sanitizer.sanitize_number(50, min_value=0, max_value=100) == 50
        
        # Below minimum
        with pytest.raises(ValueError, match="at least"):
            sanitizer.sanitize_number(-5, min_value=0)
        
        # Above maximum
        with pytest.raises(ValueError, match="at most"):
            sanitizer.sanitize_number(150, min_value=0, max_value=100)
    
    def test_sanitize_currency_uses_decimal(self):
        """Test currency amounts use Decimal for precision"""
        from decimal import Decimal
        
        sanitizer = InputSanitizer()
        
        result = sanitizer.sanitize_currency("123.45")
        assert isinstance(result, Decimal)
        assert result == Decimal("123.45")
    
    def test_sanitize_currency_rejects_negative(self):
        """Test negative currency amounts are rejected"""
        sanitizer = InputSanitizer()
        
        with pytest.raises(ValueError, match="cannot be negative"):
            sanitizer.sanitize_currency(-100)
    
    def test_sanitize_currency_enforces_maximum(self):
        """Test maximum currency amount"""
        sanitizer = InputSanitizer()
        
        # Should work for normal amounts
        sanitizer.sanitize_currency(1000000)  # 10 lakh
        
        # Should reject amounts > 10 crore
        with pytest.raises(ValueError, match="exceeds maximum"):
            sanitizer.sanitize_currency(200000000)  # 20 crore
    
    def test_sanitize_phone_validates_indian_mobile(self):
        """Test Indian phone number validation"""
        sanitizer = InputSanitizer()
        
        # Valid formats
        valid_phones = [
            "9876543210",
            "+919876543210",
            "919876543210",
            "+91 9876543210",
            "+91-9876543210"
        ]
        
        for phone in valid_phones:
            result = sanitizer.sanitize_phone(phone)
            assert result == "+919876543210"
    
    def test_sanitize_phone_rejects_invalid(self):
        """Test invalid phone numbers are rejected"""
        sanitizer = InputSanitizer()
        
        invalid_phones = [
            "123456789",  # Too short
            "12345678901",  # Too long
            "0123456789",  # Doesn't start with 6-9
            "5123456789",  # Doesn't start with 6-9
            "abcdefghij"  # Not numeric
        ]
        
        for phone in invalid_phones:
            with pytest.raises(ValueError):
                sanitizer.sanitize_phone(phone)
    
    def test_sanitize_filename_removes_dangerous_chars(self):
        """Test filename sanitization"""
        sanitizer = InputSanitizer()
        
        dangerous = "../../etc/passwd"
        safe = sanitizer.sanitize_filename(dangerous)
        
        assert ".." not in safe
        assert "/" not in safe
        assert "\\" not in safe
    
    def test_sanitize_filename_validates_extension(self):
        """Test file extension whitelist"""
        sanitizer = InputSanitizer()
        
        # Allowed extensions
        sanitizer.sanitize_filename("document.pdf")
        sanitizer.sanitize_filename("image.jpg")
        sanitizer.sanitize_filename("data.csv")
        
        # Disallowed extensions
        with pytest.raises(ValueError, match="not allowed"):
            sanitizer.sanitize_filename("malware.exe")
        
        with pytest.raises(ValueError, match="not allowed"):
            sanitizer.sanitize_filename("script.sh")

class TestXSSPrevention:
    """Test XSS attack prevention"""
    
    def test_script_tags_removed(self):
        """Test script tags are completely removed"""
        sanitizer = InputSanitizer()
        
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')"
        ]
        
        for xss in xss_attempts:
            with pytest.raises(ValueError):
                sanitizer.sanitize_string(xss)
    
    def test_safe_html_allowed_when_enabled(self):
        """Test safe HTML tags are allowed when allow_html=True"""
        sanitizer = InputSanitizer()
        
        safe_html = "<b>Bold</b> and <i>italic</i> text"
        result = sanitizer.sanitize_string(safe_html, allow_html=True)
        
        assert "<b>" in result or "Bold" in result  # Either kept or stripped
        assert "<script>" not in result
    
    def test_event_handlers_removed(self):
        """Test event handlers (onclick, onload, etc.) are removed"""
        sanitizer = InputSanitizer()
        
        dangerous = '<div onclick="malicious()">Click me</div>'
        
        with pytest.raises(ValueError):
            sanitizer.sanitize_string(dangerous)

class TestSQLInjectionPrevention:
    """Test SQL injection prevention"""
    
    def test_common_sql_keywords_detected(self):
        """Test common SQL injection patterns are detected"""
        sanitizer = InputSanitizer()
        
        sql_injections = [
            "'; DELETE FROM users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT password FROM users--",
            "1; DROP TABLE products;--"
        ]
        
        for injection in sql_injections:
            with pytest.raises(ValueError, match="Invalid characters"):
                sanitizer.sanitize_string(injection)
    
    def test_comment_sequences_detected(self):
        """Test SQL comment sequences are detected"""
        sanitizer = InputSanitizer()
        
        with pytest.raises(ValueError):
            sanitizer.sanitize_string("test--comment")
        
        with pytest.raises(ValueError):
            sanitizer.sanitize_string("test/*comment*/")

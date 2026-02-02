"""
Input Sanitization & Validation
Security utilities to prevent injection attacks
"""

import re
import bleach
from typing import Any, Optional
from decimal import Decimal, InvalidOperation


class InputSanitizer:
    """Sanitize and validate user inputs"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bCREATE\b|\bALTER\b)',
        r'(--|;|\/\*|\*\/)',
        r'(\bUNION\b|\bEXEC\b|\bEXECUTE\b)',
        r'(\bOR\s+\d+\s*=\s*\d+)',
        r'(\'\s*OR\s*\')',
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',  # onclick, onload, etc.
    ]
    
    @staticmethod
    def sanitize_string(
        value: str,
        max_length: int = 500,
        allow_html: bool = False,
        strip_whitespace: bool = True
    ) -> str:
        """
        Sanitize string input
        
        Args:
            value: Input string
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags
            strip_whitespace: Whether to strip leading/trailing whitespace
        
        Returns:
            Sanitized string
        
        Raises:
            ValueError: If input is invalid
        """
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # Strip whitespace
        if strip_whitespace:
            value = value.strip()
        
        # Check length
        if len(value) > max_length:
            raise ValueError(f"Input too long (max {max_length} characters)")
        
        # Remove HTML tags if not allowed
        if not allow_html:
            value = bleach.clean(value, tags=[], strip=True)
        else:
            # Allow only safe HTML tags
            value = bleach.clean(
                value,
                tags=['b', 'i', 'u', 'em', 'strong', 'p', 'br'],
                strip=True
            )
        
        # Check for SQL injection patterns
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError("Invalid characters detected in input")
        
        # Check for XSS patterns
        for pattern in InputSanitizer.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError("Invalid HTML/JavaScript detected in input")
        
        return value
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Sanitize and validate email
        
        Args:
            email: Email address
        
        Returns:
            Sanitized lowercase email
        
        Raises:
            ValueError: If email is invalid
        """
        email = email.strip().lower()
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        # Block temporary email services (optional)
        blocked_domains = [
            'tempmail.com', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email'
        ]
        domain = email.split('@')[1]
        if domain in blocked_domains:
            raise ValueError("Temporary email addresses are not allowed")
        
        return email
    
    @staticmethod
    def sanitize_number(
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        allow_decimal: bool = True
    ) -> float:
        """
        Sanitize and validate numeric input
        
        Args:
            value: Numeric value (int, float, str)
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_decimal: Whether to allow decimal numbers
        
        Returns:
            Validated number
        
        Raises:
            ValueError: If number is invalid or out of range
        """
        try:
            if allow_decimal:
                num = float(value)
            else:
                num = int(value)
        except (ValueError, TypeError):
            raise ValueError("Invalid number format")
        
        # Check for NaN or Infinity
        if not isinstance(num, (int, float)) or num != num:  # NaN check
            raise ValueError("Invalid number value")
        
        # Check range
        if min_value is not None and num < min_value:
            raise ValueError(f"Number must be at least {min_value}")
        
        if max_value is not None and num > max_value:
            raise ValueError(f"Number must be at most {max_value}")
        
        return num
    
    @staticmethod
    def sanitize_currency(value: Any) -> Decimal:
        """
        Sanitize currency amount (uses Decimal for precision)
        
        Args:
            value: Currency value
        
        Returns:
            Decimal value
        
        Raises:
            ValueError: If invalid currency format
        """
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError("Invalid currency format")
        
        # Check if negative
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        
        # Check reasonable range (0 to 10 crore)
        if amount > Decimal('100000000'):
            raise ValueError("Amount exceeds maximum allowed value")
        
        # Round to 2 decimal places
        return amount.quantize(Decimal('0.01'))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe file uploads
        
        Args:
            filename: Original filename
        
        Returns:
            Safe filename
        
        Raises:
            ValueError: If filename is invalid
        """
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')
        
        # Remove dangerous characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        # Check length
        if len(filename) > 255:
            raise ValueError("Filename too long")
        
        # Check extension (whitelist)
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.csv', '.xlsx', '.doc', '.docx']
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError("File type not allowed")
        
        return filename
    
    @staticmethod
    def sanitize_phone(phone: str) -> str:
        """
        Sanitize phone number (Indian format)
        
        Args:
            phone: Phone number
        
        Returns:
            Sanitized phone with +91 prefix
        
        Raises:
            ValueError: If phone is invalid
        """
        # Remove all non-digits
        phone = re.sub(r'\D', '', phone)
        
        # Check if starts with country code
        if phone.startswith('91') and len(phone) == 12:
            phone = phone[2:]  # Remove country code
        elif phone.startswith('+91'):
            phone = phone[3:]
        
        # Must be 10 digits
        if len(phone) != 10:
            raise ValueError("Phone number must be 10 digits")
        
        # Must start with 6-9 (Indian mobile numbers)
        if phone[0] not in ['6', '7', '8', '9']:
            raise ValueError("Invalid phone number")
        
        return f"+91{phone}"


# Convenience functions

def sanitize_invoice_data(data: dict) -> dict:
    """Sanitize invoice creation data"""
    sanitizer = InputSanitizer()
    
    return {
        'sale_id': int(sanitizer.sanitize_number(data['sale_id'], min_value=1)),
        'customer_name': sanitizer.sanitize_string(data.get('customer_name', ''), max_length=200),
        'amount': sanitizer.sanitize_currency(data['amount']),
        'email': sanitizer.sanitize_email(data.get('email', '')) if data.get('email') else None
    }

def sanitize_message_data(data: dict) -> dict:
    """Sanitize message data"""
    sanitizer = InputSanitizer()
    
    return {
        'subject': sanitizer.sanitize_string(data['subject'], max_length=255),
        'body': sanitizer.sanitize_string(data['body'], max_length=5000, allow_html=False),
        'recipient_id': int(sanitizer.sanitize_number(data['recipient_id'], min_value=1))
    }

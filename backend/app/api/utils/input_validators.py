"""
Input Validation & Sanitization
Security layer to prevent injection attacks and invalid data
PRIORITY 4 Implementation: Security - Input Validation
"""

import logging
import re
from typing import Any, List, Union
from decimal import Decimal

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


class InputValidator:
    """
    Comprehensive input validation for API endpoints
    Prevents XSS, SQL injection, and type mismatches
    """
    
    # Regex patterns for validation
    PATTERNS = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "phone": r"^[\d\s\-\+\(\)]{7,}$",
        "store_id": r"^[A-Za-z0-9_-]{1,50}$",
        "product_name": r"^[a-zA-Z0-9\s\-\.\(\)]{1,200}$",
        "alphanumeric": r"^[a-zA-Z0-9_-]+$",
        "numeric": r"^\d+$",
        "decimal": r"^-?\d+\.?\d*$",
    }
    
    # Dangerous characters for injection
    DANGEROUS_CHARS = {
        "'": "&#39;",
        '"': "&quot;",
        "<": "&lt;",
        ">": "&gt;",
        "&": "&amp;",
    }
    
    @staticmethod
    def validate_string(
        value: Any,
        field_name: str,
        min_length: int = 1,
        max_length: int = 1000,
        pattern: str = None,
        allow_special: bool = False
    ) -> str:
        """
        Validate string input
        
        Args:
            value: Input value
            field_name: Name of field (for error messages)
            min_length: Minimum length
            max_length: Maximum length
            pattern: Regex pattern to match
            allow_special: Allow special characters
            
        Returns:
            Validated string
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
        
        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} too short (minimum {min_length} chars)"
            )
        
        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} too long (maximum {max_length} chars)"
            )
        
        # Check for dangerous characters if not allowed
        if not allow_special:
            for char in value:
                if char in InputValidator.DANGEROUS_CHARS:
                    raise ValidationError(
                        f"{field_name} contains invalid character: {char}"
                    )
        
        # Validate against pattern
        if pattern:
            if pattern in InputValidator.PATTERNS:
                regex = InputValidator.PATTERNS[pattern]
            else:
                regex = pattern
            
            if not re.match(regex, value):
                raise ValidationError(
                    f"{field_name} format is invalid"
                )
        
        return value.strip()
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address"""
        return InputValidator.validate_string(
            email,
            "email",
            min_length=5,
            max_length=255,
            pattern="email"
        )
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validate phone number"""
        return InputValidator.validate_string(
            phone,
            "phone",
            min_length=7,
            max_length=20,
            pattern="phone"
        )
    
    @staticmethod
    def validate_store_id(store_id: str) -> str:
        """Validate store ID"""
        return InputValidator.validate_string(
            store_id,
            "store_id",
            min_length=1,
            max_length=50,
            pattern="store_id"
        )
    
    @staticmethod
    def validate_product_name(name: str) -> str:
        """Validate product name"""
        return InputValidator.validate_string(
            name,
            "product_name",
            min_length=1,
            max_length=200,
            pattern="product_name"
        )
    
    @staticmethod
    def validate_customer_name(name: str) -> str:
        """Validate customer name"""
        return InputValidator.validate_string(
            name,
            "customer_name",
            min_length=2,
            max_length=100,
            allow_special=True
        )
    
    @staticmethod
    def validate_integer(
        value: Any,
        field_name: str,
        min_value: int = None,
        max_value: int = None
    ) -> int:
        """
        Validate integer input
        
        Args:
            value: Input value
            field_name: Name of field
            min_value: Minimum value
            max_value: Maximum value
            
        Returns:
            Validated integer
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be an integer")
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(
                f"{field_name} minimum value is {min_value}"
            )
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(
                f"{field_name} maximum value is {max_value}"
            )
        
        return int_value
    
    @staticmethod
    def validate_decimal(
        value: Any,
        field_name: str,
        min_value: Decimal = None,
        max_value: Decimal = None,
        decimal_places: int = 2
    ) -> Decimal:
        """
        Validate decimal/currency input
        
        Args:
            value: Input value
            field_name: Name of field
            min_value: Minimum value
            max_value: Maximum value
            decimal_places: Maximum decimal places
            
        Returns:
            Validated Decimal
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            if isinstance(value, (int, float)):
                decimal_value = Decimal(str(value))
            else:
                decimal_value = Decimal(value)
        except:
            raise ValidationError(f"{field_name} must be a valid number")
        
        # Check if negative
        if decimal_value < 0:
            raise ValidationError(f"{field_name} cannot be negative")
        
        # Check decimal places
        if decimal_places:
            if decimal_value.as_tuple().exponent < -decimal_places:
                raise ValidationError(
                    f"{field_name} has too many decimal places (max {decimal_places})"
                )
        
        # Check min/max
        if min_value is not None and decimal_value < min_value:
            raise ValidationError(
                f"{field_name} minimum value is {min_value}"
            )
        
        if max_value is not None and decimal_value > max_value:
            raise ValidationError(
                f"{field_name} maximum value is {max_value}"
            )
        
        return decimal_value
    
    @staticmethod
    def validate_enum(
        value: Any,
        field_name: str,
        allowed_values: List[str]
    ) -> str:
        """
        Validate enum/choice field
        
        Args:
            value: Input value
            field_name: Name of field
            allowed_values: List of allowed values
            
        Returns:
            Validated value
            
        Raises:
            ValidationError: If validation fails
        """
        if value not in allowed_values:
            raise ValidationError(
                f"{field_name} must be one of: {', '.join(allowed_values)}"
            )
        
        return value
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """
        Sanitize string by escaping HTML characters
        
        Args:
            value: String to sanitize
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return value
        
        result = value
        for char, escaped in InputValidator.DANGEROUS_CHARS.items():
            result = result.replace(char, escaped)
        
        return result
    
    @staticmethod
    def validate_batch(validations: dict) -> dict:
        """
        Validate multiple fields at once
        
        Args:
            validations: Dict of {field_name: (validator_func, value)}
            
        Returns:
            Dict of validated values
            
        Raises:
            ValidationError: If any validation fails
        """
        validated = {}
        errors = []
        
        for field_name, (validator_func, value) in validations.items():
            try:
                validated[field_name] = validator_func(value)
            except ValidationError as e:
                errors.append(str(e))
        
        if errors:
            raise ValidationError(f"Validation failed: {'; '.join(errors)}")
        
        return validated


# Convenience functions for common validations
def validate_sale_request(data: dict) -> dict:
    """Validate sales transaction request"""
    return InputValidator.validate_batch({
        "store_id": (
            lambda x: InputValidator.validate_store_id(x),
            data.get("store_id")
        ),
        "customer_name": (
            lambda x: InputValidator.validate_customer_name(x),
            data.get("customer_name")
        ),
        "total_amount": (
            lambda x: InputValidator.validate_decimal(x, "total_amount", Decimal("0.01"), Decimal("999999.99")),
            data.get("total_amount")
        ),
        "payment_method": (
            lambda x: InputValidator.validate_enum(x, "payment_method", ["CASH", "CARD", "CHEQUE", "UPI"]),
            data.get("payment_method")
        ),
    })


def validate_inventory_request(data: dict) -> dict:
    """Validate inventory update request"""
    return InputValidator.validate_batch({
        "store_id": (
            lambda x: InputValidator.validate_store_id(x),
            data.get("store_id")
        ),
        "product_name": (
            lambda x: InputValidator.validate_product_name(x),
            data.get("product_name")
        ),
        "quantity": (
            lambda x: InputValidator.validate_integer(x, "quantity", 0, 1000000),
            data.get("quantity")
        ),
    })


def validate_customer_request(data: dict) -> dict:
    """Validate customer request"""
    return InputValidator.validate_batch({
        "name": (
            lambda x: InputValidator.validate_customer_name(x),
            data.get("name")
        ),
        "email": (
            lambda x: InputValidator.validate_email(x),
            data.get("email")
        ),
        "phone": (
            lambda x: InputValidator.validate_phone(x),
            data.get("phone")
        ),
    })


if __name__ == "__main__":
    print("Testing Input Validators")
    print("-" * 60)
    
    # Test 1: Valid email
    try:
        email = InputValidator.validate_email("test@example.com")
        print(f"✓ Valid email: {email}")
    except ValidationError as e:
        print(f"✗ Email validation failed: {e}")
    
    # Test 2: Invalid email
    try:
        email = InputValidator.validate_email("invalid-email")
        print(f"✓ Invalid email accepted (should not happen)")
    except ValidationError as e:
        print(f"✓ Invalid email rejected: {e}")
    
    # Test 3: Valid store ID
    try:
        store_id = InputValidator.validate_store_id("STORE_001")
        print(f"✓ Valid store ID: {store_id}")
    except ValidationError as e:
        print(f"✗ Store ID validation failed: {e}")
    
    # Test 4: Dangerous characters
    try:
        name = InputValidator.validate_string("<script>alert('xss')</script>", "test")
        print(f"✗ Dangerous characters accepted (should not happen)")
    except ValidationError as e:
        print(f"✓ Dangerous characters rejected: {e}")
    
    # Test 5: Valid amount
    try:
        amount = InputValidator.validate_decimal("1000.50", "amount", Decimal("0.01"), Decimal("999999.99"))
        print(f"✓ Valid amount: {amount}")
    except ValidationError as e:
        print(f"✗ Amount validation failed: {e}")
    
    # Test 6: Batch validation
    try:
        result = validate_sale_request({
            "store_id": "STORE_001",
            "customer_name": "John Doe",
            "total_amount": "1500.00",
            "payment_method": "CARD"
        })
        print(f"✓ Sale request validated: {len(result)} fields")
    except ValidationError as e:
        print(f"✗ Sale validation failed: {e}")
    
    print("-" * 60)
    print("✅ Input validation tests complete")

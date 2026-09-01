"""
Input Validation & Sanitization
Prevents SQL injection, XSS, and invalid data
"""

import re
import logging
from typing import Any, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error"""
    pass


class ValidationType(str, Enum):
    """Types of validation"""
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    SKU = "sku"
    AMOUNT = "amount"
    PERCENTAGE = "percentage"
    PIN = "pin"
    GSTIN = "gstin"
    AADHAR = "aadhar"
    URL = "url"


class InputValidator:
    """Validate and sanitize user inputs"""
    
    # Regex patterns
    PATTERNS = {
        ValidationType.EMAIL: r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        ValidationType.PHONE: r'^\+?1?\d{9,15}$',
        ValidationType.PIN: r'^\d{4,6}$',
        ValidationType.GSTIN: r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{3}$',
        ValidationType.AADHAR: r'^\d{12}$',
        ValidationType.SKU: r'^[A-Z0-9]{3,20}$',
        ValidationType.URL: r'^https?://[^\s/$.?#].[^\s]*$',
    }
    
    # Forbidden SQL keywords (basic XSS/injection check)
    SQL_KEYWORDS = {
        'DROP', 'DELETE', 'TRUNCATE', 'INSERT', 'UPDATE',
        'SELECT', 'EXEC', 'EXECUTE', 'UNION', 'ALTER'
    }
    
    # XSS patterns to block
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                 # JavaScript protocol
        r'on\w+\s*=',                   # Event handlers (onclick, etc)
        r'<iframe[^>]*>',               # Iframe tags
        r'<object[^>]*>',               # Object tags
    ]
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email address to validate
        
        Returns:
            True if valid
        
        Raises:
            ValidationError if invalid
        """
        email = email.strip().lower()
        
        # Length check
        if len(email) > 254:
            raise ValidationError("Email too long (max 254 characters)")
        
        # Pattern check
        if not re.match(InputValidator.PATTERNS[ValidationType.EMAIL], email):
            raise ValidationError(f"Invalid email format: {email}")
        
        return True
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Validate phone number (Indian format)
        
        Args:
            phone: Phone number to validate
        
        Returns:
            True if valid
        
        Raises:
            ValidationError if invalid
        """
        phone = re.sub(r'[^\d+]', '', phone)
        
        if not re.match(InputValidator.PATTERNS[ValidationType.PHONE], phone):
            raise ValidationError(f"Invalid phone format: {phone}")
        
        return True
    
    @staticmethod
    def validate_name(name: str, field_name: str = "Name", max_length: int = 100) -> bool:
        """
        Validate name field (no SQL/XSS injection)
        
        Args:
            name: Name to validate
            field_name: Name of field (for error message)
            max_length: Maximum length allowed
        
        Returns:
            True if valid
        
        Raises:
            ValidationError if invalid
        """
        name = name.strip()
        
        # Length check
        if len(name) == 0:
            raise ValidationError(f"{field_name} cannot be empty")
        
        if len(name) > max_length:
            raise ValidationError(f"{field_name} too long (max {max_length} characters)")
        
        # Check for XSS patterns
        if InputValidator._contains_xss(name):
            raise ValidationError(f"{field_name} contains invalid characters")
        
        # Allow letters, numbers, spaces, common punctuation (-, ', etc)
        if not re.match(r"^[a-zA-Z0-9\s\-'.,&@()]*$", name):
            raise ValidationError(f"{field_name} contains invalid characters")
        
        return True
    
    @staticmethod
    def validate_amount(amount: Any, field_name: str = "Amount", max_value: float = 10000000) -> float:
        """
        Validate numeric amount (currency)
        
        Args:
            amount: Amount to validate
            field_name: Name of field (for error message)
            max_value: Maximum allowed amount
        
        Returns:
            Validated float amount
        
        Raises:
            ValidationError if invalid
        """
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a number")
        
        if amount < 0:
            raise ValidationError(f"{field_name} cannot be negative")
        
        if amount > max_value:
            raise ValidationError(f"{field_name} exceeds maximum (max: ₹{max_value:,.2f})")
        
        # Check decimal places (currency: max 2)
        if len(str(amount).split('.')[-1]) > 2:
            raise ValidationError(f"{field_name} cannot have more than 2 decimal places")
        
        return round(amount, 2)
    
    @staticmethod
    def validate_percentage(percentage: Any, field_name: str = "Percentage") -> float:
        """
        Validate percentage (0-100)
        
        Args:
            percentage: Percentage to validate
            field_name: Name of field
        
        Returns:
            Validated percentage
        
        Raises:
            ValidationError if invalid
        """
        try:
            percentage = float(percentage)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a number")
        
        if percentage < 0 or percentage > 100:
            raise ValidationError(f"{field_name} must be between 0 and 100")
        
        return percentage
    
    @staticmethod
    def validate_pin(pin: str) -> bool:
        """
        Validate PIN (4-6 digits)
        
        Args:
            pin: PIN to validate
        
        Returns:
            True if valid
        
        Raises:
            ValidationError if invalid
        """
        if not re.match(InputValidator.PATTERNS[ValidationType.PIN], pin):
            raise ValidationError("PIN must be 4-6 digits")
        
        return True
    
    @staticmethod
    def validate_gstin(gstin: str) -> bool:
        """
        Validate GST Identification Number (Indian)
        
        Args:
            gstin: GSTIN to validate
        
        Returns:
            True if valid
        
        Raises:
            ValidationError if invalid
        """
        gstin = gstin.strip().upper()
        
        if not re.match(InputValidator.PATTERNS[ValidationType.GSTIN], gstin):
            raise ValidationError(f"Invalid GSTIN format: {gstin}")
        
        return True
    
    @staticmethod
    def validate_custom(value: str, pattern: str, field_name: str = "Field") -> bool:
        """
        Validate using custom regex pattern
        
        Args:
            value: Value to validate
            pattern: Regex pattern
            field_name: Field name for error message
        
        Returns:
            True if valid
        
        Raises:
            ValidationError if invalid
        """
        value = str(value).strip()
        
        if not re.match(pattern, value):
            raise ValidationError(f"{field_name} format is invalid")
        
        return True
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 500) -> str:
        """
        Sanitize string: remove XSS patterns and limit length
        
        Args:
            value: String to sanitize
            max_length: Maximum length
        
        Returns:
            Sanitized string
        """
        value = str(value).strip()
        
        # Remove XSS patterns
        for pattern in InputValidator.XSS_PATTERNS:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
        
        # Limit length
        value = value[:max_length]
        
        return value
    
    @staticmethod
    def validate_dict_fields(data: Dict[str, Any], schema: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Validate dictionary against schema
        
        Args:
            data: Dictionary to validate
            schema: Validation schema with field names and validation rules
                   Example:
                   {
                       'email': {'type': 'email', 'required': True},
                       'amount': {'type': 'amount', 'required': True, 'max': 100000},
                       'name': {'type': 'name', 'required': True}
                   }
        
        Returns:
            Validated dictionary
        
        Raises:
            ValidationError if any field invalid
        """
        validated = {}
        
        for field_name, rules in schema.items():
            value = data.get(field_name)
            field_type = rules.get('type')
            required = rules.get('required', False)
            
            # Check required
            if required and not value:
                raise ValidationError(f"{field_name} is required")
            
            if not value:
                continue
            
            # Validate based on type
            try:
                if field_type == ValidationType.EMAIL:
                    InputValidator.validate_email(value)
                    validated[field_name] = value.lower()
                
                elif field_type == ValidationType.PHONE:
                    InputValidator.validate_phone(value)
                    validated[field_name] = re.sub(r'[^\d+]', '', value)
                
                elif field_type == ValidationType.NAME:
                    InputValidator.validate_name(value, field_name)
                    validated[field_name] = value
                
                elif field_type == ValidationType.AMOUNT:
                    max_val = rules.get('max', 10000000)
                    validated[field_name] = InputValidator.validate_amount(value, field_name, max_val)
                
                elif field_type == ValidationType.PERCENTAGE:
                    validated[field_name] = InputValidator.validate_percentage(value, field_name)
                
                elif field_type == ValidationType.PIN:
                    InputValidator.validate_pin(value)
                    validated[field_name] = value
                
                elif field_type == ValidationType.GSTIN:
                    InputValidator.validate_gstin(value)
                    validated[field_name] = value.upper()
                
                else:
                    validated[field_name] = InputValidator.sanitize_string(value)
            
            except ValidationError as e:
                raise ValidationError(str(e))
        
        return validated
    
    @staticmethod
    def _contains_xss(value: str) -> bool:
        """Check if string contains XSS patterns"""
        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, value, flags=re.IGNORECASE | re.DOTALL):
                return True
        return False


# Export validator
validator = InputValidator()

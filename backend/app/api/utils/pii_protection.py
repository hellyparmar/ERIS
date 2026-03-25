"""
PII Protection and GDPR Compliance Module
Handles sensitive data classification, encryption, and anonymization
"""

import hashlib
import hmac
import base64
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class DataClassification:
    """Data sensitivity classification"""
    field_name: str
    classification_level: str  # 'public', 'internal', 'confidential', 'restricted'
    is_pii: bool
    is_phi: bool  # Protected Health Information
    requires_encryption: bool
    requires_audit: bool
    retention_days: Optional[int]


class PIIClassifier:
    """
    Classify data fields based on sensitivity
    GDPR/DPDPA compliance
    """
    
    # Field classification rules
    SENSITIVE_FIELDS = {
        # PII Fields
        'customers': {
            'email': DataClassification('email', 'restricted', True, False, True, True, 2555),  # 7 years
            'phone': DataClassification('phone', 'restricted', True, False, True, True, 2555),
            'address': DataClassification('address', 'confidential', True, False, True, True, 2555),
            'gstin': DataClassification('gstin', 'confidential', True, False, False, True, 2555),
            'pan_number': DataClassification('pan_number', 'restricted', True, False, True, True, 2555),
            'aadhaar_number': DataClassification('aadhaar_number', 'restricted', True, False, True, True, 2555),
            'customer_name': DataClassification('customer_name', 'confidential', True, False, False, True, 2555),
            'date_of_birth': DataClassification('date_of_birth', 'confidential', True, False, False, True, 2555),
        },
        'sales': {
            'customer_id': DataClassification('customer_id', 'internal', True, False, False, True, None),  # Indirect PII
        },
        'employees': {
            'employee_email': DataClassification('employee_email', 'restricted', True, False, True, True, 3650),
            'employee_phone': DataClassification('employee_phone', 'restricted', True, False, True, True, 3650),
            'salary': DataClassification('salary', 'restricted', False, False, True, True, 3650),
            'bank_account': DataClassification('bank_account', 'restricted', True, False, True, True, 3650),
        }
    }
    
   
 @staticmethod
    def classify_field(table: str, field: str) -> DataClassification:
        """Get classification for a field"""
        if table in PIIClassifier.SENSITIVE_FIELDS:
            if field in PIIClassifier.SENSITIVE_FIELDS[table]:
                return PIIClassifier.SENSITIVE_FIELDS[table][field]
        
        # Default: public, non-sensitive
        return DataClassification(
            field_name=field,
            classification_level='public',
            is_pii=False,
            is_phi=False,
            requires_encryption=False,
            requires_audit=False,
            retention_days=None
        )
    
    @staticmethod
    def get_pii_fields(table: str) -> List[str]:
        """Get all PII fields for a table"""
        if table not in PIIClassifier.SENSITIVE_FIELDS:
            return []
        
        return [
            field for field, classification in PIIClassifier.SENSITIVE_FIELDS[table].items()
            if classification.is_pii
        ]


class PIIProtection:
    """
    PII protection utilities
    Encryption, anonymization, and secure handling
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize PII protection
        
        Args:
            encryption_key: Fernet encryption key (32 bytes, base64-encoded)
                           If None, generates new key (NOT FOR PRODUCTION!)
        """
        if encryption_key is None:
            # Generate new key (WARNING: Only for testing!)
            encryption_key = Fernet.generate_key()
            logger.warning("Generated new encryption key. In production, use secure key management!")
        
        self.fernet = Fernet(encryption_key)
        self.encryption_key = encryption_key
    
    def encrypt_field(self, value: Any, field_name: str) -> str:
        """
        Encrypt sensitive field
        
        Args:
            value: Value to encrypt
            field_name: Field name
        
        Returns:
            Encrypted value (base64 string)
        """
        if value is None:
            return None
        
        # Convert to string
        value_str = str(value)
        
        # Encrypt
        encrypted = self.fernet.encrypt(value_str.encode())
        
        # Return as base64 string
        return encrypted.decode()
    
    def decrypt_field(self, encrypted_value: str, field_name: str) -> str:
        """
        Decrypt sensitive field
        
        Args:
            encrypted_value: Encrypted value
            field_name: Field name
        
        Returns:
            Decrypted value
        """
        if encrypted_value is None:
            return None
        
        # Decrypt
        decrypted = self.fernet.decrypt(encrypted_value.encode())
        
        return decrypted.decode()
    
    @staticmethod
    def anonymize_for_analytics(data: Dict[str, Any], table: str = 'customers') -> Dict[str, Any]:
        """
        Anonymize PII before sending to analytics
        
        Args:
            data: Data dictionary
            table: Table name
        
        Returns:
            Anonymized data
        """
        anonymized = data.copy()
        
        pii_fields = PIIClassifier.get_pii_fields(table)
        
        for field in pii_fields:
            if field in anonymized:
                if field == 'customer_id':
                    # Hash customer_id for analytics (preserve uniqueness)
                    anonymized[field] = PIIProtection.hash_pii(anonymized[field])
                elif field in ['email', 'phone', 'address', 'customer_name']:
                    # Remove entirely for analytics
                    anonymized[field] = None
                elif field in ['pan_number', 'aadhaar_number', 'gstin']:
                    # Remove entirely (highly sensitive)
                    anonymized[field] = None
        
        return anonymized
    
    @staticmethod
    def hash_pii(value: Any, salt: str = "rdios_analytics_salt") -> str:
        """
        Hash PII for analytics (one-way, deterministic)
        
        Args:
            value: Value to hash
            salt: Salt for hashing
        
        Returns:
            SHA-256 hash
        """
        if value is None:
            return None
        
        value_str = str(value)
        salted = f"{salt}:{value_str}"
        
        return hashlib.sha256(salted.encode()).hexdigest()[:16]  # First 16 chars
    
    @staticmethod
    def mask_pii(value: str, field_type: str) -> str:
        """
        Mask PII for display (e.g., in logs, UI)
        
        Args:
            value: Value to mask
            field_type: Type of field ('email', 'phone', 'pan', etc.)
        
        Returns:
            Masked value
        """
        if value is None:
            return None
        
        if field_type == 'email':
            # user@example.com → u***@example.com
            parts = value.split('@')
            if len(parts) == 2:
                return f"{parts[0][0]}***@{parts[1]}"
            return "***@***"
        
        elif field_type == 'phone':
            # +91-9876543210 → +91-***43210
            if len(value) > 5:
                return f"{value[:-5]}***{value[-2:]}"
            return "***"
        
        elif field_type in ['pan', 'aadhaar']:
            # ABCDE1234F → ABC***234F
            if len(value) > 6:
                return f"{value[:3]}***{value[-3:]}"
            return "***"
        
        else:
            # Generic: Show first 2 and last 2 chars
            if len(value) > 4:
                return f"{value[:2]}***{value[-2:]}"
            return "***"
    
    def encrypt_at_rest(self, data: Dict[str, Any], table: str) -> Dict[str, Any]:
        """
        Encrypt sensitive fields before database storage
        
        Args:
            data: Data dictionary
            table: Table name
        
        Returns:
            Data with encrypted fields
        """
        encrypted_data = data.copy()
        
        if table not in PIIClassifier.SENSITIVE_FIELDS:
            return encrypted_data
        
        for field, classification in PIIClassifier.SENSITIVE_FIELDS[table].items():
            if classification.requires_encryption and field in encrypted_data:
                if encrypted_data[field] is not None:
                    encrypted_data[field] = self.encrypt_field(encrypted_data[field], field)
        
        return encrypted_data
    
    def decrypt_for_authorized_use(self, data: Dict[str, Any], table: str) -> Dict[str, Any]:
        """
        Decrypt fields for authorized use
        
        Args:
            data: Encrypted data
            table: Table name
        
        Returns:
            Decrypted data
        """
        decrypted_data = data.copy()
        
        if table not in PIIClassifier.SENSITIVE_FIELDS:
            return decrypted_data
        
        for field, classification in PIIClassifier.SENSITIVE_FIELDS[table].items():
            if classification.requires_encryption and field in decrypted_data:
                if decrypted_data[field] is not None:
                    try:
                        decrypted_data[field] = self.decrypt_field(decrypted_data[field], field)
                    except Exception as e:
                        logger.error(f"Failed to decrypt field {field}: {e}")
                        decrypted_data[field] = None
        
        return decrypted_data


class DataRetentionPolicy:
    """
    GDPR/DPDPA data retention compliance
    """
    
    @staticmethod
    def get_retention_period(table: str, field: str) -> Optional[int]:
        """Get retention period in days"""
        classification = PIIClassifier.classify_field(table, field)
        return classification.retention_days
    
    @staticmethod
    def should_delete(created_at: datetime, table: str, field: str) -> bool:
        """Check if data should be deleted based on retention policy"""
        retention_days = DataRetentionPolicy.get_retention_period(table, field)
        
        if retention_days is None:
            return False  # No retention limit
        
        expiry_date = created_at + timedelta(days=retention_days)
        return datetime.now() > expiry_date
    
    @staticmethod
    def get_deletion_candidates(table: str) -> List[str]:
        """
        Get SQL query to find records past retention period
        
        Args:
            table: Table name
        
        Returns:
            SQL query
        """
        pii_fields = PIIClassifier.get_pii_fields(table)
        
        if not pii_fields:
            return f"-- No PII fields in {table}"
        
        # Get shortest retention period
        retention_days = min(
            PIIClassifier.classify_field(table, field).retention_days or float('inf')
            for field in pii_fields
        )
        
        if retention_days == float('inf'):
            return f"-- No retention policy for {table}"
        
        return f"""
        -- Find records past retention period for {table}
        SELECT id, created_at
        FROM {table}
        WHERE created_at < NOW() - INTERVAL '{retention_days} days';
        """


# Example usage and integration
class GDPRCompliantDataHandler:
    """
    GDPR-compliant data handler for R-DIOS
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        self.pii_protection = PIIProtection(encryption_key)
    
    def store_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store customer data with PII protection
        
        Flow:
        1. Classify fields
        2. Encrypt sensitive fields
        3. Store in database
        4. Log access in audit trail
        """
        # Encrypt sensitive fields
        encrypted_data = self.pii_protection.encrypt_at_rest(customer_data, 'customers')
        
        # In production: Insert into database
        # db.customers.insert(encrypted_data)
        
        # Log access
        # audit_log.log_access('create', 'customer', encrypted_data.get('id'))
        
        return encrypted_data
    
    def retrieve_customer(self, customer_id: int, user_id: int) -> Dict[str, Any]:
        """
        Retrieve customer data (for authorized users)
        
        Flow:
        1. Check user authorization
        2. Retrieve encrypted data
        3. Decrypt for authorized use
        4. Log access in audit trail
        """
        # In production: Check authorization
        # if not user_has_permission(user_id, 'view_customer_pii'): raise Forbidden
        
        # Retrieve encrypted data from database
        # encrypted_data = db.customers.get(customer_id)
        
        # For demo:
        encrypted_data = {'id': customer_id, 'email': 'encrypted_value'}
        
        # Decrypt
        decrypted_data = self.pii_protection.decrypt_for_authorized_use(encrypted_data, 'customers')
        
        # Log access
        # audit_log.log_access('read', 'customer', customer_id, user_id=user_id)
        
        return decrypted_data
    
    def anonymize_for_analytics_export(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare customer data for analytics (GDPR-safe)
        
        Use case: Data scientist needs sales data but shouldn't see PII
        """
        return PIIProtection.anonymize_for_analytics(customer_data, 'customers')


if __name__ == "__main__":
    # Demo
    print("PII Protection Demo\n" + "=" * 60)
    
    # Example customer data
    customer = {
        'id': 1,
        'customer_name': 'Rajesh Kumar',
        'email': 'rajesh.kumar@example.com',
        'phone': '+91-9876543210',
        'address': '123 MG Road, Bangalore',
        'pan_number': 'ABCDE1234F',
        'gstin': '29ABCDE1234F1Z5'
    }
    
    print("\n1. Original Customer Data:")
    print(customer)
    
    # Initialize PII protection
    pii_handler = GDPRCompliantDataHandler()
    
    # Store (encrypt)
    print("\n2. Encrypted for Storage:")
    encrypted = pii_handler.store_customer(customer)
    print({k: v if k == 'id' else 'ENCRYPTED' for k, v in encrypted.items()})
    
    # Anonymize for analytics
    print("\n3. Anonymized for Analytics:")
    anonymized = pii_handler.anonymize_for_analytics_export(customer)
    print(anonymized)
    
    # Mask for logs
    print("\n4. Masked for Display/Logs:")
    print(f"Email: {PIIProtection.mask_pii(customer['email'], 'email')}")
    print(f"Phone: {PIIProtection.mask_pii(customer['phone'], 'phone')}")
    print(f"PAN: {PIIProtection.mask_pii(customer['pan_number'], 'pan')}")
    
    # Check retention
    print("\n5. Data Retention Check:")
    created_at = datetime.now() - timedelta(days=3000)  # ~8 years ago
    should_delete = DataRetentionPolicy.should_delete(created_at, 'customers', 'email')
    print(f"Created: {created_at.date()}")
    print(f"Should delete: {should_delete} (7-year retention)")

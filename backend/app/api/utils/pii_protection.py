"""
PII (Personally Identifiable Information) protection utilities.
GDPR Article 5 and DPDPA Section 4 compliant masking, redaction,
and pseudonymisation helpers for customer and employee data.
"""
import re
import hashlib
from typing import Optional, List


# Fields considered PII under GDPR / DPDPA for this application
PII_FIELDS: List[str] = [
    "name", "email", "phone", "mobile",
    "aadhaar", "pan", "address", "dob",
]


def mask_email(email: str) -> str:
    """Mask email address: john.doe@example.com → j*******@example.com"""
    if not email or "@" not in email:
        return "***@***.***"
    local, domain = email.split("@", 1)
    masked_local = local[0] + "*" * max(len(local) - 1, 3)
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone number, preserving last 4 digits: +91-9876543210 → XXXXXX3210"""
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 4:
        return "X" * len(digits)
    return "X" * (len(digits) - 4) + digits[-4:]


def mask_aadhaar(aadhaar: str) -> str:
    """Mask 12-digit Aadhaar, preserving last 4: 1234 5678 9012 → XXXX-XXXX-9012"""
    digits = re.sub(r"\D", "", aadhaar)
    if len(digits) != 12:
        return "XXXX-XXXX-XXXX"
    return f"XXXX-XXXX-{digits[-4:]}"


def mask_pan(pan: str) -> str:
    """Mask PAN card: ABCDE1234F → XXXXX1234X"""
    pan = pan.upper().strip()
    if len(pan) != 10:
        return "XXXXXXXXXX"
    return "X" * 5 + pan[5:9] + "X"


def hash_identifier(value: str, salt: str = "") -> str:
    """One-way SHA-256 hash of a PII field for pseudonymisation."""
    return hashlib.sha256(f"{salt}{value}".encode()).hexdigest()[:16]


def redact_dict(data: dict, fields: Optional[List[str]] = None) -> dict:
    """Return a shallow copy of *data* with all PII fields replaced by '***REDACTED***'."""
    target_fields = [f.lower() for f in (fields or PII_FIELDS)]
    return {
        k: ("***REDACTED***" if k.lower() in target_fields else v)
        for k, v in data.items()
    }


def anonymise_customer(customer: dict) -> dict:
    """
    Return an anonymised copy of a customer record.
    Replaces PII with masked equivalents suitable for analytics export.
    """
    anon = dict(customer)
    if "email" in anon and anon["email"]:
        anon["email"] = mask_email(anon["email"])
    if "phone" in anon and anon["phone"]:
        anon["phone"] = mask_phone(anon["phone"])
    if "mobile" in anon and anon["mobile"]:
        anon["mobile"] = mask_phone(anon["mobile"])
    if "aadhaar" in anon and anon["aadhaar"]:
        anon["aadhaar"] = mask_aadhaar(anon["aadhaar"])
    if "pan" in anon and anon["pan"]:
        anon["pan"] = mask_pan(anon["pan"])
    if "name" in anon and anon["name"]:
        anon["name"] = f"Customer_{hash_identifier(anon['name'])}"
    return anon


def is_pii_field(field_name: str) -> bool:
    """Return True if *field_name* is classified as PII under this application's policy."""
    return field_name.lower() in PII_FIELDS


def strip_pii_from_log_record(record: dict) -> dict:
    """
    Recursively walk a log record dict and redact any PII fields.
    Safe to call on arbitrary nested structures.
    """
    result = {}
    for key, value in record.items():
        if is_pii_field(key):
            result[key] = "***REDACTED***"
        elif isinstance(value, dict):
            result[key] = strip_pii_from_log_record(value)
        elif isinstance(value, list):
            result[key] = [
                strip_pii_from_log_record(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result

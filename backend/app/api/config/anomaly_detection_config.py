"""
Configuration for Anomaly Detection System
Environment variables and settings.
"""

import os
from typing import Optional
from pydantic import BaseSettings


class AnomalyDetectionSettings(BaseSettings):
    """
    Anomaly Detection Configuration
    
    Set these environment variables:
    - ANOMALY_DETECTION_ENABLED
    - ISOLATION_FOREST_CONTAMINATION
    - DISCOUNT_ALERT_THRESHOLD
    - GHOST_INVENTORY_DAYS
    - WHATSAPP_PHONE_NUMBER_ID
    - WHATSAPP_ACCESS_TOKEN
    - WHATSAPP_ADMIN_PHONE
    """
    
    # ========================================================================
    # FEATURE TOGGLES
    # ========================================================================
    
    ANOMALY_DETECTION_ENABLED: bool = os.getenv(
        'ANOMALY_DETECTION_ENABLED', 'true'
    ).lower() == 'true'
    
    # ========================================================================
    # ISOLATION FOREST PARAMETERS
    # ========================================================================
    
    ISOLATION_FOREST_CONTAMINATION: float = float(
        os.getenv('ISOLATION_FOREST_CONTAMINATION', '0.05')
    )
    """Expected proportion of anomalies (0.01-0.5)"""
    
    ISOLATION_FOREST_N_ESTIMATORS: int = int(
        os.getenv('ISOLATION_FOREST_N_ESTIMATORS', '100')
    )
    """Number of decision trees"""
    
    ISOLATION_FOREST_RANDOM_STATE: int = int(
        os.getenv('ISOLATION_FOREST_RANDOM_STATE', '42')
    )
    """Random seed for reproducibility"""
    
    # ========================================================================
    # DISCOUNT FRAUD DETECTION
    # ========================================================================
    
    DISCOUNT_ALERT_THRESHOLD: float = float(
        os.getenv('DISCOUNT_ALERT_THRESHOLD', '50.0')
    )
    """Alert if discount percentage > threshold"""
    
    DISCOUNT_LOOKBACK_DAYS: int = int(
        os.getenv('DISCOUNT_LOOKBACK_DAYS', '30')
    )
    """Days of discount history to analyze"""
    
    # ========================================================================
    # SALES DROP DETECTION
    # ========================================================================
    
    SALES_DROP_LOOKBACK_DAYS: int = int(
        os.getenv('SALES_DROP_LOOKBACK_DAYS', '28')
    )
    """Days for rolling average (4 weeks)"""
    
    SALES_DROP_THRESHOLD_SIGMA: float = float(
        os.getenv('SALES_DROP_THRESHOLD_SIGMA', '2.0')
    )
    """Alert if drop > N standard deviations from mean"""
    
    # ========================================================================
    # GHOST INVENTORY DETECTION
    # ========================================================================
    
    GHOST_INVENTORY_DAYS: int = int(
        os.getenv('GHOST_INVENTORY_DAYS', '30')
    )
    """Alert if no sales for N days"""
    
    GHOST_INVENTORY_MIN_STOCK: int = int(
        os.getenv('GHOST_INVENTORY_MIN_STOCK', '50')
    )
    """Only alert if stock level > minimum"""
    
    # ========================================================================
    # SCHEDULER CONFIGURATION
    # ========================================================================
    
    ANOMALY_DETECTION_INTERVAL_HOURS: int = int(
        os.getenv('ANOMALY_DETECTION_INTERVAL_HOURS', '1')
    )
    """Frequency of anomaly detection scans"""
    
    BATCH_NOTIFICATION_INTERVAL_MINUTES: int = int(
        os.getenv('BATCH_NOTIFICATION_INTERVAL_MINUTES', '5')
    )
    """Frequency of WhatsApp batch sends"""
    
    # ========================================================================
    # WHATSAPP NOTIFICATION SETTINGS
    # ========================================================================
    
    WHATSAPP_ENABLED: bool = os.getenv(
        'WHATSAPP_ENABLED', 'true'
    ).lower() == 'true'
    
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv(
        'WHATSAPP_PHONE_NUMBER_ID',
        'default_phone_id'
    )
    """WhatsApp Business API Phone Number ID"""
    
    WHATSAPP_ACCESS_TOKEN: str = os.getenv(
        'WHATSAPP_ACCESS_TOKEN',
        'default_token'
    )
    """WhatsApp Business API Access Token"""
    
    WHATSAPP_ADMIN_PHONE: str = os.getenv(
        'WHATSAPP_ADMIN_PHONE',
        '+919999999999'
    )
    """Default admin phone for alerts (+country_code format)"""
    
    WHATSAPP_BATCH_WINDOW_SECONDS: int = int(
        os.getenv('WHATSAPP_BATCH_WINDOW_SECONDS', '300')
    )
    """Time window for batching non-critical alerts (5 minutes)"""
    
    WHATSAPP_MAX_BATCH_SIZE: int = int(
        os.getenv('WHATSAPP_MAX_BATCH_SIZE', '20')
    )
    """Maximum messages per batch"""
    
    WHATSAPP_ENABLE_BATCHING: bool = os.getenv(
        'WHATSAPP_ENABLE_BATCHING', 'true'
    ).lower() == 'true'
    """Enable smart batching for non-critical alerts"""
    
    # ========================================================================
    # ALERT SEVERITY THRESHOLDS
    # ========================================================================
    
    CRITICAL_DISCOUNT_PERCENTAGE: float = float(
        os.getenv('CRITICAL_DISCOUNT_PERCENTAGE', '75.0')
    )
    """Mark as CRITICAL if discount > threshold"""
    
    CRITICAL_SALES_DROP_PERCENTAGE: float = float(
        os.getenv('CRITICAL_SALES_DROP_PERCENTAGE', '50.0')
    )
    """Mark as CRITICAL if sales drop > threshold"""
    
    CRITICAL_GHOST_INVENTORY_STOCK: int = int(
        os.getenv('CRITICAL_GHOST_INVENTORY_STOCK', '500')
    )
    """Mark as CRITICAL if ghost inventory > threshold units"""
    
    # ========================================================================
    # LOGGING
    # ========================================================================
    
    ANOMALY_LOG_LEVEL: str = os.getenv('ANOMALY_LOG_LEVEL', 'INFO')
    """Log level for anomaly detection (DEBUG, INFO, WARNING, ERROR)"""
    
    ANOMALY_DEBUG_MODE: bool = os.getenv(
        'ANOMALY_DEBUG_MODE', 'false'
    ).lower() == 'true'
    """Enable verbose logging and dry-run mode"""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Load settings
settings = AnomalyDetectionSettings()


# ============================================================================
# ENVIRONMENT SETUP GUIDE
# ============================================================================

ENVIRONMENT_TEMPLATE = """
# ============================================================================
# ANOMALY DETECTION CONFIGURATION
# ============================================================================

# Feature Toggle
ANOMALY_DETECTION_ENABLED=true

# ============================================================================
# ISOLATION FOREST PARAMETERS
# ============================================================================

# Contamination: Expected proportion of anomalies (0.01-0.5)
# Lower = stricter (fewer false positives but misses some anomalies)
# Higher = more lenient (catches more anomalies but more false positives)
ISOLATION_FOREST_CONTAMINATION=0.05

# Number of decision trees in the forest
ISOLATION_FOREST_N_ESTIMATORS=100

# Random seed for reproducibility
ISOLATION_FOREST_RANDOM_STATE=42

# ============================================================================
# DISCOUNT FRAUD DETECTION
# ============================================================================

# Alert threshold: Alert if discount % > value
DISCOUNT_ALERT_THRESHOLD=50.0

# Historical lookback: Analyze last N days of discounts
DISCOUNT_LOOKBACK_DAYS=30

# ============================================================================
# SALES DROP DETECTION
# ============================================================================

# Rolling average window: Use 4-week (28 day) average
SALES_DROP_LOOKBACK_DAYS=28

# Threshold: Alert if drop > N standard deviations from mean
# 2.0 = 95% confidence, 3.0 = 99% confidence
SALES_DROP_THRESHOLD_SIGMA=2.0

# ============================================================================
# GHOST INVENTORY DETECTION
# ============================================================================

# Alert if product has no sales for N days
GHOST_INVENTORY_DAYS=30

# Only alert if stock level > threshold units
GHOST_INVENTORY_MIN_STOCK=50

# ============================================================================
# SCHEDULER CONFIGURATION
# ============================================================================

# Frequency of anomaly detection scans (hours)
ANOMALY_DETECTION_INTERVAL_HOURS=1

# Frequency of WhatsApp batch sends (minutes)
BATCH_NOTIFICATION_INTERVAL_MINUTES=5

# ============================================================================
# WHATSAPP NOTIFICATION SETTINGS
# ============================================================================

# Enable WhatsApp notifications
WHATSAPP_ENABLED=true

# Get these from WhatsApp Business API
# https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
WHATSAPP_ACCESS_TOKEN=your_access_token_here

# Admin phone for alerts (with country code)
WHATSAPP_ADMIN_PHONE=+919876543210

# Batching window for non-critical alerts (seconds)
WHATSAPP_BATCH_WINDOW_SECONDS=300

# Maximum messages per batch
WHATSAPP_MAX_BATCH_SIZE=20

# Enable smart batching
WHATSAPP_ENABLE_BATCHING=true

# ============================================================================
# ALERT SEVERITY THRESHOLDS
# ============================================================================

# Mark discount fraud as CRITICAL if discount % > threshold
CRITICAL_DISCOUNT_PERCENTAGE=75.0

# Mark sales drop as CRITICAL if drop % > threshold
CRITICAL_SALES_DROP_PERCENTAGE=50.0

# Mark ghost inventory as CRITICAL if stock > threshold units
CRITICAL_GHOST_INVENTORY_STOCK=500

# ============================================================================
# LOGGING
# ============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR
ANOMALY_LOG_LEVEL=INFO

# Enable debug mode (verbose logging, dry-run)
ANOMALY_DEBUG_MODE=false
"""


def print_environment_template():
    """Print environment variable template"""
    print(ENVIRONMENT_TEMPLATE)


# ============================================================================
# VALIDATION
# ============================================================================

def validate_settings():
    """Validate anomaly detection settings"""
    errors = []
    
    # Validation rules
    if not (0.01 <= settings.ISOLATION_FOREST_CONTAMINATION <= 0.5):
        errors.append("ISOLATION_FOREST_CONTAMINATION must be between 0.01 and 0.5")
    
    if settings.DISCOUNT_ALERT_THRESHOLD < 0 or settings.DISCOUNT_ALERT_THRESHOLD > 100:
        errors.append("DISCOUNT_ALERT_THRESHOLD must be between 0 and 100")
    
    if not settings.WHATSAPP_PHONE_NUMBER_ID or settings.WHATSAPP_PHONE_NUMBER_ID == 'default_phone_id':
        errors.append("WHATSAPP_PHONE_NUMBER_ID is not configured")
    
    if not settings.WHATSAPP_ACCESS_TOKEN or settings.WHATSAPP_ACCESS_TOKEN == 'default_token':
        errors.append("WHATSAPP_ACCESS_TOKEN is not configured")
    
    if not settings.WHATSAPP_ADMIN_PHONE.startswith('+'):
        errors.append("WHATSAPP_ADMIN_PHONE must include country code (e.g., +919876543210)")
    
    return errors


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("ANOMALY DETECTION CONFIGURATION")
    print("=" * 80)
    
    print("\n📋 Current Settings:")
    for key, value in settings.dict().items():
        # Hide sensitive values
        if 'TOKEN' in key or 'PHONE' in key:
            value = f"{'*' * 8}{str(value)[-4:]}"
        print(f"  {key}: {value}")
    
    print("\n\n🔍 Validation Results:")
    errors = validate_settings()
    if errors:
        print("  ❌ Errors found:")
        for error in errors:
            print(f"     - {error}")
    else:
        print("  ✅ All settings valid")
    
    print("\n\n📝 Environment Template:")
    print_environment_template()

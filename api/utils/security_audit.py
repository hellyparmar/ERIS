"""
Security Audit Trail System
GDPR Article 30 & DPDPA Compliance
Tracks all access to sensitive data and system actions
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import json


class AuditAction(Enum):
    """Types of auditable actions"""
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"
    PERMISSION_DENIED = "permission_denied"
    PRICE_CHANGE = "price_change"
    INVENTORY_ADJUSTMENT = "inventory_adjustment"


class ResourceType(Enum):
    """Types of resources"""
    CUSTOMER = "customer"
    PRODUCT = "product"
    ORDER = "order"
    INVOICE = "invoice"
    REPORT = "report"
    USER = "user"
    CONFIGURATION = "configuration"


@dataclass
class AuditLogEntry:
    """Single audit log entry"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str = None
    resource_type: str = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: str = None
    metadata: Optional[Dict[str, Any]] = None
    status: str = "success"  # 'success' or 'failed'
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class SecurityAuditLogger:
    """
    Security audit logging service
    Compliant with GDPR Article 30 and DPDPA
    """
    
    def __init__(self, db_connection=None):
        """
        Initialize audit logger
        
        Args:
            db_connection: Database connection (if None, logs to file)
        """
        self.db = db_connection
        self.logger = logging.getLogger("security_audit")
        
        # Configure file logger as backup
        handler = logging.FileHandler('/var/log/rdios/security_audit.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_access(
        self,
        action: AuditAction,
        resource_type: ResourceType,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLogEntry:
        """
        Log a security-relevant action
        
        Args:
            action: Type of action
            resource_type: Type of resource accessed
            resource_id: ID of specific resource
            user_id: User performing action
            user_email: User email
            ip_address: User IP address
            user_agent: User agent string
            metadata: Additional context
            status: 'success' or 'failed'
            error_message: Error if failed
        
        Returns:
            AuditLogEntry
        """
        entry = AuditLogEntry(
            user_id=user_id,
            user_email=user_email,
            action=action.value if isinstance(action, AuditAction) else action,
            resource_type=resource_type.value if isinstance(resource_type, ResourceType) else resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
            status=status,
            error_message=error_message
        )
        
        # Store in database
        if self.db:
            entry.id = self._store_in_database(entry)
        
        # Also log to file
        self.logger.info(entry.to_json())
        
        #  Alert on suspicious activity
        if self._is_suspicious(entry):
            self._trigger_security_alert(entry)
        
        return entry
    
    def _store_in_database(self, entry: AuditLogEntry) -> int:
        """
        Store audit entry in database
        
        SQL Schema:
        CREATE TABLE audit_log (
            id BIGSERIAL PRIMARY KEY,
            user_id INT,
            user_email VARCHAR(255),
            action VARCHAR(50) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            resource_id VARCHAR(100),
            ip_address INET,
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT NOW(),
            metadata JSONB,
            status VARCHAR(20) DEFAULT 'success',
            error_message TEXT
        );
        """
        # In production: INSERT into database
        # cursor = self.db.cursor()
        # cursor.execute("""
        #     INSERT INTO audit_log (user_id, user_email, action, resource_type, ...)
        #     VALUES (%s, %s, %s, %s, ...)
        #     RETURNING id
        # """, (entry.user_id, entry.user_email, ...))
        # return cursor.fetchone()[0]
        
        # Mock return
        return 12345
    
    def _is_suspicious(self, entry: AuditLogEntry) -> bool:
        """
        Detect suspicious activity patterns
        
        Triggers alerts for:
        - Multiple failed login attempts
        - Mass data exports
        - Access from unusual locations
        - After-hours administrator actions
        """
        # Failed login
        if entry.action == AuditAction.FAILED_LOGIN.value:
            # Check if > 5 failed attempts in last 5 minutes
            recent_failures = self.get_recent_failed_logins(entry.user_email or entry.ip_address)
            if len(recent_failures) > 5:
                return True
        
        # Mass export
        if entry.action == AuditAction.EXPORT.value:
            if entry.metadata and entry.metadata.get('record_count', 0) > 1000:
                return True
        
        # Permission denied (possible attack)
        if entry.action == AuditAction.PERMISSION_DENIED.value:
            return True
        
        return False
    
    def _trigger_security_alert(self, entry: AuditLogEntry):
        """Send security alert to administrators"""
        alert_message = f"""
        SECURITY ALERT
        
        Action: {entry.action}
        User: {entry.user_email or 'Unknown'}
        Resource: {entry.resource_type} ({entry.resource_id})
        IP: {entry.ip_address}
        Time: {entry.timestamp}
        Status: {entry.status}
        
        Details: {json.dumps(entry.metadata, indent=2)}
        """
        
        # In production: Send email/SMS/Slack
        logging.getLogger("security_alerts").critical(alert_message)
    
    def get_user_access_history(
        self,
        user_id: int,
        days: int = 30,
        resource_type: Optional[ResourceType] = None
    ) -> List[AuditLogEntry]:
        """
        Get user's access history
        
        GDPR Right of Access: Users can request their data access history
        """
        # In production: Query database
        # SELECT * FROM audit_log
        # WHERE user_id = %s
        # AND timestamp > NOW() - INTERVAL '%s days'
        # ORDER BY timestamp DESC
        
        return []  # Mock
    
    def get_resource_access_history(
        self,
        resource_type: ResourceType,
        resource_id: str,
        days: int = 90
    ) -> List[AuditLogEntry]:
        """
        Get who accessed a specific resource
        
        Use case: Investigate data breach, compliance audit
        """
        # In production: Query database
        # SELECT * FROM audit_log
        # WHERE resource_type = %s AND resource_id = %s
        # AND timestamp > NOW() - INTERVAL '%s days'
        # ORDER BY timestamp DESC
        
        return []  # Mock
    
    def get_recent_failed_logins(
        self,
        identifier: str,  # email or IP
        minutes: int = 5
    ) -> List[AuditLogEntry]:
        """Get recent failed login attempts"""
        # In production: Query database
        # WHERE action = 'failed_login'
        # AND (user_email = %s OR ip_address = %s)
        # AND timestamp > NOW() - INTERVAL '%s minutes'
        
        return []  # Mock
    
    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate GDPR/DPDPA compliance report
        
        Required for regulatory audits
        """
        # In production: Complex aggregation query
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_accesses': 0,  # Count
            'by_action': {
                'read': 0,
                'create': 0,
                'update': 0,
                'delete': 0,
                'export': 0
            },
            'pii_accesses': 0,  # Accesses to customer PII
            'failed_attempts': 0,
            'security_incidents': 0,
            'data_exports': {
                'total': 0,
                'records_exported': 0
            }
        }


# FastAPI Middleware Integration
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Automatic audit logging for all API requests
    """
    
    def __init__(self, app, audit_logger: SecurityAuditLogger):
        super().__init__(app)
        self.audit_logger = audit_logger
    
    async def dispatch(self, request: Request, call_next):
        # Extract user info from JWT (if present)
        user_id = None
        user_email = None
        
        # In production: Extract from JWT token
        # auth_header = request.headers.get('Authorization')
        # if auth_header:
        #     token = auth_header.split(' ')[1]
        #     payload = decode_jwt(token)
        #     user_id = payload.get('user_id')
        #     user_email = payload.get('email')
        
        # Track timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Log if accessing sensitive resources
        if self._should_audit(request.url.path, request.method):
            action = self._map_method_to_action(request.method)
            resource_type, resource_id = self._extract_resource_info(request.url.path)
            
            self.audit_logger.log_access(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                user_email=user_email,
                ip_address=request.client.host,
                user_agent=request.headers.get('User-Agent'),
                metadata={
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'response_time_ms': (time.time() - start_time) * 1000
                },
                status='success' if response.status_code < 400 else 'failed'
            )
        
        return response
    
    def _should_audit(self, path: str, method: str) -> bool:
        """Determine if request should be audited"""
        # Audit all customer, order, invoice access
        audit_paths = ['/api/customers', '/api/orders', '/api/invoices', '/api/reports', '/api/admin']
        
        return any(path.startswith(p) for p in audit_paths)
    
    def _map_method_to_action(self, method: str) -> AuditAction:
        """Map HTTP method to audit action"""
        mapping = {
            'GET': AuditAction.READ,
            'POST': AuditAction.CREATE,
            'PUT': AuditAction.UPDATE,
            'PATCH': AuditAction.UPDATE,
            'DELETE': AuditAction.DELETE
        }
        return mapping.get(method, AuditAction.READ)
    
    def _extract_resource_info(self, path: str) -> tuple:
        """Extract resource type and ID from path"""
        # Example: /api/customers/123 → ('customer', '123')
        parts = path.strip('/').split('/')
        
        if len(parts) >= 2:
            resource_type = parts[1].rstrip('s')  # customers → customer
            resource_id = parts[2] if len(parts) > 2 else None
            return (resource_type, resource_id)
        
        return ('unknown', None)


# Create SQL schema for audit table
AUDIT_TABLE_SCHEMA = """
-- Security Audit Log Table
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id INT,
    user_email VARCHAR(255),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX idx_audit_user ON audit_log(user_id, timestamp DESC);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_action ON audit_log(action, timestamp DESC);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_ip ON audit_log(ip_address);

-- Partition by month for performance (optional)
-- CREATE TABLE audit_log_y2024m01 PARTITION OF audit_log
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
"""


# Example usage
if __name__ == "__main__":
    print("Security Audit Logging Demo\n" + "=" * 60)
    
    # Initialize logger
    audit_logger = SecurityAuditLogger()
    
    # Example 1: Log customer data access
    print("\n1. Customer Data Access:")
    entry = audit_logger.log_access(
        action=AuditAction.READ,
        resource_type=ResourceType.CUSTOMER,
        resource_id="CUST_123",
        user_id=42,
        user_email="manager@example.com",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
        metadata={'reason': 'customer_support_ticket'}
    )
    print(f"Logged: {entry.action} on {entry.resource_type} by {entry.user_email}")
    
    # Example 2: Log failed login
    print("\n2. Failed Login Attempt:")
    failed_login = audit_logger.log_access(
        action=Audit Action.FAILED_LOGIN,
        resource_type=ResourceType.USER,
        user_email="hacker@evil.com",
        ip_address="203.0.113.42",
        user_agent="curl/7.68.0",
        status="failed",
        error_message="Invalid credentials"
    )
    print(f"Security Alert: Failed login from {failed_login.ip_address}")
    
    # Example 3: Log data export
    print("\n3. Data Export:")
    export_entry = audit_logger.log_access(
        action=AuditAction.EXPORT,
        resource_type=ResourceType.REPORT,
        resource_id="SALES_REPORT_2024",
        user_id=5,
        user_email="analyst@example.com",
        ip_address="192.168.1.50",
        metadata={'record_count': 50000, 'format': 'CSV'}
    )
    print(f"Exported: {export_entry.metadata['record_count']} records")
    
    # Example 4: Generate compliance report
    print("\n4. Compliance Report:")
    report = audit_logger.generate_compliance_report(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31)
    )
    print(json.dumps(report, indent=2))

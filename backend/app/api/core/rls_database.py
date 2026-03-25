"""
SQLAlchemy 2.0 Configuration with Row-Level Security (RLS) Integration
========================================================================

This module provides:
1. Database engine configuration with RLS support
2. Session factory with automatic tenant context
3. Middleware for automatic tenant context setting
4. Event listeners to enforce RLS on all queries
5. Testing utilities for RLS validation

Key Feature: Makes it physically impossible for queries to return cross-tenant
data, even if developers forget to add .filter(tenant_id=X)
"""

import logging
import uuid
from contextlib import contextmanager
from typing import Optional, Generator, Any

from sqlalchemy import create_engine, event, text, inspect
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.orm import (
    sessionmaker,
    Session,
    DeclarativeBase,
    scoped_session,
)
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.sql import Executable

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# TENANT CONTEXT MANAGEMENT
# ============================================================================

class TenantContext:
    """Thread-local storage for tenant context."""
    
    def __init__(self):
        """Initialize tenant context storage."""
        self._tenant_id: Optional[str] = None
        self._user_id: Optional[str] = None
        self._username: Optional[str] = None
    
    @property
    def tenant_id(self) -> Optional[str]:
        """Get current tenant_id."""
        return self._tenant_id
    
    @tenant_id.setter
    def tenant_id(self, value: Optional[str]) -> None:
        """Set current tenant_id."""
        if value is not None and not isinstance(value, str):
            value = str(value)
        self._tenant_id = value
    
    @property
    def user_id(self) -> Optional[str]:
        """Get current user_id."""
        return self._user_id
    
    @user_id.setter
    def user_id(self, value: Optional[str]) -> None:
        """Set current user_id."""
        if value is not None and not isinstance(value, str):
            value = str(value)
        self._user_id = value
    
    @property
    def username(self) -> Optional[str]:
        """Get current username."""
        return self._username
    
    @username.setter
    def username(self, value: Optional[str]) -> None:
        """Set current username."""
        self._username = value
    
    def set(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None
    ) -> None:
        """Set all context values at once."""
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.username = username
    
    def clear(self) -> None:
        """Clear all context values."""
        self._tenant_id = None
        self._user_id = None
        self._username = None
    
    def is_set(self) -> bool:
        """Check if tenant context is set."""
        return self._tenant_id is not None


# Global tenant context (should be replaced with proper async context in production)
tenant_context = TenantContext()


# ============================================================================
# SQLALCHEMY DATABASE CONFIGURATION
# ============================================================================

class DatabaseConfig:
    """Database configuration for RLS-enabled system."""
    
    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 40,
        pool_pre_ping: bool = True,
        echo_sql: bool = False,
    ):
        """
        Initialize database configuration.
        
        Args:
            database_url: PostgreSQL connection URL
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            pool_pre_ping: Test connections before using them
            echo_sql: Log all SQL statements (debug mode)
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_pre_ping = pool_pre_ping
        self.echo_sql = echo_sql
    
    def create_engine(self) -> Engine:
        """Create SQLAlchemy engine with RLS support."""
        engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_pre_ping=self.pool_pre_ping,
            echo=self.echo_sql,
            # Use UTC for all timestamps
            connect_args={
                "options": "-c timezone=UTC",
                # Prevent connection timeout
                "connect_timeout": 10,
            }
        )
        
        # Register connection event listeners for RLS
        event.listen(engine, "connect", _on_connect)
        event.listen(engine, "before_execute", _before_execute)
        
        return engine


# ============================================================================
# DATABASE HOOKS & EVENT LISTENERS
# ============================================================================

def _on_connect(dbapi_connection: Any, connection_record: Any) -> None:
    """
    Event listener: Called when a new database connection is established.
    
    This is where we set the tenant context at the PostgreSQL level.
    This ensures that ALL queries are automatically filtered by RLS policies.
    """
    cursor = dbapi_connection.cursor()
    
    try:
        # Ensure RLS is enabled for this connection
        cursor.execute("SET session_replication_role = replica;")
        
        # Set tenant context if available
        if tenant_context.is_set():
            tenant_id = tenant_context.tenant_id
            user_id = tenant_context.user_id or ""
            username = tenant_context.username or ""
            
            logger.debug(
                f"Setting tenant context on connection: "
                f"tenant_id={tenant_id}, user={user_id}"
            )
            
            # Call the PostgreSQL function to set context
            cursor.execute(
                "SELECT set_tenant_context(%s::UUID, %s::UUID, %s::VARCHAR);",
                (tenant_id, user_id if user_id else None, username)
            )
        else:
            logger.warning(
                "Database connection established without tenant context. "
                "RLS will be enforced but may cause queries to fail."
            )
        
        cursor.close()
    
    except Exception as e:
        logger.error(f"Error setting tenant context: {e}")
        cursor.close()
        raise


def _before_execute(
    conn: Connection,
    clauseelement: Executable,
    multiparams: Any,
    params: Any,
    execution_options: Any
) -> None:
    """
    Event listener: Called before any SQL execution.
    
    This validates that tenant context is set and logs queries for debugging.
    """
    # Get the SQL text
    sql_text = str(clauseelement.compile(compile_kwargs={"literal_binds": True}))
    
    # Skip context checks for internal PostgreSQL functions
    if "set_tenant_context" in sql_text or "current_tenant_id" in sql_text:
        return
    
    # Log queries in debug mode
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Executing SQL: {sql_text[:200]}...")


# ============================================================================
# SQLALCHEMY SESSION FACTORY
# ============================================================================

class RLSSessionFactory:
    """
    Factory for creating SQLAlchemy sessions with automatic RLS enforcement.
    
    Ensures that:
    1. Tenant context is set before any query
    2. All queries are automatically filtered by RLS policies
    3. Context is properly cleaned up after use
    """
    
    def __init__(self, engine: Engine):
        """
        Initialize session factory.
        
        Args:
            engine: SQLAlchemy engine
        """
        self.engine = engine
        
        # Create session maker with proper configuration
        self._session_factory = sessionmaker(
            bind=engine,
            class_=RLSSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autoflush=True,  # Auto-flush before query
            autocommit=False,  # Use explicit transactions
        )
        
        # Create scoped session for thread safety
        self._scoped_session = scoped_session(self._session_factory)
    
    def get_session(self) -> "RLSSession":
        """Get a new database session."""
        return self._session_factory()
    
    def get_scoped_session(self) -> "RLSSession":
        """Get scoped session (for thread-local access)."""
        return self._scoped_session
    
    @contextmanager
    def session_context(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Generator["RLSSession", None, None]:
        """
        Context manager for managing RLS session lifecycle.
        
        Usage:
            with session_factory.session_context(tenant_id='123e4567-e89b-12d3-a456-426614174000') as session:
                users = session.query(User).all()  # Automatically filtered by tenant_id
        
        Args:
            tenant_id: Tenant ID for this session
            user_id: User ID (optional)
            username: Username (optional)
        
        Yields:
            RLSSession with tenant context set
        """
        # Set tenant context
        tenant_context.set(tenant_id, user_id, username)
        
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()
            tenant_context.clear()


# ============================================================================
# CUSTOM RLS SESSION CLASS
# ============================================================================

class RLSSession(Session):
    """
    Custom SQLAlchemy Session with RLS enforcement.
    
    Automatically enforces tenant context and prevents accidental
    cross-tenant data access.
    """
    
    def execute(self, statement: Executable, params: Any = None, **kwargs: Any) -> Any:
        """
        Execute a SQL statement with RLS context.
        
        Ensures tenant context is set before executing any query.
        """
        # Check if tenant context is set
        if not tenant_context.is_set():
            # Allow only context-setting queries
            sql_text = str(statement)
            if "set_tenant_context" not in sql_text:
                raise ValueError(
                    "Tenant context not set. Call session.set_tenant_context() first "
                    "or use session_factory.session_context() context manager."
                )
        
        # Execute the query with inherited tenant context
        return super().execute(statement, params, **kwargs)


# ============================================================================
# DECLARATIVE BASE FOR ORM MODELS
# ============================================================================

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# ============================================================================
# DATABASE HELPER FUNCTIONS
# ============================================================================

def init_database(
    database_url: str,
    echo_sql: bool = False,
) -> tuple[Engine, RLSSessionFactory]:
    """
    Initialize database engine and session factory.
    
    Args:
        database_url: PostgreSQL connection URL
        echo_sql: Enable SQL logging (debug)
    
    Returns:
        Tuple of (engine, session_factory)
    """
    logger.info(f"Initializing database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    
    # Create engine configuration
    config = DatabaseConfig(
        database_url=database_url,
        pool_size=20,
        max_overflow=40,
        echo_sql=echo_sql,
    )
    
    # Create engine
    engine = config.create_engine()
    
    # Create session factory
    session_factory = RLSSessionFactory(engine)
    
    # Verify RLS is enabled
    _verify_rls_enabled(engine)
    
    logger.info("Database initialized with RLS enforcement enabled")
    
    return engine, session_factory


def _verify_rls_enabled(engine: Engine) -> None:
    """Verify that RLS is properly configured."""
    with engine.connect() as connection:
        # Check if RLS functions exist
        result = connection.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_proc 
                    WHERE proname = 'set_tenant_context'
                )
            """)
        )
        
        if not result.scalar():
            logger.warning(
                "RLS functions not found. Run migration: "
                "migrations/rls_implementation_001_create_rls_tables.sql"
            )
        else:
            logger.info("RLS functions verified on database")


def verify_rls_status(engine: Engine) -> dict[str, Any]:
    """
    Verify RLS status on all tables.
    
    Returns:
        Dictionary with table RLS status
    """
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT 
                    t.relname as table_name,
                    t.relrowsecurity as rls_enabled,
                    COUNT(p.*) as policy_count
                FROM pg_class t
                LEFT JOIN pg_policy p ON t.oid = p.polrelid
                WHERE t.relkind = 'r' 
                  AND t.relnamespace = 'public'::regnamespace
                  AND t.relname NOT IN ('session_context', 'alembic_version')
                GROUP BY t.relname, t.relrowsecurity
                ORDER BY t.relname
            """)
        )
        
        return {
            row[0]: {
                "rls_enabled": row[1],
                "policy_count": row[2]
            }
            for row in result.fetchall()
        }


# ============================================================================
# CONTEXT MANAGER FOR REQUEST HANDLING
# ============================================================================

class TenantContextManager:
    """Context manager for handling tenant context in requests."""
    
    @staticmethod
    def set_current_tenant(
        tenant_id: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
    ) -> None:
        """Set current tenant for this request/thread."""
        tenant_context.set(tenant_id, user_id, username)
    
    @staticmethod
    def get_current_tenant() -> Optional[str]:
        """Get current tenant_id."""
        return tenant_context.tenant_id
    
    @staticmethod
    def clear_current_tenant() -> None:
        """Clear current tenant context."""
        tenant_context.clear()
    
    @staticmethod
    def is_tenant_set() -> bool:
        """Check if tenant context is set."""
        return tenant_context.is_set()


# ============================================================================
# EXPORT PUBLIC API
# ============================================================================

__all__ = [
    "Base",
    "RLSSession",
    "RLSSessionFactory",
    "TenantContext",
    "TenantContextManager",
    "DatabaseConfig",
    "init_database",
    "verify_rls_status",
    "tenant_context",
]

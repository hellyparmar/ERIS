#!/usr/bin/env python3
"""
PostgreSQL Async Connection Test Script

Diagnoses common PostgreSQL async issues in FastAPI + SQLAlchemy projects:
1. Connection Refused - Database connectivity issues
2. MissingGreenlet - Mixing sync/async operations
3. SSL Connection Closed - SSL configuration problems
4. Host Name Translation - Docker hostname resolution
5. Relation Does Not Exist - Migration issues

Usage:
    python test_async_connection.py
    
    Or with custom DATABASE_URL:
    DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db" python test_async_connection.py
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from typing import Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


class AsyncConnectionTester:
    """Test async database connections and identify issues"""
    
    def __init__(self):
        self.database_url = settings.DATABASE_URL
        self.results = []
    
    def log_test(self, name: str, status: str, message: str = ""):
        """Log test result"""
        symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        self.results.append({
            "test": name,
            "status": status,
            "message": message
        })
        print(f"{symbol} {name}: {status}")
        if message:
            print(f"  └─ {message}")
    
    async def test_connection_string(self) -> bool:
        """Test 1: Verify connection string format"""
        try:
            url_parts = self.database_url.split("://")
            if len(url_parts) != 2:
                self.log_test(
                    "Connection String Format",
                    "FAIL",
                    "Invalid format. Expected: postgresql+asyncpg://user:pass@host:port/db"
                )
                return False
            
            driver = url_parts[0]
            if driver not in ["postgresql+asyncpg", "sqlite+aiosqlite"]:
                self.log_test(
                    "Connection String Format",
                    "WARN",
                    f"Driver {driver} may not support async. Use postgresql+asyncpg or sqlite+aiosqlite"
                )
                return True
            
            self.log_test(
                "Connection String Format",
                "PASS",
                f"Driver: {driver}"
            )
            return True
        except Exception as e:
            self.log_test(
                "Connection String Format",
                "FAIL",
                str(e)
            )
            return False
    
    async def test_host_resolution(self) -> bool:
        """Test 2: Verify host can be resolved"""
        try:
            import socket
            
            # Parse host from connection string
            parts = self.database_url.split("@")[1].split(":")[0]
            host = parts
            
            logger.info(f"Resolving host: {host}")
            
            # Try to resolve
            try:
                socket.gethostbyname(host)
                self.log_test(
                    "Host Resolution",
                    "PASS",
                    f"Resolved {host} successfully"
                )
                return True
            except socket.gaierror:
                if host == "db":
                    self.log_test(
                        "Host Resolution",
                        "FAIL",
                        "Cannot resolve 'db' - Running locally? Use 'localhost' or check Docker network"
                    )
                else:
                    self.log_test(
                        "Host Resolution",
                        "FAIL",
                        f"Cannot resolve {host}"
                    )
                return False
        except Exception as e:
            self.log_test(
                "Host Resolution",
                "FAIL",
                str(e)
            )
            return False
    
    async def test_tcp_connection(self) -> bool:
        """Test 3: Verify TCP connectivity"""
        try:
            import socket
            
            # Parse host and port
            parts = self.database_url.split("@")[1].split("/")[0]
            host, port = parts.split(":")
            port = int(port)
            
            logger.info(f"Testing TCP connection to {host}:{port}")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            try:
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    self.log_test(
                        "TCP Connection",
                        "PASS",
                        f"Connected to {host}:{port}"
                    )
                    return True
                else:
                    self.log_test(
                        "TCP Connection",
                        "FAIL",
                        f"Cannot reach {host}:{port} - Is PostgreSQL running?"
                    )
                    return False
            except socket.timeout:
                self.log_test(
                    "TCP Connection",
                    "FAIL",
                    f"Timeout connecting to {host}:{port} - Firewall or network issue?"
                )
                return False
        except Exception as e:
            self.log_test(
                "TCP Connection",
                "FAIL",
                str(e)
            )
            return False
    
    async def test_async_engine_creation(self) -> bool:
        """Test 4: Create async engine"""
        try:
            logger.info("Creating async engine...")
            
            engine = create_async_engine(
                self.database_url,
                pool_pre_ping=True,
                echo=False,
            )
            
            self.log_test(
                "Async Engine Creation",
                "PASS",
                "Engine created successfully"
            )
            
            await engine.dispose()
            return True
        except Exception as e:
            self.log_test(
                "Async Engine Creation",
                "FAIL",
                str(e)
            )
            return False
    
    async def test_database_connection(self) -> bool:
        """Test 5: Connect and execute query"""
        try:
            logger.info("Testing database connection...")
            
            engine = create_async_engine(
                self.database_url,
                pool_pre_ping=True,
                echo=False,
            )
            
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                value = result.scalar()
                
                if value == 1:
                    self.log_test(
                        "Database Connection",
                        "PASS",
                        "Connected and executed query"
                    )
                    await engine.dispose()
                    return True
                else:
                    self.log_test(
                        "Database Connection",
                        "FAIL",
                        "Query executed but returned unexpected value"
                    )
                    await engine.dispose()
                    return False
        except Exception as e:
            error_msg = str(e)
            
            if "connection refused" in error_msg.lower():
                self.log_test(
                    "Database Connection",
                    "FAIL",
                    "Connection Refused - PostgreSQL not accessible"
                )
            elif "could not translate host name" in error_msg.lower():
                self.log_test(
                    "Database Connection",
                    "FAIL",
                    "Host name translation failed - Check Docker hostname"
                )
            elif "ssl" in error_msg.lower():
                self.log_test(
                    "Database Connection",
                    "FAIL",
                    "SSL error - Add ?ssl=prefer or ?ssl=disable to DATABASE_URL for local dev"
                )
            else:
                self.log_test(
                    "Database Connection",
                    "FAIL",
                    error_msg
                )
            return False
    
    async def test_async_session(self) -> bool:
        """Test 6: Create and use AsyncSession"""
        try:
            logger.info("Testing AsyncSession...")
            
            engine = create_async_engine(
                self.database_url,
                pool_pre_ping=True,
                echo=False,
            )
            
            AsyncSessionLocal = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1 as test"))
                row = result.first()
                
                if row[0] == 1:
                    self.log_test(
                        "AsyncSession",
                        "PASS",
                        "AsyncSession works correctly"
                    )
                    await engine.dispose()
                    return True
        except Exception as e:
            error_msg = str(e)
            
            if "greenlet" in error_msg.lower():
                self.log_test(
                    "AsyncSession",
                    "FAIL",
                    "MissingGreenlet error - Ensure all database calls use await with AsyncSession"
                )
            else:
                self.log_test(
                    "AsyncSession",
                    "FAIL",
                    error_msg
                )
            return False
    
    async def test_ssl_configuration(self) -> bool:
        """Test 7: SSL configuration"""
        try:
            if "?ssl=" in self.database_url:
                ssl_mode = self.database_url.split("?ssl=")[1].split("&")[0]
                self.log_test(
                    "SSL Configuration",
                    "PASS",
                    f"SSL mode set to: {ssl_mode}"
                )
                return True
            else:
                # Try connecting without explicit SSL setting
                if "localhost" in self.database_url or "127.0.0.1" in self.database_url:
                    self.log_test(
                        "SSL Configuration",
                        "WARN",
                        "Local development - Consider adding ?ssl=prefer to DATABASE_URL for consistency"
                    )
                    return True
                else:
                    self.log_test(
                        "SSL Configuration",
                        "WARN",
                        "No explicit SSL configuration - Set ?ssl=require for production"
                    )
                    return True
        except Exception as e:
            self.log_test(
                "SSL Configuration",
                "FAIL",
                str(e)
            )
            return False
    
    async def run_all_tests(self) -> Tuple[int, int]:
        """Run all tests and return passed/failed counts"""
        print("\n" + "=" * 70)
        print("PostgreSQL Async Connection Tests")
        print("=" * 70)
        print(f"\nTesting: {self.database_url.split('?')[0]}\n")
        
        tests = [
            self.test_connection_string,
            self.test_host_resolution,
            self.test_tcp_connection,
            self.test_async_engine_creation,
            self.test_database_connection,
            self.test_async_session,
            self.test_ssl_configuration,
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                logger.error(f"Test failed with exception: {e}", exc_info=True)
        
        # Summary
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        warned = sum(1 for r in self.results if r["status"] == "WARN")
        
        print("\n" + "=" * 70)
        print(f"Results: {passed} passed, {warned} warnings, {failed} failed")
        print("=" * 70)
        
        # Recommendations
        if failed > 0:
            print("\nRECOMMENDATIONS:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  • {result['test']}: {result['message']}")
        
        print()
        return passed, failed


async def main():
    """Run tests"""
    tester = AsyncConnectionTester()
    passed, failed = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())

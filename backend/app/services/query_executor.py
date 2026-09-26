"""
Query Executor for AI Assistant
Safely executes pre-approved SQL templates against the PostgreSQL database.
Provides data context to LLM for generating informed responses.

IMPORTANT — RLS & TENANT CONTEXT
---------------------------------
All query execution that is tenant-scoped MUST use execute_query_with_session(),
passing a SQLAlchemy Session that was opened via get_db_sync(tenant_id=...).
That context manager issues SELECT set_config('app.current_tenant_id', ...) on
the same connection *before* yielding it, so PostgreSQL FORCE ROW LEVEL SECURITY
policies are satisfied without creating a second independent engine.

The legacy execute_query() (which creates its own connection from self.engine)
is kept for internal tooling/diagnostics only and MUST NOT be called from any
user-facing endpoint.
"""

import logging
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class QueryExecutor:
    """
    Executes validated SQL queries against PostgreSQL.
    Only executes queries that pass semantic layer validation.
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize executor with a PostgreSQL database URL.
        Uses environment variable or default connection string.
        """
        if db_url is None:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise RuntimeError(
                    "DATABASE_URL environment variable is required but not set. "
                    "Format: postgresql+psycopg://user:password@host:port/database"
                )

        if not (db_url.startswith("postgresql") or db_url.startswith("sqlite")):
            raise ValueError("QueryExecutor requires a PostgreSQL or SQLite DATABASE_URL")
            
        # create_engine is synchronous, so strip +aiosqlite if present
        if db_url.startswith("sqlite+aiosqlite"):
            db_url = db_url.replace("sqlite+aiosqlite", "sqlite")

        self.db_url = db_url
        self.engine: Engine = create_engine(
            self.db_url,
            pool_pre_ping=True,
            echo=False,
        )

    # ------------------------------------------------------------------
    # PRIMARY PATH — tenant-scoped, uses the app's existing session
    # ------------------------------------------------------------------

    def execute_query_with_session(
        self,
        sql: str,
        db: Session,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 100,
    ) -> Dict[str, Any]:
        """
        Execute a SELECT query using an already-open SQLAlchemy Session that
        was obtained via get_db_sync(tenant_id=...).

        This is the correct path for all user-facing AI-assistant queries.
        The Session's connection already has app.current_tenant_id set via
        SELECT set_config(), so PostgreSQL RLS policies are satisfied.
        """
        start_time = time.time()

        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "execution_time_ms": (time.time() - start_time) * 1000,
                "error": "Only SELECT queries allowed",
            }

        try:
            result = db.execute(text(sql), params or {})
            rows = result.fetchmany(max_rows)
            data = [dict(row._mapping) for row in rows]

            data = self._serialize_data(data)
            execution_time = (time.time() - start_time) * 1000

            logger.info(
                f"Query (tenant-scoped session) executed successfully. "
                f"Rows: {len(data)}, Time: {execution_time:.2f}ms"
            )

            return {
                "success": True,
                "data": data,
                "row_count": len(data),
                "execution_time_ms": round(execution_time, 2),
                "error": None,
            }

        except SQLAlchemyError as exc:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Database error: {str(exc)}"
            logger.error(error_msg)
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "execution_time_ms": round(execution_time, 2),
                "error": error_msg,
            }

        except Exception as exc:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Unexpected error: {str(exc)}"
            logger.error(error_msg)
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "execution_time_ms": round(execution_time, 2),
                "error": error_msg,
            }

    def execute_template_query_with_session(
        self,
        template_sql: str,
        semantic_layer,
        db: Session,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate + execute a template query using a tenant-scoped Session.
        params -- extra bind parameters (e.g. {"outlet_ids": (1, 2)}) from
                  inject_outlet_filter(); merged into the query execution.
        """
        try:
            is_valid, issues = semantic_layer.validate_sql(template_sql)
            if not is_valid:
                error_issues = [i for i in issues if i["severity"] == "error"]
                return {
                    "success": False,
                    "data": [],
                    "row_count": 0,
                    "execution_time_ms": 0,
                    "error": f"SQL validation failed: {error_issues[0]['message']}",
                    "validation_issues": issues,
                }

            result = self.execute_query_with_session(template_sql, db, params=params)
            result["validation_issues"] = issues
            return result

        except Exception as exc:
            logger.error(f"Template execution error: {str(exc)}")
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "execution_time_ms": 0,
                "error": f"Template execution failed: {str(exc)}",
            }

    # ------------------------------------------------------------------
    # LEGACY PATH — no tenant context; do NOT call from user endpoints
    # ------------------------------------------------------------------

    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 100,
    ) -> Dict[str, Any]:
        """
        Execute a SQL query using the executor's own engine connection.

        WARNING: This method creates its own connection and NEVER sets the
        PostgreSQL session variable app.current_tenant_id.  It bypasses RLS
        entirely.  Only use this for internal diagnostics (get_table_stats).
        User-facing endpoints MUST use execute_query_with_session() instead.
        """
        start_time = time.time()

        try:
            sql_upper = sql.strip().upper()
            if not sql_upper.startswith("SELECT"):
                return {
                    "success": False,
                    "data": [],
                    "row_count": 0,
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "error": "Only SELECT queries allowed",
                }

            with self.engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                rows = result.fetchmany(max_rows)
                data = [dict(row._mapping) for row in rows]

            data = self._serialize_data(data)
            execution_time = (time.time() - start_time) * 1000

            logger.info(
                f"Query executed successfully. Rows: {len(data)}, Time: {execution_time:.2f}ms"
            )

            return {
                "success": True,
                "data": data,
                "row_count": len(data),
                "execution_time_ms": round(execution_time, 2),
                "error": None,
            }

        except SQLAlchemyError as exc:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Database error: {str(exc)}"
            logger.error(error_msg)
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "execution_time_ms": round(execution_time, 2),
                "error": error_msg,
            }

        except Exception as exc:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Unexpected error: {str(exc)}"
            logger.error(error_msg)
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "execution_time_ms": round(execution_time, 2),
                "error": error_msg,
            }

    def execute_template_query(
        self,
        template_sql: str,
        semantic_layer,
    ) -> Dict[str, Any]:
        """Legacy unscoped template execution. Do NOT call from user endpoints."""
        try:
            is_valid, issues = semantic_layer.validate_sql(template_sql)
            if not is_valid:
                error_issues = [i for i in issues if i["severity"] == "error"]
                return {
                    "success": False,
                    "data": [],
                    "row_count": 0,
                    "execution_time_ms": 0,
                    "error": f"SQL validation failed: {error_issues[0]['message']}",
                    "validation_issues": issues,
                }

            result = self.execute_query(template_sql)
            result["validation_issues"] = issues
            return result

        except Exception as exc:
            logger.error(f"Template execution error: {str(exc)}")
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "execution_time_ms": 0,
                "error": f"Template execution failed: {str(exc)}",
            }

    def _serialize_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        serialized = []
        for row in data:
            serialized_row = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    serialized_row[key] = value.isoformat()
                elif isinstance(value, (int, float, str, bool, type(None))):
                    serialized_row[key] = value
                else:
                    serialized_row[key] = str(value)
            serialized.append(serialized_row)
        return serialized

    def get_table_stats(self) -> Dict[str, Dict[str, Any]]:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                        "ORDER BY table_name"
                    )
                )
                tables = [row[0] for row in result.fetchall()]

                stats = {}
                for table in tables:
                    count_result = conn.execute(
                        text(f"SELECT COUNT(*) AS count FROM {table}")
                    )
                    count = count_result.scalar() or 0
                    stats[table] = {"row_count": count}

            return stats

        except Exception as exc:
            logger.error(f"Error getting table stats: {str(exc)}")
            return {}

    def format_results_for_llm(
        self,
        query_result: Dict[str, Any],
        max_display_rows: int = 10,
    ) -> str:
        if not query_result.get("success"):
            return f"Query failed: {query_result.get('error', 'Unknown error')}"

        data = query_result.get("data", [])
        row_count = query_result.get("row_count", 0)

        if not data:
            return "Query returned no results."

        summary = f"Query Results: {row_count} rows found\n\n"
        if data:
            headers = list(data[0].keys())
            summary += f"Columns: {', '.join(headers)}\n\n"

        display_rows = min(max_display_rows, len(data))
        summary += f"Sample Data ({display_rows} of {row_count} rows):\n"

        for i, row in enumerate(data[:display_rows], 1):
            summary += f"\n{i}. "
            row_items = [f"{k}: {v}" for k, v in row.items()]
            summary += " | ".join(row_items)

        if row_count > max_display_rows:
            summary += f"\n\n... and {row_count - max_display_rows} more rows"

        return summary


# Singleton instance
query_executor = QueryExecutor()

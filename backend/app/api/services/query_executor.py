"""
Query Executor for AI Assistant
Safely executes pre-approved SQL templates against the database.
Provides data context to LLM for generating informed responses.
"""

import sqlite3
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class QueryExecutor:
    """
    Executes validated SQL queries against SQLite database.
    Only executes queries that pass semantic layer validation.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize executor with database path.
        Uses environment variable or default path.
        """
        if db_path is None:
            # Use environment variable or default
            db_path = os.getenv("DATABASE_URL", "api/rdios_dev.db")
        
        # Handle SQLite URI format (convert to file path)
        if db_path.startswith("sqlite:///"):
            # sqlite:///./api/rdios_dev.db → ./api/rdios_dev.db
            db_path = db_path.replace("sqlite://", "")
        
        # Convert to absolute path if relative
        if not os.path.isabs(db_path):
            # If path already contains api/, just use it from current directory
            if db_path.startswith("./"):
                db_path = db_path[2:]  # Remove leading ./
            
            # If path contains api/, it's relative to workspace root
            if "api/" in db_path:
                # Get workspace root (parent of api directory)
                api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                workspace_root = os.path.dirname(api_dir)
                db_path = os.path.join(workspace_root, db_path)
            else:
                # Path is relative to api directory
                api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                db_path = os.path.join(api_dir, db_path)
        
        self.db_path = db_path
        self._verify_db_exists()

    def _verify_db_exists(self):
        """Verify database file exists."""
        if not os.path.exists(self.db_path):
            logger.warning(f"Database not found at {self.db_path}")

    def execute_query(
        self, 
        sql: str, 
        params: Optional[Dict] = None,
        max_rows: int = 100
    ) -> Dict[str, Any]:
        """
        Execute a SQL query and return structured results.
        
        Args:
            sql: SQL query string (should be pre-validated)
            params: Query parameters (for parameterized queries)
            max_rows: Maximum rows to return (safety limit)
        
        Returns:
            {
                "success": bool,
                "data": List[Dict],
                "row_count": int,
                "execution_time_ms": float,
                "error": Optional[str]
            }
        """
        import time
        start_time = time.time()

        try:
            # Validate SQL is read-only (extra safety check)
            sql_upper = sql.strip().upper()
            if not sql_upper.startswith('SELECT'):
                return {
                    "success": False,
                    "data": [],
                    "row_count": 0,
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "error": "Only SELECT queries allowed"
                }

            # Connect and execute
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()

            # Execute with parameters if provided
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            # Fetch results with limit
            rows = cursor.fetchmany(max_rows)
            data = [dict(row) for row in rows]

            # Convert non-JSON-serializable types
            data = self._serialize_data(data)

            conn.close()

            execution_time = (time.time() - start_time) * 1000

            logger.info(f"Query executed successfully. Rows: {len(data)}, Time: {execution_time:.2f}ms")

            return {
                "success": True,
                "data": data,
                "row_count": len(data),
                "execution_time_ms": round(execution_time, 2),
                "error": None
            }

        except sqlite3.Error as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "execution_time_ms": round(execution_time, 2),
                "error": error_msg
            }

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "execution_time_ms": round(execution_time, 2),
                "error": error_msg
            }

    def execute_template_query(
        self,
        template_sql: str,
        semantic_layer
    ) -> Dict[str, Any]:
        """
        Execute a template query with semantic layer validation.
        
        Args:
            template_sql: SQL from semantic layer template
            semantic_layer: SemanticLayer instance for validation
        
        Returns:
            Query execution result with validation metadata
        """
        try:
            # Validate SQL before execution
            is_valid, issues = semantic_layer.validate_sql(template_sql)
            
            if not is_valid:
                error_issues = [i for i in issues if i['severity'] == 'error']
                return {
                    "success": False,
                    "data": [],
                    "row_count": 0,
                    "execution_time_ms": 0,
                    "error": f"SQL validation failed: {error_issues[0]['message']}",
                    "validation_issues": issues
                }
            
            # Execute validated query
            result = self.execute_query(template_sql)
            result["validation_issues"] = issues
            
            return result

        except Exception as e:
            logger.error(f"Template execution error: {str(e)}")
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "execution_time_ms": 0,
                "error": f"Template execution failed: {str(e)}"
            }

    def _serialize_data(self, data: List[Dict]) -> List[Dict]:
        """Convert non-JSON-serializable types to strings."""
        serialized = []
        
        for row in data:
            serialized_row = {}
            for key, value in row.items():
                if isinstance(value, (datetime,)):
                    serialized_row[key] = value.isoformat()
                elif isinstance(value, (int, float, str, bool, type(None))):
                    serialized_row[key] = value
                else:
                    serialized_row[key] = str(value)
            
            serialized.append(serialized_row)
        
        return serialized

    def get_table_stats(self) -> Dict[str, Dict]:
        """Get row counts for all tables (for context to LLM)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            stats = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()[0]
                    stats[table] = {"row_count": count}
                except Exception as e:
                    stats[table] = {"row_count": 0, "error": str(e)}
            
            conn.close()
            return stats

        except Exception as e:
            logger.error(f"Error getting table stats: {str(e)}")
            return {}

    def format_results_for_llm(
        self, 
        query_result: Dict[str, Any],
        max_display_rows: int = 10
    ) -> str:
        """
        Format query results as natural language summary for LLM context.
        
        Args:
            query_result: Result from execute_query()
            max_display_rows: Max rows to include in summary
        
        Returns:
            Formatted string suitable for LLM system prompt
        """
        if not query_result.get("success"):
            return f"Query failed: {query_result.get('error', 'Unknown error')}"
        
        data = query_result.get("data", [])
        row_count = query_result.get("row_count", 0)
        
        if not data:
            return "Query returned no results."
        
        # Build summary
        summary = f"Query Results: {row_count} rows found\n\n"
        
        # Show column headers
        if data:
            headers = list(data[0].keys())
            summary += f"Columns: {', '.join(headers)}\n\n"
        
        # Show sample rows
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

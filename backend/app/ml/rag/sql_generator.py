"""
SQL Generator for Retail Queries
Converts natural language to SQL with safety checks
"""

import re
from typing import Dict, List, Tuple, Optional
import logging
import pandas as pd
from sqlalchemy import text

logger = logging.getLogger(__name__)


class SQLGenerator:
    """Convert natural language queries to SQL with safety validation."""

    # Unsafe SQL operations to block
    UNSAFE_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]

    def __init__(self, db_connection=None):
        """
        Initialize SQL generator.
        
        Args:
            db_connection: SQLAlchemy database connection
        """
        self.db_connection = db_connection
        self.schema = self._get_schema() if db_connection else {}

    def _get_schema(self) -> Dict[str, List[str]]:
        """Get database schema (tables and columns)."""
        try:
            schema = {}
            
            tables = [
                "products", "sales", "customers", "inventory",
                "suppliers", "invoices", "stores", "users"
            ]
            
            for table in tables:
                # Mock schema - would fetch real schema from DB
                if table == "products":
                    schema[table] = ["id", "name", "category", "price", "stock", "margin"]
                elif table == "sales":
                    schema[table] = ["id", "date", "outlet", "customer_id", "total_amount", "items_count"]
                elif table == "customers":
                    schema[table] = ["id", "name", "email", "phone", "tier", "total_purchases"]
                elif table == "inventory":
                    schema[table] = ["id", "product_id", "outlet_id", "quantity", "last_updated"]
                elif table == "stores":
                    schema[table] = ["id", "name", "location", "type"]
            
            return schema
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return {}

    def classify_query_intent(self, question: str) -> str:
        """
        Classify query intent for SQL generation.
        
        Returns: "select", "aggregate", "time_series", "comparison"
        """
        question_lower = question.lower()
        
        if any(x in question_lower for x in ["total", "sum", "count", "average", "min", "max"]):
            return "aggregate"
        elif any(x in question_lower for x in ["trend", "over time", "by month", "by week"]):
            return "time_series"
        elif any(x in question_lower for x in ["compare", "versus", "vs", "better", "difference"]):
            return "comparison"
        else:
            return "select"

    def natural_to_sql(self, question: str, entities: Optional[Dict] = None) -> Optional[str]:
        """
        Convert natural language to SQL query.
        
        Args:
            question: Natural language question
            entities: Extracted entities dict
        
        Returns:
            SQL query string or None if generation fails
        """
        try:
            intent = self.classify_query_intent(question)
            question_lower = question.lower()
            
            # Determine table and metric
            table = self._determine_table(question_lower)
            metric = self._determine_metric(question_lower)
            
            if intent == "aggregate":
                return self._generate_aggregate_query(table, metric, question_lower, entities)
            elif intent == "time_series":
                return self._generate_time_series_query(table, metric, question_lower, entities)
            elif intent == "comparison":
                return self._generate_comparison_query(table, metric, question_lower, entities)
            else:
                return self._generate_select_query(table, question_lower, entities)
                
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return None

    def _determine_table(self, question_lower: str) -> str:
        """Determine main table from question."""
        if "product" in question_lower:
            return "products"
        elif "customer" in question_lower or "buyer" in question_lower:
            return "customers"
        elif "stock" in question_lower or "inventory" in question_lower:
            return "inventory"
        else:
            return "sales"  # Default

    def _determine_metric(self, question_lower: str) -> str:
        """Determine metric from question."""
        if "quantity" in question_lower or "units" in question_lower:
            return "quantity"
        elif "price" in question_lower:
            return "price"
        elif "profit" in question_lower or "margin" in question_lower:
            return "margin"
        else:
            return "total_amount"

    def _generate_aggregate_query(
        self, 
        table: str, 
        metric: str, 
        question_lower: str, 
        entities: Optional[Dict]
    ) -> str:
        """Generate aggregate SQL query."""
        
        # Determine aggregation function
        if "total" in question_lower or "sum" in question_lower:
            agg_func = "SUM"
        elif "average" in question_lower or "avg" in question_lower:
            agg_func = "AVG"
        elif "count" in question_lower or "how many" in question_lower:
            agg_func = "COUNT"
        elif "min" in question_lower or "lowest" in question_lower:
            agg_func = "MIN"
        elif "max" in question_lower or "highest" in question_lower:
            agg_func = "MAX"
        else:
            agg_func = "SUM"
        
        # Build base query
        if metric == "total_amount":
            col = "total_amount" if table == "sales" else "price"
        else:
            col = metric
        
        sql = f"SELECT {agg_func}({col}) as result FROM {table}"
        
        # Add filters based on entities
        if entities:
            filters = []
            
            if entities.get("date_range"):
                date_range = entities["date_range"]
                if isinstance(date_range, dict):
                    start = date_range.get("start_date", "2026-01-01")
                    end = date_range.get("end_date", "2026-03-28")
                    filters.append(f"date >= '{start}' AND date <= '{end}'")
            
            if entities.get("outlet"):
                filters.append(f"outlet LIKE '%{entities['outlet']}%'")
            
            if entities.get("product_name"):
                filters.append(f"name LIKE '%{entities['product_name']}%'")
            
            if filters:
                sql += " WHERE " + " AND ".join(filters)
        
        return sql

    def _generate_time_series_query(
        self, 
        table: str, 
        metric: str, 
        question_lower: str, 
        entities: Optional[Dict]
    ) -> str:
        """Generate time series SQL query."""
        
        # Determine grouping
        if "by month" in question_lower or "monthly" in question_lower:
            group_by = "DATE_TRUNC('month', date)"
        elif "by week" in question_lower or "weekly" in question_lower:
            group_by = "DATE_TRUNC('week', date)"
        elif "by day" in question_lower or "daily" in question_lower:
            group_by = "DATE_TRUNC('day', date)"
        else:
            group_by = "DATE_TRUNC('month', date)"  # Default
        
        if metric == "total_amount":
            col = "total_amount" if table == "sales" else "price"
        else:
            col = metric
        
        sql = f"""
        SELECT {group_by} as period, SUM({col}) as value, COUNT(*) as count
        FROM {table}
        """
        
        # Add filters
        if entities and entities.get("date_range"):
            date_range = entities["date_range"]
            if isinstance(date_range, dict):
                start = date_range.get("start_date", "2026-01-01")
                end = date_range.get("end_date", "2026-03-28")
                sql += f" WHERE date >= '{start}' AND date <= '{end}'"
        
        sql += f" GROUP BY {group_by} ORDER BY period DESC"
        
        return sql.strip()

    def _generate_comparison_query(
        self, 
        table: str, 
        metric: str, 
        question_lower: str, 
        entities: Optional[Dict]
    ) -> str:
        """Generate comparison SQL query."""
        
        # Determine comparison dimension
        if "outlet" in question_lower or "store" in question_lower:
            group_col = "outlet"
        elif "product" in question_lower:
            group_col = "name"
        elif "customer" in question_lower:
            group_col = "customer_id"
        else:
            group_col = "outlet"
        
        if metric == "total_amount":
            col = "total_amount" if table == "sales" else "price"
        else:
            col = metric
        
        sql = f"""
        SELECT {group_col}, SUM({col}) as total, COUNT(*) as count, 
               ROUND(AVG({col}), 2) as average
        FROM {table}
        """
        
        # Add filters
        if entities and entities.get("date_range"):
            date_range = entities["date_range"]
            if isinstance(date_range, dict):
                start = date_range.get("start_date", "2026-01-01")
                end = date_range.get("end_date", "2026-03-28")
                sql += f" WHERE date >= '{start}' AND date <= '{end}'"
        
        sql += f" GROUP BY {group_col} ORDER BY total DESC"
        
        return sql.strip()

    def _generate_select_query(
        self, 
        table: str, 
        question_lower: str, 
        entities: Optional[Dict]
    ) -> str:
        """Generate basic SELECT query."""
        
        sql = f"SELECT * FROM {table} LIMIT 10"
        
        # Add simple filters
        if entities:
            filters = []
            
            if entities.get("product_name"):
                filters.append(f"name LIKE '%{entities['product_name']}%'")
            
            if entities.get("outlet"):
                filters.append(f"outlet LIKE '%{entities['outlet']}%'")
            
            if filters:
                sql = f"SELECT * FROM {table} WHERE " + " AND ".join(filters) + " LIMIT 10"
        
        return sql

    def is_safe_query(self, sql: str) -> Tuple[bool, str]:
        """
        Validate SQL query for safety.
        
        Args:
            sql: SQL query string
        
        Returns:
            Tuple of (is_safe, reason)
        """
        sql_upper = sql.upper().strip()
        
        # Check for unsafe keywords
        for keyword in self.UNSAFE_KEYWORDS:
            if keyword in sql_upper:
                return False, f"Unsafe operation '{keyword}' not allowed"
        
        # Check for comment injection
        if "--" in sql or "/*" in sql or "*/" in sql:
            return False, "SQL comments not allowed"
        
        # Only SELECT allowed
        if not sql_upper.startswith("SELECT"):
            return False, "Only SELECT queries allowed"
        
        return True, "Query is safe"

    def execute_safe_query(self, sql: str) -> Optional[pd.DataFrame]:
        """
        Execute SQL query with safety validation.
        
        Args:
            sql: SQL query string
        
        Returns:
            DataFrame with results or None if query is unsafe/fails
        """
        # Validate safety
        is_safe, reason = self.is_safe_query(sql)
        if not is_safe:
            logger.warning(f"Unsafe query rejected: {reason}")
            return None
        
        try:
            if not self.db_connection:
                logger.warning("No database connection available")
                return None
            
            result = pd.read_sql(sql, self.db_connection)
            logger.info(f"Query executed successfully: {len(result)} rows returned")
            return result
            
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return None

    def format_query_results(self, df: Optional[pd.DataFrame], max_rows: int = 5) -> str:
        """
        Format query results as natural language summary.
        
        Args:
            df: Results DataFrame
            max_rows: Max rows to display
        
        Returns:
            Formatted result string
        """
        if df is None or len(df) == 0:
            return "No results found."
        
        summary = f"Found {len(df)} records:\n\n"
        
        # Display first few rows
        display_df = df.head(max_rows)
        summary += display_df.to_string(index=False)
        
        if len(df) > max_rows:
            summary += f"\n\n... and {len(df) - max_rows} more records"
        
        return summary

"""
Dynamic Query Generator for AI Assistant
Converts natural language questions directly to SQL queries.
Falls back to semantic templates when available.
"""

import re
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class DynamicQueryGenerator:
    """
    Generates SQL queries from natural language questions.
    Handles common retail analytics patterns.
    """

    def __init__(self):
        # Business term mappings
        self.metric_mapping = {
            "revenue": "SUM(s.total_amount)",
            "sales": "SUM(s.total_amount)",
            "total": "SUM(s.total_amount)",
            "income": "SUM(s.total_amount)",
            "earnings": "SUM(s.total_amount)",
            
            "count": "COUNT(*)",
            "orders": "COUNT(DISTINCT s.id)",
            "transactions": "COUNT(DISTINCT s.id)",
            "number of orders": "COUNT(DISTINCT s.id)",
            "customers": "COUNT(DISTINCT s.customer_id)",
            "unique customers": "COUNT(DISTINCT s.customer_id)",
            
            "average": "AVG(s.total_amount)",
            "avg": "AVG(s.total_amount)",
            "mean": "AVG(s.total_amount)",
        }

        self.table_mapping = {
            "sales": "sales s",
            "products": "products p",
            "customers": "customers c",
            "items": "sale_items si",
        }

        self.date_mapping = {
            "today": "DATE(s.transaction_date) = DATE('now')",
            "yesterday": "DATE(s.transaction_date) = DATE('now', '-1 day')",
            "last week": "s.transaction_date >= DATE('now', '-7 days')",
            "last month": "strftime('%Y-%m', s.transaction_date) = strftime('%Y-%m', 'now', '-1 month')",
            "this month": "strftime('%Y-%m', s.transaction_date) = strftime('%Y-%m', 'now')",
            "this year": "strftime('%Y', s.transaction_date) = strftime('%Y', 'now')",
            "last year": "strftime('%Y', s.transaction_date) = strftime('%Y', 'now', '-1 year')",
        }

    def generate_query(self, question: str) -> Optional[Tuple[str, str]]:
        """
        Generate SQL query from natural language question.
        
        Returns:
            Tuple of (query_type, sql_query) or None if generation fails
        """
        q = question.lower().strip()
        logger.info(f"Generating query for: {question}")

        # Pattern 0: Top-N queries (check early for "top", "best", "show", "popular", "leading")
        # "Show me top 5 products" or "Best selling products" or "Most popular products"
        if any(word in q for word in ["top", "best", "show", "popular", "most", "leading"]) and ("product" in q or "customer" in q or "item" in q or "selling" in q):
            sql = self._generate_top_n_query(q)
            if sql:
                return ("top_n", sql)

        # Pattern 1: Time-based analysis (check before metric)
        # "Revenue by month" → SELECT date, SUM(revenue) ... GROUP BY month
        if "by " in q and any(t in q for t in ["month", "day", "week", "year", "category"]):
            sql = self._generate_groupby_query(q)
            if sql:
                return ("groupby", sql)

        # Pattern 2: Simple metric queries
        # "What is the total revenue?" → SELECT SUM(total_amount) FROM sales
        if self._is_metric_query(q):
            sql = self._generate_metric_query(q)
            if sql:
                return ("metric", sql)

        # Pattern 3: Trending/Changes
        # "What is our sales trend?" → Historical data comparison
        if any(t in q for t in ["trend", "growth", "change", "increase", "decrease"]):
            sql = self._generate_trend_query(q)
            if sql:
                return ("trend", sql)

        return None

    def _is_metric_query(self, q: str) -> bool:
        """Check if question asks for a simple metric."""
        keywords = [
            "what is", "what's", "how much", "total", "overall",
            "how many", "count", "number of", "sales", "revenue",
            "today", "yesterday", "average", "avg", "mean",
            "earn", "earned", "performance", "trend"
        ]
        return any(k in q for k in keywords)

    def _generate_metric_query(self, q: str) -> Optional[str]:
        """Generate query for simple metric questions."""
        try:
            # Extract metric
            metric = None
            for key, value in self.metric_mapping.items():
                if key in q:
                    metric = value
                    break

            if not metric:
                # Default to revenue for "what is..." questions
                metric = "SUM(s.total_amount) as total_revenue"

            # Extract date constraint
            where_clause = ""
            for date_key, date_value in self.date_mapping.items():
                if date_key in q:
                    where_clause = f"WHERE {date_value}"
                    break

            # Handle counting specific things
            if "customer" in q and "count" in q:
                metric = "COUNT(DISTINCT s.customer_id) as unique_customers"
            elif "order" in q and "count" in q:
                metric = "COUNT(DISTINCT s.id) as total_orders"

            sql = f"SELECT {metric} FROM sales s {where_clause}"
            return sql

        except Exception as e:
            logger.error(f"Error generating metric query: {e}")
            return None

    def _generate_top_n_query(self, q: str) -> Optional[str]:
        """Generate top N products/customers query."""
        try:
            # Extract N
            n_match = re.search(r"top\s+(\d+)", q)
            n = int(n_match.group(1)) if n_match else 10

            # Determine if products, items, or customers
            if "product" in q or "item" in q or "selling" in q:
                sql = f"""
                SELECT 
                    p.name, 
                    SUM(si.quantity) as units_sold,
                    SUM(s.total_amount) as total_revenue
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                JOIN products p ON si.product_id = p.id
                GROUP BY p.id, p.name
                ORDER BY total_revenue DESC
                LIMIT {n}
                """
            elif "customer" in q:
                sql = f"""
                SELECT 
                    c.name,
                    COUNT(DISTINCT s.id) as order_count,
                    SUM(s.total_amount) as total_spent,
                    AVG(s.total_amount) as avg_order_value
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                GROUP BY s.customer_id, c.name
                ORDER BY total_spent DESC
                LIMIT {n}
                """
            else:
                return None

            return " ".join(sql.split())  # Clean whitespace

        except Exception as e:
            logger.error(f"Error generating top N query: {e}")
            return None

    def _generate_groupby_query(self, q: str) -> Optional[str]:
        """Generate GROUP BY queries."""
        try:
            # Extract grouping dimension
            group_by = None
            if "category" in q:
                sql = """
                SELECT 
                    p.category,
                    COUNT(DISTINCT s.id) as order_count,
                    SUM(s.total_amount) as total_revenue,
                    AVG(s.total_amount) as avg_order_value
                FROM sales s
                JOIN sale_items si ON s.id = si.sale_id
                JOIN products p ON si.product_id = p.id
                GROUP BY p.category
                ORDER BY total_revenue DESC
                LIMIT 20
                """
            elif "month" in q or "monthly" in q:
                sql = """
                SELECT 
                    strftime('%Y-%m', s.transaction_date) as month,
                    COUNT(DISTINCT s.id) as order_count,
                    SUM(s.total_amount) as total_revenue,
                    AVG(s.total_amount) as avg_order_value
                FROM sales s
                GROUP BY strftime('%Y-%m', s.transaction_date)
                ORDER BY month DESC
                LIMIT 20
                """
            elif "day" in q or "daily" in q:
                sql = """
                SELECT 
                    DATE(s.transaction_date) as date,
                    COUNT(DISTINCT s.id) as order_count,
                    SUM(s.total_amount) as total_revenue,
                    AVG(s.total_amount) as avg_order_value
                FROM sales s
                GROUP BY DATE(s.transaction_date)
                ORDER BY date DESC
                LIMIT 30
                """
            elif "week" in q or "weekly" in q:
                sql = """
                SELECT 
                    strftime('%Y-W%W', s.transaction_date) as week,
                    COUNT(DISTINCT s.id) as order_count,
                    SUM(s.total_amount) as total_revenue,
                    AVG(s.total_amount) as avg_order_value
                FROM sales s
                GROUP BY strftime('%Y-W%W', s.transaction_date)
                ORDER BY week DESC
                LIMIT 52
                """
            else:
                return None

            return " ".join(sql.split())

        except Exception as e:
            logger.error(f"Error generating groupby query: {e}")
            return None

    def _generate_trend_query(self, q: str) -> Optional[str]:
        """Generate trend/comparison queries."""
        try:
            # Get monthly trend
            sql = """
            SELECT 
                strftime('%Y-%m', s.transaction_date) as month,
                COUNT(DISTINCT s.id) as orders,
                COUNT(DISTINCT s.customer_id) as unique_customers,
                SUM(s.total_amount) as revenue,
                AVG(s.total_amount) as avg_order_value
            FROM sales s
            GROUP BY strftime('%Y-%m', s.transaction_date)
            ORDER BY month DESC
            LIMIT 12
            """

            return " ".join(sql.split())

        except Exception as e:
            logger.error(f"Error generating trend query: {e}")
            return None


# Singleton instance
dynamic_query_generator = DynamicQueryGenerator()

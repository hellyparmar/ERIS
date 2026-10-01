"""Small, auditable semantic layer used by the ERIS AI assistant.

Only pre-approved SELECT templates can execute. Date values and result limits
are produced locally; user text is never interpolated into SQL.
"""

from __future__ import annotations

from datetime import date, timedelta
import logging
import re
from typing import Optional


logger = logging.getLogger(__name__)

BUSINESS_DEFINITIONS = {
    "revenue": "sum of completed sale totals",
    "average_order_value": "revenue divided by completed order count",
    "units_sold": "sum of sale-item quantities",
    "low_stock": "outlet inventory at or below the product reorder level",
    "dead_stock": "inventory on hand with no sales during the last 90 days",
}

SCHEMA_DESCRIPTIONS = {
    "sales": ["id", "outlet_id", "customer_id", "sale_date", "total_amount", "status"],
    "sale_items": ["sale_id", "product_id", "quantity", "unit_price", "line_total"],
    "products": ["id", "sku", "name", "cost_price", "selling_price", "reorder_level"],
    "inventory": ["outlet_id", "product_id", "current_stock", "reserved_stock"],
    "customers": ["id", "first_name", "last_name", "email", "phone"],
    "suppliers": ["id", "name", "outstanding_payable", "phone", "contact_person"],
    "outlets": ["id", "name", "code", "city"],
    "forecast_results": ["outlet_id", "product_id", "model_type", "forecast_json", "mape", "rmse", "mae", "created_at"],
}

QUERY_TEMPLATES = {
    "top_products_by_revenue": {
        "pattern": r"top\s*(\d+)?\s*(selling\s+)?products?|best\s*(selling\s+)?products?",
        "sql": """
            SELECT p.name, ROUND(SUM(si.line_total), 2) AS revenue,
                   SUM(si.quantity) AS units
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE s.status = 'completed'
              AND s.sale_date >= '{start_date}'
              AND __OUTLET_SCOPE_s__
            GROUP BY p.id, p.name
            ORDER BY revenue DESC
            LIMIT {limit}
        """,
    },
    "revenue_by_period": {
        "pattern": r"(total\s+)?(revenue|sales)(\s+summary)?\s+(last|this)\s+(week|month|year)",
        "sql": """
            SELECT ROUND(COALESCE(SUM(s.total_amount), 0), 2) AS total_revenue,
                   COUNT(DISTINCT s.id) AS order_count,
                   ROUND(COALESCE(AVG(s.total_amount), 0), 2) AS avg_order_value
            FROM sales s
            WHERE s.status = 'completed'
              AND s.sale_date >= '{start_date}'
              AND s.sale_date < '{end_date}'
              AND __OUTLET_SCOPE_s__
        """,
    },
    "daily_sales_trend": {
        "pattern": r"(daily|day\s*wise)\s*(sales|revenue)(\s*trend)?",
        "sql": """
            SELECT DATE(s.sale_date) AS sale_day,
                   ROUND(SUM(s.total_amount), 2) AS revenue,
                   COUNT(DISTINCT s.id) AS orders
            FROM sales s
            WHERE s.status = 'completed'
              AND s.sale_date >= '{start_date}'
              AND __OUTLET_SCOPE_s__
            GROUP BY DATE(s.sale_date)
            ORDER BY sale_day
        """,
    },
    "top_customers": {
        "pattern": r"top\s*(\d+)?\s*customers?(\s+by\s+(revenue|spend|value))?",
        "sql": """
            SELECT c.first_name || ' ' || c.last_name AS name, c.email,
                   ROUND(SUM(s.total_amount), 2) AS total_spend,
                   COUNT(DISTINCT s.id) AS order_count
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            WHERE s.status = 'completed' AND __OUTLET_SCOPE_s__
            GROUP BY c.id, c.first_name, c.last_name, c.email
            ORDER BY total_spend DESC
            LIMIT {limit}
        """,
    },
    "low_stock_products": {
        "pattern": r"low\s*stock|out\s*of\s*stock|need(s)?\s+reorder|inventory\s*alert",
        "sql": """
            SELECT i.outlet_id, p.name, p.sku, i.current_stock,
                   i.reserved_stock, p.reorder_level
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            WHERE i.current_stock - i.reserved_stock <= p.reorder_level
              AND __OUTLET_SCOPE_i__
            ORDER BY (i.current_stock - i.reserved_stock - p.reorder_level)
            LIMIT 20
        """,
    },
    "dead_stock_analysis": {
        "pattern": r"(dead|stagnant|slow\s*moving)\s*(stock|inventory|products?|items?)",
        "sql": """
            SELECT i.outlet_id, p.name, p.sku, i.current_stock AS stock_on_hand,
                   ROUND(i.current_stock * p.cost_price, 2) AS tied_capital
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            WHERE i.current_stock > 0 AND __OUTLET_SCOPE_i__
              AND NOT EXISTS (
                  SELECT 1 FROM sale_items si
                  JOIN sales s ON si.sale_id = s.id
                  WHERE si.product_id = p.id
                    AND s.outlet_id = i.outlet_id
                    AND s.sale_date >= '{start_date}'
              )
            ORDER BY tied_capital DESC
            LIMIT 20
        """,
    },
    "compare_revenue_periods": {
        "pattern": r"compare\s+this\s+month\s+(to|with)\s+last\s+month|this\s+month\s+vs\.?\s+last\s+month",
        "sql": """
            SELECT
              ROUND(SUM(CASE WHEN s.sale_date >= '{current_start}' THEN s.total_amount ELSE 0 END), 2) AS this_month_revenue,
              ROUND(SUM(CASE WHEN s.sale_date >= '{previous_start}' AND s.sale_date < '{current_start}' THEN s.total_amount ELSE 0 END), 2) AS last_month_revenue,
              SUM(CASE WHEN s.sale_date >= '{current_start}' THEN 1 ELSE 0 END) AS this_month_orders,
              SUM(CASE WHEN s.sale_date >= '{previous_start}' AND s.sale_date < '{current_start}' THEN 1 ELSE 0 END) AS last_month_orders
            FROM sales s
            WHERE s.status = 'completed' AND s.sale_date >= '{previous_start}'
              AND __OUTLET_SCOPE_s__
        """,
    },
    "underperforming_outlets": {
        "pattern": r"underperforming\s+(outlets?|stores?)|(which|what)\s+(outlets?|stores?).*underperforming",
        "sql": """
            SELECT o.id AS outlet_id, o.name AS outlet_name,
                   ROUND(SUM(s.total_amount), 2) AS total_revenue,
                   COUNT(DISTINCT s.id) AS order_count,
                   ROUND(AVG(s.total_amount), 2) AS avg_order_value
            FROM outlets o
            JOIN sales s ON s.outlet_id = o.id
            WHERE s.status = 'completed' AND s.sale_date >= '{start_date}'
              AND __OUTLET_SCOPE_s__
            GROUP BY o.id, o.name
            ORDER BY total_revenue ASC
            LIMIT 3
        """,
    },
    "supplier_debt": {
        "pattern": r"supplier\s+debt|supplier.*owe|who\s+do\s+i\s+owe",
        "sql": """
            SELECT id, name AS supplier_name, outstanding_payable, phone, contact_person
            FROM suppliers
            WHERE is_active = TRUE
            ORDER BY outstanding_payable DESC
            LIMIT 5
        """,
    },
    "aov_trend": {
        "pattern": r"average\s+order\s+value\s+trend|aov\s+trend",
        "sql": """
            SELECT DATE(s.sale_date) AS sale_day,
                   ROUND(AVG(s.total_amount), 2) AS average_order_value,
                   COUNT(DISTINCT s.id) AS order_count
            FROM sales s
            WHERE s.status = 'completed' AND s.sale_date >= '{start_date}'
              AND __OUTLET_SCOPE_s__
            GROUP BY DATE(s.sale_date)
            ORDER BY sale_day
        """,
    },
    "latest_forecast": {
        "pattern": r"(sales|demand)?\s*forecast|predict(ed|ion)?\s+(sales|demand)",
        "sql": """
            SELECT fr.outlet_id, p.name AS product_name, fr.model_type,
                   fr.forecast_json, fr.mape, fr.rmse, fr.mae, fr.created_at
            FROM forecast_results fr
            LEFT JOIN products p ON fr.product_id = p.id
            WHERE __OUTLET_SCOPE_fr__
            ORDER BY fr.created_at DESC
            LIMIT 10
        """,
    },
}

VALIDATION_RULES = [
    {
        "name": "read_only",
        "pattern": r"\b(DELETE|DROP|TRUNCATE|UPDATE|INSERT|ALTER|CREATE|GRANT|REVOKE)\b",
        "message": "Only read-only queries are allowed",
        "severity": "error",
    },
    {"name": "no_select_star", "pattern": r"SELECT\s+\*", "message": "Columns must be explicit", "severity": "error"},
    {
        "name": "single_statement",
        "pattern": r";",
        "message": "Multiple SQL statements are not allowed",
        "severity": "error",
    },
]


def _month_start(value: date) -> date:
    return value.replace(day=1)


class SemanticLayer:
    def __init__(self) -> None:
        self.definitions = BUSINESS_DEFINITIONS
        self.schema = SCHEMA_DESCRIPTIONS
        self.templates = QUERY_TEMPLATES
        self.rules = VALIDATION_RULES

    def match_template(self, query: str) -> Optional[tuple[str, str]]:
        query_lower = query.lower().strip()
        today = date.today()
        current_month = _month_start(today)
        previous_month = _month_start(current_month - timedelta(days=1))

        for name, template in self.templates.items():
            if not re.search(template["pattern"], query_lower):
                continue

            limit_match = re.search(r"top\s*(\d+)", query_lower)
            limit = min(max(int(limit_match.group(1)), 1), 20) if limit_match else 5
            start_date = today - timedelta(days=30)
            end_date = today + timedelta(days=1)
            if "yesterday" in query_lower:
                start_date, end_date = today - timedelta(days=1), today
            elif "today" in query_lower:
                start_date = today
            elif "last week" in query_lower:
                start_date, end_date = today - timedelta(days=14), today - timedelta(days=7)
            elif "this week" in query_lower:
                start_date = today - timedelta(days=7)
            elif "last month" in query_lower and name == "revenue_by_period":
                start_date, end_date = previous_month, current_month
            elif "this month" in query_lower:
                start_date = current_month
            elif "this year" in query_lower:
                start_date = today.replace(month=1, day=1)
            elif name in {"dead_stock_analysis", "aov_trend"}:
                start_date = today - timedelta(days=90 if name == "dead_stock_analysis" else 180)

            sql = (
                template["sql"]
                .format(
                    limit=limit,
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    current_start=current_month.isoformat(),
                    previous_start=previous_month.isoformat(),
                )
                .strip()
            )
            logger.info("Matched AI query template: %s", name)
            return name, sql
        return None

    @staticmethod
    def inject_outlet_filter(sql: str, outlet_ids: list[int]) -> tuple[str, dict[str, int]]:
        marker_pattern = re.compile(r"__OUTLET_SCOPE_(\w+)__")
        aliases = set(marker_pattern.findall(sql))
        if not aliases:
            return sql, {}
        if not outlet_ids:
            return marker_pattern.sub("1=0", sql), {}

        params = {f"outlet_{index}": outlet_id for index, outlet_id in enumerate(outlet_ids)}
        placeholders = ", ".join(f":{key}" for key in params)
        for alias in aliases:
            sql = sql.replace(f"__OUTLET_SCOPE_{alias}__", f"{alias}.outlet_id IN ({placeholders})")
        return sql, params

    def validate_sql(self, sql: str) -> tuple[bool, list[dict[str, str]]]:
        issues: list[dict[str, str]] = []
        if not sql.lstrip().upper().startswith("SELECT"):
            issues.append({"rule": "select_only", "message": "Query must start with SELECT", "severity": "error"})
        for rule in self.rules:
            if re.search(rule["pattern"], sql, re.IGNORECASE):
                issues.append(rule.copy())

        allowed = set(self.schema)
        referenced = re.findall(r"\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)", sql, re.IGNORECASE)
        for table in referenced:
            if table.lower() not in allowed:
                issues.append({"rule": "known_tables", "message": f"Unknown table: {table}", "severity": "error"})
        return not any(item["severity"] == "error" for item in issues), issues


semantic_layer = SemanticLayer()

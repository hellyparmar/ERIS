"""
Semantic Layer for AI Assistant
Provides business definitions and schema context to improve LLM-to-SQL accuracy.
Created: January 2026

This layer addresses the 40-50% SQL accuracy problem by:
1. Providing clear business term definitions
2. Schema descriptions with column types
3. Pre-approved query templates for common requests
4. Validation rules to catch common errors
"""

from typing import Dict, List, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# BUSINESS DEFINITIONS - Map business terms to SQL expressions
# ============================================================================

BUSINESS_DEFINITIONS = {
    # Revenue Metrics
    "revenue": "SUM(total_amount)",
    "total_revenue": "SUM(total_amount)",
    "sales": "SUM(total_amount)",
    "net_revenue": "SUM(total_amount - COALESCE(tax, 0) - COALESCE(discount, 0))",
    "gross_revenue": "SUM(total_amount)",
    
    # Volume Metrics
    "orders": "COUNT(DISTINCT id)",
    "order_count": "COUNT(DISTINCT id)",
    "transactions": "COUNT(DISTINCT transaction_id)",
    "units_sold": "SUM(quantity)",
    "quantity": "SUM(quantity)",
    
    # Average Metrics
    "average_order_value": "ROUND(SUM(total_amount) / COUNT(DISTINCT id), 2)",
    "aov": "ROUND(SUM(total_amount) / COUNT(DISTINCT id), 2)",
    "average_price": "ROUND(AVG(unit_price), 2)",
    
    # Time-based
    "today": "DATE(transaction_date) = DATE('now')",
    "yesterday": "DATE(transaction_date) = DATE('now', '-1 day')",
    "this_week": "transaction_date >= DATE('now', '-7 days')",
    "last_week": "transaction_date >= DATE('now', '-14 days') AND transaction_date < DATE('now', '-7 days')",
    "this_month": "strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now')",
    "last_month": "strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now', '-1 month')",
    "this_year": "strftime('%Y', transaction_date) = strftime('%Y', 'now')",
    
    # Customer Metrics
    "unique_customers": "COUNT(DISTINCT customer_id)",
    "customer_count": "COUNT(DISTINCT customer_id)",
    "repeat_customers": "COUNT(DISTINCT customer_id) FILTER (WHERE customer_id IN (SELECT customer_id FROM sales GROUP BY customer_id HAVING COUNT(*) > 1))",

    # Inventory Metrics
    "dead_stock": "stock > 0 AND id NOT IN (SELECT product_id FROM sales WHERE transaction_date >= DATE('now', '-90 days'))",
    "stock_turnover": "SUM(quantity) / AVG(stock)",
    "days_inventory_outstanding": "(AVG(stock) / SUM(quantity)) * 365",
    "stock_value": "SUM(stock * cost)",
}

# ============================================================================
# DATA TRANSLATION - Map raw database values to User-Friendly English
# ============================================================================

CATEGORY_MAPPING = {
    "moveis_decoracao": "Restaurant Interiors",
    "moveis_cozinha_area_de_servico_jantar_e_jardim": "Kitchen Area Furniture",
    "cama_mesa_banho": "Table Linens",
    "utilidades_domesticas": "Kitchen Equipment",
    "eletrodomesticos": "Commercial Appliances",
    "eletrodomesticos_2": "Commercial Appliances",
    "eletroportateis": "Food Prep Equipment",
    "casa_conforto": "Ambiance & Comfort",
    "casa_conforto_2": "Ambiance & Comfort",
    "alimentos": "Raw Ingredients",
    "alimentos_bebidas": "Food & Beverages",
    "bebidas": "Bar Inventory",
    "la_cuisine": "Gourmet Supplies",
    "portateis_cozinha_e_preparadores_de_alimentos": "Prep Machines",
    "informatica_acessorios": "Electronics Accessories",
    "telefonia": "Mobile Phones",
    "eletronicos": "Electronics",
    "bebes": "Kids Menu Toys",
    "esporte_lazer": "Staff Recreation"
}


# ============================================================================
# DATABASE SCHEMA - Describe tables and columns for LLM context
# ============================================================================

SCHEMA_DESCRIPTIONS = {
    "sales": {
        "description": "Transaction-level sales data. Each row is a product sold in a transaction.",
        "columns": {
            "id": "INTEGER PRIMARY KEY - Unique sale record ID",
            "transaction_id": "VARCHAR(100) - Transaction identifier (groups items in same order)",
            "product_id": "INTEGER - Foreign key to products table",
            "customer_id": "INTEGER - Foreign key to customers table (nullable)",
            "store_id": "INTEGER - Store location identifier",
            "transaction_date": "DATETIME - When the sale occurred",
            "quantity": "INTEGER - Number of units sold",
            "unit_price": "DECIMAL(12,2) - Price per unit",
            "discount": "DECIMAL(12,2) - Discount applied (nullable)",
            "tax": "DECIMAL(12,2) - Tax amount (nullable)",
            "total_amount": "DECIMAL(12,2) - Final amount charged",
            "payment_method": "VARCHAR(50) - cash/card/upi/credit",
            "payment_status": "VARCHAR(7) - paid/pending",
        }
    },
    "products": {
        "description": "Product catalog with pricing and inventory info.",
        "columns": {
            "id": "INTEGER PRIMARY KEY - Unique product ID",
            "name": "VARCHAR(255) - Product name",
            "sku": "VARCHAR(100) - Stock keeping unit",
            "category": "VARCHAR(100) - Product category",
            "price": "DECIMAL(12,2) - List price",
            "cost": "DECIMAL(12,2) - Cost price (for margin calculation)",
            "stock": "INTEGER - Current stock quantity",
        }
    },
    "customers": {
        "description": "Customer profiles with contact info.",
        "columns": {
            "id": "INTEGER PRIMARY KEY - Unique customer ID",
            "name": "VARCHAR(255) - Customer name",
            "email": "VARCHAR(255) - Email address",
            "phone": "VARCHAR(20) - Phone number",
            "created_at": "DATETIME - Registration date",
        }
    },
    "inventory": {
        "description": "Current stock levels by product and location.",
        "columns": {
            "id": "INTEGER PRIMARY KEY",
            "product_id": "INTEGER - Foreign key to products",
            "location": "VARCHAR(100) - Warehouse/store location",
            "quantity": "INTEGER - Current stock",
            "reorder_point": "INTEGER - Minimum before reorder alert",
        }
    }
}


# ============================================================================
# QUERY TEMPLATES - Pre-approved SQL patterns for common questions
# ============================================================================

QUERY_TEMPLATES = {
    "top_products_by_revenue": {
        "pattern": r"top\s*(\d+)?\s*products?\s*(by\s+)?(revenue|sales)",
        "sql": """
            SELECT p.name, SUM(s.total_amount) as revenue, SUM(s.quantity) as units
            FROM sales s
            JOIN products p ON s.product_id = p.id
            WHERE {date_filter}
            GROUP BY p.id, p.name
            ORDER BY revenue DESC
            LIMIT {limit}
        """,
        "defaults": {"limit": 5, "date_filter": "1=1"}
    },
    
    "revenue_by_period": {
        "pattern": r"(total\s+)?(revenue|sales)\s+(last|this)\s+(week|month|year)",
        "sql": """
            SELECT SUM(total_amount) as total_revenue,
                   COUNT(DISTINCT id) as order_count,
                   ROUND(SUM(total_amount) / COUNT(DISTINCT id), 2) as avg_order_value
            FROM sales
            WHERE {date_filter}
        """,
        "defaults": {}
    },
    
    "daily_sales_trend": {
        "pattern": r"(daily|day\s*wise)\s*(sales|revenue)\s*(trend)?",
        "sql": """
            SELECT DATE(transaction_date) as date,
                   SUM(total_amount) as revenue,
                   COUNT(DISTINCT id) as orders
            FROM sales
            WHERE transaction_date >= DATE('now', '-30 days')
            GROUP BY DATE(transaction_date)
            ORDER BY date
        """,
        "defaults": {}
    },
    
    "top_customers": {
        "pattern": r"top\s*(\d+)?\s*customers?\s*(by\s+)?(revenue|spend|value)",
        "sql": """
            SELECT c.name, c.email, SUM(s.total_amount) as total_spend,
                   COUNT(DISTINCT s.transaction_id) as order_count
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            WHERE {date_filter}
            GROUP BY c.id, c.name, c.email
            ORDER BY total_spend DESC
            LIMIT {limit}
        """,
        "defaults": {"limit": 10, "date_filter": "1=1"}
    },
    
    "low_stock_products": {
        "pattern": r"low\s*stock|out\s*of\s*stock|reorder|inventory\s*alert",
        "sql": """
            SELECT p.name, p.sku, i.quantity as current_stock, i.reorder_point
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            WHERE i.quantity <= i.reorder_point
            ORDER BY (i.quantity - i.reorder_point)
        """,
        "defaults": {}
    },
    
    "category_performance": {
        "pattern": r"(category|categories)\s*(performance|sales|revenue|breakdown)",
        "sql": """
            SELECT p.category, SUM(s.total_amount) as revenue,
                   SUM(s.quantity) as units_sold,
                   COUNT(DISTINCT s.id) as transactions
            FROM sales s
            JOIN products p ON s.product_id = p.id
            WHERE {date_filter}
            GROUP BY p.category
            ORDER BY revenue DESC
        """,
        "defaults": {"date_filter": "1=1"}
    },

    "dead_stock_analysis": {
        "pattern": r"(dead|stagnant|slow\s*moving)\s*(stock|inventory|products|items)",
        "sql": """
            SELECT p.name, p.sku, p.category, i.quantity as stock_on_hand, (i.quantity * p.cost) as tied_capital
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            WHERE i.quantity > 0 
            AND i.product_id NOT IN (
                SELECT product_id FROM sales 
                WHERE transaction_date >= DATE('now', '-90 days')
            )
            ORDER BY tied_capital DESC
            LIMIT {limit}
        """,
        "defaults": {"limit": 20}
    }
}


# ============================================================================
# VALIDATION RULES - Catch common SQL generation errors
# ============================================================================

VALIDATION_RULES = [
    {
        "name": "prevent_select_star",
        "pattern": r"SELECT\s+\*",
        "message": "Avoid SELECT * - specify columns explicitly",
        "severity": "warning"
    },
    {
        "name": "prevent_delete",
        "pattern": r"DELETE\s+FROM",
        "message": "DELETE command blocked - read-only access",
        "severity": "error"
    },
    {
        "name": "prevent_drop",
        "pattern": r"DROP\s+(TABLE|DATABASE|INDEX|VIEW)",
        "message": "DROP command blocked - destructive operation",
        "severity": "error"
    },
    {
        "name": "prevent_truncate",
        "pattern": r"TRUNCATE",
        "message": "TRUNCATE blocked - destructive operation",
        "severity": "error"
    },
    {
        "name": "prevent_update",
        "pattern": r"UPDATE\s+\w+\s+SET",
        "message": "UPDATE command blocked - read-only access",
        "severity": "error"
    },
    {
        "name": "prevent_insert",
        "pattern": r"INSERT\s+INTO",
        "message": "INSERT command blocked - read-only access",
        "severity": "error"
    },
    {
        "name": "check_table_exists",
        "pattern": r"FROM\s+(\w+)",
        "allowed_tables": ["sales", "products", "customers", "inventory", "invoices", "alerts", "sale_items", "users"],
        "message": "Unknown table referenced",
        "severity": "error"
    }
]


class SemanticLayer:
    """
    Semantic layer for improving LLM-to-SQL accuracy.
    
    Usage:
        layer = SemanticLayer()
        enhanced_prompt = layer.enhance_prompt(user_query)
        sql = layer.match_template(user_query)
        validation = layer.validate_sql(generated_sql)
    """
    
    def __init__(self):
        self.definitions = BUSINESS_DEFINITIONS
        self.schema = SCHEMA_DESCRIPTIONS
        self.templates = QUERY_TEMPLATES
        self.rules = VALIDATION_RULES
    
    def get_schema_context(self) -> str:
        """
        Generate schema description for LLM context.
        """
        context_parts = ["## Database Schema\n"]
        
        for table_name, table_info in self.schema.items():
            context_parts.append(f"### Table: {table_name}")
            context_parts.append(f"Description: {table_info['description']}")
            context_parts.append("Columns:")
            for col_name, col_desc in table_info['columns'].items():
                context_parts.append(f"  - {col_name}: {col_desc}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_translation_context(self) -> str:
        """
        Generate translation context for category names.
        """
        context_parts = ["## Category Translations (IMPORTANT)\n"]
        context_parts.append("The database uses Portuguese category names. You MUST TRANSLATE them to English equivalents in your final response:\n")
        
        for portuguese, english in CATEGORY_MAPPING.items():
            context_parts.append(f"- **{portuguese}** → **{english}**")
            # Also add reverse mapping for query understanding
            context_parts.append(f"- (User asks for '{english}') → Use '{portuguese}' in SQL")
            
        return "\n".join(context_parts)
    
    def get_business_terms_context(self) -> str:
        """
        Generate business terms glossary for LLM context.
        """
        context_parts = ["## Business Terms Glossary\n"]
        context_parts.append("When users ask about these terms, use the following SQL expressions:\n")
        
        for term, sql_expr in self.definitions.items():
            context_parts.append(f"- **{term}**: `{sql_expr}`")
        
        return "\n".join(context_parts)
    
    def enhance_prompt(self, user_query: str, include_schema: bool = True) -> str:
        """
        Enhance the system prompt with semantic layer context.
        """
        parts = [
            "You are an AI assistant for R-DIOS, a retail intelligence system.",
            "When generating SQL queries, follow these rules strictly:",
            "",
        ]
        
        if include_schema:
            parts.append(self.get_schema_context())
        
        parts.append(self.get_business_terms_context())
        
        # Add translation context
        parts.append(self.get_translation_context())
        
        parts.extend([
            "",
            "## Important SQL Rules:",
            "1. Only use tables: sales, products, customers, inventory",
            "2. Always specify columns explicitly (no SELECT *)",
            "3. Use DATE() for date comparisons",
            "4. Use COALESCE for nullable columns (tax, discount)",
            "5. For date columns, use 'transaction_date' not 'date'",
            "6. Join products table when you need product names",
            "7. IF generating results, replace raw category names with their English translations defined above.",
            "",
            f"User Query: {user_query}",
        ])
        
        return "\n".join(parts)
    
    def match_template(self, query: str) -> Optional[Tuple[str, dict]]:
        """
        Check if query matches a pre-approved template.
        Returns (template_name, filled_sql) if matched, None otherwise.
        """
        query_lower = query.lower()
        
        for template_name, template_info in self.templates.items():
            match = re.search(template_info['pattern'], query_lower)
            if match:
                # Fill in template with defaults
                sql = template_info['sql'].strip()
                for key, default_value in template_info['defaults'].items():
                    # Try to extract values from query
                    if key == 'limit':
                        limit_match = re.search(r'top\s*(\d+)', query_lower)
                        value = int(limit_match.group(1)) if limit_match else default_value
                    elif key == 'date_filter':
                        if 'last month' in query_lower:
                            value = "strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now', '-1 month')"
                        elif 'last week' in query_lower:
                            value = "transaction_date >= DATE('now', '-7 days')"
                        elif 'this month' in query_lower:
                            value = "strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now')"
                        elif 'this year' in query_lower:
                            value = "strftime('%Y', transaction_date) = strftime('%Y', 'now')"
                        else:
                            value = default_value
                    else:
                        value = default_value
                    
                    sql = sql.replace('{' + key + '}', str(value))
                
                logger.info(f"Matched template: {template_name}")
                return (template_name, sql)
        
        return None
    
    def validate_sql(self, sql: str) -> Tuple[bool, List[dict]]:
        """
        Validate generated SQL against security rules.
        Returns (is_valid, list of issues).
        """
        issues = []
        sql_upper = sql.upper()
        
        for rule in self.rules:
            if rule['name'] == 'check_table_exists':
                # Special handling for table validation
                tables_found = re.findall(r'FROM\s+(\w+)', sql, re.IGNORECASE)
                for table in tables_found:
                    if table.lower() not in rule['allowed_tables']:
                        issues.append({
                            'rule': rule['name'],
                            'message': f"{rule['message']}: {table}",
                            'severity': rule['severity']
                        })
            else:
                if re.search(rule['pattern'], sql_upper):
                    issues.append({
                        'rule': rule['name'],
                        'message': rule['message'],
                        'severity': rule['severity']
                    })
        
        has_errors = any(issue['severity'] == 'error' for issue in issues)
        return (not has_errors, issues)
    
    def calculate_confidence(self, query: str, generated_sql: str) -> Tuple[int, str]:
        """
        Calculate confidence score for generated SQL.
        Returns (confidence_percentage, reasoning).
        """
        score = 70  # Base score
        reasons = []
        
        # Check if matched template
        template_match = self.match_template(query)
        if template_match:
            score += 20
            reasons.append("Matched pre-approved template")
        
        # Check if uses known tables
        tables_found = re.findall(r'FROM\s+(\w+)', generated_sql, re.IGNORECASE)
        known_tables = {'sales', 'products', 'customers', 'inventory'}
        if all(t.lower() in known_tables for t in tables_found):
            score += 5
            reasons.append("Uses verified tables")
        else:
            score -= 20
            reasons.append("Uses unknown tables")
        
        # Check if uses business terms correctly
        for term in self.definitions:
            if term in query.lower():
                if self.definitions[term] in generated_sql:
                    score += 2
                    reasons.append(f"Correctly uses '{term}' definition")
        
        # Validation check
        is_valid, issues = self.validate_sql(generated_sql)
        if not is_valid:
            score -= 30
            reasons.append(f"Validation issues: {len(issues)}")
        
        # Cap score
        score = max(0, min(100, score))
        
        reasoning = "; ".join(reasons) if reasons else "Standard generation"
        return (score, reasoning)


# Singleton instance
semantic_layer = SemanticLayer()

# AI Database Integration - Developer Quick Reference

## What Was Built

A complete database integration layer for the AI Assistant that allows the chat widget to:
- Execute SQL queries against the R-DIOS database
- Format results for natural language AI responses
- Return both AI responses AND database results to the frontend

## Architecture

```
User Chat Input
    ↓
Semantic Layer (matches to templates)
    ↓
Query Executor (runs SQL safely)
    ↓
Format Results (convert to text)
    ↓
AI Service (injects context + gets response)
    ↓
Chat API (returns response + data)
    ↓
Frontend (displays AI response + table)
```

## Key Components

### 1. QueryExecutor (`api/services/query_executor.py`)
```python
from api.services.query_executor import query_executor

# Execute a query
result = query_executor.execute_query("SELECT * FROM sales LIMIT 10")

# Format results for AI
formatted = query_executor.format_results_for_llm(result)

# Execute with validation
result = query_executor.execute_template_query(sql, semantic_layer)
```

**Returns**:
```python
{
    "success": True,
    "data": [{"id": 1, "amount": 100}, ...],
    "row_count": 10,
    "execution_time_ms": 5.2,
    "error": None
}
```

### 2. Enhanced AI Service
```python
from api.services.ai_service import ai_service

# Generate response with database context
response = await ai_service.generate_response(
    message="Show me top products",
    system_prompt="You are helpful...",
    session_history=[],
    execute_templates=True  # NEW: Execute database queries
)
```

### 3. Updated Chat API
```
POST /api/v1/ai/chat
{
    "message": {
        "text": "What was our revenue last month?",
        "language": "en",
        "script": "roman"
    },
    "session_id": "user-123"
}

Response:
{
    "message": {
        "text": "Based on your data, last month's revenue was..."
    },
    "query_result": {
        "success": true,
        "data": [{...}],
        "row_count": 1,
        "execution_time_ms": 45.2
    }
}
```

## Usage Examples

### Example 1: Direct Query Execution
```python
from api.services.query_executor import query_executor

sql = """
SELECT category, SUM(total_amount) as revenue
FROM sales s
JOIN sale_items si ON s.id = si.sale_id
JOIN products p ON si.product_id = p.id
GROUP BY category
ORDER BY revenue DESC
"""

result = query_executor.execute_query(sql)
print(f"Top category: {result['data'][0]}")
```

### Example 2: With Semantic Layer Validation
```python
from api.services.semantic_layer import semantic_layer
from api.services.query_executor import query_executor

sql = "SELECT COUNT(*) as customers FROM customers"
result = query_executor.execute_template_query(sql, semantic_layer)

if result["success"]:
    formatted = query_executor.format_results_for_llm(result)
    # Use 'formatted' in AI system prompt
```

### Example 3: Frontend Integration
```javascript
// Send message to AI with database
const response = await fetch('http://localhost:8000/api/v1/ai/chat', {
    method: 'POST',
    body: JSON.stringify({
        message: {
            text: "Show me top customers",
            language: "en",
            script: "roman"
        },
        session_id: "user-123"
    })
});

const data = await response.json();

// Use AI response
console.log(data.message.text);

// Use database results
if (data.query_result?.success) {
    console.log(data.query_result.data);
}
```

## Database Schema

**Available Tables**:

| Table | Rows | Key Columns |
|-------|------|------------|
| `sales` | 100,000 | id, customer_id, total_amount, transaction_date |
| `sale_items` | 199,337 | sale_id, product_id, quantity, unit_price |
| `products` | 26,400 | id, name, category, selling_price, cost_price |
| `customers` | 99,000 | id, name, email, total_spent, lifetime_value |
| `users` | 3 | id, username, password_hash (for auth) |

**Key Relationships**:
```
sales (sale_id) ──→ sale_items ──→ products
     └─ customer_id ──→ customers
```

## Testing

### Run Integration Tests
```bash
python test_ai_database_integration.py
```

### Quick CLI Test
```bash
python3 << 'EOF'
from api.services.query_executor import query_executor

result = query_executor.execute_query(
    "SELECT COUNT(*) as count FROM sales"
)
print(f"Total sales: {result['data'][0]['count']}")
EOF
```

## Performance Metrics

| Query Type | Execution Time |
|------------|-----------------|
| Count/Simple | 1-10ms |
| Aggregates | 5-20ms |
| Joins | 50-350ms |
| Complex Analysis | <500ms |

## Error Handling

```python
result = query_executor.execute_query(sql)

if result["success"]:
    print(f"Got {result['row_count']} rows")
else:
    print(f"Error: {result['error']}")
    # error formats:
    # - "Only SELECT queries allowed"
    # - "Database error: [sqlite3 error]"
    # - "Unexpected error: [exception]"
```

## Common Queries

### Top Products
```sql
SELECT p.name, SUM(si.quantity) as units_sold, SUM(s.total_amount) as revenue
FROM sale_items si
JOIN sales s ON si.sale_id = s.id
JOIN products p ON si.product_id = p.id
GROUP BY p.id, p.name
ORDER BY revenue DESC
LIMIT 10
```

### Revenue by Month
```sql
SELECT 
    STRFTIME('%Y-%m', transaction_date) as month,
    COUNT(*) as orders,
    SUM(total_amount) as revenue
FROM sales
GROUP BY STRFTIME('%Y-%m', transaction_date)
ORDER BY month DESC
```

### Customer Analytics
```sql
SELECT 
    name, 
    COUNT(*) as orders,
    SUM(total_amount) as total_spent,
    AVG(total_amount) as avg_order_value
FROM sales s
JOIN customers c ON s.customer_id = c.id
GROUP BY s.customer_id
ORDER BY total_spent DESC
LIMIT 20
```

## Debugging

### Enable SQL Logging
```python
import logging
logging.getLogger('api.services.query_executor').setLevel(logging.DEBUG)
```

### Check Database Connection
```bash
sqlite3 api/rdios_dev.db ".tables"
```

### Verify Module Imports
```bash
python3 -c "from api.services.query_executor import query_executor; print('✓ OK')"
```

## Deployment

### Prerequisites
```bash
# Install dependencies (already in requirements.txt)
pip install -r requirements.txt

# Set environment variable
export DATABASE_URL=api/rdios_dev.db
```

### Start Backend
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Verify Integration
```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": {"text": "Show revenue", "language": "en", "script": "roman"},
    "session_id": "test"
  }'
```

## Future Enhancements

1. **Caching**: Cache frequent queries
2. **Pagination**: Support large result sets
3. **Filters**: User-specific data filtering
4. **Analytics**: Track AI query accuracy
5. **Real-time**: Stream results for large queries
6. **Export**: Download results as CSV/Excel

## Support

For issues with database integration:
1. Check `test_ai_database_integration.py` for examples
2. Review logs: `tail -f logs/api.log`
3. Verify database: `sqlite3 api/rdios_dev.db ".schema"`
4. Check configuration: `printenv | grep DATABASE`

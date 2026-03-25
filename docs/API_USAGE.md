# ERIS API Usage Guide

Welcome to the Enterprise Retail Intelligence System (ERIS) API. This guide provides instructions on how to interact with our endpoints effectively.

## Authentication Flow

ERIS uses JWT-based authentication. Most endpoints require a valid access token.

### 1. Register or Login

Send a POST request to `/api/v1/auth/login` with your credentials:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@example.com", "password": "password123"}'
```

### 2. Use the Token

Include the received token in the `Authorization` header for all protected requests:

```bash
curl -X GET "http://localhost:8000/api/v1/inventory/products" \
     -H "Authorization: Bearer <your_access_token>"
```

## Common Workflows

### Creating a Sale

To record a transaction, use the Sales endpoint. Note that stock is automatically deducted from inventory.

```bash
curl -X POST "http://localhost:8000/api/v1/sales/" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "customer_id": 1,
       "items": [{"product_id": 1, "quantity": 2, "unit_price": 49.99}],
       "payment_method": "credit_card"
     }'
```

## AI Intelligence Features

### Requesting a Forecast

The intelligence module provides ARIMA-based sales forecasting.

```bash
curl -X GET "http://localhost:8000/api/v1/intelligence/forecast?days=7" \
     -H "Authorization: Bearer <token>"
```

## Best Practices

- **Pagination**: Use `limit` and `offset` parameters for large list requests.
- **Rate Limiting**: Our API enforces a limit of 100 requests per minute per user.
- **Error Handling**: Always check the response status code and the `detail` field in the response body.

For a full list of endpoints and interactable examples, visit the auto-generated documentation at `/docs` or `/redoc`.

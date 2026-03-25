# Phase 2 & 3 Quick Reference Guide

## ABC Classification API

### Analyze Products (ABC Analysis)
```bash
POST /api/v1/inventory/abc/analyze?days=365
Authorization: Bearer {token}

Response:
{
  "status": "success",
  "a_items": [...],
  "b_items": [...],
  "c_items": [...],
  "summary": {
    "total_products": 245,
    "a_count": 32,
    "a_revenue_percentage": 80.2,
    ...
  }
}
```

### Get Items by Classification
```bash
GET /api/v1/inventory/abc/items/A
Authorization: Bearer {token}

Classification values: A, B, or C
Response includes: name, sku, price, stock, turnover
```

### Get Classification Metrics
```bash
GET /api/v1/inventory/abc/metrics
Authorization: Bearer {token}

Response shows current classification distribution
```

---

## Dead Stock Identification API

### Analyze Dead Stock
```bash
POST /api/v1/inventory/dead-stock/analyze?days=90
Authorization: Bearer {token}

Response includes:
- Dead stock items list
- Suggested discount percentages
- Total value at risk
- Disposal recommendations
```

### Analyze Slow-Moving Items
```bash
POST /api/v1/inventory/slow-moving/analyze?days=30
Authorization: Bearer {token}

Returns items with:
- Daily velocity
- Stock coverage (days of inventory)
- Recommendations per item
```

### Get Dead Stock Summary
```bash
GET /api/v1/inventory/dead-stock/summary
Authorization: Bearer {token}

Response shows:
- Dead stock by category
- Total value at risk
- Potential recovery amount
```

### Export Dead Stock Analysis
```bash
GET /api/v1/inventory/dead-stock/export?format=csv
Authorization: Bearer {token}

Formats: json or csv
Use for management reporting
```

---

## Smart Stock Alerts API

### Get Active Alerts
```bash
GET /api/v1/inventory/alerts?severity=critical&limit=20
Authorization: Bearer {token}

Severity options: critical, warning, info
```

### Acknowledge Alert
```bash
POST /api/v1/inventory/alerts/{alert_id}/acknowledge
Authorization: Bearer {token}

Body: {"user_id": 123}
```

---

## Reorder Recommendations API

### Get Reorder Suggestions
```bash
GET /api/v1/inventory/reorder/suggestions
Authorization: Bearer {token}

Returns items needing reorder with:
- Suggested quantity
- Supplier info
- Lead time
- Priority ranking
```

---

## GST Invoice API

### Create Invoice with GST
```bash
POST /api/v1/invoices/create
Authorization: Bearer {token}

Body:
{
  "customer_id": 123,
  "items": [
    {
      "product_id": 456,
      "quantity": 2,
      "unit_rate": 500,
      "hsn_code": "4901",
      "tax_rate": "18"
    }
  ],
  "payment_method": "cash"
}

Response includes:
- Invoice ID
- GST breakdown (CGST, SGST, IGST)
- QR code
```

### Generate IRN (E-Invoice)
```bash
POST /api/v1/gst/e-invoice/{invoice_id}/generate-irn
Authorization: Bearer {token}

For GST portal compliance
Generates QR code with invoice details
```

---

## Khata (Credit) API

### Create Credit Account
```bash
POST /api/v1/credit/accounts/create
Authorization: Bearer {token}

Body:
{
  "customer_id": 123,
  "credit_limit": 50000,
  "terms_days": 30
}
```

### Record Credit Sale
```bash
POST /api/v1/credit/accounts/{customer_id}/transactions
Authorization: Bearer {token}

Body:
{
  "type": "sale",
  "amount": 5000,
  "invoice_id": "INV-001"
}
```

### Record Payment
```bash
POST /api/v1/credit/accounts/{customer_id}/payments
Authorization: Bearer {token}

Body:
{
  "amount": 5000,
  "payment_method": "cash",
  "date": "2026-03-02"
}
```

### Get Aging Report
```bash
GET /api/v1/credit/accounts/{customer_id}/aging-report
Authorization: Bearer {token}

Shows outstanding by age bucket:
- 0-30 days
- 30-60 days
- 60-90 days
- 90+ days
```

### Send Payment Reminder
```bash
POST /api/v1/credit/reminders/send
Authorization: Bearer {token}

Body:
{
  "customer_id": 123,
  "message": "Payment reminder for outstanding amount"
}

Sends via WhatsApp
```

---

## GST Configuration API

### Configure GST for Business
```bash
POST /api/v1/gst/configure
Authorization: Bearer {token}

Body:
{
  "business_type": "retail",
  "gstin": "18AABCT1234H1Z0",
  "state": "Gujarat",
  "category_rates": {
    "food": 5,
    "clothing": 12,
    "electronics": 18
  }
}
```

### Get Current GST Rates
```bash
GET /api/v1/gst/rates
Authorization: Bearer {token}

Shows all configured rates by category
```

### Update Rate
```bash
PUT /api/v1/gst/rates/{rate_id}
Authorization: Bearer {token}

Body:
{
  "rate_percentage": 18,
  "effective_date": "2026-04-01"
}
```

---

## Day Operations API

### Open Day
```bash
POST /api/v1/day-operations/open
Authorization: Bearer {token}

Body:
{
  "opening_cash": 10000,
  "business_id": 1
}
```

### Close Day
```bash
POST /api/v1/day-operations/close
Authorization: Bearer {token}

Body:
{
  "closing_cash": 12500,
  "business_id": 1
}

Response:
{
  "status": "success",
  "total_sales": 2500,
  "variance": 0,
  "variance_percentage": 0
}
```

### Get Day Summary
```bash
GET /api/v1/day-operations/summary/{business_id}
Authorization: Bearer {token}

Shows today's summary:
- Cash sales
- UPI sales
- Card sales
- Khata sales
- Variance
```

---

## Common Response Formats

### Success Response
```json
{
  "status": "success",
  "data": {...},
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "status": "error",
  "error": "Invalid input",
  "message": "Field 'amount' is required"
}
```

---

## Authentication

All endpoints require JWT token in header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Get Token
```bash
POST /api/v1/auth/login
Body:
{
  "username": "manager@store.com",
  "password": "password123"
}

Returns: {"token": "..."}
```

---

## Rate Limits

- Default: 100 requests/minute per user
- Sensitive operations: 10 requests/minute
- Analysis endpoints: 5 requests/minute (heavy operations)

---

## Example Workflows

### Workflow 1: Identify and Clear Dead Stock

1. **Analyze Dead Stock**
   ```bash
   POST /api/v1/inventory/dead-stock/analyze?days=90
   ```

2. **Review Recommendations**
   - Get suggested discounts
   - Check disposal options

3. **Export for Management**
   ```bash
   GET /api/v1/inventory/dead-stock/export?format=csv
   ```

4. **Update Prices** (using separate pricing API)
   - Apply suggested discounts

5. **Monitor Sales** (via alerts API)
   - Track clearance progress

---

### Workflow 2: Manage Credit Sales with Khata

1. **Create Credit Account**
   ```bash
   POST /api/v1/credit/accounts/create
   ```

2. **Record Sale**
   ```bash
   POST /api/v1/credit/accounts/{id}/transactions
   ```

3. **Monitor Due Dates**
   ```bash
   GET /api/v1/credit/accounts/{id}/aging-report
   ```

4. **Send Reminders**
   ```bash
   POST /api/v1/credit/reminders/send
   ```

5. **Record Payment**
   ```bash
   POST /api/v1/credit/accounts/{id}/payments
   ```

---

### Workflow 3: ABC Analysis for Inventory Control

1. **Run Analysis**
   ```bash
   POST /api/v1/inventory/abc/analyze?days=365
   ```

2. **Get A Items** (high value)
   ```bash
   GET /api/v1/inventory/abc/items/A
   ```

3. **Review Recommendations**
   - High stock control needed
   - Frequent monitoring required

4. **Get B & C Items**
   ```bash
   GET /api/v1/inventory/abc/items/B
   GET /api/v1/inventory/abc/items/C
   ```

5. **Adjust Reorder Points**
   - A Items: Higher safety stock
   - B Items: Standard control
   - C Items: Minimal stock

---

## Performance Tips

1. **ABC Analysis**: Run daily during off-hours
   - Configurable period: 30-1095 days
   - Impacts: Minimal (< 5 seconds)

2. **Dead Stock Detection**: Weekly or bi-weekly
   - Heavy operation for large catalogs
   - Recommended: Run at night

3. **Credit Reports**: Cache for 1 hour
   - Reloading frequently can impact performance
   - Consider pagination for large datasets

4. **GST Calculations**: Cached
   - Rates updated immediately on configuration change
   - No need to recalculate historical invoices

---

## Troubleshooting

### ABC Analysis Returns Empty
- **Cause**: No sales data in period
- **Solution**: Check if product has sales in selected period
- **Check**: `GET /api/v1/products/{id}` for last_sale_date

### Dead Stock List Shows All Products
- **Cause**: Classification period too long
- **Solution**: Reduce days parameter (default: 90)
- **Check**: Ensure sales data is being recorded

### Khata Reminders Not Sending
- **Cause**: WhatsApp not configured
- **Solution**: Check WhatsApp integration settings
- **Verify**: Customer phone number in database

### GST Rates Not Updating
- **Cause**: Cache not cleared
- **Solution**: Restart API server or clear cache
- **Check**: Verify effective_date in database

---

## API Documentation

Full Swagger documentation available at:
```
http://localhost:8000/docs
```

Try endpoints directly in Swagger UI with authentication token.

---

## Support

For issues or questions:
1. Check this guide first
2. Review Swagger documentation
3. Check database schema in models_v6.py
4. Review service implementations in api/services/
5. Contact development team

---

Last Updated: 2 March 2026
Version: 1.0
Status: Production Ready ✅

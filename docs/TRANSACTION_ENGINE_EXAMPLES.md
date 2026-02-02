# Transaction Engine - Usage Examples
**R-DIOS v5.0 Phase 2**

---

## 🎯 Overview

The Transaction Engine provides complete invoice management with:
- **GST Automation**: Automatic tax calculation based on HSN codes
- **Khata Tracking**: Credit management and partial payments
- **WhatsApp Receipts**: Automated receipt delivery via Twilio
- **PDF Generation**: Professional invoices with tax breakdown

---

## 📚 API Endpoints

Base URL: `http://localhost:8000/api/invoices`

### 1. Create Invoice from Sale

**POST** `/create`

```json
{
  "sale_id": 123,
  "payment_terms_days": 30,
  "send_whatsapp_receipt": true
}
```

**Response:**
```json
{
  "id": 45,
  "invoice_number": "INV-20260119-0001",
  "customer_id": 789,
  "invoice_date": "2026-01-19T23:30:00",
  "due_date": "2026-02-18T23:30:00",
  "total_amount": 15000.00,
  "amount_paid": 0.00,
  "amount_due": 15000.00,
  "payment_status": "pending",
  "hsn_code": "8517",
  "tax_rate": 18.00
}
```

### 2. Record Payment (Khata)

**POST** `/record-payment`

```json
{
  "invoice_id": 45,
  "amount": 5000.00,
  "payment_method": "upi",
  "reference_number": "UPI123456789",
  "notes": "First installment",
  "send_receipt": true
}
```

**Response:**
```json
{
  "id": 12,
  "invoice_id": 45,
  "amount_paid": 5000.00,
  "payment_method": "upi",
  "payment_date": "2026-01-19T23:35:00",
  "reference_number": "UPI123456789"
}
```

### 3. Get Invoice Summary

**GET** `/45/summary`

**Response:**
```json
{
  "invoice": {
    "invoice_number": "INV-20260119-0001",
    "customer_id": 789,
    "invoice_date": "2026-01-19T23:30:00",
    "due_date": "2026-02-18T23:30:00",
    "hsn_code": "8517",
    "tax_rate": 18.0,
    "taxable_amount": 12711.86,
    "tax_amount": 2288.14,
    "total_amount": 15000.00,
    "amount_paid": 5000.00,
    "amount_due": 10000.00,
    "payment_status": "partial",
    "receipt_sent_via": "whatsapp"
  },
  "payments": [
    {
      "id": 12,
      "amount": 5000.00,
      "method": "upi",
      "reference": "UPI123456789",
      "date": "2026-01-19T23:35:00",
      "notes": "First installment"
    }
  ],
  "payment_count": 1,
  "is_overdue": false
}
```

### 4. Download Invoice PDF

**GET** `/45/pdf`

Downloads PDF file: `invoice_INV-20260119-0001.pdf`

**PDF Contents:**
- Company details with GSTIN
- Invoice number and dates
- HSN code and GST breakdown
- Payment history
- Payment status stamp

### 5. Get Customer Khata (Credit Ledger)

**GET** `/customer/789/khata`

**Response:**
```json
{
  "customer_id": 789,
  "credit_limit": 50000.00,
  "current_balance": 10000.00,
  "available_credit": 40000.00,
  "credit_score": 72,
  "last_payment_date": "2026-01-19T23:35:00",
  "pending_invoices_count": 2,
  "partial_invoices_count": 1,
  "total_outstanding": 25000.00
}
```

### 6. Get Overdue Invoices

**GET** `/overdue?days=7`

**Response:** List of invoices overdue by at least 7 days

### 7. Send Payment Reminders

**POST** `/send-reminders?min_days_overdue=1`

**Response:**
```json
{
  "total_overdue": 15,
  "reminders_attempted": 12,
  "results": {
    "sent": 10,
    "failed": 0,
    "simulated": 2
  }
}
```

### 8. Invoice Statistics

**GET** `/stats/summary`

**Response:**
```json
{
  "total_invoices": 250,
  "by_status": {
    "paid": 180,
    "partial": 40,
    "pending": 25,
    "overdue": 5
  },
  "financials": {
    "total_revenue": 5000000.00,
    "total_collected": 4500000.00,
    "total_outstanding": 500000.00,
    "collection_rate": 90.0
  }
}
```

---

## 🔧 Python Usage Examples

### Example 1: Create Invoice with GST

```python
from api.services.invoice_service import InvoiceService
from api.db.database import SessionLocal

db = SessionLocal()
service = InvoiceService(db)

# Create invoice from sale
invoice = service.create_invoice_from_sale(
    sale_id=123,
    payment_terms_days=30
)

print(f"Invoice created: {invoice.invoice_number}")
print(f"GST @ {invoice.tax_rate}%: ₹{invoice.tax_amount}")
print(f"Total: ₹{invoice.total_amount}")

db.close()
```

**Output:**
```
Invoice created: INV-20260119-0001
GST @ 18.0%: ₹2288.14
Total: ₹15000.00
```

### Example 2: Record Partial Payment

```python
from decimal import Decimal

# Record payment
payment = service.record_payment(
    invoice_id=45,
    amount=Decimal("5000.00"),
    payment_method="upi",
    reference_number="UPI123456789"
)

# Check updated balance
invoice = service.db.query(Invoice).get(45)
print(f"Paid: ₹{invoice.amount_paid}")
print(f"Due: ₹{invoice.amount_due}")
print(f"Status: {invoice.payment_status.value}")
```

**Output:**
```
Paid: ₹5000.00
Due: ₹10000.00
Status: partial
```

### Example 3: Generate PDF Invoice

```python
from api.services.invoice_pdf_generator import InvoicePDFGenerator

# Get invoice summary
summary = service.get_invoice_summary(45)

# Generate PDF
pdf_generator = InvoicePDFGenerator()
pdf_generator.save_invoice_pdf(
    invoice_data=summary,
    output_path="invoices/INV-20260119-0001.pdf"
)

print("PDF saved to invoices/INV-20260119-0001.pdf")
```

### Example 4: Send WhatsApp Receipt

```python
from api.services.whatsapp_service import WhatsAppReceiptService

whatsapp = WhatsAppReceiptService()

result = whatsapp.send_invoice_receipt(
    customer_whatsapp="+91-98765-43210",
    invoice_number="INV-20260119-0001",
    total_amount=15000.00,
    amount_due=10000.00,
    payment_status="partial"
)

print(f"WhatsApp status: {result['status']}")
```

**Output:**
```
WhatsApp status: sent
```

**WhatsApp Message:**
```
⏳ *Invoice Receipt - R-DIOS*

*Invoice #:* INV-20260119-0001
*Total Amount:* ₹15,000.00
*Amount Due:* ₹10,000.00
*Status:* PARTIAL

Remaining balance: ₹10,000.00
Please clear dues at your earliest convenience.

📞 For queries: billing@rdios.com
🔒 Powered by R-DIOS Transaction Engine
```

### Example 5: Get Customer Khata Summary

```python
khata = service.get_khata_summary(customer_id=789)

print(f"Credit Limit: ₹{khata['credit_limit']:,.2f}")
print(f"Current Balance: ₹{khata['current_balance']:,.2f}")
print(f"Available Credit: ₹{khata['available_credit']:,.2f}")
print(f"Credit Score: {khata['credit_score']}/100")
print(f"Outstanding: ₹{khata['total_outstanding']:,.2f}")
```

**Output:**
```
Credit Limit: ₹50,000.00
Current Balance: ₹10,000.00
Available Credit: ₹40,000.00
Credit Score: 72/100
Outstanding: ₹25,000.00
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file:

```bash
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Database
USE_SQLITE=true
DATABASE_URL=sqlite:///./rdios_dev.db
```

### Company Information (Optional)

Customize PDF invoice header:

```python
company_info = {
    "name": "Your Store Name",
    "address": "123 Market St, Mumbai, MH 400001",
    "phone": "+91-98765-43210",
    "email": "billing@yourstore.com",
    "gstin": "27AABCU9603R1ZX",
    "pan": "AABCU9603R"
}

pdf_generator.generate_invoice_pdf(
    invoice_data=summary,
    company_info=company_info
)
```

---

## 🎨 Features Demonstrated

### 1. GST Automation ✅
- Automatic HSN code lookup from product
- Tax calculation: `tax = amount - (amount / (1 + rate/100))`
- Breakdown: Taxable amount, Tax amount, Total

### 2. Khata/Credit Management ✅
- Credit limits per customer (₹5k-₹50k)
- Current balance tracking
- Credit score (0-100) based on utilization
- Payment history with references

### 3. Installment Plans ✅
- Split payments across N installments
- First installment recorded automatically
- Track remaining balance

### 4. Overdue Management ✅
- Automatic status updates based on due date
- Bulk reminder sending via WhatsApp
- Days overdue tracking

### 5. Professional Invoices ✅
- PDF generation with ReportLab
- GST-compliant format
- Payment history included
- Status stamps (PAID/OVERDUE)

### 6. WhatsApp Integration ✅
- Receipt delivery via Twilio
- Payment confirmations
- Overdue reminders
- Bulk messaging support

---

## 📊 Example Workflow: Complete Transaction

```python
# 1. Sale occurs (already in database)
sale_id = 123

# 2. Create invoice with GST calculation
invoice = service.create_invoice_from_sale(
    sale_id=sale_id,
    payment_terms_days=30
)
# → Invoice: ₹15,000 (₹12,711.86 taxable + ₹2,288.14 GST @ 18%)

# 3. Customer pays first installment
payment1 = service.record_payment(
    invoice_id=invoice.id,
    amount=Decimal("5000.00"),
    payment_method="upi"
)
# → Status: PARTIAL, Due: ₹10,000

# 4. Send WhatsApp receipt
whatsapp.send_invoice_receipt(
    customer_whatsapp=invoice.customer.whatsapp_number,
    invoice_number=invoice.invoice_number,
    total_amount=15000.00,
    amount_due=10000.00,
    payment_status="partial"
)
# → WhatsApp sent ✅

# 5. Customer pays remaining amount
payment2 = service.record_payment(
    invoice_id=invoice.id,
    amount=Decimal("10000.00"),
    payment_method="cash"
)
# → Status: PAID, Due: ₹0

# 6. Generate final invoice PDF
pdf_generator.save_invoice_pdf(
    invoice_data=service.get_invoice_summary(invoice.id),
    output_path=f"invoices/{invoice.invoice_number}.pdf"
)
# → PDF with 2 payments listed
```

---

## 🚀 Testing the API

### Start Backend
```bash
cd api
uvicorn main:app --reload --port 8000
```

### View API Documentation
```
http://localhost:8000/docs
```

### Test with cURL

**Create Invoice:**
```bash
curl -X POST http://localhost:8000/api/invoices/create \
  -H "Content-Type: application/json" \
  -d '{"sale_id": 123, "payment_terms_days": 30}'
```

**Record Payment:**
```bash
curl -X POST http://localhost:8000/api/invoices/record-payment \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": 1,
    "amount": 5000.00,
    "payment_method": "upi",
    "reference_number": "UPI123456789"
  }'
```

**Get Khata:**
```bash
curl http://localhost:8000/api/invoices/customer/1/khata
```

**Download PDF:**
```bash
curl http://localhost:8000/api/invoices/1/pdf --output invoice.pdf
```

---

## ✅ Phase 2 Complete!

**What's Working**:
- ✅ GST calculation based on HSN codes
- ✅ Invoice generation with tax breakdown
- ✅ Khata/credit tracking with credit scores
- ✅ Partial payment recording
- ✅ PDF invoice generation (reportlab)
- ✅ WhatsApp receipt delivery (Twilio)
- ✅ Overdue management & reminders
- ✅ Complete REST API (12 endpoints)

**Next**: Phase 3 - Communication Hub (Unified Inbox)

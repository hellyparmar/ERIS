from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import random

# Anti-DDoS Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(title="R-DIOS API", version="3.0")

# Register Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Middleware
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "testserver", "*.googleapis.com"] # Add allowed hosts
)

# CORS - Allow frontend on multiple ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "System Online", "message": "R-DIOS Backend API v3.0 is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "3.0"}

# Mock API endpoints for demo
@app.get("/api/v1/dashboard/stats")
def get_dashboard_stats():
    return {
        "total_sales": 1250000,
        "total_orders": 3420,
        "total_customers": 856,
        "total_products": 245,
        "sales_growth": 12.5,
        "orders_growth": 8.3,
        "customers_growth": 15.2,
        "low_stock_count": 12
    }

@app.get("/api/v1/dashboard/recent-sales")
def get_recent_sales():
    return [
        {"id": "INV-001", "customer": "ABC Corp", "amount": 15000, "date": "2026-01-21", "status": "paid"},
        {"id": "INV-002", "customer": "XYZ Ltd", "amount": 22500, "date": "2026-01-21", "status": "pending"},
        {"id": "INV-003", "customer": "Demo Store", "amount": 8750, "date": "2026-01-20", "status": "paid"},
        {"id": "INV-004", "customer": "Retail Hub", "amount": 31200, "date": "2026-01-20", "status": "paid"},
        {"id": "INV-005", "customer": "Shop Plus", "amount": 12400, "date": "2026-01-19", "status": "pending"},
    ]

@app.get("/api/v1/analytics/sales-trend")
def get_sales_trend():
    return {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "data": [45000, 52000, 48000, 61000, 55000, 67000]
    }

@app.get("/api/v1/inventory/low-stock")
def get_low_stock():
    return [
        {"id": "P001", "name": "Product A", "current_stock": 5, "min_stock": 20, "status": "critical"},
        {"id": "P002", "name": "Product B", "current_stock": 15, "min_stock": 30, "status": "low"},
        {"id": "P003", "name": "Product C", "current_stock": 8, "min_stock": 25, "status": "critical"},
    ]

@app.get("/api/v1/forecasts/demand")
def get_demand_forecast():
    return {
        "product_id": "P001",
        "product_name": "Product A",
        "current_demand": 150,
        "forecasted_demand": [165, 178, 172, 185, 192, 188],
        "confidence": 0.87
    }

@app.get("/api/v1/alerts")
def get_alerts():
    return [
        {"id": 1, "type": "warning", "message": "Low stock alert: Product A", "timestamp": "2026-01-21T10:30:00"},
        {"id": 2, "type": "info", "message": "Sales target achieved", "timestamp": "2026-01-21T09:15:00"},
        {"id": 3, "type": "critical", "message": "Product C out of stock", "timestamp": "2026-01-20T16:45:00"},
    ]

@app.get("/api/v1/dashboard/realtime")
def get_dashboard_realtime():
    """Real-time dashboard metrics matching frontend expectations"""
    return {
        "total_revenue": 1250000,
        "today_revenue": 45000,
        "total_orders": 3420,
        "active_orders": 156,
        "avg_order_value": 365,
        "time_multiplier": 1.2,
        "data_source": "Live Data",
        "top_products": [
            {"rank": 1, "name": "Wireless Headphones", "revenue": 125000, "units_sold": 342},
            {"rank": 2, "name": "Smart Watch", "revenue": 98000, "units_sold": 245},
            {"rank": 3, "name": "Laptop Stand", "revenue": 76000, "units_sold": 380},
            {"rank": 4, "name": "USB-C Cable", "revenue": 54000, "units_sold": 900},
            {"rank": 5, "name": "Phone Case", "revenue": 45000, "units_sold": 750},
            {"rank": 6, "name": "Screen Protector", "revenue": 32000, "units_sold": 640},
            {"rank": 7, "name": "Power Bank", "revenue": 28000, "units_sold": 140},
            {"rank": 8, "name": "Keyboard", "revenue": 25000, "units_sold": 125},
            {"rank": 9, "name": "Mouse Pad", "revenue": 18000, "units_sold": 360},
            {"rank": 10, "name": "Webcam", "revenue": 15000, "units_sold": 75}
        ]
    }

@app.get("/api/petpooja/analytics/daily-summary")
def get_petpooja_daily_summary():
    """Restaurant analytics data for Petpooja integration"""
    return {
        "total_orders": 156,
        "total_revenue": 45000,
        "total_gst_collected": 5400,
        "average_order_value": 288.46,
        "order_type_breakdown": {
            "Dine-in": {"count": 78, "amount": 22500},
            "Takeaway": {"count": 45, "amount": 13000},
            "Delivery": {"count": 33, "amount": 9500}
        },
        "payment_method_breakdown": {
            "Cash": {"count": 62, "amount": 18000},
            "Card": {"count": 48, "amount": 13800},
            "UPI": {"count": 38, "amount": 11000},
            "Wallet": {"count": 8, "amount": 2200}
        },
        "peak_hours": {
            "lunch": "12:00 PM - 2:00 PM",
            "dinner": "7:00 PM - 9:00 PM"
        }
    }


# Tally Integration Endpoint
from api.services.tally_connector import TallyConnector
from datetime import datetime

@app.post("/api/v1/invoices/{invoice_id}/sync-tally")
def sync_invoice_to_tally(invoice_id: str):
    # Mock data retrieval (In production, query DB)
    # Finding the invoice in our mock list
    mock_invoices = [
        {"id": "INV-001", "customer": "ABC Corp", "amount": 15000, "date": "2026-01-21"},
        {"id": "INV-002", "customer": "XYZ Ltd", "amount": 22500, "date": "2026-01-21"},
        {"id": "INV-003", "customer": "Demo Store", "amount": 8750, "date": "2026-01-20"},
        {"id": "INV-004", "customer": "Retail Hub", "amount": 31200, "date": "2026-01-20"},
        {"id": "INV-005", "customer": "Shop Plus", "amount": 12400, "date": "2026-01-19"},
    ]
    
    invoice = next((inv for inv in mock_invoices if inv["id"] == invoice_id), None)
    
    if not invoice:
        # Fallback for demo if ID not found, just use dummy data
        invoice = {"id": invoice_id, "customer": "Unknown Client", "amount": 1000, "date": "2026-01-24"}

    # Prepare data for Connector
    voucher_data = {
        "invoice_number": invoice["id"],
        "date": datetime.strptime(invoice["date"], "%Y-%m-%d"),
        "customer_ledger_name": invoice["customer"], # Assuming mapped name is same for demo
        "total_amount": invoice["amount"],
        "items": [
             # Mock items
             {"product_name": "Consulting Service", "unit_price": invoice["amount"], "total": invoice["amount"]}
        ]
    }

    success, message = TallyConnector.push_voucher(voucher_data)
    
    if success:
        return {"status": "success", "message": message, "tally_vch_no": invoice_id}
    else:
        return {"status": "error", "message": message}

# Loyalty & Referral Endpoints
@app.get("/api/v1/loyalty/dashboard")
def get_loyalty_dashboard():
    # Mock data for frontend
    return {
        "total_referrals": 142,
        "pending_rewards": 5600,
        "active_udhaar": 450000,
        "top_referrers": [
            {"name": "Rahul Verma", "count": 12, "earned": 2400},
            {"name": "Priya Singh", "count": 9, "earned": 1800},
            {"name": "Amit Shah", "count": 7, "earned": 1400}
        ]
    }

@app.get("/api/v1/loyalty/credits")
def get_digital_udhaar_list():
    # Mock Credit List
    return [
        {"id": 1, "customer": "Ravi Kumar", "balance": 12500, "limit": 20000, "score": 750, "last_payment": "2026-01-15", "status": "good"},
        {"id": 2, "customer": "Sneha Gupta", "balance": 45000, "limit": 50000, "score": 620, "last_payment": "2025-12-20", "status": "warning"},
        {"id": 3, "customer": "Vikram Malhotra", "balance": 8200, "limit": 15000, "score": 810, "last_payment": "2026-01-22", "status": "good"},
    ]

@app.post("/api/v1/loyalty/send-reminder/{customer_id}")
def send_payment_reminder(customer_id: int):
    # Simulate sending WhatsApp reminder
    return {"status": "success", "message": f"Payment reminder sent to customer {customer_id} via WhatsApp"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
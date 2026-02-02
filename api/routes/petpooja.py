"""
Enterprise Retail Intelligence System v3.0
PETPOOJA TRANSACTION API

REST API endpoints for restaurant transaction management:
- Order creation and tracking
- Invoice generation with GST
- Payment processing
- Credit management
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from generate_petpooja_data import PetpoojaRestaurantDataGenerator

router = APIRouter(prefix="/api/petpooja", tags=["Petpooja Restaurant"])

# Initialize generator
generator = PetpoojaRestaurantDataGenerator()

# In-memory storage (replace with database in production)
_orders_cache = {}
_daily_stats_cache = {}


# ============================================================
# PYDANTIC MODELS
# ============================================================

class OrderItem(BaseModel):
    category: str
    name: str
    quantity: int
    unit_price: float
    amount: float


class CreateOrderRequest(BaseModel):
    order_type: str = Field(..., description="Dine-in, Takeaway, or Delivery")
    table_number: Optional[int] = None
    items: List[Dict[str, Any]]


class OrderResponse(BaseModel):
    order_id: str
    timestamp: str
    order_type: str
    table_number: Optional[int]
    items: List[Dict[str, Any]]
    subtotal: float
    gst_amount: float
    total_amount: float
    payment_method: str
    estimated_prep_time: int
    status: str


class PaymentRequest(BaseModel):
    order_id: str
    payment_method: str = Field(..., description="Cash, Card, UPI, or Credit")
    amount_paid: float


# ============================================================
# ORDER MANAGEMENT ENDPOINTS
# ============================================================

@router.get("/orders/today")
async def get_todays_orders(
    order_type: Optional[str] = Query(None, description="Filter by Dine-in, Takeaway, or Delivery")
):
    """Get all orders for today"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_key = today.strftime("%Y-%m-%d")
    
    # Generate if not cached
    if today_key not in _orders_cache:
        orders = generator.generate_daily_orders(today)
        _orders_cache[today_key] = orders
    
    orders = _orders_cache[today_key]
    
    # Filter by order type if specified
    if order_type:
        orders = [o for o in orders if o["order_type"] == order_type]
    
    return {
        "date": today_key,
        "total_orders": len(orders),
        "orders": orders
    }


@router.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get specific order details"""
    today_key = datetime.now().strftime("%Y-%m-%d")
    
    if today_key not in _orders_cache:
        await get_todays_orders()
    
    orders = _orders_cache[today_key]
    order = next((o for o in orders if o["order_id"] == order_id), None)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


@router.post("/orders/create")
async def create_order(request: CreateOrderRequest):
    """Create a new order"""
    today = datetime.now()
    today_key = today.strftime("%Y-%m-%d")
    
    # Get existing orders count
    if today_key not in _orders_cache:
        _orders_cache[today_key] = []
    
    order_num = len(_orders_cache[today_key]) + 1
    
    # Calculate totals
    subtotal = sum(item["amount"] for item in request.items)
    gst_amount = subtotal * 0.05
    total_amount = subtotal + gst_amount
    
    # Create order
    order = {
        "order_id": f"ORD{order_num:06d}",
        "timestamp": today.isoformat(),
        "order_type": request.order_type,
        "table_number": request.table_number,
        "items": request.items,
        "subtotal": round(subtotal, 2),
        "gst_amount": round(gst_amount, 2),
        "total_amount": round(total_amount, 2),
        "payment_method": "Pending",
        "estimated_prep_time": 20,
        "status": "Pending"
    }
    
    _orders_cache[today_key].append(order)
    
    return {
        "success": True,
        "order": order,
        "kot": generator.generate_kot(order)
    }



class UpdateStatusRequest(BaseModel):
    status: str = Field(..., description="Pending, Preparing, Ready, or Completed")


@router.get("/orders/{order_id}/kot")
async def get_kot(order_id: str):
    """Get Kitchen Order Ticket for an order"""
    order = await get_order(order_id)
    kot = generator.generate_kot(order)
    
    return {
        "order_id": order_id,
        "kot": kot
    }


@router.put("/orders/{order_id}/status")
async def update_status(order_id: str, request: UpdateStatusRequest):
    """Update order status (KDS)"""
    today_key = datetime.now().strftime("%Y-%m-%d")
    
    if today_key not in _orders_cache:
        raise HTTPException(status_code=404, detail="No orders found for today")
    
    orders = _orders_cache[today_key]
    order = next((o for o in orders if o["order_id"] == order_id), None)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order["status"] = request.status
    
    # If completed, set timestamp
    if request.status == "Completed":
        order["completed_at"] = datetime.now().isoformat()
        
    return {
        "success": True,
        "order_id": order_id,
        "status": request.status,
        "updated_at": datetime.now().isoformat()
    }


@router.get("/orders/{order_id}/invoice")
async def get_invoice(order_id: str):
    """Get invoice for an order"""
    order = await get_order(order_id)
    invoice = generator.generate_invoice(order)
    
    return {
        "order_id": order_id,
        "invoice": invoice,
        "total_amount": order["total_amount"],
        "gst_amount": order["gst_amount"]
    }


# ============================================================
# PAYMENT PROCESSING
# ============================================================

@router.post("/payments/process")
async def process_payment(request: PaymentRequest):
    """Process payment for an order"""
    today_key = datetime.now().strftime("%Y-%m-%d")
    
    if today_key not in _orders_cache:
        raise HTTPException(status_code=404, detail="No orders found for today")
    
    orders = _orders_cache[today_key]
    order = next((o for o in orders if o["order_id"] == request.order_id), None)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if request.amount_paid < order["total_amount"]:
        raise HTTPException(status_code=400, detail="Insufficient payment amount")
    
    # Update order
    order["payment_method"] = request.payment_method
    order["status"] = "Completed"
    order["paid_at"] = datetime.now().isoformat()
    order["amount_paid"] = request.amount_paid
    order["change_returned"] = round(request.amount_paid - order["total_amount"], 2)
    
    return {
        "success": True,
        "order_id": request.order_id,
        "payment_method": request.payment_method,
        "amount_paid": request.amount_paid,
        "change_returned": order["change_returned"],
        "invoice": generator.generate_invoice(order)
    }


# ============================================================
# CREDIT MANAGEMENT
# ============================================================

@router.get("/credit/customers")
async def get_credit_customers():
    """Get customers with credit facility"""
    # Mock credit customers
    return {
        "total_credit_customers": 45,
        "customers": [
            {
                "customer_id": "CUST001",
                "name": "Rajesh Kumar",
                "phone": "+91-9876543210",
                "credit_limit": 50000,
                "outstanding_balance": 12500,
                "available_credit": 37500,
                "last_payment_date": "2026-01-25"
            },
            {
                "customer_id": "CUST002",
                "name": "Priya Sharma",
                "phone": "+91-9876543211",
                "credit_limit": 30000,
                "outstanding_balance": 8200,
                "available_credit": 21800,
                "last_payment_date": "2026-01-28"
            },
            {
                "customer_id": "CUST003",
                "name": "Amit Patel",
                "phone": "+91-9876543212",
                "credit_limit": 75000,
                "outstanding_balance": 45000,
                "available_credit": 30000,
                "last_payment_date": "2026-01-20"
            }
        ]
    }


@router.post("/credit/charge")
async def charge_to_credit(order_id: str, customer_id: str):
    """Charge order to customer's credit account"""
    order = await get_order(order_id)
    
    # Mock credit check
    credit_customers = await get_credit_customers()
    customer = next((c for c in credit_customers["customers"] if c["customer_id"] == customer_id), None)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if customer["available_credit"] < order["total_amount"]:
        raise HTTPException(status_code=400, detail="Insufficient credit limit")
    
    # Update order
    today_key = datetime.now().strftime("%Y-%m-%d")
    orders = _orders_cache[today_key]
    order_obj = next((o for o in orders if o["order_id"] == order_id), None)
    
    order_obj["payment_method"] = "Credit"
    order_obj["status"] = "Completed"
    order_obj["credit_customer_id"] = customer_id
    order_obj["charged_at"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "order_id": order_id,
        "customer_id": customer_id,
        "amount_charged": order["total_amount"],
        "new_outstanding": customer["outstanding_balance"] + order["total_amount"],
        "remaining_credit": customer["available_credit"] - order["total_amount"]
    }


# ============================================================
# ANALYTICS & REPORTS
# ============================================================

@router.get("/analytics/daily-summary")
async def get_daily_summary(date: Optional[str] = None):
    """Get daily sales summary"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Generate orders if not cached
    if date not in _orders_cache:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        orders = generator.generate_daily_orders(date_obj)
        _orders_cache[date] = orders
    
    orders = _orders_cache[date]
    
    # Calculate stats
    total_revenue = sum(o["total_amount"] for o in orders)
    total_gst = sum(o["gst_amount"] for o in orders)
    
    # By order type
    order_type_stats = {}
    for order_type in ["Dine-in", "Takeaway", "Delivery"]:
        type_orders = [o for o in orders if o["order_type"] == order_type]
        order_type_stats[order_type] = {
            "count": len(type_orders),
            "revenue": sum(o["total_amount"] for o in type_orders)
        }
    
    # By payment method
    payment_stats = {}
    for method in ["Cash", "Card", "UPI", "Credit"]:
        method_orders = [o for o in orders if o["payment_method"] == method]
        payment_stats[method] = {
            "count": len(method_orders),
            "amount": sum(o["total_amount"] for o in method_orders)
        }
    
    return {
        "date": date,
        "total_orders": len(orders),
        "total_revenue": round(total_revenue, 2),
        "total_gst_collected": round(total_gst, 2),
        "average_order_value": round(total_revenue / len(orders), 2) if orders else 0,
        "order_type_breakdown": order_type_stats,
        "payment_method_breakdown": payment_stats,
        "peak_hours": {
            "lunch": "12:00 PM - 2:00 PM",
        "dinner": "7:00 PM - 10:00 PM"
        }
    }


@router.get("/menu")
async def get_menu():
    """Get restaurant menu"""
    return {
        "restaurant": "Petpooja Restaurant",
        "menu": generator.menu,
        "categories": list(generator.menu.keys())
    }


# ============================================================
# TABLE MANAGEMENT
# ============================================================

# In-memory table status (10 tables)
_tables_status = {}

def initialize_tables():
    """Initialize table status if not already done"""
    global _tables_status
    if not _tables_status:
        for i in range(1, 11):  # 10 tables
            _tables_status[i] = {
                "table_number": i,
                "status": "Available",  # Available, Occupied, Reserved
                "current_order_id": None,
                "occupied_since": None,
                "reserved_for": None,
                "guest_count": 0
            }

@router.get("/tables/status")
async def get_tables_status():
    """Get status of all tables"""
    initialize_tables()
    
    # Calculate occupancy duration for occupied tables
    tables_with_duration = []
    for table in _tables_status.values():
        table_info = table.copy()
        if table["status"] == "Occupied" and table["occupied_since"]:
            occupied_time = datetime.fromisoformat(table["occupied_since"])
            duration_minutes = int((datetime.now() - occupied_time).total_seconds() / 60)
            table_info["occupied_duration_minutes"] = duration_minutes
        tables_with_duration.append(table_info)
    
    # Summary stats
    available_count = sum(1 for t in _tables_status.values() if t["status"] == "Available")
    occupied_count = sum(1 for t in _tables_status.values() if t["status"] == "Occupied")
    reserved_count = sum(1 for t in _tables_status.values() if t["status"] == "Reserved")
    
    return {
        "total_tables": len(_tables_status),
        "available": available_count,
        "occupied": occupied_count,
        "reserved": reserved_count,
        "tables": tables_with_duration
    }

@router.post("/tables/{table_number}/assign")
async def assign_table(table_number: int, order_id: str, guest_count: int = 2):
    """Assign a table to an order"""
    initialize_tables()
    
    if table_number not in _tables_status:
        raise HTTPException(status_code=404, detail="Table not found")
    
    table = _tables_status[table_number]
    
    if table["status"] != "Available":
        raise HTTPException(status_code=400, detail=f"Table {table_number} is not available")
    
    # Update table status
    table["status"] = "Occupied"
    table["current_order_id"] = order_id
    table["occupied_since"] = datetime.now().isoformat()
    table["guest_count"] = guest_count
    
    return {
        "success": True,
        "message": f"Table {table_number} assigned successfully",
        "table": table
    }

@router.post("/tables/{table_number}/clear")
async def clear_table(table_number: int):
    """Clear a table after guests leave"""
    initialize_tables()
    
    if table_number not in _tables_status:
        raise HTTPException(status_code=404, detail="Table not found")
    
    table = _tables_status[table_number]
    
    # Reset table status
    table["status"] = "Available"
    table["current_order_id"] = None
    table["occupied_since"] = None
    table["reserved_for"] = None
    table["guest_count"] = 0
    
    return {
        "success": True,
        "message": f"Table {table_number} cleared successfully",
        "table": table
    }

@router.post("/tables/{table_number}/reserve")
async def reserve_table(table_number: int, reserved_for: str, guest_count: int = 2):
    """Reserve a table for a customer"""
    initialize_tables()
    
    if table_number not in _tables_status:
        raise HTTPException(status_code=404, detail="Table not found")
    
    table = _tables_status[table_number]
    
    if table["status"] != "Available":
        raise HTTPException(status_code=400, detail=f"Table {table_number} is not available")
    
    # Update table status
    table["status"] = "Reserved"
    table["reserved_for"] = reserved_for
    table["guest_count"] = guest_count
    
    return {
        "success": True,
        "message": f"Table {table_number} reserved successfully",
        "table": table
    }

"""
Phase 4: WebSocket Integration

Real-time live metrics, notifications, and event streaming using WebSocket
for dashboard and mobile client updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Set, Dict, List
import asyncio
import json
from datetime import datetime
from decimal import Decimal

router = APIRouter(prefix="/api/v4/ws", tags=["websocket"])


# ==================== Connection Manager ====================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, business_id: str, websocket: WebSocket):
        """Accept connection and add to group"""
        await websocket.accept()
        if business_id not in self.active_connections:
            self.active_connections[business_id] = set()
        self.active_connections[business_id].add(websocket)
    
    def disconnect(self, business_id: str, websocket: WebSocket):
        """Remove connection"""
        if business_id in self.active_connections:
            self.active_connections[business_id].discard(websocket)
    
    async def broadcast(self, business_id: str, message: dict):
        """Broadcast to all connections in business"""
        if business_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[business_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
            
            # Clean up disconnected
            for conn in disconnected:
                self.active_connections[business_id].discard(conn)
    
    async def broadcast_all(self, message: dict):
        """Broadcast to all connections"""
        for business_id in self.active_connections:
            await self.broadcast(business_id, message)
    
    def get_connection_count(self, business_id: str) -> int:
        """Get active connection count"""
        return len(self.active_connections.get(business_id, set()))


manager = ConnectionManager()


# ==================== WebSocket Events ====================

class SalesEvent:
    """Sales event for real-time streaming"""
    
    @staticmethod
    def new_sale(sale_id: int, amount: Decimal, payment_method: str) -> dict:
        return {
            "type": "sale",
            "event": "new_sale",
            "data": {
                "sale_id": sale_id,
                "amount": float(amount),
                "payment_method": payment_method,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def payment_received(customer_name: str, amount: Decimal) -> dict:
        return {
            "type": "payment",
            "event": "payment_received",
            "data": {
                "customer_name": customer_name,
                "amount": float(amount),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def low_stock_alert(product_name: str, current_stock: int, reorder_point: int) -> dict:
        return {
            "type": "alert",
            "event": "low_stock",
            "level": "warning",
            "data": {
                "product_name": product_name,
                "current_stock": current_stock,
                "reorder_point": reorder_point,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def invoice_overdue(invoice_number: str, days_overdue: int, amount_due: Decimal) -> dict:
        return {
            "type": "alert",
            "event": "invoice_overdue",
            "level": "alert",
            "data": {
                "invoice_number": invoice_number,
                "days_overdue": days_overdue,
                "amount_due": float(amount_due),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def metrics_update(metrics: dict) -> dict:
        return {
            "type": "metrics",
            "event": "metrics_update",
            "data": {
                **metrics,
                "timestamp": datetime.now().isoformat()
            }
        }


# ==================== WebSocket Endpoints ====================

@router.websocket("/connect/{business_id}")
async def websocket_endpoint(websocket: WebSocket, business_id: str):
    """
    WebSocket endpoint for real-time updates
    
    Args:
        websocket: WebSocket connection
        business_id: Business identifier
        
    Emits:
        - sale: New sale event
        - payment: Payment received
        - alert: System alerts
        - metrics: Live metrics update
    """
    await manager.connect(business_id, websocket)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "event": "connected",
            "business_id": business_id,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Listen for client messages (keep-alive, subscriptions, etc)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            elif message.get("type") == "subscribe":
                # Client can subscribe to specific event types
                await websocket.send_json({
                    "type": "subscribed",
                    "event_types": message.get("events", []),
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(business_id, websocket)
    except Exception as e:
        manager.disconnect(business_id, websocket)


@router.websocket("/dashboard/{business_id}")
async def dashboard_websocket(websocket: WebSocket, business_id: str):
    """
    WebSocket for dashboard live metrics
    
    Streams:
        - Real-time sales metrics
        - Transaction updates
        - Payment breakdowns
        - Stock alerts
        - Order alerts
    """
    await manager.connect(business_id, websocket)
    
    try:
        await websocket.send_json({
            "type": "dashboard",
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout
                )
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except asyncio.TimeoutError:
                # Send metrics update every 30 seconds
                await websocket.send_json({
                    "type": "metrics",
                    "event": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(business_id, websocket)


@router.websocket("/notifications/{business_id}")
async def notifications_websocket(websocket: WebSocket, business_id: str):
    """
    WebSocket for notifications and alerts
    
    Delivers:
        - Stock alerts
        - Overdue invoices
        - Payment reminders
        - System notifications
    """
    await manager.connect(business_id, websocket)
    
    try:
        await websocket.send_json({
            "type": "notification",
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            # Handle client subscription/acknowledgment
            
    except WebSocketDisconnect:
        manager.disconnect(business_id, websocket)


# ==================== Server-Sent Events (Broadcast) ====================

@router.post("/broadcast/sale/{business_id}")
async def broadcast_sale(
    business_id: str,
    sale_id: int,
    amount: float,
    payment_method: str = "cash"
):
    """
    Broadcast new sale event to all connected clients
    
    Args:
        business_id: Business identifier
        sale_id: Sale identifier
        amount: Sale amount
        payment_method: Payment method used
    """
    try:
        event = SalesEvent.new_sale(sale_id, Decimal(str(amount)), payment_method)
        await manager.broadcast(business_id, event)
        
        return {
            "status": "success",
            "message": "Sale event broadcasted",
            "connections": manager.get_connection_count(business_id)
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/broadcast/payment/{business_id}")
async def broadcast_payment(
    business_id: str,
    customer_name: str,
    amount: float
):
    """
    Broadcast payment received event
    
    Args:
        business_id: Business identifier
        customer_name: Customer name
        amount: Payment amount
    """
    try:
        event = SalesEvent.payment_received(customer_name, Decimal(str(amount)))
        await manager.broadcast(business_id, event)
        
        return {
            "status": "success",
            "message": "Payment event broadcasted",
            "connections": manager.get_connection_count(business_id)
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/broadcast/alert/{business_id}")
async def broadcast_alert(
    business_id: str,
    alert_type: str,
    level: str,
    message: str
):
    """
    Broadcast custom alert
    
    Args:
        business_id: Business identifier
        alert_type: Type of alert (stock, invoice, payment, etc)
        level: Alert level (info, warning, alert)
        message: Alert message
    """
    try:
        event = {
            "type": "alert",
            "alert_type": alert_type,
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(business_id, event)
        
        return {
            "status": "success",
            "message": "Alert broadcasted",
            "connections": manager.get_connection_count(business_id)
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/broadcast/metrics/{business_id}")
async def broadcast_metrics(
    business_id: str,
    metrics: dict
):
    """
    Broadcast metrics update
    
    Args:
        business_id: Business identifier
        metrics: Metrics data
    """
    try:
        event = SalesEvent.metrics_update(metrics)
        await manager.broadcast(business_id, event)
        
        return {
            "status": "success",
            "message": "Metrics broadcasted",
            "connections": manager.get_connection_count(business_id)
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ==================== Connection Status ====================

@router.get("/status/{business_id}")
async def get_connection_status(business_id: str):
    """
    Get WebSocket connection status
    
    Args:
        business_id: Business identifier
        
    Returns:
        Connection statistics
    """
    return {
        "business_id": business_id,
        "connected_clients": manager.get_connection_count(business_id),
        "total_businesses": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/disconnect/{business_id}")
async def disconnect_all(business_id: str):
    """
    Disconnect all clients for business (admin only)
    
    Args:
        business_id: Business identifier
    """
    try:
        if business_id in manager.active_connections:
            for websocket in list(manager.active_connections[business_id]):
                try:
                    await websocket.close()
                except:
                    pass
            del manager.active_connections[business_id]
        
        return {
            "status": "success",
            "message": f"All connections for {business_id} closed"
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

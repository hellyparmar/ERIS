"""
WebSocket Handler for Real-time Updates
Manages connections, subscriptions, and broadcasts
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and subscriptions"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, Set[WebSocket]] = {}  # channel -> websockets
        self.client_subscriptions: Dict[WebSocket, Set[str]] = {}  # websocket -> channels
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_subscriptions[websocket] = set()
        logger.info(f"✓ WebSocket connected. Active connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Unsubscribe from all channels
        if websocket in self.client_subscriptions:
            channels = self.client_subscriptions[websocket].copy()
            for channel in channels:
                self.unsubscribe(websocket, channel)
            del self.client_subscriptions[websocket]
        
        logger.info(f"✓ WebSocket disconnected. Active connections: {len(self.active_connections)}")
    
    def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe a WebSocket to a channel"""
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
        
        self.subscriptions[channel].add(websocket)
        self.client_subscriptions[websocket].add(channel)
        logger.info(f"✓ Subscribed to {channel}. Total subscribers: {len(self.subscriptions[channel])}")
    
    def unsubscribe(self, websocket: WebSocket, channel: str):
        """Unsubscribe a WebSocket from a channel"""
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(websocket)
            if len(self.subscriptions[channel]) == 0:
                del self.subscriptions[channel]
        
        if websocket in self.client_subscriptions:
            self.client_subscriptions[websocket].discard(channel)
    
    async def broadcast(self, channel: str, data: dict):
        """Broadcast data to all subscribers of a channel"""
        if channel not in self.subscriptions:
            return
        
        message = {
            "type": "update",
            "channel": channel,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected = []
        for websocket in self.subscriptions[channel]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected websockets
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast_to_all(self, data: dict):
        """Broadcast data to all connected clients"""
        message = {
            "type": "broadcast",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected websockets
        for ws in disconnected:
            self.disconnect(ws)
    
    async def handle_client_message(self, websocket: WebSocket, message: dict):
        """Handle incoming client message"""
        msg_type = message.get("type")
        
        if msg_type == "subscribe":
            channel = message.get("channel")
            if channel:
                self.subscribe(websocket, channel)
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "channel": channel,
                    "timestamp": datetime.now().isoformat()
                })
        
        elif msg_type == "unsubscribe":
            channel = message.get("channel")
            if channel:
                self.unsubscribe(websocket, channel)
                await websocket.send_json({
                    "type": "unsubscription_confirmed",
                    "channel": channel,
                    "timestamp": datetime.now().isoformat()
                })
        
        elif msg_type == "ping":
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            })
    
    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "active_connections": len(self.active_connections),
            "total_channels": len(self.subscriptions),
            "channels": {
                channel: len(sockets)
                for channel, sockets in self.subscriptions.items()
            }
        }


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint handler"""
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await manager.handle_client_message(websocket, message)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON received")
        try:
            await websocket.send_json({"error": "Invalid JSON format"})
        except:
            pass
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Broadcast functions for use throughout the app

async def broadcast_inventory_update(product_id: int, data: dict):
    """Broadcast inventory update"""
    await manager.broadcast("inventory", {
        "product_id": product_id,
        "update": data
    })


async def broadcast_sales_update(sale_id: int, data: dict):
    """Broadcast sales update"""
    await manager.broadcast("sales", {
        "sale_id": sale_id,
        "update": data
    })


async def broadcast_alerts_update(alert_count: int):
    """Broadcast alerts update"""
    await manager.broadcast("alerts", {
        "total_alerts": alert_count,
        "timestamp": datetime.now().isoformat()
    })


async def broadcast_dashboard_update(metrics: dict):
    """Broadcast dashboard metrics update"""
    await manager.broadcast("dashboard", {
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    })

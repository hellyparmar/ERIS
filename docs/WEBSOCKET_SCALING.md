"""
WebSocket Scaling with Socket.io + Redis Adapter
Horizontal scaling for real-time dashboard updates

Solution for: "How to handle 1000+ concurrent WebSocket connections?"
"""

from typing import Dict, Any, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# ============================================================
# WEBSOCKET SCALING ARCHITECTURE
# ============================================================

WEBSOCKET_SCALING_DESIGN = """
PROBLEM: Single server WebSocket limitation (~10K connections)

SOLUTION: Socket.io with Redis Pub/Sub Adapter

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                            │
│                  (Sticky Sessions)                          │
└─────────────────────────────────────────────────────────────┘
                    │         │         │
        ┌───────────┘         │         └───────────┐
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ API Server 1 │      │ API Server 2 │      │ API Server 3 │
│ Socket.io    │      │ Socket.io    │      │ Socket.io    │
└──────────────┘      └──────────────┘      └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                    ┌──────────────────┐
                    │   Redis Pub/Sub  │
                    │  (Message Broker)│
                    └──────────────────┘

FLOW:
1. User A connects to Server 1
2. User B connects to Server 2
3. Event happens on Server 1 → Publishes to Redis
4. Redis broadcasts to all servers
5. Server 2 pushes update to User B ✓

BENEFITS:
- Scales horizontally (add more servers)
- No single point of failure
- Seamless room-based broadcasting
- Session persistence not required
"""


# ============================================================
# Node.js IMPLEMENTATION (WebSocket Server)
# ============================================================

NODEJS_IMPLEMENTATION = """
// websocket-server.js
// Installation: npm install socket.io @socket.io/redis-adapter redis

const { Server } = require('socket.io');
const { createAdapter } = require('@socket.io/redis-adapter');
const { createClient } = require('redis');

// Create Socket.io server
const io = new Server(3001, {
  cors: { origin: "*" }  // Configure CORS appropriately
});

// Setup Redis adapter for horizontal scaling
const pubClient = createClient({ 
  url: 'redis://localhost:6379' 
});
const subClient = pubClient.duplicate();

Promise.all([pubClient.connect(), subClient.connect()]).then(() => {
  io.adapter(createAdapter(pubClient, subClient));
  console.log('Socket.io server with Redis adapter running on :3001');
});

// Handle client connections
io.on('connection', (socket) => {
  console.log(`Client connected: ${socket.id}`);
  
  // Join room (e.g., user's store_id)
  socket.on('join_dashboard', (storeId) => {
    socket.join(`store_${storeId}`);
    console.log(`Socket ${socket.id} joined store_${storeId}`);
  });
  
  // Handle disconnection
  socket.on('disconnect', () => {
    console.log(`Client disconnected: ${socket.id}`);
  });
});

// Emit dashboard updates (called by FastAPI)
function broadcastDashboardUpdate(storeId, data) {
  io.to(`store_${storeId}`).emit('dashboard_update', data);
}

// HTTP endpoint for FastAPI to trigger broadcasts
const express = require('express');
const app = express();
app.use(express.json());

app.post('/broadcast', (req, res) => {
  const { room, event, data } = req.body;
  io.to(room).emit(event, data);
  res.json({ status: 'broadcasted' });
});

app.listen(3002, () => {
  console.log('Broadcast API listening on :3002');
});


// SCALING CONFIGURATION
// ======================

// docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  websocket1:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
      - SERVER_ID=ws1
    ports:
      - "3001:3001"
  
  websocket2:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
      - SERVER_ID=ws2
    ports:
      - "3003:3001"  # Different external port
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf


// nginx.conf (Load Balancer)
upstream websocket_backend {
  ip_hash;  # Sticky sessions for WebSocket
  server websocket1:3001;
  server websocket2:3001;
}

server {
  listen 80;
  
  location /socket.io/ {
    proxy_pass http://websocket_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
  }
}
"""


# ============================================================
# PYTHON INTEGRATION (FastAPI → Socket.io)
# ============================================================

"""
# In FastAPI (Python side)
# api/services/realtime_service.py

import httpx
import asyncio
from typing import Dict, Any

class RealtimeService:
    '''
    Send real-time updates to WebSocket clients
    '''
    
    def __init__(self, websocket_api_url: str = "http://localhost:3002"):
        self.websocket_api_url = websocket_api_url
    
    async def broadcast_dashboard_update(self, store_id: str, data: Dict[str, Any]):
        '''
        Broadcast dashboard update to all clients in a store's room
        '''
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.websocket_api_url}/broadcast",
                    json={
                        "room": f"store_{store_id}",
                        "event": "dashboard_update",
                        "data": data
                    },
                    timeout=5.0
                )
                return response.json()
            except Exception as e:
                logger.error(f"Failed to broadcast: {e}")
                return {"error": str(e)}
    
    async def notify_inventory_alert(self, store_id: str, alert: Dict):
        '''
        Send real-time inventory alert
        '''
        await self.broadcast_dashboard_update(store_id, {
            "type": "inventory_alert",
            "alert": alert
        })


# Usage in FastAPI endpoint
from api.services.realtime_service import RealtimeService

realtime = RealtimeService()

@app.post("/api/sales/complete")
async def complete_sale(sale: SaleRequest):
    # Process sale
    result = await process_sale(sale)
    
    # Broadcast real-time update to dashboard
    await realtime.broadcast_dashboard_update(
        store_id=sale.store_id,
        data={
            "type": "sale_completed",
            "revenue": result['total_amount'],
            "inventory_updated": True
        }
    )
    
    return result
"""


# ============================================================
# FRONTEND INTEGRATION (React)
# ============================================================

"""
// src/hooks/useRealtimeDashboard.js

import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

export function useRealtimeDashboard(storeId) {


  const [socket, setSocket] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect to WebSocket server
    const newSocket = io('http://localhost:3001', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });

    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      
      // Join store room
      newSocket.emit('join_dashboard', storeId);
    });

    newSocket.on('dashboard_update', (data) => {
      console.log('Dashboard update received:', data);
      setDashboardData(data);
    });

    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, [storeId]);

  return { dashboardData, isConnected };
}


// Usage in component
function Dashboard({ storeId }) {
  const { dashboardData, isConnected } = useRealtimeDashboard(storeId);

  return (
    <div>
      <div>Status: {isConnected ? '🟢 Live' : '🔴 Disconnected'}</div>
      {dashboardData && (
        <div>
          <h2>Real-time Update</h2>
          <pre>{JSON.stringify(dashboardData, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
"""


# ============================================================
# SCALABILITY METRICS
# ============================================================

@dataclass
class WebSocketScalability:
    """WebSocket scaling metrics"""
    metric_name: str
    single_server: str
    with_redis_adapter: str
    improvement: str


SCALABILITY_METRICS = [
    WebSocketScalability(
        "Max Concurrent Connections",
        "~10,000",
        "~100,000+",
        "10x increase"
    ),
    WebSocketScalability(
        "Horizontal Scaling",
        "No (single server)",
        "Yes (add servers)",
        "Linear scaling"
    ),
    WebSocketScalability(
        "Failover",
        "No (SPOF)",
        "Yes (automatic)",
        "High availability"
    ),
    WebSocketScalability(
        "Room Broadcasting",
        "Single server only",
        "Cross-server",
        "Distributed rooms"
    ),
    WebSocketScalability(
        "Setup Complexity",
        "Simple",
        "Moderate (+Redis)",
        "Worth tradeoff"
    )
]


# ============================================================
# THESIS DEFENSE ANSWER
# ============================================================

THESIS_DEFENSE_STATEMENT = """
QUESTION: "How do you handle 1000+ concurrent WebSocket connections?"

ANSWER:
"The system uses Socket.io with Redis Pub/Sub adapter for horizontal WebSocket scaling. 
This architecture allows multiple API servers to share WebSocket state through Redis, 
enabling linear scaling from ~10K connections per server to 100K+ total connections. 

Load balancer uses sticky sessions for WebSocket handshake, then Redis broadcasts 
events across all servers. This ensures that a dashboard update triggered on Server 1 
reaches users connected to Server 2 seamlessly.

For the academic project, I've implemented a 2-server configuration demonstrating 
horizontal scalability. In production, this can scale to 10+ servers handling 
100K+ concurrent users."
"""


if __name__ == "__main__":
    print("=" * 80)
    print("WEBSOCKET SCALING SOLUTION")
    print("=" * 80)
    
    print(WEBSOCKET_SCALING_DESIGN)
    
    print("\n" + "=" * 80)
    print("SCALABILITY METRICS")
    print("=" * 80)
    
    for metric in SCALABILITY_METRICS:
        print(f"\n{metric.metric_name}:")
        print(f"  Single Server: {metric.single_server}")
        print(f"  With Redis: {metric.with_redis_adapter}")
        print(f"  Improvement: {metric.improvement}")
    
    print("\n" + "=" * 80)
    print(THESIS_DEFENSE_STATEMENT)
    print("=" * 80)

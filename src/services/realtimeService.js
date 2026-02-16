/**
 * Real-time Updates Service
 * Manages WebSocket connections for live data updates
 * Handles reconnection logic, message queuing, and event subscriptions
 */

class RealtimeService {
    constructor() {
        this.ws = null;
        this.url = `ws://${window.location.hostname}:8000/api/ws`;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.subscriptions = new Map();
        this.messageQueue = [];
        this.isConnected = false;
        this.heartbeatInterval = null;
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.url);

                this.ws.onopen = () => {
                    console.log('✓ WebSocket connected');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    this.flushMessageQueue();
                    this.startHeartbeat();
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    reject(error);
                };

                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.isConnected = false;
                    this.stopHeartbeat();
                    this.attemptReconnect();
                };
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            console.log(`Attempting reconnect in ${delay}ms...`);
            setTimeout(() => this.connect().catch(() => {}), delay);
        }

    /**
     * Send heartbeat to keep connection alive
     */
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            this.send({ type: 'ping', timestamp: Date.now() });
        }, 30000);
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }

    /**
     * Subscribe to data updates
     */
    subscribe(channel, callback) {
        if (!this.subscriptions.has(channel)) {
            this.subscriptions.set(channel, []);
        }
        this.subscriptions.get(channel).push(callback);

        // Send subscription message
        this.send({
            type: 'subscribe',
            channel: channel,
            timestamp: Date.now()
        });

        return () => this.unsubscribe(channel, callback);
    }

    /**
     * Unsubscribe from data updates
     */
    unsubscribe(channel, callback) {
        if (this.subscriptions.has(channel)) {
            const callbacks = this.subscriptions.get(channel);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
            if (callbacks.length === 0) {
                this.subscriptions.delete(channel);
                this.send({
                    type: 'unsubscribe',
                    channel: channel,
                    timestamp: Date.now()
                });
            }
    }

    /**
     * Handle incoming messages
     */
    handleMessage(message) {
        const { type, channel, data } = message;

        if (type === 'pong') {
            // Heartbeat response
            return;
        }

        if (type === 'update' && channel && this.subscriptions.has(channel)) {
            const callbacks = this.subscriptions.get(channel);
            callbacks.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Error in subscription callback:', error);
                }
            });
        }

    /**
     * Send message through WebSocket
     */
    send(message) {
        if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            // Queue message if not connected
            this.messageQueue.push(message);
        }

    /**
     * Flush queued messages when connection is established
     */
    flushMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.send(message);
        }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close();
        }
        this.isConnected = false;
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            isConnected: this.isConnected,
            url: this.url,
            subscriptions: Array.from(this.subscriptions.keys()),
            queuedMessages: this.messageQueue.length
        };
    }

// Export singleton instance
export const realtimeService = new RealtimeService();

/**
 * React Hook for using real-time updates
 */
export const useRealtimeUpdates = (channel, onUpdate) => {
    const [data, setData] = React.useState(null);
    const [isConnected, setIsConnected] = React.useState(realtimeService.isConnected);

    React.useEffect(() => {
        // Try to connect if not already connected
        if (!realtimeService.isConnected) {
            realtimeService.connect().catch(err => console.error('Failed to connect:', err));
        }

        // Subscribe to channel
        const unsubscribe = realtimeService.subscribe(channel, (newData) => {
            setData(newData);
            if (onUpdate) {
                onUpdate(newData);
            }
        });

        setIsConnected(realtimeService.isConnected);

        // Cleanup on unmount
        return () => {
            unsubscribe();
        };
    }, [channel, onUpdate]);

    return { data, isConnected };
};

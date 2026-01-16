// frontend/src/services/websocketService.ts
import { API_BASE_URL } from "../config/env";

export type WebSocketConnectionState = "disconnected" | "connecting" | "connected" | "error";

export interface WebSocketMessage {
  type: "availability_update" | "connected" | "pong" | "error" | "subscribed";
  data: any;
}

export interface AvailabilityUpdate {
  spot_id: string;
  is_occupied: boolean;
  estimated_availability_time: string | null;
  timestamp: string;
}

export interface WebSocketSubscriptionBounds {
  min_lat?: number;
  max_lat?: number;
  min_lng?: number;
  max_lng?: number;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private connectionState: WebSocketConnectionState = "disconnected";
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private subscriptionBounds: WebSocketSubscriptionBounds | null = null;

  constructor() {
    this.setupEventListeners();
  }

  private setupEventListeners() {
    // Handle app state changes for reconnection
    // In React Native, you'd use AppState.addEventListener
  }

  connect(bounds?: WebSocketSubscriptionBounds): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.connectionState === "connecting") {
        // Already connecting, wait for connection
        const checkConnection = setInterval(() => {
          if (this.connectionState === "connected") {
            clearInterval(checkConnection);
            resolve();
          } else if (this.connectionState === "error") {
            clearInterval(checkConnection);
            reject(new Error("Connection failed"));
          }
        }, 100);
        return;
      }

      this.connectionState = "connecting";
      this.subscriptionBounds = bounds || null;

      try {
        // Convert HTTP URL to WS URL
        const wsUrl = API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://");
        const url = this.buildWebSocketUrl(wsUrl + "/api/v1/ws", bounds);
        
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          this.connectionState = "connected";
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          this.startPingInterval();
          this.emit("connected", {});
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
          }
        };

        this.ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          this.connectionState = "error";
          this.emit("error", { error });
          reject(error);
        };

        this.ws.onclose = () => {
          this.connectionState = "disconnected";
          this.stopPingInterval();
          this.emit("disconnected", {});
          this.handleReconnect();
        };
      } catch (error) {
        this.connectionState = "error";
        reject(error);
      }
    });
  }

  private buildWebSocketUrl(baseUrl: string, bounds?: WebSocketSubscriptionBounds): string {
    if (!bounds) {
      return baseUrl;
    }

    const params = new URLSearchParams();
    if (bounds.min_lat !== undefined) params.append("min_lat", String(bounds.min_lat));
    if (bounds.max_lat !== undefined) params.append("max_lat", String(bounds.max_lat));
    if (bounds.min_lng !== undefined) params.append("min_lng", String(bounds.min_lng));
    if (bounds.max_lng !== undefined) params.append("max_lng", String(bounds.max_lng));

    const queryString = params.toString();
    return queryString ? `${baseUrl}?${queryString}` : baseUrl;
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopPingInterval();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connectionState = "disconnected";
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      this.emit("max_reconnect_attempts", {});
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000); // Max 30 seconds

    this.reconnectTimer = setTimeout(() => {
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      this.connect(this.subscriptionBounds || undefined).catch(() => {
        // Reconnection will be retried
      });
    }, delay);
  }

  private startPingInterval() {
    this.pingInterval = setInterval(() => {
      this.send({ type: "ping", data: {} });
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private handleMessage(message: WebSocketMessage) {
    switch (message.type) {
      case "availability_update":
        this.emit("availability_update", message.data);
        break;
      case "pong":
        // Pong received, connection is alive
        break;
      case "error":
        this.emit("error", message.data);
        break;
      case "connected":
      case "subscribed":
        this.emit(message.type, message.data);
        break;
      default:
        console.warn("Unknown message type:", message.type);
    }
  }

  send(message: { type: string; data: any }) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket is not open. Message not sent:", message);
    }
  }

  subscribe(bounds: WebSocketSubscriptionBounds) {
    this.subscriptionBounds = bounds;
    this.send({
      type: "subscribe",
      data: { bounds },
    });
  }

  // Event listener system
  on(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: (data: any) => void) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.delete(callback);
    }
  }

  private emit(event: string, data: any) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error("Error in WebSocket event callback:", error);
        }
      });
    }
  }

  getConnectionState(): WebSocketConnectionState {
    return this.connectionState;
  }
}

// Singleton instance
export const websocketService = new WebSocketService();


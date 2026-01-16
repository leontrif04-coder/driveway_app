# backend/app/websocket_manager.py
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime
from app.schemas.occupancy import SpotAvailabilityUpdate

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts availability updates."""

    def __init__(self):
        # Store active connections
        self.active_connections: Set[WebSocket] = set()
        # Store client subscriptions (lat/lng bounds for filtering)
        self.client_subscriptions: Dict[WebSocket, Optional[dict]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.client_subscriptions[websocket] = None
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_subscriptions:
            del self.client_subscriptions[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    def set_subscription(self, websocket: WebSocket, bounds: Optional[dict]):
        """Set geographic bounds for a client's subscription (filter updates by location)."""
        if websocket in self.client_subscriptions:
            self.client_subscriptions[websocket] = bounds

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast_update(self, update: SpotAvailabilityUpdate, spot_lat: float, spot_lng: float):
        """Broadcast availability update to all connected clients (filtered by subscription bounds)."""
        if not self.active_connections:
            return

        message = {
            "type": "availability_update",
            "data": {
                "spot_id": update.spot_id,
                "is_occupied": update.is_occupied,
                "estimated_availability_time": update.estimated_availability_time.isoformat() if update.estimated_availability_time else None,
                "timestamp": update.timestamp.isoformat(),
            },
        }

        disconnected = []
        for connection in self.active_connections:
            # Check if client's subscription bounds include this spot
            subscription = self.client_subscriptions.get(connection)
            if subscription and not self._is_within_bounds(spot_lat, spot_lng, subscription):
                continue

            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    def _is_within_bounds(self, lat: float, lng: float, bounds: dict) -> bool:
        """Check if a point is within subscription bounds."""
        if not bounds:
            return True  # No bounds = subscribe to all updates

        min_lat = bounds.get("min_lat")
        max_lat = bounds.get("max_lat")
        min_lng = bounds.get("min_lng")
        max_lng = bounds.get("max_lng")

        if min_lat is not None and lat < min_lat:
            return False
        if max_lat is not None and lat > max_lat:
            return False
        if min_lng is not None and lng < min_lng:
            return False
        if max_lng is not None and lng > max_lng:
            return False

        return True

    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


# Global connection manager instance
manager = ConnectionManager()


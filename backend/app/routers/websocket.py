# backend/app/routers/websocket.py
# WebSocket endpoint - registered directly in main.py (not via APIRouter)
from fastapi import WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json
import logging
from datetime import datetime
from app.websocket_manager import manager

logger = logging.getLogger(__name__)


async def websocket_endpoint(
    websocket: WebSocket,
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lng: Optional[float] = Query(None),
    max_lng: Optional[float] = Query(None),
):
    """
    WebSocket endpoint for real-time parking availability updates.
    
    Query parameters (optional) for filtering updates by geographic bounds:
    - min_lat, max_lat: Latitude bounds
    - min_lng, max_lng: Longitude bounds
    
    Messages:
    - Client can send: {"type": "subscribe", "data": {"bounds": {...}}}
    - Server sends: {"type": "availability_update", "data": {...}}
    - Server sends: {"type": "pong"} in response to "ping"
    """
    await manager.connect(websocket)
    
    # Set subscription bounds from query params
    bounds = None
    if min_lat is not None or max_lat is not None or min_lng is not None or max_lng is not None:
        bounds = {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lng": min_lng,
            "max_lng": max_lng,
        }
    manager.set_subscription(websocket, bounds)
    
    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "connected",
                "data": {"message": "Connected to parking availability updates", "timestamp": datetime.utcnow().isoformat()},
            },
            websocket,
        )
        
        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                msg_type = message.get("type")
                
                if msg_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message(
                        {"type": "pong", "data": {"timestamp": datetime.utcnow().isoformat()}},
                        websocket,
                    )
                elif msg_type == "subscribe":
                    # Update subscription bounds
                    bounds_data = message.get("data", {}).get("bounds")
                    manager.set_subscription(websocket, bounds_data)
                    await manager.send_personal_message(
                        {
                            "type": "subscribed",
                            "data": {"bounds": bounds_data, "timestamp": datetime.utcnow().isoformat()},
                        },
                        websocket,
                    )
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
                    
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "data": {"message": "Invalid JSON"}},
                    websocket,
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await manager.send_personal_message(
                    {"type": "error", "data": {"message": str(e)}},
                    websocket,
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

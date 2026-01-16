# backend/app/schemas/occupancy.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OccupancyEvent(BaseModel):
    """Represents a check-in or check-out event for a parking spot."""
    spot_id: str
    event_type: str  # "check_in" or "check_out"
    timestamp: datetime
    estimated_duration_minutes: Optional[int] = None  # Estimated duration when checking in


class OccupancyUpdate(BaseModel):
    """Request to update spot occupancy status."""
    is_occupied: bool
    estimated_duration_minutes: Optional[int] = None  # For check-in: estimated parking duration


class SpotAvailabilityUpdate(BaseModel):
    """WebSocket message for spot availability updates."""
    spot_id: str
    is_occupied: bool
    estimated_availability_time: Optional[datetime] = None
    timestamp: datetime


class WebSocketMessage(BaseModel):
    """Base WebSocket message format."""
    type: str  # "availability_update", "error", "pong"
    data: dict



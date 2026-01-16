# backend/app/schemas/parking.py
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

MeterStatus = Literal["working", "broken", "unknown"]

class ParkingSpot(BaseModel):
    id: str
    latitude: float
    longitude: float
    street_name: str
    max_duration_minutes: Optional[int] = None
    price_per_hour_usd: Optional[float] = None

    safety_score: float
    tourism_density: float
    meter_status: MeterStatus
    meter_status_confidence: float

    distance_to_user_m: Optional[float] = None
    distance_to_destination_m: Optional[float] = None

    review_count: int
    last_updated_at: datetime

    composite_score: Optional[float] = None
    score: Optional[float] = None  # Computed from reviews

    # Real-time availability fields
    is_occupied: bool = False
    estimated_availability_time: Optional[datetime] = None  # When occupied spot will be available

    class Config:
        orm_mode = True

class ParkingSpotCreate(BaseModel):
    latitude: float
    longitude: float
    street_name: str
    max_duration_minutes: Optional[int] = None
    price_per_hour_usd: Optional[float] = None
    safety_score: float
    tourism_density: float
    meter_status: MeterStatus
    meter_status_confidence: float



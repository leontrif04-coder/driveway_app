# backend/app/schemas/user_behavior.py
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

DestinationType = Literal["restaurant", "office", "entertainment", "shopping", "residential", "other"]


class UserParkingEvent(BaseModel):
    """Represents a user parking event for ML training."""
    user_id: str
    spot_id: str
    timestamp: datetime
    time_of_day: str  # "morning", "afternoon", "evening", "night"
    day_of_week: int  # 0=Monday, 6=Sunday
    duration_minutes: Optional[int] = None
    price_paid_usd: Optional[float] = None
    final_destination_type: Optional[DestinationType] = None
    user_rating: Optional[int] = None  # User's rating of this parking choice (1-5)
    safety_score_at_time: float
    distance_to_destination_m: Optional[float] = None


class UserPreferences(BaseModel):
    """User parking preferences for recommendations."""
    user_id: str
    preferred_price_range_min: Optional[float] = None
    preferred_price_range_max: Optional[float] = None
    max_walking_distance_m: Optional[float] = None
    min_safety_score: Optional[float] = None
    preferred_duration_minutes: Optional[int] = None
    preferred_parking_times: list[str] = []  # ["morning", "evening"]
    preferred_destination_types: list[DestinationType] = []
    last_updated: datetime


class RecommendationRequest(BaseModel):
    """Request for parking spot recommendations."""
    user_id: Optional[str] = None
    latitude: float
    longitude: float
    destination_type: Optional[DestinationType] = None
    radius_m: float = 1000
    limit: int = 10


class Recommendation(BaseModel):
    """A parking spot recommendation with explanation."""
    spot_id: str
    score: float  # Confidence score 0-100
    reasons: list[str]  # Explanation tags
    match_confidence: float  # 0-1


class RecommendationResponse(BaseModel):
    """Response containing recommendations."""
    recommendations: list[Recommendation]
    user_id: Optional[str] = None
    model_version: str = "v1.0"
    generated_at: datetime


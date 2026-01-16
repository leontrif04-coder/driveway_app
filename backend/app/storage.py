# backend/app/storage.py
from typing import Dict, List, Optional
from datetime import datetime
from app.schemas.parking import ParkingSpot
from app.schemas.review import Review
from app.schemas.occupancy import OccupancyEvent
from app.schemas.user_behavior import UserParkingEvent, UserPreferences
import uuid

# In-memory storage
_spots: Dict[str, ParkingSpot] = {}
_reviews: Dict[str, List[Review]] = {}  # spot_id -> list of reviews
_occupancy_history: Dict[str, List] = {}  # spot_id -> List[OccupancyEvent]
_user_parking_history: Dict[str, List[UserParkingEvent]] = {}  # user_id -> List[UserParkingEvent]
_user_preferences: Dict[str, UserPreferences] = {}  # user_id -> UserPreferences

def get_all_spots() -> List[ParkingSpot]:
    """Get all parking spots."""
    return list(_spots.values())

def get_spot(spot_id: str) -> Optional[ParkingSpot]:
    """Get a parking spot by ID."""
    return _spots.get(spot_id)

def create_spot(spot: ParkingSpot) -> ParkingSpot:
    """Create a new parking spot."""
    _spots[spot.id] = spot
    _reviews[spot.id] = []
    return spot

def get_reviews(spot_id: str) -> List[Review]:
    """Get all reviews for a parking spot."""
    return _reviews.get(spot_id, [])

def add_review(spot_id: str, review: Review) -> Review:
    """Add a review to a parking spot."""
    if spot_id not in _reviews:
        _reviews[spot_id] = []
    _reviews[spot_id].append(review)
    return review

def update_spot(spot: ParkingSpot) -> ParkingSpot:
    """Update an existing parking spot."""
    _spots[spot.id] = spot
    return spot

def add_occupancy_event(spot_id: str, event: OccupancyEvent) -> OccupancyEvent:
    """Add an occupancy event to history."""
    if spot_id not in _occupancy_history:
        _occupancy_history[spot_id] = []
    _occupancy_history[spot_id].append(event)
    return event

def get_occupancy_history(spot_id: str) -> List[OccupancyEvent]:
    """Get occupancy history for a spot."""
    return _occupancy_history.get(spot_id, [])

def clear_occupancy_history(spot_id: Optional[str] = None):
    """Clear occupancy history for a spot or all spots."""
    if spot_id:
        _occupancy_history.pop(spot_id, None)
    else:
        _occupancy_history.clear()

def add_user_parking_event(event: UserParkingEvent) -> UserParkingEvent:
    """Add a user parking event to history."""
    if event.user_id not in _user_parking_history:
        _user_parking_history[event.user_id] = []
    _user_parking_history[event.user_id].append(event)
    return event

def get_user_parking_history(user_id: str) -> List[UserParkingEvent]:
    """Get parking history for a user."""
    return _user_parking_history.get(user_id, [])

def get_all_user_parking_events() -> List[UserParkingEvent]:
    """Get all user parking events (for ML training)."""
    all_events = []
    for events in _user_parking_history.values():
        all_events.extend(events)
    return all_events

def save_user_preferences(prefs: UserPreferences) -> UserPreferences:
    """Save or update user preferences."""
    _user_preferences[prefs.user_id] = prefs
    return prefs

def get_user_preferences(user_id: str) -> Optional[UserPreferences]:
    """Get user preferences."""
    return _user_preferences.get(user_id)

def get_all_users() -> List[str]:
    """Get all user IDs."""
    return list(_user_parking_history.keys())

def seed_data():
    """Seed 10 fake parking spots around a default location (NYC: 40.7128, -74.0060)."""
    base_lat = 40.7128
    base_lng = -74.0060
    now = datetime.utcnow()
    
    # Clear existing data
    _spots.clear()
    _reviews.clear()
    _occupancy_history.clear()
    # Note: Don't clear user data on seed
    
    spots_data = [
        {"lat": 40.7128, "lng": -74.0060, "street": "Broadway", "safety": 80, "tourism": 70, "meter": "working", "confidence": 0.9, "price": 4.0, "duration": 120},
        {"lat": 40.7138, "lng": -74.0030, "street": "Church St", "safety": 60, "tourism": 50, "meter": "broken", "confidence": 0.8, "price": 3.0, "duration": 60},
        {"lat": 40.7118, "lng": -74.0090, "street": "Park Pl", "safety": 75, "tourism": 60, "meter": "working", "confidence": 0.85, "price": 3.5, "duration": 90},
        {"lat": 40.7148, "lng": -74.0000, "street": "Canal St", "safety": 70, "tourism": 80, "meter": "working", "confidence": 0.95, "price": 5.0, "duration": 120},
        {"lat": 40.7108, "lng": -74.0120, "street": "Vesey St", "safety": 85, "tourism": 40, "meter": "working", "confidence": 0.9, "price": 2.5, "duration": 180},
        {"lat": 40.7158, "lng": -74.0040, "street": "Lafayette St", "safety": 65, "tourism": 55, "meter": "unknown", "confidence": 0.5, "price": 3.0, "duration": 60},
        {"lat": 40.7098, "lng": -74.0150, "street": "West St", "safety": 90, "tourism": 30, "meter": "working", "confidence": 0.92, "price": 2.0, "duration": 240},
        {"lat": 40.7168, "lng": -74.0010, "street": "Mulberry St", "safety": 55, "tourism": 90, "meter": "broken", "confidence": 0.75, "price": 6.0, "duration": 60},
        {"lat": 40.7088, "lng": -74.0180, "street": "Greenwich St", "safety": 78, "tourism": 45, "meter": "working", "confidence": 0.88, "price": 3.5, "duration": 120},
        {"lat": 40.7178, "lng": -74.0020, "street": "Mott St", "safety": 68, "tourism": 75, "meter": "working", "confidence": 0.82, "price": 4.5, "duration": 90},
    ]
    
    for i, data in enumerate(spots_data, 1):
        spot_id = f"spot-{i}"
        spot = ParkingSpot(
            id=spot_id,
            latitude=data["lat"],
            longitude=data["lng"],
            street_name=data["street"],
            max_duration_minutes=data["duration"],
            price_per_hour_usd=data["price"],
            safety_score=data["safety"],
            tourism_density=data["tourism"],
            meter_status=data["meter"],
            meter_status_confidence=data["confidence"],
            review_count=0,
            last_updated_at=now,
        )
        _spots[spot_id] = spot
        _reviews[spot_id] = []


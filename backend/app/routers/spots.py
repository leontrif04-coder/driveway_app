# backend/app/routers/spots.py
from fastapi import APIRouter, Query, Path, HTTPException
from typing import List, Optional
from app.schemas.parking import ParkingSpot, ParkingSpotCreate
from app.services import scoring, geo
from app.services.scoring import compute_spot_score
from app.storage import get_all_spots, get_spot, create_spot
from datetime import datetime
import uuid

router = APIRouter()

def _add_score_to_spot(spot: ParkingSpot) -> ParkingSpot:
    """Add computed score to a spot."""
    spot_dict = spot.dict()
    spot_dict["score"] = compute_spot_score(spot.id)
    return ParkingSpot(**spot_dict)

@router.get("/", response_model=List[ParkingSpot])
async def list_spots(
    lat: float = Query(..., description="Latitude of center point"),
    lng: float = Query(..., description="Longitude of center point"),
    radius_m: float = Query(1000, description="Radius in meters"),
    limit: int = Query(50, description="Maximum number of spots to return"),
):
    """
    Get parking spots near a point.
    Returns spots within radius_m meters of (lat, lng), limited to 'limit' results.
    """
    from app.services.geo import haversine_distance_m
    
    all_spots = get_all_spots()
    center = (lat, lng)
    
    # Filter spots within radius and compute distances
    nearby_spots = []
    for spot in all_spots:
        distance = haversine_distance_m(center, (spot.latitude, spot.longitude))
        if distance <= radius_m:
            spot_dict = spot.dict()
            spot_dict["distance_to_user_m"] = distance
            spot_with_distance = ParkingSpot(**spot_dict)
            # Add computed score
            nearby_spots.append(_add_score_to_spot(spot_with_distance))
    
    # Sort by distance and limit
    nearby_spots.sort(key=lambda s: s.distance_to_user_m or float('inf'))
    return nearby_spots[:limit]

@router.get("/{spot_id}", response_model=ParkingSpot)
async def get_spot_by_id(spot_id: str = Path(...)):
    """Get a specific parking spot by ID."""
    spot = get_spot(spot_id)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")
    return _add_score_to_spot(spot)

@router.post("/", response_model=ParkingSpot)
async def create_spot_endpoint(spot_data: ParkingSpotCreate):
    """Create a new parking spot (for dev/testing)."""
    spot_id = f"spot-{uuid.uuid4().hex[:8]}"
    spot = ParkingSpot(
        id=spot_id,
        latitude=spot_data.latitude,
        longitude=spot_data.longitude,
        street_name=spot_data.street_name,
        max_duration_minutes=spot_data.max_duration_minutes,
        price_per_hour_usd=spot_data.price_per_hour_usd,
        safety_score=spot_data.safety_score,
        tourism_density=spot_data.tourism_density,
        meter_status=spot_data.meter_status,
        meter_status_confidence=spot_data.meter_status_confidence,
        review_count=0,
        last_updated_at=datetime.utcnow(),
    )
    created_spot = create_spot(spot)
    return _add_score_to_spot(created_spot)



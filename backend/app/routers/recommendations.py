# backend/app/routers/recommendations.py
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.schemas.user_behavior import (
    RecommendationRequest,
    RecommendationResponse,
    Recommendation,
    DestinationType,
)
from app.database.config import get_db
from app.database.sync_repositories import RepositoryFactory, ParkingSpotRepository, UserParkingEventRepository
from app.database.mappers import db_spot_to_schema
from app.services.ml.recommender import get_recommender

router = APIRouter()


def get_spot_repository(db: Session = Depends(get_db)) -> ParkingSpotRepository:
    """Dependency to get parking spot repository."""
    factory = RepositoryFactory(db)
    return factory.parking_spots


def get_parking_event_repository(db: Session = Depends(get_db)) -> UserParkingEventRepository:
    """Dependency to get user parking event repository."""
    factory = RepositoryFactory(db)
    return factory.parking_events


@router.get("/api/v1/recommendations")
async def get_recommendations(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    user_id: Optional[str] = Query(None, description="User ID for personalization"),
    destination_type: Optional[DestinationType] = Query(None, description="Destination type"),
    radius_m: float = Query(1000, description="Search radius in meters"),
    limit: int = Query(10, description="Number of recommendations"),
    spot_repo: ParkingSpotRepository = Depends(get_spot_repository),
    parking_event_repo: UserParkingEventRepository = Depends(get_parking_event_repository),
):
    """
    Get personalized parking spot recommendations.
    
    Uses ML model to rank spots based on:
    - User preferences and history
    - Current context (time, destination type)
    - Spot attributes
    """
    try:
        # Get spots within radius using PostGIS
        db_spots_with_distance = spot_repo.find_within_radius(
            latitude=lat,
            longitude=lng,
            radius_meters=radius_m,
            limit=100  # Get more spots for ML to rank
        )
        
        if not db_spots_with_distance:
            return RecommendationResponse(
                recommendations=[],
                user_id=user_id,
                model_version="v1.0",
                generated_at=datetime.utcnow(),
            )
        
        # Convert to Pydantic schemas
        nearby_spots = []
        for db_spot, distance_m in db_spots_with_distance:
            spot_schema = db_spot_to_schema(db_spot, distance_m=distance_m)
            nearby_spots.append(spot_schema)
        
        # Get recommendations from ML model
        recommender = get_recommender()
        
        # If user_id provided, get user preferences from history
        user_preferences = None
        if user_id:
            try:
                from uuid import UUID
                user_uuid = UUID(user_id)
                user_preferences = parking_event_repo.get_user_preferences_from_history(user_uuid)
            except (ValueError, Exception):
                # Invalid user_id or no history, continue without preferences
                pass
        
        recommendations = recommender.generate_recommendations(
            user_id=user_id,
            spots=nearby_spots,
            user_lat=lat,
            user_lng=lng,
            destination_type=destination_type,
            limit=limit,
        )
        
        return RecommendationResponse(
            recommendations=recommendations,
            user_id=user_id,
            model_version=recommender.model_version,
            generated_at=datetime.utcnow(),
        )
        
    except Exception as e:
        # Fallback to distance-based ranking
        from fastapi import status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}",
        )

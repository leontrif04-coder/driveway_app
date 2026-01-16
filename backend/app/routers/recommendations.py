# backend/app/routers/recommendations.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
from app.schemas.user_behavior import (
    RecommendationRequest,
    RecommendationResponse,
    Recommendation,
    DestinationType,
)
from app.storage import get_all_spots
from app.services.ml.recommender import get_recommender
from app.services.geo import haversine_distance_m
from app.schemas.parking import ParkingSpot

router = APIRouter()


@router.get("/api/v1/recommendations")
async def get_recommendations(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    user_id: Optional[str] = Query(None, description="User ID for personalization"),
    destination_type: Optional[DestinationType] = Query(None, description="Destination type"),
    radius_m: float = Query(1000, description="Search radius in meters"),
    limit: int = Query(10, description="Number of recommendations"),
):
    """
    Get personalized parking spot recommendations.
    
    Uses ML model to rank spots based on:
    - User preferences and history
    - Current context (time, destination type)
    - Spot attributes
    """
    try:
        # Get all spots
        all_spots = get_all_spots()
        
        # Filter spots within radius
        nearby_spots = []
        for spot in all_spots:
            distance = haversine_distance_m((lat, lng), (spot.latitude, spot.longitude))
            if distance <= radius_m:
                nearby_spots.append(spot)
        
        if not nearby_spots:
            return RecommendationResponse(
                recommendations=[],
                user_id=user_id,
                model_version="v1.0",
                generated_at=datetime.utcnow(),
            )
        
        # Get recommendations from ML model
        recommender = get_recommender()
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


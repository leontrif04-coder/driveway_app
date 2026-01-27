"""
Smart Parking Assistant - Database Model to Pydantic Schema Mappers
==================================================================

Helper functions to convert database ORM models to Pydantic schemas.
Handles field name differences and type conversions.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.schemas.parking import ParkingSpot as ParkingSpotSchema
from app.schemas.review import Review as ReviewSchema
from .models import ParkingSpot as ParkingSpotModel, Review as ReviewModel


def db_spot_to_schema(db_spot: ParkingSpotModel, distance_m: Optional[float] = None) -> ParkingSpotSchema:
    """
    Convert database ParkingSpot model to Pydantic schema.
    
    Args:
        db_spot: Database model instance
        distance_m: Optional distance in meters (from geospatial query)
    
    Returns:
        Pydantic ParkingSpot schema
    """
    return ParkingSpotSchema(
        id=str(db_spot.id),
        latitude=float(db_spot.latitude),
        longitude=float(db_spot.longitude),
        street_name=db_spot.street_name,
        max_duration_minutes=db_spot.max_duration_minutes,
        price_per_hour_usd=float(db_spot.price_per_hour_usd) if db_spot.price_per_hour_usd else None,
        safety_score=float(db_spot.safety_score),
        tourism_density=float(db_spot.tourism_density),
        meter_status=db_spot.meter_status.value,
        meter_status_confidence=float(db_spot.meter_status_confidence),
        distance_to_user_m=distance_m,
        review_count=db_spot.review_count,
        last_updated_at=db_spot.updated_at,
        score=float(db_spot.computed_score) if db_spot.computed_score else None,
        composite_score=float(db_spot.computed_score) if db_spot.computed_score else None,
        is_occupied=db_spot.is_occupied,
        estimated_availability_time=db_spot.estimated_available_at,
    )


def db_review_to_schema(db_review: ReviewModel) -> ReviewSchema:
    """
    Convert database Review model to Pydantic schema.
    
    Args:
        db_review: Database model instance
    
    Returns:
        Pydantic Review schema
    """
    return ReviewSchema(
        id=str(db_review.id),
        spot_id=str(db_review.spot_id),
        rating=db_review.rating,
        text=db_review.review_text or "",
        created_at=db_review.created_at,
    )


def schema_spot_to_db(spot_data, spot_id: Optional[UUID] = None) -> ParkingSpotModel:
    """
    Convert Pydantic ParkingSpotCreate schema to database model.
    
    Args:
        spot_data: ParkingSpotCreate schema instance
        spot_id: Optional UUID (if None, will be generated)
    
    Returns:
        Database ParkingSpot model instance (not yet persisted)
    """
    from .models import MeterStatus
    
    return ParkingSpotModel(
        id=spot_id or UUID(spot_data.id) if hasattr(spot_data, 'id') and spot_data.id else None,
        latitude=Decimal(str(spot_data.latitude)),
        longitude=Decimal(str(spot_data.longitude)),
        street_name=spot_data.street_name,
        max_duration_minutes=spot_data.max_duration_minutes,
        price_per_hour_usd=Decimal(str(spot_data.price_per_hour_usd)) if spot_data.price_per_hour_usd else None,
        safety_score=int(spot_data.safety_score),
        tourism_density=int(spot_data.tourism_density),
        meter_status=MeterStatus(spot_data.meter_status),
        meter_status_confidence=Decimal(str(spot_data.meter_status_confidence)),
    )


def schema_review_to_db(review_data, spot_id: UUID, user_id: Optional[UUID] = None) -> ReviewModel:
    """
    Convert Pydantic ReviewCreate schema to database model.
    
    Args:
        review_data: ReviewCreate schema instance
        spot_id: UUID of the parking spot
        user_id: Optional UUID of the user
    
    Returns:
        Database Review model instance (not yet persisted)
    """
    return ReviewModel(
        spot_id=spot_id,
        user_id=user_id,
        rating=review_data.rating,
        review_text=review_data.text,
    )


"""
Smart Parking Assistant - Synchronous Repository Wrappers
========================================================

Sync versions of repositories for use with FastAPI sync routers.
These wrap the async repositories but use sync sessions.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, cast, func, or_, select, update
from sqlalchemy.orm import Session
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint, ST_SetSRID

from .models import (
    MeterStatus,
    OccupancyEvent,
    ParkingSpot,
    Review,
    UserParkingEvent,
)
from sqlalchemy import func


# ============================================================================
# Parking Spot Repository (Sync)
# ============================================================================

class ParkingSpotRepository:
    """Synchronous repository for ParkingSpot with geospatial queries."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def find_within_radius(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float,
        limit: int = 50,
        only_available: bool = False,
        min_safety_score: Optional[int] = None,
        max_price: Optional[Decimal] = None,
    ) -> List[tuple[ParkingSpot, float]]:
        """
        Find parking spots within a radius of a point.
        
        Uses PostGIS ST_DWithin for efficient geospatial queries.
        
        Returns:
            List of tuples (ParkingSpot, distance_m)
        """
        # Create the search point
        point = ST_MakePoint(longitude, latitude)
        search_point = ST_SetSRID(point, 4326)
        
        # Build base query with distance calculation
        query = (
            select(
                ParkingSpot,
                ST_Distance(
                    cast(ParkingSpot.location, Geography),
                    cast(search_point, Geography)
                ).label("distance_m")
            )
            .where(
                and_(
                    ParkingSpot.is_active == True,
                    ST_DWithin(
                        cast(ParkingSpot.location, Geography),
                        cast(search_point, Geography),
                        radius_meters
                    )
                )
            )
        )
        
        # Apply filters
        if only_available:
            query = query.where(ParkingSpot.is_occupied == False)
        
        if min_safety_score is not None:
            query = query.where(ParkingSpot.safety_score >= min_safety_score)
        
        if max_price is not None:
            query = query.where(
                or_(
                    ParkingSpot.price_per_hour_usd <= max_price,
                    ParkingSpot.price_per_hour_usd.is_(None)
                )
            )
        
        # Order by distance and limit
        query = query.order_by("distance_m").limit(limit)
        
        result = self.session.execute(query)
        rows = result.all()
        
        # Return list of (spot, distance) tuples
        return [(spot, float(distance_m)) for spot, distance_m in rows]
    
    def get_by_id(self, spot_id: UUID) -> Optional[ParkingSpot]:
        """Get a parking spot by ID."""
        return self.session.get(ParkingSpot, spot_id)
    
    def create(self, spot: ParkingSpot) -> ParkingSpot:
        """Create a new parking spot."""
        self.session.add(spot)
        self.session.flush()
        self.session.refresh(spot)
        return spot
    
    def update(self, spot: ParkingSpot) -> ParkingSpot:
        """Update an existing parking spot."""
        self.session.merge(spot)
        self.session.flush()
        return spot
    
    def update_occupancy(
        self,
        spot_id: UUID,
        is_occupied: bool,
        estimated_available_at: Optional[datetime] = None,
    ) -> Optional[ParkingSpot]:
        """Update spot occupancy status."""
        spot = self.get_by_id(spot_id)
        if spot:
            spot.is_occupied = is_occupied
            spot.last_occupancy_change = datetime.utcnow()
            spot.estimated_available_at = estimated_available_at
            self.session.flush()
        return spot
    
    def update_meter_status(
        self,
        spot_id: UUID,
        status: MeterStatus,
        confidence: float,
    ) -> Optional[ParkingSpot]:
        """Update meter status from review analysis."""
        self.session.execute(
            update(ParkingSpot)
            .where(ParkingSpot.id == spot_id)
            .values(
                meter_status=status,
                meter_status_confidence=Decimal(str(confidence)),
                meter_last_verified_at=func.now(),
            )
        )
        self.session.flush()
        return self.get_by_id(spot_id)


# ============================================================================
# Review Repository (Sync)
# ============================================================================

class ReviewRepository:
    """Synchronous repository for Review operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_for_spot(
        self,
        spot_id: UUID,
        limit: int = 50,
        include_hidden: bool = False,
    ) -> Sequence[Review]:
        """Get reviews for a specific spot."""
        query = (
            select(Review)
            .where(Review.spot_id == spot_id)
            .order_by(Review.created_at.desc())
            .limit(limit)
        )
        
        if not include_hidden:
            query = query.where(Review.is_visible == True)
        
        result = self.session.execute(query)
        return result.scalars().all()
    
    def create(self, review: Review) -> Review:
        """Create a new review."""
        self.session.add(review)
        self.session.flush()
        self.session.refresh(review)
        # Note: The trigger will automatically update spot review stats
        return review
    
    def get_by_id(self, review_id: UUID) -> Optional[Review]:
        """Get a review by ID."""
        return self.session.get(Review, review_id)


# ============================================================================
# Occupancy Event Repository (Sync)
# ============================================================================

class OccupancyEventRepository:
    """Synchronous repository for OccupancyEvent operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, event: OccupancyEvent) -> OccupancyEvent:
        """Create a new occupancy event."""
        self.session.add(event)
        self.session.flush()
        self.session.refresh(event)
        # Note: The trigger will automatically update spot occupancy status
        return event


# ============================================================================
# User Parking Event Repository (Sync)
# ============================================================================

class UserParkingEventRepository:
    """Synchronous repository for user parking history (ML training data)."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_training_data(
        self,
        since: Optional[datetime] = None,
        limit: int = 10000,
    ) -> Sequence[UserParkingEvent]:
        """Get parking events for ML training."""
        query = (
            select(UserParkingEvent)
            .where(UserParkingEvent.user_rating.isnot(None))
            .order_by(UserParkingEvent.started_at.desc())
            .limit(limit)
        )
        
        if since:
            query = query.where(UserParkingEvent.started_at >= since)
        
        result = self.session.execute(query)
        return result.scalars().all()
    
    def get_user_preferences_from_history(
        self,
        user_id: UUID,
    ) -> dict:
        """
        Compute user preferences from parking history.
        Used for feature engineering.
        """
        result = self.session.execute(
            select(
                func.avg(UserParkingEvent.price_paid_usd).label("avg_price"),
                func.avg(
                    func.extract("epoch", UserParkingEvent.ended_at - UserParkingEvent.started_at) / 60
                ).label("avg_duration"),
                func.avg(UserParkingEvent.spot_safety_score).label("avg_safety"),
                func.avg(UserParkingEvent.distance_to_dest_m).label("avg_distance"),
                func.count().label("total_events"),
            )
            .where(UserParkingEvent.user_id == user_id)
        )
        
        row = result.one_or_none()
        if row:
            return {
                "avg_price_tolerance": float(row.avg_price) if row.avg_price else None,
                "avg_duration_minutes": float(row.avg_duration) if row.avg_duration else None,
                "avg_safety_preference": float(row.avg_safety) if row.avg_safety else None,
                "avg_walking_distance": float(row.avg_distance) if row.avg_distance else None,
                "total_parkings": row.total_events,
            }
        return {}


# ============================================================================
# Repository Factory (Sync)
# ============================================================================

class RepositoryFactory:
    """
    Factory for creating synchronous repository instances.
    
    Usage:
        from app.database.config import get_db
        from app.database.sync_repositories import RepositoryFactory
        
        def get_spot_repository(db: Session = Depends(get_db)):
            factory = RepositoryFactory(db)
            return factory.parking_spots
    """
    
    def __init__(self, session: Session):
        self.session = session
        self._parking_spots: Optional[ParkingSpotRepository] = None
        self._reviews: Optional[ReviewRepository] = None
        self._occupancy_events: Optional[OccupancyEventRepository] = None
        self._parking_events: Optional[UserParkingEventRepository] = None
    
    @property
    def parking_spots(self) -> ParkingSpotRepository:
        if self._parking_spots is None:
            self._parking_spots = ParkingSpotRepository(self.session)
        return self._parking_spots
    
    @property
    def reviews(self) -> ReviewRepository:
        if self._reviews is None:
            self._reviews = ReviewRepository(self.session)
        return self._reviews
    
    @property
    def occupancy_events(self) -> OccupancyEventRepository:
        if self._occupancy_events is None:
            self._occupancy_events = OccupancyEventRepository(self.session)
        return self._occupancy_events
    
    @property
    def parking_events(self) -> UserParkingEventRepository:
        if self._parking_events is None:
            self._parking_events = UserParkingEventRepository(self.session)
        return self._parking_events


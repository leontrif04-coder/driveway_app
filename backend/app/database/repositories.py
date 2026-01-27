"""
Smart Parking Assistant - Repository Pattern
=============================================

Repository classes encapsulating database operations.
Provides clean separation between business logic and data access.

Design Principles:
    - Single Responsibility: Each repository handles one entity type
    - Dependency Injection: Sessions are injected, not created
    - Async-First: Primary interface is async, with sync alternatives
    - Type Safety: Full type hints for IDE support
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Generic, List, Optional, Sequence, Type, TypeVar
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload, selectinload
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint, ST_SetSRID

from .models import (
    ABTestResult,
    ABTestVariant,
    Base,
    MeterStatus,
    MLModel,
    OccupancyEvent,
    ParkingSpot,
    Review,
    TimeOfDay,
    User,
    UserFavoriteSpot,
    UserParkingEvent,
    UserPreferences,
)


# Type variable for generic repository
ModelT = TypeVar("ModelT", bound=Base)


# ============================================================================
# Base Repository
# ============================================================================

class BaseRepository(Generic[ModelT], ABC):
    """
    Abstract base repository with common CRUD operations.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @property
    @abstractmethod
    def model(self) -> Type[ModelT]:
        """Return the model class for this repository."""
        pass
    
    async def get_by_id(self, id: UUID) -> Optional[ModelT]:
        """Get entity by ID."""
        return await self.session.get(self.model, id)
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        """Get all entities with pagination."""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return result.scalars().all()
    
    async def create(self, entity: ModelT) -> ModelT:
        """Create a new entity."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, entity: ModelT) -> ModelT:
        """Update an existing entity."""
        await self.session.merge(entity)
        await self.session.flush()
        return entity
    
    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID."""
        entity = await self.get_by_id(id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()
            return True
        return False
    
    async def count(self) -> int:
        """Count total entities."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0


# ============================================================================
# User Repository
# ============================================================================

class UserRepository(BaseRepository[User]):
    """Repository for User entity operations."""
    
    @property
    def model(self) -> Type[User]:
        return User
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_external_id(self, external_id: str) -> Optional[User]:
        """Find user by external OAuth ID."""
        result = await self.session.execute(
            select(User).where(User.external_id == external_id)
        )
        return result.scalar_one_or_none()
    
    async def get_with_preferences(self, user_id: UUID) -> Optional[User]:
        """Get user with preferences loaded."""
        result = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .options(joinedload(User.preferences))
        )
        return result.scalar_one_or_none()
    
    async def update_last_active(self, user_id: UUID) -> None:
        """Update user's last active timestamp."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_active_at=func.now())
        )
    
    async def get_active_users(
        self,
        since: datetime,
        limit: int = 100
    ) -> Sequence[User]:
        """Get users active since a given timestamp."""
        result = await self.session.execute(
            select(User)
            .where(
                and_(
                    User.is_active == True,
                    User.last_active_at >= since
                )
            )
            .order_by(User.last_active_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


# ============================================================================
# Parking Spot Repository
# ============================================================================

class ParkingSpotRepository(BaseRepository[ParkingSpot]):
    """
    Repository for ParkingSpot entity with geospatial queries.
    """
    
    @property
    def model(self) -> Type[ParkingSpot]:
        return ParkingSpot
    
    async def find_within_radius(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        limit: int = 50,
        only_available: bool = False,
        min_safety_score: Optional[int] = None,
        max_price: Optional[Decimal] = None,
    ) -> List[dict]:
        """
        Find parking spots within a radius of a point.
        
        Args:
            lat: Latitude of center point
            lng: Longitude of center point
            radius_m: Radius in meters
            limit: Maximum results
            only_available: Filter to only unoccupied spots
            min_safety_score: Minimum safety score filter
            max_price: Maximum price filter
            
        Returns:
            List of spots with distance_m field
        """
        # Create the search point
        search_point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
        
        # Build base query
        query = (
            select(
                ParkingSpot,
                ST_Distance(
                    func.cast(ParkingSpot.location, func.geography),
                    func.cast(search_point, func.geography)
                ).label("distance_m")
            )
            .where(
                and_(
                    ParkingSpot.is_active == True,
                    ST_DWithin(
                        func.cast(ParkingSpot.location, func.geography),
                        func.cast(search_point, func.geography),
                        radius_m
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
        
        result = await self.session.execute(query)
        rows = result.all()
        
        # Transform to list of dicts with distance
        spots = []
        for spot, distance_m in rows:
            spot_dict = {
                "id": spot.id,
                "latitude": float(spot.latitude),
                "longitude": float(spot.longitude),
                "street_name": spot.street_name,
                "street_number": spot.street_number,
                "price_per_hour_usd": float(spot.price_per_hour_usd) if spot.price_per_hour_usd else None,
                "safety_score": spot.safety_score,
                "tourism_density": spot.tourism_density,
                "meter_status": spot.meter_status.value,
                "meter_status_confidence": float(spot.meter_status_confidence),
                "review_count": spot.review_count,
                "avg_rating": float(spot.avg_rating) if spot.avg_rating else None,
                "computed_score": float(spot.computed_score) if spot.computed_score else None,
                "is_occupied": spot.is_occupied,
                "distance_m": round(distance_m, 2),
            }
            spots.append(spot_dict)
        
        return spots
    
    async def update_occupancy(
        self,
        spot_id: UUID,
        is_occupied: bool,
        estimated_available_at: Optional[datetime] = None,
    ) -> Optional[ParkingSpot]:
        """Update spot occupancy status."""
        spot = await self.get_by_id(spot_id)
        if spot:
            spot.is_occupied = is_occupied
            spot.last_occupancy_change = datetime.utcnow()
            spot.estimated_available_at = estimated_available_at
            await self.session.flush()
        return spot
    
    async def update_meter_status(
        self,
        spot_id: UUID,
        status: MeterStatus,
        confidence: float,
    ) -> Optional[ParkingSpot]:
        """Update meter status from review analysis."""
        await self.session.execute(
            update(ParkingSpot)
            .where(ParkingSpot.id == spot_id)
            .values(
                meter_status=status,
                meter_status_confidence=confidence,
                meter_last_verified_at=func.now(),
            )
        )
        return await self.get_by_id(spot_id)
    
    async def get_top_rated(
        self,
        limit: int = 10,
        min_reviews: int = 3,
    ) -> Sequence[ParkingSpot]:
        """Get top-rated spots with minimum review count."""
        result = await self.session.execute(
            select(ParkingSpot)
            .where(
                and_(
                    ParkingSpot.is_active == True,
                    ParkingSpot.review_count >= min_reviews,
                    ParkingSpot.computed_score.isnot(None),
                )
            )
            .order_by(ParkingSpot.computed_score.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_city(
        self,
        city: str,
        limit: int = 100,
    ) -> Sequence[ParkingSpot]:
        """Get all spots in a city."""
        result = await self.session.execute(
            select(ParkingSpot)
            .where(
                and_(
                    ParkingSpot.is_active == True,
                    func.lower(ParkingSpot.city) == city.lower(),
                )
            )
            .order_by(ParkingSpot.computed_score.desc().nulls_last())
            .limit(limit)
        )
        return result.scalars().all()


# ============================================================================
# Review Repository
# ============================================================================

class ReviewRepository(BaseRepository[Review]):
    """Repository for Review entity operations."""
    
    @property
    def model(self) -> Type[Review]:
        return Review
    
    async def get_for_spot(
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
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_for_user(
        self,
        user_id: UUID,
        limit: int = 50,
    ) -> Sequence[Review]:
        """Get reviews by a specific user."""
        result = await self.session.execute(
            select(Review)
            .where(
                and_(
                    Review.user_id == user_id,
                    Review.is_visible == True,
                )
            )
            .order_by(Review.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_rating_distribution(self, spot_id: UUID) -> dict:
        """Get rating distribution for a spot."""
        result = await self.session.execute(
            select(Review.rating, func.count(Review.id))
            .where(
                and_(
                    Review.spot_id == spot_id,
                    Review.is_visible == True,
                )
            )
            .group_by(Review.rating)
        )
        
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating, count in result.all():
            distribution[rating] = count
        
        return distribution
    
    async def get_recent_with_meter_status(
        self,
        spot_id: UUID,
        limit: int = 10,
    ) -> Sequence[Review]:
        """Get recent reviews that mention meter status."""
        result = await self.session.execute(
            select(Review)
            .where(
                and_(
                    Review.spot_id == spot_id,
                    Review.is_visible == True,
                    Review.detected_meter_status.isnot(None),
                )
            )
            .order_by(Review.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def hide_review(self, review_id: UUID) -> bool:
        """Soft-delete a review."""
        result = await self.session.execute(
            update(Review)
            .where(Review.id == review_id)
            .values(is_visible=False)
        )
        return result.rowcount > 0


# ============================================================================
# User Parking Event Repository (ML Training Data)
# ============================================================================

class UserParkingEventRepository(BaseRepository[UserParkingEvent]):
    """Repository for user parking history (ML training data)."""
    
    @property
    def model(self) -> Type[UserParkingEvent]:
        return UserParkingEvent
    
    async def get_user_history(
        self,
        user_id: UUID,
        limit: int = 100,
    ) -> Sequence[UserParkingEvent]:
        """Get parking history for a user."""
        result = await self.session.execute(
            select(UserParkingEvent)
            .where(UserParkingEvent.user_id == user_id)
            .order_by(UserParkingEvent.started_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_training_data(
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
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_user_preferences_from_history(
        self,
        user_id: UUID,
    ) -> dict:
        """
        Compute user preferences from parking history.
        Used for feature engineering.
        """
        result = await self.session.execute(
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
    
    async def get_time_preferences(self, user_id: UUID) -> dict:
        """Get user's time-of-day parking preferences."""
        result = await self.session.execute(
            select(
                UserParkingEvent.time_of_day,
                func.count().label("count"),
            )
            .where(UserParkingEvent.user_id == user_id)
            .group_by(UserParkingEvent.time_of_day)
        )
        
        total = 0
        counts = {}
        for time_of_day, count in result.all():
            counts[time_of_day.value] = count
            total += count
        
        # Normalize to scores
        if total > 0:
            return {
                "morning_preference": counts.get("morning", 0) / total,
                "afternoon_preference": counts.get("afternoon", 0) / total,
                "evening_preference": counts.get("evening", 0) / total,
                "night_preference": counts.get("night", 0) / total,
            }
        return {}


# ============================================================================
# A/B Test Repository
# ============================================================================

class ABTestRepository(BaseRepository[ABTestResult]):
    """Repository for A/B test results and analysis."""
    
    @property
    def model(self) -> Type[ABTestResult]:
        return ABTestResult
    
    async def record_impression(
        self,
        user_id: UUID,
        variant: ABTestVariant,
        spots_shown: List[UUID],
        search_lat: float,
        search_lng: float,
        search_radius_m: Optional[int] = None,
    ) -> ABTestResult:
        """Record an A/B test impression."""
        result = ABTestResult(
            user_id=user_id,
            variant=variant,
            spots_shown=spots_shown,
            search_lat=Decimal(str(search_lat)),
            search_lng=Decimal(str(search_lng)),
            search_radius_m=search_radius_m,
        )
        return await self.create(result)
    
    async def record_conversion(
        self,
        result_id: UUID,
        spot_selected: UUID,
        time_to_select_ms: int,
    ) -> bool:
        """Record a conversion (spot selection)."""
        update_result = await self.session.execute(
            update(ABTestResult)
            .where(ABTestResult.id == result_id)
            .values(
                spot_selected=spot_selected,
                selected_at=func.now(),
                time_to_select_ms=time_to_select_ms,
            )
        )
        return update_result.rowcount > 0
    
    async def get_variant_metrics(
        self,
        since: Optional[datetime] = None,
    ) -> dict:
        """Get aggregated metrics by variant."""
        query = select(
            ABTestResult.variant,
            func.count().label("impressions"),
            func.count(ABTestResult.spot_selected).label("conversions"),
            func.avg(ABTestResult.time_to_select_ms).filter(
                ABTestResult.spot_selected.isnot(None)
            ).label("avg_time_to_select"),
        ).group_by(ABTestResult.variant)
        
        if since:
            query = query.where(ABTestResult.shown_at >= since)
        
        result = await self.session.execute(query)
        
        metrics = {}
        for row in result.all():
            metrics[row.variant.value] = {
                "impressions": row.impressions,
                "conversions": row.conversions,
                "conversion_rate": row.conversions / row.impressions if row.impressions > 0 else 0,
                "avg_time_to_select_ms": float(row.avg_time_to_select) if row.avg_time_to_select else None,
            }
        
        return metrics


# ============================================================================
# Favorite Spots Repository
# ============================================================================

class FavoriteSpotRepository:
    """Repository for user favorite spots."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add_favorite(
        self,
        user_id: UUID,
        spot_id: UUID,
        nickname: Optional[str] = None,
    ) -> UserFavoriteSpot:
        """Add a spot to user's favorites."""
        favorite = UserFavoriteSpot(
            user_id=user_id,
            spot_id=spot_id,
            nickname=nickname,
        )
        self.session.add(favorite)
        await self.session.flush()
        return favorite
    
    async def remove_favorite(self, user_id: UUID, spot_id: UUID) -> bool:
        """Remove a spot from user's favorites."""
        result = await self.session.execute(
            delete(UserFavoriteSpot)
            .where(
                and_(
                    UserFavoriteSpot.user_id == user_id,
                    UserFavoriteSpot.spot_id == spot_id,
                )
            )
        )
        return result.rowcount > 0
    
    async def get_user_favorites(
        self,
        user_id: UUID,
    ) -> Sequence[UserFavoriteSpot]:
        """Get all favorites for a user."""
        result = await self.session.execute(
            select(UserFavoriteSpot)
            .where(UserFavoriteSpot.user_id == user_id)
            .options(joinedload(UserFavoriteSpot.spot))
            .order_by(UserFavoriteSpot.created_at.desc())
        )
        return result.scalars().all()
    
    async def is_favorite(self, user_id: UUID, spot_id: UUID) -> bool:
        """Check if a spot is in user's favorites."""
        result = await self.session.execute(
            select(func.count())
            .where(
                and_(
                    UserFavoriteSpot.user_id == user_id,
                    UserFavoriteSpot.spot_id == spot_id,
                )
            )
        )
        return (result.scalar() or 0) > 0


# ============================================================================
# Repository Factory
# ============================================================================

class RepositoryFactory:
    """
    Factory for creating repository instances.
    
    Usage:
        async with get_async_db_session() as session:
            factory = RepositoryFactory(session)
            spots = await factory.spots.find_within_radius(...)
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._users: Optional[UserRepository] = None
        self._spots: Optional[ParkingSpotRepository] = None
        self._reviews: Optional[ReviewRepository] = None
        self._parking_events: Optional[UserParkingEventRepository] = None
        self._ab_tests: Optional[ABTestRepository] = None
        self._favorites: Optional[FavoriteSpotRepository] = None
    
    @property
    def users(self) -> UserRepository:
        if self._users is None:
            self._users = UserRepository(self.session)
        return self._users
    
    @property
    def spots(self) -> ParkingSpotRepository:
        if self._spots is None:
            self._spots = ParkingSpotRepository(self.session)
        return self._spots
    
    @property
    def reviews(self) -> ReviewRepository:
        if self._reviews is None:
            self._reviews = ReviewRepository(self.session)
        return self._reviews
    
    @property
    def parking_events(self) -> UserParkingEventRepository:
        if self._parking_events is None:
            self._parking_events = UserParkingEventRepository(self.session)
        return self._parking_events
    
    @property
    def ab_tests(self) -> ABTestRepository:
        if self._ab_tests is None:
            self._ab_tests = ABTestRepository(self.session)
        return self._ab_tests
    
    @property
    def favorites(self) -> FavoriteSpotRepository:
        if self._favorites is None:
            self._favorites = FavoriteSpotRepository(self.session)
        return self._favorites

"""
Smart Parking Assistant - SQLAlchemy Models
============================================

Production-ready ORM models with PostGIS integration.
Designed for seamless migration from in-memory storage.

Usage:
    from app.database.models import ParkingSpot, Review, User
    
    # Query spots within radius
    spots = session.execute(
        select(ParkingSpot).where(
            func.ST_DWithin(
                ParkingSpot.location,
                func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326),
                radius_m
            )
        )
    ).scalars().all()
"""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime, Enum, ForeignKey,
    Index, Integer, Numeric, PrimaryKeyConstraint, SmallInteger, String, Text, UniqueConstraint,
    cast, func, text
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, declared_attr
)
from geoalchemy2 import Geometry


# ============================================================================
# Enums
# ============================================================================

class MeterStatus(str, enum.Enum):
    WORKING = "working"
    BROKEN = "broken"
    UNKNOWN = "unknown"


class DestinationType(str, enum.Enum):
    RESTAURANT = "restaurant"
    SHOPPING = "shopping"
    OFFICE = "office"
    ENTERTAINMENT = "entertainment"
    MEDICAL = "medical"
    RESIDENTIAL = "residential"
    OTHER = "other"


class TimeOfDay(str, enum.Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class ABTestVariant(str, enum.Enum):
    CONTROL = "control"
    ML_POWERED = "ml_powered"
    HYBRID = "hybrid"


# ============================================================================
# Base Classes
# ============================================================================

class Base(DeclarativeBase):
    """Base class for all models with common configurations."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


# ============================================================================
# User Models
# ============================================================================

class User(Base, TimestampMixin):
    """User account model."""
    
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    username: Mapped[Optional[str]] = mapped_column(String(100))
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Denormalized stats (updated via triggers)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_parkings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    preferences: Mapped[Optional["UserPreferences"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    reviews: Mapped[List["Review"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    parking_events: Mapped[List["UserParkingEvent"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    favorite_spots: Mapped[List["UserFavoriteSpot"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="users_email_format"
        ),
        Index("idx_users_email", "email"),
        Index("idx_users_last_active", "last_active_at", postgresql_where=text("is_active = TRUE")),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


class UserPreferences(Base, TimestampMixin):
    """User preferences for parking recommendations."""
    
    __tablename__ = "user_preferences"
    
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    
    # Explicit preferences
    preferred_max_price_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    preferred_max_walk_distance_m: Mapped[Optional[int]] = mapped_column(Integer)
    preferred_min_safety_score: Mapped[Optional[int]] = mapped_column(Integer)
    tourism_preference: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Computed preferences (ML pipeline)
    avg_parking_duration_min: Mapped[Optional[int]] = mapped_column(Integer)
    avg_price_tolerance_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    morning_preference_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    afternoon_preference_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    evening_preference_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    night_preference_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    
    # A/B Testing
    ab_test_variant: Mapped[ABTestVariant] = mapped_column(
        Enum(ABTestVariant, name="ab_test_variant"),
        default=ABTestVariant.CONTROL,
        nullable=False
    )
    
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationship
    user: Mapped["User"] = relationship(back_populates="preferences")
    
    __table_args__ = (
        CheckConstraint(
            "preferred_min_safety_score BETWEEN 0 AND 100",
            name="check_safety_score_range"
        ),
        CheckConstraint(
            "tourism_preference IN ('low', 'medium', 'high')",
            name="check_tourism_preference"
        ),
    )


# ============================================================================
# Parking Spot Models
# ============================================================================

class ParkingSpot(Base, TimestampMixin):
    """Parking spot model with PostGIS location."""
    
    __tablename__ = "parking_spots"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # PostGIS geometry (auto-computed from lat/lng via trigger)
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    
    # Denormalized coordinates for API responses
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(11, 8), nullable=False)
    
    # Address
    street_name: Mapped[str] = mapped_column(String(255), nullable=False)
    street_number: Mapped[Optional[str]] = mapped_column(String(20))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(2), default="US")
    
    # Parking attributes
    max_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    price_per_hour_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    spot_type: Mapped[str] = mapped_column(String(50), default="street")
    
    # Quality metrics
    safety_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    tourism_density: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    
    # Meter information
    meter_status: Mapped[MeterStatus] = mapped_column(
        Enum(MeterStatus, name="meter_status"),
        default=MeterStatus.UNKNOWN,
        nullable=False
    )
    meter_status_confidence: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=0,
        nullable=False
    )
    meter_last_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Denormalized review stats (trigger-updated)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    computed_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    
    # Real-time availability
    is_occupied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_occupancy_change: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    estimated_available_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Metadata
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    spot_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Relationships
    reviews: Mapped[List["Review"]] = relationship(
        back_populates="spot",
        cascade="all, delete-orphan"
    )
    occupancy_events: Mapped[List["OccupancyEvent"]] = relationship(
        back_populates="spot",
        cascade="all, delete-orphan"
    )
    parking_events: Mapped[List["UserParkingEvent"]] = relationship(
        back_populates="spot",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint(
            "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180",
            name="valid_coordinates"
        ),
        CheckConstraint("safety_score BETWEEN 0 AND 100", name="check_safety_range"),
        CheckConstraint("tourism_density BETWEEN 0 AND 100", name="check_tourism_range"),
        CheckConstraint("avg_rating BETWEEN 1 AND 5", name="check_rating_range"),
        CheckConstraint("computed_score BETWEEN 0 AND 100", name="check_score_range"),
        CheckConstraint(
            "meter_status_confidence BETWEEN 0 AND 1",
            name="check_confidence_range"
        ),
        Index("idx_spots_location_gist", "location", postgresql_using="gist"),
        Index(
            "idx_spots_safety", "safety_score",
            postgresql_where=text("is_active = TRUE")
        ),
        Index(
            "idx_spots_price", "price_per_hour_usd",
            postgresql_where=text("is_active = TRUE")
        ),
        Index(
            "idx_spots_score", computed_score.desc().nulls_last(),
            postgresql_where=text("is_active = TRUE")
        ),
        Index("idx_spots_active_score", "is_active", computed_score.desc().nulls_last()),
    )
    
    @hybrid_property
    def full_address(self) -> str:
        """Compute full address string."""
        parts = [self.street_number, self.street_name]
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        return ", ".join(filter(None, parts))
    
    def __repr__(self) -> str:
        return f"<ParkingSpot(id={self.id}, street={self.street_name})>"


# ============================================================================
# Review Model
# ============================================================================

class Review(Base):
    """Review model with NLP-extracted metadata."""
    
    __tablename__ = "reviews"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    spot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("parking_spots.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    review_text: Mapped[Optional[str]] = mapped_column(Text)
    
    # NLP-extracted metadata
    detected_meter_status: Mapped[Optional[MeterStatus]] = mapped_column(
        Enum(MeterStatus, name="meter_status")
    )
    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    extracted_keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    spot: Mapped["ParkingSpot"] = relationship(back_populates="reviews")
    user: Mapped[Optional["User"]] = relationship(back_populates="reviews")
    
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="check_review_rating"),
        CheckConstraint("sentiment_score BETWEEN -1 AND 1", name="check_sentiment_range"),
        # Use functional unique index for date casting
        # Reference columns directly and use PostgreSQL date cast syntax
        Index(
            "unique_user_spot_day",
            user_id, spot_id, text("(created_at::date)"),
            unique=True
        ),
        Index(
            "idx_reviews_spot", "spot_id", created_at.desc(),
            postgresql_where=text("is_visible = TRUE")
        ),
        Index(
            "idx_reviews_user", "user_id", created_at.desc(),
            postgresql_where=text("is_visible = TRUE")
        ),
        Index(
            "idx_reviews_rating", "spot_id", "rating",
            postgresql_where=text("is_visible = TRUE")
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Review(id={self.id}, spot_id={self.spot_id}, rating={self.rating})>"


# ============================================================================
# Occupancy Event Model
# ============================================================================

class OccupancyEvent(Base):
    """Time-series occupancy events (partitioned by event_time)."""
    
    __tablename__ = "occupancy_events"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        default=uuid4
    )
    spot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("parking_spots.id", ondelete="CASCADE"),
        nullable=False
    )
    
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    source: Mapped[str] = mapped_column(String(50), default="user_report", nullable=False)
    reported_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id")
    )
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=1.0)
    
    event_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Relationship
    spot: Mapped["ParkingSpot"] = relationship(back_populates="occupancy_events")
    
    __table_args__ = (
        # Composite primary key for partitioning
        PrimaryKeyConstraint("id", "event_time"),
        CheckConstraint(
            "event_type IN ('occupied', 'available', 'unknown')",
            name="check_event_type"
        ),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="check_occupancy_confidence"),
        Index("idx_occupancy_spot_time", "spot_id", event_time.desc()),
    )


# ============================================================================
# User Parking Event Model (ML Training Data)
# ============================================================================

class UserParkingEvent(Base):
    """User parking history for ML feature engineering."""
    
    __tablename__ = "user_parking_events"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    spot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("parking_spots.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Temporal
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # Note: duration_minutes is GENERATED ALWAYS in PostgreSQL
    
    time_of_day: Mapped[TimeOfDay] = mapped_column(
        Enum(TimeOfDay, name="time_of_day"),
        nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    
    # Destination context
    destination_type: Mapped[Optional[DestinationType]] = mapped_column(
        Enum(DestinationType, name="destination_type")
    )
    distance_to_dest_m: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Cost
    price_paid_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    
    # Snapshot of spot attributes (for accurate ML features)
    spot_safety_score: Mapped[int] = mapped_column(Integer, nullable=False)
    spot_tourism_density: Mapped[int] = mapped_column(Integer, nullable=False)
    spot_price_per_hour: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    
    # Outcome metrics
    user_rating: Mapped[Optional[int]] = mapped_column(SmallInteger)
    would_return: Mapped[Optional[bool]] = mapped_column(Boolean)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="parking_events")
    spot: Mapped["ParkingSpot"] = relationship(back_populates="parking_events")
    
    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="check_day_of_week"),
        CheckConstraint("user_rating BETWEEN 1 AND 5", name="check_parking_rating"),
        Index("idx_parking_events_user", "user_id", started_at.desc()),
        Index("idx_parking_events_spot", "spot_id", started_at.desc()),
        Index("idx_parking_events_ml", "user_id", "time_of_day", "day_of_week"),
    )
    
    @hybrid_property
    def duration_minutes(self) -> Optional[int]:
        """Calculate parking duration in minutes."""
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None


# ============================================================================
# User Favorite Spots Model
# ============================================================================

class UserFavoriteSpot(Base):
    """User bookmarked parking spots."""
    
    __tablename__ = "user_favorite_spots"
    
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    spot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("parking_spots.id", ondelete="CASCADE"),
        primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    nickname: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="favorite_spots")
    spot: Mapped["ParkingSpot"] = relationship()


# ============================================================================
# ML Model Metadata
# ============================================================================

class MLModel(Base):
    """Tracks ML model versions and performance."""
    
    __tablename__ = "ml_models"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Performance metrics
    accuracy: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    precision_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    recall: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    f1_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    
    # Training metadata
    training_samples: Mapped[Optional[int]] = mapped_column(Integer)
    feature_count: Mapped[Optional[int]] = mapped_column(Integer)
    hyperparameters: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Artifact location
    artifact_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Lifecycle
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deployed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


# ============================================================================
# A/B Test Results Model
# ============================================================================

class ABTestResult(Base):
    """Tracks A/B test impressions and conversions."""
    
    __tablename__ = "ab_test_results"
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    variant: Mapped[ABTestVariant] = mapped_column(
        Enum(ABTestVariant, name="ab_test_variant"),
        nullable=False
    )
    
    # What was shown
    spots_shown: Mapped[List[UUID]] = mapped_column(ARRAY(PG_UUID(as_uuid=True)), nullable=False)
    
    # What was selected
    spot_selected: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("parking_spots.id")
    )
    
    # Search context
    search_lat: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    search_lng: Mapped[Decimal] = mapped_column(Numeric(11, 8), nullable=False)
    search_radius_m: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Timestamps
    shown_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    selected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Metrics (converted is GENERATED ALWAYS in PostgreSQL)
    time_to_select_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    __table_args__ = (
        Index("idx_ab_test_variant", "variant", "shown_at"),
        Index(
            "idx_ab_test_conversion", "variant", text("(spot_selected IS NOT NULL)"),
            postgresql_where=text("shown_at > NOW() - INTERVAL '30 days'")
        ),
    )
    
    @hybrid_property
    def converted(self) -> bool:
        """Whether the user selected a spot."""
        return self.spot_selected is not None

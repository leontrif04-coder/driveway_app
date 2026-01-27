# backend/tests/conftest.py
import pytest
from typing import List
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from app.schemas.parking import ParkingSpot
from app.schemas.review import Review
from app.database.config import create_test_engine, TestingSessionManager
from app.database.models import Base, ParkingSpot as ParkingSpotModel, Review as ReviewModel
from app.database.sync_repositories import RepositoryFactory
from app.database.mappers import db_spot_to_schema, db_review_to_schema


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_test_engine()
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Provide transactional test session."""
    with TestingSessionManager(seed_data=False) as session:
        yield session
        # Rollback any uncommitted changes
        session.rollback()


@pytest.fixture
def sample_spot() -> ParkingSpot:
    """Create a sample parking spot for testing."""
    return ParkingSpot(
        id="550e8400-e29b-41d4-a716-446655440001",
        latitude=40.7128,
        longitude=-74.0060,
        street_name="Test Street",
        max_duration_minutes=120,
        price_per_hour_usd=4.0,
        safety_score=80.0,
        tourism_density=70.0,
        meter_status="working",
        meter_status_confidence=0.9,
        review_count=0,
        last_updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_spot_2() -> ParkingSpot:
    """Create a second sample parking spot for testing."""
    return ParkingSpot(
        id="550e8400-e29b-41d4-a716-446655440002",
        latitude=40.7138,
        longitude=-74.0030,
        street_name="Test Avenue",
        max_duration_minutes=60,
        price_per_hour_usd=3.0,
        safety_score=60.0,
        tourism_density=50.0,
        meter_status="broken",
        meter_status_confidence=0.8,
        review_count=0,
        last_updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_review(sample_spot: ParkingSpot) -> Review:
    """Create a sample review for testing."""
    return Review(
        id="rev-test-1",
        spot_id=sample_spot.id,
        rating=5,
        text="Great parking spot! Meter works fine.",
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def nyc_location() -> tuple[float, float]:
    """NYC coordinates (40.7128, -74.0060)."""
    return (40.7128, -74.0060)


@pytest.fixture
def london_location() -> tuple[float, float]:
    """London coordinates (51.5074, -0.1278)."""
    return (51.5074, -0.1278)


@pytest.fixture
def populated_db(db_session: Session, sample_spot: ParkingSpot, sample_spot_2: ParkingSpot):
    """Populate database with test spots."""
    from app.database.mappers import schema_spot_to_db
    from app.database.sync_repositories import RepositoryFactory
    
    factory = RepositoryFactory(db_session)
    spot_repo = factory.parking_spots
    
    # Convert schemas to DB models and create
    db_spot1 = schema_spot_to_db(sample_spot, UUID(sample_spot.id))
    db_spot2 = schema_spot_to_db(sample_spot_2, UUID(sample_spot_2.id))
    
    spot_repo.create(db_spot1)
    spot_repo.create(db_spot2)
    db_session.commit()
    
    return [sample_spot, sample_spot_2]


@pytest.fixture
def client(db_session):
    """Create a test client for FastAPI with database."""
    from fastapi.testclient import TestClient
    from main import app
    from app.database.config import get_db
    
    # Override get_db dependency to use test session
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        yield TestClient(app)
    finally:
        # Clean up dependency override
        app.dependency_overrides.clear()

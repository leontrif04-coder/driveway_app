# backend/tests/conftest.py
import pytest
from typing import List
from datetime import datetime
from app.schemas.parking import ParkingSpot
from app.schemas.review import Review
from app.storage import (
    _spots,
    _reviews,
    get_all_spots,
    get_spot,
    create_spot,
    update_spot,
    get_reviews,
    add_review,
)


@pytest.fixture(autouse=True)
def reset_storage():
    """Reset storage before and after each test."""
    _spots.clear()
    _reviews.clear()
    yield
    _spots.clear()
    _reviews.clear()


@pytest.fixture
def sample_spot() -> ParkingSpot:
    """Create a sample parking spot for testing."""
    return ParkingSpot(
        id="spot-test-1",
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
        id="spot-test-2",
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
def populated_storage(sample_spot: ParkingSpot, sample_spot_2: ParkingSpot) -> List[ParkingSpot]:
    """Populate storage with test spots."""
    create_spot(sample_spot)
    create_spot(sample_spot_2)
    return [sample_spot, sample_spot_2]


@pytest.fixture
def client():
    """Create a test client for FastAPI."""
    from fastapi.testclient import TestClient
    from main import app
    
    # Clear storage before creating client
    _spots.clear()
    _reviews.clear()
    
    return TestClient(app)


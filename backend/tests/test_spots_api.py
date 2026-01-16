# backend/tests/test_spots_api.py
import pytest
from datetime import datetime
from app.storage import create_spot, _spots
from app.schemas.parking import ParkingSpot


class TestListSpots:
    """Test GET /api/v1/spots endpoint."""

    def test_list_spots_near_location(self, client):
        """Test finding spots near a location."""
        # Create spots at different locations
        spot1 = ParkingSpot(
            id="spot-1",
            latitude=40.7128,
            longitude=-74.0060,
            street_name="Street 1",
            safety_score=80.0,
            tourism_density=70.0,
            meter_status="working",
            meter_status_confidence=0.9,
            review_count=0,
            last_updated_at=datetime.utcnow(),
        )
        spot2 = ParkingSpot(
            id="spot-2",
            latitude=40.7228,  # ~1km north
            longitude=-74.0060,
            street_name="Street 2",
            safety_score=70.0,
            tourism_density=60.0,
            meter_status="working",
            meter_status_confidence=0.8,
            review_count=0,
            last_updated_at=datetime.utcnow(),
        )
        spot3 = ParkingSpot(
            id="spot-3",
            latitude=51.5074,  # London (very far)
            longitude=-0.1278,
            street_name="Street 3",
            safety_score=75.0,
            tourism_density=65.0,
            meter_status="working",
            meter_status_confidence=0.85,
            review_count=0,
            last_updated_at=datetime.utcnow(),
        )
        
        create_spot(spot1)
        create_spot(spot2)
        create_spot(spot3)
        
        # Search near NYC with 2000m radius
        response = client.get("/api/v1/spots?lat=40.7128&lng=-74.0060&radius_m=2000&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2  # Should find spot1 and spot2, not spot3
        
        # Verify all returned spots have required fields
        for spot in data:
            assert "id" in spot
            assert "latitude" in spot
            assert "longitude" in spot
            assert "score" in spot
            assert "distance_to_user_m" in spot

    def test_list_spots_radius_filtering(self, client, populated_storage):
        """Test that radius filtering works correctly."""
        center_lat, center_lng = 40.7128, -74.0060
        
        # Search with small radius (100m)
        response = client.get(f"/api/v1/spots?lat={center_lat}&lng={center_lng}&radius_m=100&limit=10")
        assert response.status_code == 200
        data = response.json()
        
        # All returned spots should be within radius
        for spot in data:
            assert spot["distance_to_user_m"] <= 100

    def test_list_spots_limit(self, client):
        """Test that limit parameter works."""
        # Create 10 spots
        for i in range(10):
            spot = ParkingSpot(
                id=f"spot-{i}",
                latitude=40.7128 + (i * 0.001),  # Small offsets
                longitude=-74.0060 + (i * 0.001),
                street_name=f"Street {i}",
                safety_score=80.0,
                tourism_density=70.0,
                meter_status="working",
                meter_status_confidence=0.9,
                review_count=0,
                last_updated_at=datetime.utcnow(),
            )
            create_spot(spot)
        
        # Request with limit of 5
        response = client.get("/api/v1/spots?lat=40.7128&lng=-74.0060&radius_m=10000&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_list_spots_sorting_by_distance(self, client):
        """Test that spots are sorted by distance (ascending)."""
        # Create spots at increasing distances
        base_lat, base_lng = 40.7128, -74.0060
        
        spot1 = ParkingSpot(
            id="spot-close",
            latitude=base_lat + 0.001,  # Very close
            longitude=base_lng,
            street_name="Close Street",
            safety_score=80.0,
            tourism_density=70.0,
            meter_status="working",
            meter_status_confidence=0.9,
            review_count=0,
            last_updated_at=datetime.utcnow(),
        )
        spot2 = ParkingSpot(
            id="spot-far",
            latitude=base_lat + 0.01,  # Farther
            longitude=base_lng,
            street_name="Far Street",
            safety_score=80.0,
            tourism_density=70.0,
            meter_status="working",
            meter_status_confidence=0.9,
            review_count=0,
            last_updated_at=datetime.utcnow(),
        )
        
        create_spot(spot1)
        create_spot(spot2)
        
        response = client.get(f"/api/v1/spots?lat={base_lat}&lng={base_lng}&radius_m=10000&limit=10")
        assert response.status_code == 200
        data = response.json()
        
        # Verify sorting
        distances = [spot["distance_to_user_m"] for spot in data]
        assert distances == sorted(distances)

    def test_list_spots_missing_required_params(self, client):
        """Test that missing required parameters return 422."""
        # Missing lat
        response = client.get("/api/v1/spots?lng=-74.0060")
        assert response.status_code == 422
        
        # Missing lng
        response = client.get("/api/v1/spots?lat=40.7128")
        assert response.status_code == 422

    def test_list_spots_empty_result(self, client):
        """Test query that returns no results."""
        response = client.get("/api/v1/spots?lat=0.0&lng=0.0&radius_m=100&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_spots_score_computation(self, client, sample_spot):
        """Test that scores are computed for all spots."""
        create_spot(sample_spot)
        
        response = client.get("/api/v1/spots?lat=40.7128&lng=-74.0060&radius_m=10000&limit=10")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) > 0
        for spot in data:
            assert "score" in spot
            assert isinstance(spot["score"], (int, float))
            assert spot["score"] >= 0.0


class TestGetSpotById:
    """Test GET /api/v1/spots/{spot_id} endpoint."""

    def test_get_spot_by_id_success(self, client, sample_spot):
        """Test getting a spot by ID."""
        create_spot(sample_spot)
        
        response = client.get(f"/api/v1/spots/{sample_spot.id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == sample_spot.id
        assert data["latitude"] == sample_spot.latitude
        assert data["longitude"] == sample_spot.longitude
        assert "score" in data

    def test_get_spot_by_id_not_found(self, client):
        """Test getting a non-existent spot returns 404."""
        response = client.get("/api/v1/spots/non-existent-id")
        assert response.status_code == 404
        assert "detail" in response.json()


class TestCreateSpot:
    """Test POST /api/v1/spots endpoint."""

    def test_create_spot_success(self, client):
        """Test creating a new spot."""
        spot_data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "street_name": "New Street",
            "max_duration_minutes": 120,
            "price_per_hour_usd": 4.0,
            "safety_score": 80.0,
            "tourism_density": 70.0,
            "meter_status": "working",
            "meter_status_confidence": 0.9,
        }
        
        response = client.post("/api/v1/spots", json=spot_data)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["latitude"] == spot_data["latitude"]
        assert data["longitude"] == spot_data["longitude"]
        assert data["street_name"] == spot_data["street_name"]
        assert data["review_count"] == 0
        assert "score" in data

    def test_create_spot_missing_required_fields(self, client):
        """Test creating spot with missing required fields."""
        spot_data = {
            "latitude": 40.7128,
            # Missing longitude and other required fields
        }
        
        response = client.post("/api/v1/spots", json=spot_data)
        assert response.status_code == 422

    def test_create_spot_invalid_data(self, client):
        """Test creating spot with invalid data types."""
        spot_data = {
            "latitude": "not a number",
            "longitude": -74.0060,
            "street_name": "Street",
            "safety_score": 80.0,
            "tourism_density": 70.0,
            "meter_status": "working",
            "meter_status_confidence": 0.9,
        }
        
        response = client.post("/api/v1/spots", json=spot_data)
        assert response.status_code == 422


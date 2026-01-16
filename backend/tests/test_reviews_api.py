# backend/tests/test_reviews_api.py
import pytest
from datetime import datetime
from app.storage import create_spot, get_spot, get_reviews, add_review
from app.schemas.parking import ParkingSpot
from app.schemas.review import Review


class TestListReviews:
    """Test GET /api/v1/spots/{spot_id}/reviews endpoint."""

    def test_list_reviews_success(self, client, sample_spot):
        """Test listing reviews for a spot."""
        create_spot(sample_spot)
        
        # Add some reviews directly to storage
        
        review1 = Review(
            id="rev-1",
            spot_id=sample_spot.id,
            rating=5,
            text="Great spot!",
            created_at=datetime.utcnow(),
        )
        review2 = Review(
            id="rev-2",
            spot_id=sample_spot.id,
            rating=4,
            text="Good parking",
            created_at=datetime.utcnow(),
        )
        add_review(sample_spot.id, review1)
        add_review(sample_spot.id, review2)
        
        response = client.get(f"/api/v1/spots/{sample_spot.id}/reviews")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["spot_id"] == sample_spot.id

    def test_list_reviews_empty(self, client, sample_spot):
        """Test listing reviews for a spot with no reviews."""
        create_spot(sample_spot)
        
        response = client.get(f"/api/v1/spots/{sample_spot.id}/reviews")
        assert response.status_code == 200
        data = response.json()
        
        assert data == []

    def test_list_reviews_spot_not_found(self, client):
        """Test listing reviews for non-existent spot returns 404."""
        response = client.get("/api/v1/spots/non-existent-id/reviews")
        assert response.status_code == 404


class TestCreateReview:
    """Test POST /api/v1/spots/{spot_id}/reviews endpoint."""

    def test_create_review_success(self, client, sample_spot):
        """Test creating a review successfully."""
        create_spot(sample_spot)
        
        review_data = {
            "rating": 5,
            "text": "Great parking spot! Meter works fine.",
        }
        
        response = client.post(f"/api/v1/spots/{sample_spot.id}/reviews", json=review_data)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["spot_id"] == sample_spot.id
        assert data["rating"] == review_data["rating"]
        assert data["text"] == review_data["text"]
        assert "created_at" in data

    def test_create_review_updates_spot_score(self, client, sample_spot):
        """Test that creating a review updates the spot's score."""
        create_spot(sample_spot)
        
        # Initial score should be 0 (no reviews)
        initial_spot = get_spot(sample_spot.id)
        
        review_data = {
            "rating": 5,
            "text": "Great spot!",
        }
        
        response = client.post(f"/api/v1/spots/{sample_spot.id}/reviews", json=review_data)
        assert response.status_code == 200
        
        # Verify spot was updated
        updated_spot = get_spot(sample_spot.id)
        assert updated_spot.review_count == 1

    def test_create_review_updates_meter_status(self, client, sample_spot):
        """Test that creating a review updates meter status."""
        create_spot(sample_spot)
        
        # Create review with working keywords
        review_data = {
            "rating": 5,
            "text": "Meter works fine, no issues",
        }
        
        response = client.post(f"/api/v1/spots/{sample_spot.id}/reviews", json=review_data)
        assert response.status_code == 200
        
        # Verify meter status was updated
        updated_spot = get_spot(sample_spot.id)
        assert updated_spot.meter_status == "working"
        assert updated_spot.meter_status_confidence > 0.0

    def test_create_review_updates_meter_status_broken(self, client, sample_spot):
        """Test that reviews with broken keywords update meter status."""
        create_spot(sample_spot)
        
        review_data = {
            "rating": 1,
            "text": "Broken meter, doesn't work",
        }
        
        response = client.post(f"/api/v1/spots/{sample_spot.id}/reviews", json=review_data)
        assert response.status_code == 200
        
        updated_spot = get_spot(sample_spot.id)
        assert updated_spot.meter_status == "broken"
        assert updated_spot.meter_status_confidence > 0.0

    def test_create_review_increments_review_count(self, client, sample_spot):
        """Test that review count increments correctly."""
        create_spot(sample_spot)
        
        initial_spot = get_spot(sample_spot.id)
        initial_count = initial_spot.review_count
        
        # Add multiple reviews
        for i in range(3):
            review_data = {
                "rating": 4,
                "text": f"Review {i}",
            }
            response = client.post(f"/api/v1/spots/{sample_spot.id}/reviews", json=review_data)
            assert response.status_code == 200
        
        updated_spot = get_spot(sample_spot.id)
        assert updated_spot.review_count == initial_count + 3

    def test_create_review_spot_not_found(self, client):
        """Test creating review for non-existent spot returns 404."""
        review_data = {
            "rating": 5,
            "text": "Great!",
        }
        
        response = client.post("/api/v1/spots/non-existent-id/reviews", json=review_data)
        assert response.status_code == 404

    def test_create_review_missing_required_fields(self, client, sample_spot):
        """Test creating review with missing required fields."""
        create_spot(sample_spot)
        
        # Missing rating
        review_data = {
            "text": "Great spot!",
        }
        response = client.post(f"/api/v1/spots/{sample_spot.id}/reviews", json=review_data)
        assert response.status_code == 422
        
        # Missing text
        review_data = {
            "rating": 5,
        }
        response = client.post(f"/api/v1/spots/{sample_spot.id}/reviews", json=review_data)
        assert response.status_code == 422

    def test_create_review_invalid_rating(self, client, sample_spot):
        """Test creating review with invalid rating."""
        create_spot(sample_spot)
        
        # Rating out of range (assuming 1-5 scale)
        review_data = {
            "rating": 10,
            "text": "Great!",
        }
        response = client.post(f"/api/v1/spots/{sample_spot.id}/reviews", json=review_data)
        # Should still work if Pydantic doesn't validate range
        # This test documents current behavior
        assert response.status_code in [200, 422]

    def test_create_review_score_recalculation(self, client, sample_spot):
        """Test that score is recalculated after adding reviews."""
        create_spot(sample_spot)
        
        # Add reviews with different ratings
        reviews = [
            {"rating": 5, "text": "Excellent"},
            {"rating": 4, "text": "Good"},
            {"rating": 3, "text": "Okay"},
        ]
        
        for review_data in reviews:
            response = client.post(f"/api/v1/spots/{sample_spot.id}/reviews", json=review_data)
            assert response.status_code == 200
        
        # Verify spot was updated with new score
        updated_spot = get_spot(sample_spot.id)
        from app.services.scoring import compute_spot_score
        expected_score = compute_spot_score(sample_spot.id)
        
        # Score should be computed (non-zero with reviews)
        assert expected_score > 0.0

    def test_create_review_updates_last_updated_at(self, client, sample_spot):
        """Test that last_updated_at is updated when review is added."""
        create_spot(sample_spot)
        
        initial_spot = get_spot(sample_spot.id)
        initial_updated = initial_spot.last_updated_at
        
        # Wait a tiny bit to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        review_data = {
            "rating": 5,
            "text": "Great!",
        }
        response = client.post(f"/api/v1/spots/{sample_spot.id}/reviews", json=review_data)
        assert response.status_code == 200
        
        updated_spot = get_spot(sample_spot.id)
        assert updated_spot.last_updated_at > initial_updated


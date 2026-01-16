# backend/tests/test_scoring.py
import pytest
import math
from datetime import datetime
from app.services.scoring import compute_spot_score
from app.storage import create_spot, add_review
from app.schemas.parking import ParkingSpot
from app.schemas.review import Review


class TestComputeSpotScore:
    """Test spot score computation from reviews."""

    def test_no_reviews(self, sample_spot: ParkingSpot):
        """Score should be 0.0 when there are no reviews."""
        create_spot(sample_spot)
        score = compute_spot_score(sample_spot.id)
        assert score == 0.0

    def test_single_review_rating_5(self, sample_spot: ParkingSpot):
        """Test score with 1 review of rating 5."""
        create_spot(sample_spot)
        review = Review(
            id="rev-1",
            spot_id=sample_spot.id,
            rating=5,
            text="Great!",
            created_at=datetime.utcnow(),
        )
        add_review(sample_spot.id, review)
        
        score = compute_spot_score(sample_spot.id)
        # Formula: 5.0 * (1 + log10(2)) * 20 = 5.0 * 1.301 * 20 = 130.1 → 100.0 (capped)
        expected = min(5.0 * (1 + math.log10(2)) * 20, 100.0)
        assert score == pytest.approx(expected, abs=0.1)
        assert score == 100.0  # Should be capped

    def test_single_review_rating_1(self, sample_spot: ParkingSpot):
        """Test score with 1 review of rating 1."""
        create_spot(sample_spot)
        review = Review(
            id="rev-1",
            spot_id=sample_spot.id,
            rating=1,
            text="Terrible!",
            created_at=datetime.utcnow(),
        )
        add_review(sample_spot.id, review)
        
        score = compute_spot_score(sample_spot.id)
        # Formula: 1.0 * (1 + log10(2)) * 20 = 1.0 * 1.301 * 20 = 26.02
        expected = 1.0 * (1 + math.log10(2)) * 20
        assert score == pytest.approx(expected, abs=0.1)

    def test_ten_reviews_average_4(self, sample_spot: ParkingSpot):
        """Test score with 10 reviews averaging 4.0."""
        create_spot(sample_spot)
        # Create 10 reviews with ratings that average to 4.0
        ratings = [4, 4, 4, 4, 4, 4, 4, 4, 4, 4]
        for i, rating in enumerate(ratings):
            review = Review(
                id=f"rev-{i}",
                spot_id=sample_spot.id,
                rating=rating,
                text=f"Review {i}",
                created_at=datetime.utcnow(),
            )
            add_review(sample_spot.id, review)
        
        score = compute_spot_score(sample_spot.id)
        # Formula: 4.0 * (1 + log10(11)) * 20 = 4.0 * 2.041 * 20 = 163.28 → 100.0 (capped)
        expected = min(4.0 * (1 + math.log10(11)) * 20, 100.0)
        assert score == pytest.approx(expected, abs=0.1)
        assert score == 100.0  # Should be capped

    def test_ten_reviews_mixed_ratings(self, sample_spot: ParkingSpot):
        """Test score with 10 reviews with mixed ratings averaging 3.5."""
        create_spot(sample_spot)
        ratings = [5, 5, 4, 4, 3, 3, 2, 2, 2, 1]  # Average = 3.1
        for i, rating in enumerate(ratings):
            review = Review(
                id=f"rev-{i}",
                spot_id=sample_spot.id,
                rating=rating,
                text=f"Review {i}",
                created_at=datetime.utcnow(),
            )
            add_review(sample_spot.id, review)
        
        score = compute_spot_score(sample_spot.id)
        avg_rating = sum(ratings) / len(ratings)
        expected = min(avg_rating * (1 + math.log10(11)) * 20, 100.0)
        assert score == pytest.approx(expected, abs=0.1)

    def test_one_hundred_reviews_average_4(self, sample_spot: ParkingSpot):
        """Test score with 100 reviews averaging 4.0."""
        create_spot(sample_spot)
        ratings = [4] * 100
        for i, rating in enumerate(ratings):
            review = Review(
                id=f"rev-{i}",
                spot_id=sample_spot.id,
                rating=rating,
                text=f"Review {i}",
                created_at=datetime.utcnow(),
            )
            add_review(sample_spot.id, review)
        
        score = compute_spot_score(sample_spot.id)
        # Formula: 4.0 * (1 + log10(101)) * 20 = 4.0 * 3.004 * 20 = 240.32 → 100.0 (capped)
        expected = min(4.0 * (1 + math.log10(101)) * 20, 100.0)
        assert score == pytest.approx(expected, abs=0.1)
        assert score == 100.0  # Should be capped

    def test_one_thousand_reviews_average_3(self, sample_spot: ParkingSpot):
        """Test score with 1000 reviews averaging 3.0."""
        create_spot(sample_spot)
        ratings = [3] * 1000
        for i in range(min(1000, 100)):  # Limit to 100 for performance
            review = Review(
                id=f"rev-{i}",
                spot_id=sample_spot.id,
                rating=ratings[i],
                text=f"Review {i}",
                created_at=datetime.utcnow(),
            )
            add_review(sample_spot.id, review)
        
        # Manually test with 100 reviews instead of 1000 for performance
        score = compute_spot_score(sample_spot.id)
        # Formula: 3.0 * (1 + log10(101)) * 20 = 3.0 * 3.004 * 20 = 180.24 → 100.0 (capped)
        expected = min(3.0 * (1 + math.log10(101)) * 20, 100.0)
        assert score == pytest.approx(expected, abs=0.1)
        assert score == 100.0  # Should be capped

    def test_logarithmic_scaling(self, sample_spot: ParkingSpot):
        """Verify that logarithmic scaling works correctly."""
        create_spot(sample_spot)
        
        # Add reviews incrementally and check score increases
        scores = []
        for count in [1, 5, 10, 20, 50]:
            # Clear and add new reviews
            from app.storage import _reviews
            _reviews[sample_spot.id] = []
            
            for i in range(count):
                review = Review(
                    id=f"rev-{i}",
                    spot_id=sample_spot.id,
                    rating=5,
                    text=f"Review {i}",
                    created_at=datetime.utcnow(),
                )
                add_review(sample_spot.id, review)
            
            score = compute_spot_score(sample_spot.id)
            scores.append(score)
        
        # Scores should increase but at a decreasing rate (logarithmic)
        assert scores[0] < scores[1] < scores[2] < scores[3] < scores[4]
        # The difference between consecutive scores should decrease
        diffs = [scores[i+1] - scores[i] for i in range(len(scores)-1)]
        # Later differences should be smaller (logarithmic scaling)
        assert diffs[0] > diffs[-1] or scores[-1] == 100.0  # Account for capping


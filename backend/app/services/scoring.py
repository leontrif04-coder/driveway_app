# backend/app/services/scoring.py
from typing import List, Optional
from datetime import datetime
from app.schemas.parking import ParkingSpot
from app.storage import get_reviews

def compute_spot_score(spot_id: str) -> float:
    """
    Compute spot score from average rating and number of reviews.
    Formula: avg_rating * (1 + log10(review_count + 1))
    This gives more weight to spots with more reviews.
    """
    reviews = get_reviews(spot_id)
    if not reviews:
        return 0.0
    
    avg_rating = sum(r.rating for r in reviews) / len(reviews)
    import math
    review_bonus = math.log10(len(reviews) + 1)
    score = avg_rating * (1 + review_bonus)
    
    # Normalize to 0-100 scale (assuming ratings are 1-5)
    return min(score * 20, 100.0)

def get_time_of_day_weight(time_of_day: Optional[str]) -> float:
    if time_of_day == "morning":
        return 5
    if time_of_day == "afternoon":
        return 0
    if time_of_day == "evening":
        return -5
    if time_of_day == "night":
        return -10
    return 0

def get_tourism_bias_weight(bias: Optional[str]) -> float:
    if bias == "low":
        return -0.4
    if bias == "medium":
        return 0
    if bias == "high":
        return 0.4
    return 0

async def get_spots_in_bounds(
    min_lat: float,
    max_lat: float,
    min_lng: float,
    max_lng: float,
) -> List[ParkingSpot]:
    """Get spots within bounds from storage."""
    from app.storage import get_all_spots
    all_spots = get_all_spots()
    return [
        spot for spot in all_spots
        if min_lat <= spot.latitude <= max_lat and min_lng <= spot.longitude <= max_lng
    ]

def score_and_filter_spots(
    spots: List[ParkingSpot],
    min_safety: Optional[float],
    max_walk_m: Optional[float],
    time_of_day: Optional[str],
    tourism_bias: Optional[str],
) -> List[ParkingSpot]:
    t_weight = get_time_of_day_weight(time_of_day)
    tour_weight = get_tourism_bias_weight(tourism_bias)

    result: List[ParkingSpot] = []
    for spot in spots:
        base_score = spot.safety_score
        tourism_component = spot.tourism_density * tour_weight
        time_component = t_weight
        meter_penalty = (
            -20 * spot.meter_status_confidence
            if spot.meter_status == "broken"
            else 0
        )
        composite = base_score + tourism_component + time_component + meter_penalty

        if (
            max_walk_m is not None
            and spot.distance_to_destination_m is not None
            and spot.distance_to_destination_m > max_walk_m
        ):
            continue

        if min_safety is not None and spot.safety_score < min_safety:
            continue

        data = spot.dict()
        data["composite_score"] = composite
        result.append(ParkingSpot(**data))

    result.sort(key=lambda s: s.composite_score or 0, reverse=True)
    return result



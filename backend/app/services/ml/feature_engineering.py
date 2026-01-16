# backend/app/services/ml/feature_engineering.py
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.storage import get_user_parking_history, get_user_preferences, get_spot, get_all_spots
from app.schemas.user_behavior import UserParkingEvent, UserPreferences, DestinationType
from app.schemas.parking import ParkingSpot
import math


def extract_user_features(user_id: str) -> Dict[str, float]:
    """
    Extract user features from parking history.
    
    Returns a dictionary of feature values:
    - avg_price_tolerance
    - preferred_duration_minutes
    - morning_preference, afternoon_preference, evening_preference
    - avg_safety_score
    - avg_walking_distance_m
    """
    history = get_user_parking_history(user_id)
    prefs = get_user_preferences(user_id)
    
    features = {
        "avg_price_tolerance": 0.0,
        "preferred_duration_minutes": 60.0,
        "morning_preference": 0.0,
        "afternoon_preference": 0.0,
        "evening_preference": 0.0,
        "night_preference": 0.0,
        "avg_safety_score": 70.0,
        "avg_walking_distance_m": 500.0,
        "has_history": 0.0,
    }
    
    if not history and not prefs:
        # Cold start - return defaults
        return features
    
    # Use preferences if available (more accurate)
    if prefs:
        features["avg_price_tolerance"] = (
            (prefs.preferred_price_range_min or 0) + (prefs.preferred_price_range_max or 10)
        ) / 2
        features["preferred_duration_minutes"] = prefs.preferred_duration_minutes or 60.0
        features["avg_safety_score"] = prefs.min_safety_score or 70.0
        features["avg_walking_distance_m"] = prefs.max_walking_distance_m or 500.0
        
        # Time preferences
        if "morning" in prefs.preferred_parking_times:
            features["morning_preference"] = 1.0
        if "afternoon" in prefs.preferred_parking_times:
            features["afternoon_preference"] = 1.0
        if "evening" in prefs.preferred_parking_times:
            features["evening_preference"] = 1.0
    
    # Extract from history if available
    if history:
        features["has_history"] = 1.0
        
        prices = [e.price_paid_usd for e in history if e.price_paid_usd]
        if prices:
            features["avg_price_tolerance"] = sum(prices) / len(prices)
        
        durations = [e.duration_minutes for e in history if e.duration_minutes]
        if durations:
            features["preferred_duration_minutes"] = sum(durations) / len(durations)
        
        safety_scores = [e.safety_score_at_time for e in history]
        if safety_scores:
            features["avg_safety_score"] = sum(safety_scores) / len(safety_scores)
        
        distances = [e.distance_to_destination_m for e in history if e.distance_to_destination_m]
        if distances:
            features["avg_walking_distance_m"] = sum(distances) / len(distances)
        
        # Time preferences from history
        time_counts = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
        for event in history:
            if event.time_of_day in time_counts:
                time_counts[event.time_of_day] += 1
        
        total = sum(time_counts.values())
        if total > 0:
            features["morning_preference"] = time_counts["morning"] / total
            features["afternoon_preference"] = time_counts["afternoon"] / total
            features["evening_preference"] = time_counts["evening"] / total
            features["night_preference"] = time_counts["night"] / total
    
    return features


def extract_contextual_features(
    current_time: datetime,
    destination_type: Optional[DestinationType] = None,
) -> Dict[str, float]:
    """
    Extract contextual features from current situation.
    
    Features:
    - hour_of_day (0-23, normalized)
    - is_weekend (0 or 1)
    - destination_type_* (one-hot encoded)
    """
    features = {
        "hour_of_day": current_time.hour / 24.0,  # Normalized to 0-1
        "is_weekend": 1.0 if current_time.weekday() >= 5 else 0.0,
        "day_of_week": current_time.weekday() / 6.0,  # Normalized to 0-1
        "destination_type_restaurant": 0.0,
        "destination_type_office": 0.0,
        "destination_type_entertainment": 0.0,
        "destination_type_shopping": 0.0,
        "destination_type_residential": 0.0,
        "destination_type_other": 0.0,
    }
    
    if destination_type:
        feature_key = f"destination_type_{destination_type}"
        if feature_key in features:
            features[feature_key] = 1.0
    
    return features


def extract_spot_features(spot: ParkingSpot, user_lat: float, user_lng: float) -> Dict[str, float]:
    """
    Extract features for a parking spot.
    
    Features:
    - price_per_hour
    - safety_score
    - tourism_density
    - distance_to_user
    - review_score
    - meter_status_working
    """
    from app.services.geo import haversine_distance_m
    from app.services.scoring import compute_spot_score
    
    distance = haversine_distance_m((user_lat, user_lng), (spot.latitude, spot.longitude))
    
    features = {
        "price_per_hour": spot.price_per_hour_usd or 5.0,
        "safety_score": spot.safety_score / 100.0,  # Normalized to 0-1
        "tourism_density": spot.tourism_density / 100.0,  # Normalized to 0-1
        "distance_to_user_m": distance,
        "distance_to_user_km": distance / 1000.0,
        "review_score": compute_spot_score(spot.id) / 100.0,  # Normalized to 0-1
        "meter_status_working": 1.0 if spot.meter_status == "working" else 0.0,
        "meter_status_broken": 1.0 if spot.meter_status == "broken" else 0.0,
        "is_occupied": 1.0 if spot.is_occupied else 0.0,
    }
    
    return features


def create_feature_vector(
    user_features: Dict[str, float],
    contextual_features: Dict[str, float],
    spot_features: Dict[str, float],
) -> List[float]:
    """
    Combine all features into a single feature vector for ML model.
    
    Returns a flat list of feature values in consistent order.
    """
    # Define feature order (important for model compatibility)
    feature_order = [
        # User features
        "avg_price_tolerance",
        "preferred_duration_minutes",
        "morning_preference",
        "afternoon_preference",
        "evening_preference",
        "night_preference",
        "avg_safety_score",
        "avg_walking_distance_m",
        "has_history",
        # Contextual features
        "hour_of_day",
        "is_weekend",
        "day_of_week",
        "destination_type_restaurant",
        "destination_type_office",
        "destination_type_entertainment",
        "destination_type_shopping",
        "destination_type_residential",
        "destination_type_other",
        # Spot features
        "price_per_hour",
        "safety_score",
        "tourism_density",
        "distance_to_user_km",
        "review_score",
        "meter_status_working",
        "meter_status_broken",
        "is_occupied",
    ]
    
    all_features = {**user_features, **contextual_features, **spot_features}
    
    # Extract features in order
    feature_vector = [all_features.get(feature, 0.0) for feature in feature_order]
    
    return feature_vector


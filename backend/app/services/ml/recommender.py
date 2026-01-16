# backend/app/services/ml/recommender.py
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pickle
import os
import logging
from app.storage import get_all_spots, get_spot
from app.schemas.parking import ParkingSpot
from app.schemas.user_behavior import Recommendation, DestinationType
from app.services.ml.feature_engineering import (
    extract_user_features,
    extract_contextual_features,
    extract_spot_features,
    create_feature_vector,
)
from app.services.geo import haversine_distance_m

logger = logging.getLogger(__name__)

# Model file path
MODEL_PATH = "models/parking_recommender.pkl"
FEATURE_ORDER_PATH = "models/feature_order.pkl"


class ParkingRecommender:
    """ML-based parking spot recommendation system."""
    
    def __init__(self):
        self.model = None
        self.feature_order = None
        self.model_version = "v1.0"
        self.load_model()
    
    def load_model(self):
        """Load trained model from disk."""
        try:
            if os.path.exists(MODEL_PATH):
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                logger.info(f"ML model loaded from {MODEL_PATH}")
            else:
                logger.warning(f"Model file not found at {MODEL_PATH}. Using fallback ranking.")
        except Exception as e:
            logger.error(f"Error loading model: {e}. Using fallback ranking.")
            self.model = None
    
    def predict_scores(
        self,
        user_id: Optional[str],
        spots: List[ParkingSpot],
        user_lat: float,
        user_lng: float,
        destination_type: Optional[DestinationType] = None,
    ) -> List[Tuple[ParkingSpot, float]]:
        """
        Predict recommendation scores for spots.
        
        Returns list of (spot, score) tuples sorted by score descending.
        """
        if not self.model:
            # Fallback to distance-based ranking
            return self._fallback_ranking(spots, user_lat, user_lng)
        
        current_time = datetime.utcnow()
        user_features = extract_user_features(user_id or "anonymous")
        contextual_features = extract_contextual_features(current_time, destination_type)
        
        spot_scores = []
        
        for spot in spots:
            try:
                spot_features = extract_spot_features(spot, user_lat, user_lng)
                feature_vector = create_feature_vector(user_features, contextual_features, spot_features)
                
                # Predict score (0-1 probability)
                score = self.model.predict_proba([feature_vector])[0][1] if hasattr(self.model, "predict_proba") else self.model.predict([feature_vector])[0]
                
                # Convert to 0-100 scale
                score = max(0.0, min(100.0, float(score) * 100.0))
                spot_scores.append((spot, score))
            except Exception as e:
                logger.error(f"Error predicting score for spot {spot.id}: {e}")
                # Use fallback score
                distance = haversine_distance_m((user_lat, user_lng), (spot.latitude, spot.longitude))
                fallback_score = max(0.0, 100.0 - (distance / 10.0))  # Decrease by 1 point per 10m
                spot_scores.append((spot, fallback_score))
        
        # Sort by score descending
        spot_scores.sort(key=lambda x: x[1], reverse=True)
        return spot_scores
    
    def _fallback_ranking(self, spots: List[ParkingSpot], user_lat: float, user_lng: float) -> List[Tuple[ParkingSpot, float]]:
        """Fallback distance-based ranking when ML model unavailable."""
        spot_scores = []
        for spot in spots:
            distance = haversine_distance_m((user_lat, user_lng), (spot.latitude, spot.longitude))
            # Inverse distance scoring (closer = higher score)
            score = max(0.0, 100.0 - (distance / 10.0))
            spot_scores.append((spot, score))
        spot_scores.sort(key=lambda x: x[1], reverse=True)
        return spot_scores
    
    def generate_recommendations(
        self,
        user_id: Optional[str],
        spots: List[ParkingSpot],
        user_lat: float,
        user_lng: float,
        destination_type: Optional[DestinationType] = None,
        limit: int = 10,
    ) -> List[Recommendation]:
        """
        Generate recommendations with explanations.
        
        Returns list of Recommendation objects with scores and reasons.
        """
        spot_scores = self.predict_scores(user_id, spots, user_lat, user_lng, destination_type)
        
        recommendations = []
        user_features = extract_user_features(user_id or "anonymous")
        
        for spot, score in spot_scores[:limit]:
            reasons = self._generate_reasons(spot, score, user_features, user_lat, user_lng)
            
            recommendation = Recommendation(
                spot_id=spot.id,
                score=score,
                reasons=reasons,
                match_confidence=score / 100.0,
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_reasons(
        self,
        spot: ParkingSpot,
        score: float,
        user_features: Dict[str, float],
        user_lat: float,
        user_lng: float,
    ) -> List[str]:
        """Generate explanation reasons for recommendation."""
        reasons = []
        
        from app.services.geo import haversine_distance_m
        distance = haversine_distance_m((user_lat, user_lng), (spot.latitude, spot.longitude))
        
        # Distance reasons
        if distance < 200:
            reasons.append("Very close to destination")
        elif distance < 500:
            reasons.append("Close walking distance")
        
        # Price reasons
        if spot.price_per_hour_usd:
            avg_price = user_features.get("avg_price_tolerance", 5.0)
            if spot.price_per_hour_usd < avg_price * 0.8:
                reasons.append("Great price")
            elif spot.price_per_hour_usd < avg_price:
                reasons.append("Good value")
        
        # Safety reasons
        if spot.safety_score >= 80:
            reasons.append("High safety score")
        elif spot.safety_score >= user_features.get("avg_safety_score", 70):
            reasons.append("Meets your safety preference")
        
        # Availability reasons
        if not spot.is_occupied:
            reasons.append("Available now")
        
        # Review reasons
        if spot.review_count > 5:
            reasons.append("Highly rated")
        
        # Meter status
        if spot.meter_status == "working":
            reasons.append("Meter working")
        
        # If no specific reasons, add generic
        if not reasons:
            reasons.append("Good match for you")
        
        return reasons[:3]  # Limit to 3 reasons


# Global recommender instance
_recommender: Optional[ParkingRecommender] = None


def get_recommender() -> ParkingRecommender:
    """Get or create global recommender instance."""
    global _recommender
    if _recommender is None:
        _recommender = ParkingRecommender()
    return _recommender


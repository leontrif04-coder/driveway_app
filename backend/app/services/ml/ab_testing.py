# backend/app/services/ml/ab_testing.py
from typing import Optional, Literal
from enum import Enum
import random
import logging
from datetime import datetime
from app.storage import add_user_parking_event, get_user_parking_history
from app.schemas.user_behavior import UserParkingEvent

logger = logging.getLogger(__name__)


class RankingAlgorithm(str, Enum):
    """Available ranking algorithms for A/B testing."""
    DISTANCE_ONLY = "distance_only"
    ML_POWERED = "ml_powered"
    HYBRID = "hybrid"


class ABTestTracker:
    """Track A/B test results for ranking algorithms."""
    
    def __init__(self):
        # Track conversions: {user_id: {algorithm: {"recommended": count, "selected": count}}}
        self.conversions: dict = {}
        # User assignments: {user_id: algorithm}
        self.user_assignments: dict = {}
    
    def assign_algorithm(self, user_id: Optional[str]) -> RankingAlgorithm:
        """
        Assign user to A/B test group.
        
        Uses consistent hashing to ensure same user always gets same algorithm.
        """
        if not user_id:
            # Anonymous users: 50/50 split
            return random.choice([RankingAlgorithm.DISTANCE_ONLY, RankingAlgorithm.ML_POWERED])
        
        if user_id in self.user_assignments:
            return self.user_assignments[user_id]
        
        # Consistent assignment based on user_id hash
        assignment = RankingAlgorithm.ML_POWERED if hash(user_id) % 2 == 0 else RankingAlgorithm.DISTANCE_ONLY
        self.user_assignments[user_id] = assignment
        return assignment
    
    def track_recommendation(
        self,
        user_id: Optional[str],
        algorithm: RankingAlgorithm,
        spot_ids: list[str],
    ):
        """Track that spots were recommended to user."""
        if not user_id:
            return
        
        if user_id not in self.conversions:
            self.conversions[user_id] = {}
        if algorithm.value not in self.conversions[user_id]:
            self.conversions[user_id][algorithm.value] = {"recommended": 0, "selected": 0}
        
        self.conversions[user_id][algorithm.value]["recommended"] += len(spot_ids)
    
    def track_selection(
        self,
        user_id: Optional[str],
        algorithm: RankingAlgorithm,
        spot_id: str,
    ):
        """Track that user selected a recommended spot."""
        if not user_id:
            return
        
        if user_id not in self.conversions:
            self.conversions[user_id] = {}
        if algorithm.value not in self.conversions[user_id]:
            self.conversions[user_id][algorithm.value] = {"recommended": 0, "selected": 0}
        
        self.conversions[user_id][algorithm.value]["selected"] += 1
    
    def get_conversion_rate(self, algorithm: RankingAlgorithm) -> float:
        """Calculate conversion rate for an algorithm."""
        total_recommended = 0
        total_selected = 0
        
        for user_data in self.conversions.values():
            if algorithm.value in user_data:
                total_recommended += user_data[algorithm.value]["recommended"]
                total_selected += user_data[algorithm.value]["selected"]
        
        if total_recommended == 0:
            return 0.0
        
        return total_selected / total_recommended
    
    def get_stats(self) -> dict:
        """Get A/B test statistics."""
        stats = {}
        for algorithm in RankingAlgorithm:
            stats[algorithm.value] = {
                "conversion_rate": self.get_conversion_rate(algorithm),
            }
        return stats


# Global A/B test tracker
_ab_tracker = ABTestTracker()


def get_ab_tracker() -> ABTestTracker:
    """Get global A/B test tracker."""
    return _ab_tracker


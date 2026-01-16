# backend/app/services/availability_predictor.py
from typing import Optional
from datetime import datetime, timedelta
from app.storage import get_occupancy_history, get_spot


def predict_availability_time(spot_id: str, current_time: datetime, estimated_duration_minutes: Optional[int] = None) -> Optional[datetime]:
    """
    Predict when an occupied parking spot will become available.
    
    Uses a simple ML-like approach based on:
    - Historical occupancy durations
    - Time of day patterns
    - Day of week patterns
    - Provided estimated duration
    
    Args:
        spot_id: The parking spot ID
        current_time: Current timestamp
        estimated_duration_minutes: User-provided estimated parking duration (optional)
    
    Returns:
        Predicted availability datetime, or None if unable to predict
    """
    # Get historical data
    history = get_occupancy_history(spot_id)
    spot = get_spot(spot_id)
    
    if not spot:
        return None
    
    # If user provided estimated duration, use it with some confidence
    if estimated_duration_minutes:
        # Add 20% buffer for variability
        predicted_minutes = int(estimated_duration_minutes * 1.2)
        return current_time + timedelta(minutes=predicted_minutes)
    
    # Analyze historical patterns
    if not history or len(history) == 0:
        # No history: use default based on max_duration
        if spot.max_duration_minutes:
            default_minutes = min(spot.max_duration_minutes, 120)  # Cap at 2 hours
        else:
            default_minutes = 60  # Default 1 hour
        return current_time + timedelta(minutes=default_minutes)
    
    # Calculate average duration from history
    durations = []
    check_in_time = None
    
    for event in sorted(history, key=lambda e: e.timestamp):
        if event.event_type == "check_in":
            check_in_time = event.timestamp
        elif event.event_type == "check_out" and check_in_time:
            duration = (event.timestamp - check_in_time).total_seconds() / 60
            durations.append(duration)
            check_in_time = None
    
    if durations:
        avg_duration = sum(durations) / len(durations)
        
        # Time-of-day adjustment
        hour = current_time.hour
        day_of_week = current_time.weekday()  # 0 = Monday
        
        # Adjust based on time patterns
        # Peak hours (8-10 AM, 5-7 PM): longer stays
        # Off-peak: shorter stays
        if 8 <= hour <= 10 or 17 <= hour <= 19:
            avg_duration *= 1.3
        elif 22 <= hour or hour <= 6:  # Night
            avg_duration *= 0.7
        
        # Weekend adjustment
        if day_of_week >= 5:  # Saturday, Sunday
            avg_duration *= 1.2
        
        # Cap at reasonable maximum
        avg_duration = min(avg_duration, 240)  # Max 4 hours
        
        return current_time + timedelta(minutes=int(avg_duration))
    
    # Fallback: use max_duration or default
    if spot.max_duration_minutes:
        return current_time + timedelta(minutes=min(spot.max_duration_minutes, 120))
    
    return current_time + timedelta(minutes=60)


def calculate_availability_confidence(spot_id: str) -> float:
    """
    Calculate confidence level (0-1) for availability predictions.
    
    Higher confidence when:
    - More historical data available
    - Consistent patterns in history
    - Recent data points
    """
    history = get_occupancy_history(spot_id)
    
    if not history or len(history) < 3:
        return 0.3  # Low confidence with little data
    
    if len(history) < 10:
        return 0.5  # Medium confidence
    
    if len(history) < 50:
        return 0.7  # Good confidence
    
    return 0.9  # High confidence with lots of data


# ML Recommendation System - Smart Parking Assistant

## Overview

The Smart Parking Assistant uses a machine learning-powered recommendation system to provide personalized parking spot recommendations. The system combines collaborative filtering, content-based filtering, and context-aware features to rank parking spots based on user preferences and current situation.

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    ML Pipeline                          │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Data       │  │   Feature    │  │   Model      │ │
│  │  Collection  │→ │ Engineering  │→ │  Training    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Inference   │  │   Ranking    │  │  A/B Testing │ │
│  │   Service    │→ │  Algorithm   │→ │   Tracking   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Behavior Tracking**: User parking events are collected and stored
2. **Feature Engineering**: Extract user, contextual, and spot features
3. **Model Training**: Train ML model on historical data
4. **Inference**: Use trained model to rank spots for recommendations
5. **A/B Testing**: Compare algorithm performance

---

## Feature Engineering

### User Features

Extracted from user parking history:

- `avg_price_tolerance`: Average price user pays
- `preferred_duration_minutes`: Average parking duration
- `morning_preference`, `afternoon_preference`, `evening_preference`: Time preferences (0-1)
- `avg_safety_score`: Preferred safety score
- `avg_walking_distance_m`: Average walking distance tolerance
- `has_history`: Binary flag (1 if user has history, 0 for cold start)

### Contextual Features

Current situation features:

- `hour_of_day`: Current hour (normalized 0-1)
- `is_weekend`: Binary flag (1 if weekend)
- `day_of_week`: Day of week (normalized 0-1)
- `destination_type_*`: One-hot encoded destination type

### Spot Features

Parking spot attributes:

- `price_per_hour`: Price per hour in USD
- `safety_score`: Safety score (normalized 0-1)
- `tourism_density`: Tourism density (normalized 0-1)
- `distance_to_user_km`: Distance from user (km)
- `review_score`: Review-based score (normalized 0-1)
- `meter_status_working`, `meter_status_broken`: Binary flags
- `is_occupied`: Current occupancy status

**Total Features**: 28 features per spot-user combination

---

## ML Model

### Algorithm

**Primary Model**: Gradient Boosting Regressor (scikit-learn)

- **Algorithm**: GradientBoostingRegressor
- **Hyperparameters**:
  - `n_estimators`: 100
  - `max_depth`: 5
  - `learning_rate`: 0.1
- **Output**: Probability score (0-1) converted to 0-100 scale

### Training Pipeline

1. **Data Generation**: Generate training data from historical events
2. **Feature Extraction**: Extract features for each training sample
3. **Model Training**: Train on 80% of data, validate on 20%
4. **Cross-Validation**: 5-fold cross-validation for robustness
5. **Model Persistence**: Save model as pickle file

### Training Script

```bash
cd backend
python train_model.py
```

The script:
- Generates synthetic training data (or uses real data)
- Trains multiple models and selects best
- Validates performance
- Saves model to `models/parking_recommender.pkl`

---

## Recommendation Endpoint

### API Endpoint

**GET** `/api/v1/recommendations`

**Query Parameters**:
- `lat` (required): User latitude
- `lng` (required): User longitude
- `user_id` (optional): User ID for personalization
- `destination_type` (optional): "restaurant", "office", "entertainment", etc.
- `radius_m` (optional, default: 1000): Search radius in meters
- `limit` (optional, default: 10): Number of recommendations

**Response**:
```json
{
  "recommendations": [
    {
      "spot_id": "spot-1",
      "score": 85.5,
      "reasons": ["Very close to destination", "Great price", "Available now"],
      "match_confidence": 0.855
    }
  ],
  "user_id": "user-123",
  "model_version": "v1.0",
  "generated_at": "2024-01-01T12:00:00Z"
}
```

### Example Usage

```bash
# Get recommendations for a location
curl "http://localhost:8000/api/v1/recommendations?lat=40.7128&lng=-74.0060&user_id=user-123&destination_type=restaurant"
```

---

## Cold Start Problem

The system handles new users (no history) using:

1. **Default Features**: Use default values based on general population
2. **Preference-Based**: If user sets preferences, use those
3. **Fallback Ranking**: If ML model unavailable, use distance-based ranking
4. **Gradual Learning**: As user history accumulates, recommendations improve

---

## A/B Testing

### Framework

The system includes A/B testing to compare algorithms:

- **Distance-Only**: Simple distance-based ranking
- **ML-Powered**: ML-based personalized ranking
- **Hybrid**: Combination of both

### Assignment

- Users are consistently assigned to groups (based on user_id hash)
- Same user always gets same algorithm
- Anonymous users: 50/50 split

### Metrics

- **Conversion Rate**: (Spots Selected) / (Spots Recommended)
- **Performance Comparison**: Compare conversion rates between algorithms

### Tracking

```python
from app.services.ml.ab_testing import get_ab_tracker

tracker = get_ab_tracker()
tracker.track_recommendation(user_id, algorithm, spot_ids)
tracker.track_selection(user_id, algorithm, spot_id)
stats = tracker.get_stats()
```

---

## Performance

### Model Performance

- **Training Time**: ~10-30 seconds for 1000 samples
- **Inference Time**: <100ms per recommendation request
- **Model Size**: <5MB (pickle file)
- **Accuracy**: R2 score >0.6 (varies with data quality)

### Optimization

- **Caching**: Model loaded once at startup
- **Feature Caching**: Cache user features for session
- **Batch Prediction**: Predict scores for multiple spots in batch
- **Fallback**: Graceful degradation to distance-based ranking

---

## User Behavior Tracking

### Event Schema

```python
UserParkingEvent(
    user_id: str,
    spot_id: str,
    timestamp: datetime,
    time_of_day: str,
    day_of_week: int,
    duration_minutes: Optional[int],
    price_paid_usd: Optional[float],
    final_destination_type: Optional[str],
    user_rating: Optional[int],
    safety_score_at_time: float,
    distance_to_destination_m: Optional[float],
)
```

### Tracking Events

1. **Spot Selected**: When user views spot details
2. **Spot Parked**: When user confirms parking
3. **Spot Rated**: When user rates parking experience
4. **Preferences Updated**: When user changes preferences

---

## Frontend Integration

### User Profile Service

Track user behavior and send to backend:

```typescript
// Track spot selection
userProfileService.trackSpotSelection(spotId, userId);

// Track parking event
userProfileService.trackParkingEvent(event);
```

### Recommendation UI

- Display "Recommended for You" section
- Show match score and reasons
- Allow sorting: "Distance" vs "Recommended"

### Preference Settings

- Allow users to set preferences:
  - Price range
  - Max walking distance
  - Safety score minimum
  - Preferred parking duration
- Preferences influence recommendations

---

## Monitoring

### Metrics to Track

1. **Model Performance**:
   - Prediction accuracy
   - Inference latency
   - Error rates

2. **Recommendation Quality**:
   - Click-through rate
   - Conversion rate (recommended → selected)
   - User satisfaction (ratings)

3. **System Health**:
   - Model load success rate
   - Feature extraction errors
   - Fallback usage rate

### Logging

- Model training logs
- Inference errors
- A/B test results
- Performance metrics

---

## Future Enhancements

### Advanced Features

1. **Deep Learning**: Neural network models for better accuracy
2. **Real-Time Learning**: Online learning from user feedback
3. **Multi-Objective Optimization**: Balance price, distance, safety
4. **Time-Based Pricing Predictions**: Predict best time to park
5. **Multi-Destination Optimization**: Find optimal spot for multiple destinations

### Model Improvements

1. **Feature Engineering**:
   - Weather data integration
   - Traffic congestion data
   - Historical availability patterns
   - Popularity trends

2. **Algorithm Upgrades**:
   - Factorization Machines
   - Deep Learning models
   - Reinforcement Learning

3. **Personalization**:
   - User embeddings
   - Item embeddings
   - Attention mechanisms

---

## Troubleshooting

### Model Not Loading

```bash
# Check if model file exists
ls models/parking_recommender.pkl

# Retrain model
python train_model.py
```

### Low Accuracy

- Check training data quality
- Increase training samples
- Tune hyperparameters
- Add more features

### High Inference Time

- Optimize feature extraction
- Use model compression
- Cache frequently used features
- Consider simpler model

### Cold Start Issues

- Improve default features
- Use content-based features
- Prompt users to set preferences
- Use popularity-based fallback

---

## References

- **scikit-learn**: https://scikit-learn.org/
- **Gradient Boosting**: https://scikit-learn.org/stable/modules/ensemble.html#gradient-boosting
- **Recommendation Systems**: Collaborative Filtering, Content-Based Filtering
- **Feature Engineering**: Feature scaling, one-hot encoding, normalization

---

## Summary

The ML recommendation system provides personalized parking spot recommendations using:

- **28 features** per recommendation
- **Gradient Boosting** model
- **<100ms inference** time
- **A/B testing** framework
- **Cold start** handling
- **Fallback** to distance-based ranking

The system is production-ready with error handling, logging, and monitoring capabilities.


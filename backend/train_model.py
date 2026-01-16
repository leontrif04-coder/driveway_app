#!/usr/bin/env python3
"""
Train ML model for parking spot recommendations.

Usage:
    python train_model.py

This script:
1. Loads historical user parking events
2. Generates training data
3. Trains a recommendation model
4. Validates model performance
5. Saves model to disk
"""

import os
import sys
import pickle
import logging
from datetime import datetime
from typing import List, Tuple
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_all_user_parking_events, seed_data
from app.services.ml.feature_engineering import (
    extract_user_features,
    extract_contextual_features,
    extract_spot_features,
    create_feature_vector,
)
from app.storage import get_spot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure models directory exists
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODELS_DIR, "parking_recommender.pkl")


def generate_training_data(num_samples: int = 1000) -> Tuple[List, List]:
    """
    Generate synthetic training data for model training.
    
    In production, this would use real user parking events.
    """
    logger.info(f"Generating {num_samples} training samples...")
    
    # Seed data for spots
    seed_data()
    
    # Get all spots
    from app.storage import get_all_spots
    spots = get_all_spots()
    
    if not spots:
        logger.error("No spots available. Cannot generate training data.")
        return [], []
    
    X = []  # Features
    y = []  # Target (rating or preference score)
    
    np.random.seed(42)
    
    for _ in range(num_samples):
        # Random user
        user_id = f"user_{np.random.randint(1, 100)}"
        
        # Random spot
        spot = np.random.choice(spots)
        
        # Random context
        hour = np.random.randint(0, 24)
        is_weekend = np.random.choice([0, 1])
        current_time = datetime(2024, 1, 1, hour, 0, 0)
        if is_weekend:
            current_time = datetime(2024, 1, 6, hour, 0, 0)  # Saturday
        
        # Extract features
        user_features = extract_user_features(user_id)
        contextual_features = extract_contextual_features(current_time)
        spot_features = extract_spot_features(spot, 40.7128, -74.0060)  # NYC center
        
        feature_vector = create_feature_vector(user_features, contextual_features, spot_features)
        X.append(feature_vector)
        
        # Generate target score (0-1) based on simple rules
        # Higher score for: closer distance, better safety, lower price
        distance_score = max(0, 1.0 - (spot_features["distance_to_user_km"] / 5.0))
        safety_score = spot_features["safety_score"]
        price_score = max(0, 1.0 - (spot_features["price_per_hour"] / 10.0))
        
        # Combined score
        target_score = (distance_score * 0.4 + safety_score * 0.3 + price_score * 0.3)
        target_score += np.random.normal(0, 0.1)  # Add noise
        target_score = max(0.0, min(1.0, target_score))
        
        y.append(target_score)
    
    logger.info(f"Generated {len(X)} training samples")
    return X, y


def train_model(X: List[List[float]], y: List[float]):
    """Train ML model on training data."""
    logger.info("Training model...")
    
    X_array = np.array(X)
    y_array = np.array(y)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_array, y_array, test_size=0.2, random_state=42
    )
    
    logger.info(f"Training set: {len(X_train)} samples")
    logger.info(f"Test set: {len(X_test)} samples")
    
    # Try different models
    models = {
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
        ),
        "RandomForest": RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
        ),
    }
    
    best_model = None
    best_score = float("-inf")
    best_name = None
    
    for name, model in models.items():
        logger.info(f"Training {name}...")
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        logger.info(f"{name} - MSE: {mse:.4f}, R2: {r2:.4f}")
        
        if r2 > best_score:
            best_score = r2
            best_model = model
            best_name = name
    
    logger.info(f"Best model: {name} (R2: {best_score:.4f})")
    
    # Cross-validation
    cv_scores = cross_val_score(best_model, X_array, y_array, cv=5, scoring="r2")
    logger.info(f"Cross-validation R2: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    return best_model


def save_model(model, model_path: str):
    """Save trained model to disk."""
    logger.info(f"Saving model to {model_path}...")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    logger.info("Model saved successfully")


def main():
    """Main training pipeline."""
    logger.info("Starting ML model training...")
    
    # Generate training data
    X, y = generate_training_data(num_samples=1000)
    
    if not X or not y:
        logger.error("Failed to generate training data")
        return 1
    
    # Train model
    model = train_model(X, y)
    
    # Save model
    save_model(model, MODEL_PATH)
    
    logger.info("Training completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())


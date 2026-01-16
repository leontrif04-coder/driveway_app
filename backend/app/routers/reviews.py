# backend/app/routers/reviews.py
from fastapi import APIRouter, Path, HTTPException
from typing import List
from datetime import datetime
from app.schemas.review import Review, ReviewCreate
from app.storage import get_reviews, add_review, get_spot, update_spot
from app.services.scoring import compute_spot_score
from app.utils.review_parser import parse_meter_status
import uuid

router = APIRouter()

@router.get("/{spot_id}/reviews", response_model=List[Review])
async def list_reviews(spot_id: str = Path(...)):
    """Get all reviews for a parking spot."""
    spot = get_spot(spot_id)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")
    return get_reviews(spot_id)

@router.post("/{spot_id}/reviews", response_model=Review)
async def create_review(spot_id: str, payload: ReviewCreate):
    """Add a review to a parking spot and update the spot's score."""
    spot = get_spot(spot_id)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")
    
    # Create review
    review = Review(
        id=f"rev-{uuid.uuid4().hex[:8]}",
        spot_id=spot_id,
        rating=payload.rating,
        text=payload.text,
        created_at=datetime.utcnow(),
    )
    add_review(spot_id, review)
    
    # Update spot: recalculate score, review count, and meter status
    all_reviews = get_reviews(spot_id)
    spot_dict = spot.dict()
    spot_dict["review_count"] = len(all_reviews)
    spot_dict["score"] = compute_spot_score(spot_id)
    spot_dict["last_updated_at"] = datetime.utcnow()
    
    # Update meter status from reviews
    review_texts = [r.text for r in all_reviews]
    meter_status, meter_confidence = parse_meter_status(review_texts)
    spot_dict["meter_status"] = meter_status
    spot_dict["meter_status_confidence"] = meter_confidence
    
    updated_spot = update_spot(spot.__class__(**spot_dict))
    
    return review



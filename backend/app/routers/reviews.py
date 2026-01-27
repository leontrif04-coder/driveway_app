# backend/app/routers/reviews.py
from fastapi import APIRouter, Path, HTTPException, Depends
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from app.schemas.review import Review, ReviewCreate
from app.database.config import get_db
from app.database.sync_repositories import RepositoryFactory, ReviewRepository, ParkingSpotRepository
from app.database.mappers import db_review_to_schema, schema_review_to_db
from app.utils.review_parser import parse_meter_status

router = APIRouter()


def get_review_repository(db: Session = Depends(get_db)) -> ReviewRepository:
    """Dependency to get review repository."""
    factory = RepositoryFactory(db)
    return factory.reviews


def get_spot_repository(db: Session = Depends(get_db)) -> ParkingSpotRepository:
    """Dependency to get parking spot repository."""
    factory = RepositoryFactory(db)
    return factory.parking_spots


@router.get("/{spot_id}/reviews", response_model=List[Review])
async def list_reviews(
    spot_id: str = Path(...),
    repo: ReviewRepository = Depends(get_review_repository),
    spot_repo: ParkingSpotRepository = Depends(get_spot_repository),
):
    """Get all reviews for a parking spot."""
    try:
        spot_uuid = UUID(spot_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid spot ID format")
    
    # Verify spot exists
    spot = spot_repo.get_by_id(spot_uuid)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")
    
    # Get reviews
    db_reviews = repo.get_for_spot(spot_uuid)
    
    # Convert to schemas
    return [db_review_to_schema(db_review) for db_review in db_reviews]


@router.post("/{spot_id}/reviews", response_model=Review)
async def create_review(
    spot_id: str,
    payload: ReviewCreate,
    repo: ReviewRepository = Depends(get_review_repository),
    spot_repo: ParkingSpotRepository = Depends(get_spot_repository),
):
    """
    Add a review to a parking spot.
    
    Note: The database trigger automatically updates:
    - spot.review_count
    - spot.avg_rating
    - spot.computed_score
    """
    try:
        spot_uuid = UUID(spot_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid spot ID format")
    
    # Verify spot exists
    spot = spot_repo.get_by_id(spot_uuid)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")
    
    # Create review
    db_review = schema_review_to_db(payload, spot_uuid)
    created_review = repo.create(db_review)
    repo.session.commit()
    
    # Update meter status from review text analysis
    # Get all reviews for meter status parsing
    all_reviews = repo.get_for_spot(spot_uuid, include_hidden=True)
    review_texts = [r.review_text for r in all_reviews if r.review_text]
    
    if review_texts:
        meter_status, meter_confidence = parse_meter_status(review_texts)
        from app.database.models import MeterStatus
        spot_repo.update_meter_status(
            spot_uuid,
            MeterStatus(meter_status),
            meter_confidence
        )
        spot_repo.session.commit()
    
    # Convert to schema and return
    return db_review_to_schema(created_review)

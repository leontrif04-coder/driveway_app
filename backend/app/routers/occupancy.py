# backend/app/routers/occupancy.py
from fastapi import APIRouter, Path, HTTPException, Depends
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from app.schemas.occupancy import OccupancyUpdate, OccupancyEvent, SpotAvailabilityUpdate
from app.database.config import get_db
from app.database.sync_repositories import RepositoryFactory, ParkingSpotRepository, OccupancyEventRepository
from app.database.mappers import db_spot_to_schema
from app.database.models import OccupancyEvent as OccupancyEventModel
from app.websocket_manager import manager
from app.services.availability_predictor import predict_availability_time

router = APIRouter()


def get_spot_repository(db: Session = Depends(get_db)) -> ParkingSpotRepository:
    """Dependency to get parking spot repository."""
    factory = RepositoryFactory(db)
    return factory.parking_spots


def get_occupancy_repository(db: Session = Depends(get_db)) -> OccupancyEventRepository:
    """Dependency to get occupancy event repository."""
    factory = RepositoryFactory(db)
    return factory.occupancy_events


@router.post("/{spot_id}/occupancy")
async def update_occupancy(
    spot_id: str,
    payload: OccupancyUpdate,
    spot_repo: ParkingSpotRepository = Depends(get_spot_repository),
    occupancy_repo: OccupancyEventRepository = Depends(get_occupancy_repository),
):
    """
    Update parking spot occupancy status.
    
    When a spot becomes occupied, it triggers:
    1. Create occupancy event (trigger updates spot.is_occupied)
    2. Predict estimated_availability_time
    3. Update spot with estimated time
    4. Broadcast update via WebSocket
    """
    try:
        spot_uuid = UUID(spot_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid spot ID format")
    
    # Verify spot exists
    spot = spot_repo.get_by_id(spot_uuid)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")
    
    current_time = datetime.utcnow()
    
    # Create occupancy event (trigger will update spot.is_occupied)
    event_type = "occupied" if payload.is_occupied else "available"
    db_event = OccupancyEventModel(
        spot_id=spot_uuid,
        event_type=event_type,
        event_time=current_time,
        source="user_report",
        confidence=1.0,
    )
    occupancy_repo.create(db_event)
    occupancy_repo.session.commit()
    
    # Predict availability time if occupied
    estimated_time = None
    if payload.is_occupied:
        estimated_time = predict_availability_time(
            spot_id,
            current_time,
            payload.estimated_duration_minutes,
        )
        # Update spot with estimated time
        spot_repo.update_occupancy(
            spot_uuid,
            is_occupied=True,
            estimated_available_at=estimated_time,
        )
        spot_repo.session.commit()
    else:
        # Clear estimated time when available
        spot_repo.update_occupancy(
            spot_uuid,
            is_occupied=False,
            estimated_available_at=None,
        )
        spot_repo.session.commit()
    
    # Refresh spot to get updated data
    updated_spot = spot_repo.get_by_id(spot_uuid)
    spot_schema = db_spot_to_schema(updated_spot)
    
    # Broadcast update via WebSocket
    update_message = SpotAvailabilityUpdate(
        spot_id=spot_id,
        is_occupied=payload.is_occupied,
        estimated_availability_time=estimated_time,
        timestamp=current_time,
    )
    await manager.broadcast_update(update_message, spot_schema.latitude, spot_schema.longitude)
    
    return {
        "spot_id": spot_id,
        "is_occupied": payload.is_occupied,
        "estimated_availability_time": estimated_time.isoformat() if estimated_time else None,
        "timestamp": current_time.isoformat(),
    }

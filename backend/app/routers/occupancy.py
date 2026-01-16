# backend/app/routers/occupancy.py
from fastapi import APIRouter, Path, HTTPException
from datetime import datetime
from app.schemas.occupancy import OccupancyUpdate, OccupancyEvent
from app.schemas.occupancy import SpotAvailabilityUpdate
from app.storage import get_spot, update_spot, add_occupancy_event
from app.websocket_manager import manager
from app.services.availability_predictor import predict_availability_time

router = APIRouter()


@router.post("/{spot_id}/occupancy")
async def update_occupancy(spot_id: str, payload: OccupancyUpdate):
    """
    Update parking spot occupancy status.
    
    When a spot becomes occupied, it triggers:
    1. Update spot.is_occupied flag
    2. Predict estimated_availability_time
    3. Store occupancy event in history
    4. Broadcast update via WebSocket
    """
    spot = get_spot(spot_id)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")
    
    current_time = datetime.utcnow()
    
    # Create occupancy event
    event_type = "check_in" if payload.is_occupied else "check_out"
    event = OccupancyEvent(
        spot_id=spot_id,
        event_type=event_type,
        timestamp=current_time,
        estimated_duration_minutes=payload.estimated_duration_minutes if payload.is_occupied else None,
    )
    add_occupancy_event(spot_id, event)
    
    # Update spot
    spot_dict = spot.dict()
    spot_dict["is_occupied"] = payload.is_occupied
    
    # Predict availability time if occupied
    if payload.is_occupied:
        estimated_time = predict_availability_time(
            spot_id,
            current_time,
            payload.estimated_duration_minutes,
        )
        spot_dict["estimated_availability_time"] = estimated_time
    else:
        spot_dict["estimated_availability_time"] = None
    
    spot_dict["last_updated_at"] = current_time
    from app.schemas.parking import ParkingSpot
    updated_spot = update_spot(ParkingSpot(**spot_dict))
    
    # Broadcast update via WebSocket
    update_message = SpotAvailabilityUpdate(
        spot_id=spot_id,
        is_occupied=payload.is_occupied,
        estimated_availability_time=spot_dict.get("estimated_availability_time"),
        timestamp=current_time,
    )
    await manager.broadcast_update(update_message, updated_spot.latitude, updated_spot.longitude)
    
    return {
        "spot_id": spot_id,
        "is_occupied": payload.is_occupied,
        "estimated_availability_time": spot_dict.get("estimated_availability_time").isoformat() if spot_dict.get("estimated_availability_time") else None,
        "timestamp": current_time.isoformat(),
    }


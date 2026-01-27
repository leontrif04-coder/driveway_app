# backend/app/routers/spots.py
from fastapi import APIRouter, Query, Path, HTTPException, Depends
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from app.schemas.parking import ParkingSpot, ParkingSpotCreate
from app.database.config import get_db
from app.database.sync_repositories import RepositoryFactory, ParkingSpotRepository
from app.database.mappers import db_spot_to_schema, schema_spot_to_db

router = APIRouter()


def get_spot_repository(db: Session = Depends(get_db)) -> ParkingSpotRepository:
    """Dependency to get parking spot repository."""
    factory = RepositoryFactory(db)
    return factory.parking_spots


@router.get("/", response_model=List[ParkingSpot])
async def list_spots(
    lat: float = Query(..., description="Latitude of center point"),
    lng: float = Query(..., description="Longitude of center point"),
    radius_m: float = Query(1000, description="Radius in meters"),
    limit: int = Query(50, description="Maximum number of spots to return"),
    repo: ParkingSpotRepository = Depends(get_spot_repository),
):
    """
    Get parking spots near a point.
    Returns spots within radius_m meters of (lat, lng), limited to 'limit' results.
    Uses PostGIS for efficient geospatial queries.
    """
    # Query spots within radius using PostGIS
    db_spots_with_distance = repo.find_within_radius(
        latitude=lat,
        longitude=lng,
        radius_meters=radius_m,
        limit=limit
    )
    
    # Convert database models to Pydantic schemas with distance
    spots = []
    for db_spot, distance_m in db_spots_with_distance:
        spot_schema = db_spot_to_schema(db_spot, distance_m=distance_m)
        spots.append(spot_schema)
    
    return spots


@router.get("/{spot_id}", response_model=ParkingSpot)
async def get_spot_by_id(
    spot_id: str = Path(...),
    repo: ParkingSpotRepository = Depends(get_spot_repository),
):
    """Get a specific parking spot by ID."""
    try:
        spot_uuid = UUID(spot_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid spot ID format")
    
    db_spot = repo.get_by_id(spot_uuid)
    if not db_spot:
        raise HTTPException(status_code=404, detail="Spot not found")
    
    return db_spot_to_schema(db_spot)


@router.post("/", response_model=ParkingSpot)
async def create_spot_endpoint(
    spot_data: ParkingSpotCreate,
    repo: ParkingSpotRepository = Depends(get_spot_repository),
):
    """Create a new parking spot (for dev/testing)."""
    # Convert schema to database model
    db_spot = schema_spot_to_db(spot_data)
    
    # Create in database
    created_spot = repo.create(db_spot)
    repo.session.commit()
    
    # Convert back to schema
    return db_spot_to_schema(created_spot)

# backend/app/services/geo.py
from typing import List, Optional, Tuple
from math import radians, sin, cos, sqrt, atan2
from app.schemas.parking import ParkingSpot

def haversine_distance_m(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    # Returns distance in meters
    R = 6371000
    lat1, lon1 = map(radians, a)
    lat2, lon2 = map(radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(h), sqrt(1 - h))
    return R * c

def add_distances(
    spots: List[ParkingSpot],
    user_coords: Optional[tuple[float, float]],
    dest_coords: Optional[tuple[float, float]],
) -> List[ParkingSpot]:
    updated = []

    for s in spots:
        data = s.dict()
        if user_coords is not None:
            data["distance_to_user_m"] = haversine_distance_m(
                user_coords, (s.latitude, s.longitude)
            )
        if dest_coords is not None:
            data["distance_to_destination_m"] = haversine_distance_m(
                dest_coords, (s.latitude, s.longitude)
            )
        updated.append(ParkingSpot(**data))
    return updated



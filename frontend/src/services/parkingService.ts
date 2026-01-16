// frontend/src/services/parkingService.ts
import type { Region } from "react-native-maps";
import type { ParkingSpot } from "../domain/models";
import { API_BASE_URL } from "../config/env";

export interface ParkingFiltersDto {
  minSafetyScore?: number;
  maxWalkingDistanceM?: number;
  timeOfDay?: "morning" | "afternoon" | "evening" | "night";
  tourismBias?: "low" | "medium" | "high";
  userLat?: number;
  userLng?: number;
  destLat?: number;
  destLng?: number;
}

export const parkingService = {
  async fetchSpots(
    region: Region,
    filters: ParkingFiltersDto = {}
  ): Promise<ParkingSpot[]> {
    const minLat = region.latitude - region.latitudeDelta / 2;
    const maxLat = region.latitude + region.latitudeDelta / 2;
    const minLng = region.longitude - region.longitudeDelta / 2;
    const maxLng = region.longitude + region.longitudeDelta / 2;

    const params = new URLSearchParams({
      min_lat: String(minLat),
      max_lat: String(maxLat),
      min_lng: String(minLng),
      max_lng: String(maxLng),
    });

    if (filters.userLat != null && filters.userLng != null) {
      params.append("user_lat", String(filters.userLat));
      params.append("user_lng", String(filters.userLng));
    }
    if (filters.destLat != null && filters.destLng != null) {
      params.append("dest_lat", String(filters.destLat));
      params.append("dest_lng", String(filters.destLng));
    }
    if (filters.minSafetyScore != null) {
      params.append("min_safety", String(filters.minSafetyScore));
    }
    if (filters.maxWalkingDistanceM != null) {
      params.append("max_walk_m", String(filters.maxWalkingDistanceM));
    }
    if (filters.timeOfDay) {
      params.append("time_of_day", filters.timeOfDay);
    }
    if (filters.tourismBias) {
      params.append("tourism_bias", filters.tourismBias);
    }

    const res = await fetch(`${API_BASE_URL}/api/v1/spots?${params.toString()}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch spots: ${res.status}`);
    }

    const json = await res.json();
    const mapped: ParkingSpot[] = json.map((s: any) => ({
      id: s.id,
      latitude: s.latitude,
      longitude: s.longitude,
      streetName: s.street_name,
      maxDurationMinutes: s.max_duration_minutes,
      pricePerHourUsd: s.price_per_hour_usd,
      safetyScore: s.safety_score,
      tourismDensity: s.tourism_density,
      meterStatus: s.meter_status,
      meterStatusConfidence: s.meter_status_confidence,
      distanceToUserM: s.distance_to_user_m,
      distanceToDestinationM: s.distance_to_destination_m,
      reviewCount: s.review_count,
      lastUpdatedAt: s.last_updated_at,
      compositeScore: s.composite_score,
    }));

    return mapped;
  },
};



// frontend/src/domain/models.ts
export type MeterStatus = "working" | "broken" | "unknown";

export interface ParkingSpot {
  id: string;
  latitude: number;
  longitude: number;
  streetName: string;
  maxDurationMinutes?: number;
  pricePerHourUsd?: number;

  safetyScore: number;      // 0–100
  tourismDensity: number;   // 0–100
  meterStatus: MeterStatus;
  meterStatusConfidence: number; // 0–1

  distanceToUserM?: number;
  distanceToDestinationM?: number;

  reviewCount: number;
  lastUpdatedAt: string;
  compositeScore?: number;
  
  // Real-time availability
  isOccupied?: boolean;
  estimatedAvailabilityTime?: string; // ISO datetime string
}

export interface ParkingFilters {
  minSafetyScore?: number;
  maxWalkingDistanceM?: number;
  tourismBias?: "low" | "medium" | "high";
  timeOfDay?: "morning" | "afternoon" | "evening" | "night";
}



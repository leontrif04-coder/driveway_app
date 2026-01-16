// frontend/src/utils/filters.ts
import type { ParkingSpot, ParkingFilters } from "../domain/models";

export const scoreAndFilterSpots = (
  spots: ParkingSpot[],
  filters: ParkingFilters
): ParkingSpot[] => {
  const timeWeight = getTimeOfDayWeight(filters.timeOfDay);
  const tourismWeight = getTourismBiasWeight(filters.tourismBias);

  return spots
    .map((spot) => {
      const baseScore = spot.safetyScore;
      const tourismComponent = spot.tourismDensity * tourismWeight;
      const timeComponent = timeWeight;

      const meterPenalty =
        spot.meterStatus === "broken"
          ? -20 * spot.meterStatusConfidence
          : 0;

      const compositeScore =
        baseScore + tourismComponent + timeComponent + meterPenalty;

      return { ...spot, compositeScore };
    })
    .filter((spot) => {
      if (
        filters.minSafetyScore != null &&
        spot.safetyScore < filters.minSafetyScore
      ) {
        return false;
      }
      if (
        filters.maxWalkingDistanceM != null &&
        spot.distanceToDestinationM != null &&
        spot.distanceToDestinationM > filters.maxWalkingDistanceM
      ) {
        return false;
      }
      return true;
    })
    .sort((a, b) => (b.compositeScore ?? 0) - (a.compositeScore ?? 0));
};

const getTimeOfDayWeight = (
  timeOfDay?: ParkingFilters["timeOfDay"]
): number => {
  switch (timeOfDay) {
    case "morning":
      return 5;
    case "afternoon":
      return 0;
    case "evening":
      return -5;
    case "night":
      return -10;
    default:
      return 0;
  }
};

const getTourismBiasWeight = (
  bias?: ParkingFilters["tourismBias"]
): number => {
  switch (bias) {
    case "low":
      return -0.4;
    case "medium":
      return 0;
    case "high":
      return 0.4;
    default:
      return 0;
  }
};



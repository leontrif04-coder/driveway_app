// frontend/src/hooks/useParkingSpots.ts
import { useCallback, useMemo, useState } from "react";
import type { Region } from "react-native-maps";
import type { ParkingSpot, ParkingFilters } from "../domain/models";
import { parkingService, ParkingFiltersDto } from "../services/parkingService";
import { scoreAndFilterSpots } from "../utils/filters";

export const useParkingSpots = () => {
  const [rawSpots, setRawSpots] = useState<ParkingSpot[]>([]);
  const [filters, setFilters] = useState<ParkingFilters>({});
  const [isLoading, setIsLoading] = useState(false);

  const fetchSpotsForRegion = useCallback(
    async (region: Region, extraFilters?: ParkingFiltersDto) => {
      try {
        setIsLoading(true);
        const spots = await parkingService.fetchSpots(region, extraFilters);
        setRawSpots(spots);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const applyFilters = useCallback((nextFilters: ParkingFilters) => {
    setFilters(nextFilters);
  }, []);

  const spots = useMemo(
    () => scoreAndFilterSpots(rawSpots, filters),
    [rawSpots, filters]
  );

  return {
    spots,
    isLoading,
    fetchSpotsForRegion,
    applyFilters,
    filters,
  };
};



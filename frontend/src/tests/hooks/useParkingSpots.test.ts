// frontend/src/tests/hooks/useParkingSpots.test.ts
import { renderHook, act, waitFor } from "@testing-library/react-native";
import { useParkingSpots } from "../../hooks/useParkingSpots";
import type { Region } from "react-native-maps";

const mockRegion: Region = {
  latitude: 40.7128,
  longitude: -74.006,
  latitudeDelta: 0.05,
  longitudeDelta: 0.05,
};

describe("useParkingSpots", () => {
  beforeEach(() => {
    // Reset fetch mock
    global.fetch = jest.fn();
  });

  it("initializes with empty spots and loading false", () => {
    const { result } = renderHook(() => useParkingSpots());
    
    expect(result.current.spots).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.filters).toEqual({});
  });

  it("fetches spots for region", async () => {
    const mockSpots = [
      {
        id: "spot-1",
        latitude: 40.7128,
        longitude: -74.006,
        street_name: "Test Street",
        safety_score: 80.0,
        tourism_density: 70.0,
        meter_status: "working",
        meter_status_confidence: 0.9,
        review_count: 5,
        last_updated_at: "2024-01-01T12:00:00Z",
      },
    ];

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockSpots,
    });

    const { result } = renderHook(() => useParkingSpots());

    await act(async () => {
      await result.current.fetchSpotsForRegion(mockRegion);
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.rawSpots.length).toBeGreaterThan(0);
  });

  it("sets loading state during fetch", async () => {
    let resolveFetch: (value: any) => void;
    const fetchPromise = new Promise((resolve) => {
      resolveFetch = resolve;
    });

    (global.fetch as jest.Mock).mockReturnValueOnce(fetchPromise);

    const { result } = renderHook(() => useParkingSpots());

    act(() => {
      result.current.fetchSpotsForRegion(mockRegion);
    });

    // Should be loading
    expect(result.current.isLoading).toBe(true);

    // Resolve fetch
    await act(async () => {
      resolveFetch!({
        ok: true,
        json: async () => [],
      });
      await fetchPromise;
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });

  it("applies filters to spots", () => {
    const { result } = renderHook(() => useParkingSpots());

    // Set initial spots
    act(() => {
      // Manually set spots for testing (normally done via fetch)
      (result.current as any).rawSpots = [
        {
          id: "spot-1",
          safetyScore: 80.0,
          distanceToDestinationM: 500.0,
        },
        {
          id: "spot-2",
          safetyScore: 60.0,
          distanceToDestinationM: 1000.0,
        },
      ];
    });

    // Apply filter
    act(() => {
      result.current.applyFilters({ minSafetyScore: 70.0 });
    });

    expect(result.current.filters.minSafetyScore).toBe(70.0);
  });

  it("handles fetch errors gracefully", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useParkingSpots());

    await act(async () => {
      try {
        await result.current.fetchSpotsForRegion(mockRegion);
      } catch (error) {
        // Error is expected
      }
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });
});


// frontend/src/tests/services/parkingService.test.ts
import { parkingService } from "../../services/parkingService";
import type { Region } from "react-native-maps";

const mockRegion: Region = {
  latitude: 40.7128,
  longitude: -74.006,
  latitudeDelta: 0.05,
  longitudeDelta: 0.05,
};

describe("parkingService", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it("fetches spots for region", async () => {
    const mockResponse = [
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
      json: async () => mockResponse,
    });

    const spots = await parkingService.fetchSpots(mockRegion);

    expect(spots).toHaveLength(1);
    expect(spots[0].id).toBe("spot-1");
    expect(spots[0].streetName).toBe("Test Street");
  });

  it("handles API errors", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    await expect(parkingService.fetchSpots(mockRegion)).rejects.toThrow(
      "Failed to fetch spots: 500"
    );
  });

  it("includes filters in request", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    });

    await parkingService.fetchSpots(mockRegion, {
      minSafetyScore: 70.0,
      maxWalkingDistanceM: 500.0,
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("min_safety=70")
    );
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("max_walk_m=500")
    );
  });

  it("maps response fields correctly", async () => {
    const mockResponse = [
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
      json: async () => mockResponse,
    });

    const spots = await parkingService.fetchSpots(mockRegion);

    expect(spots[0]).toMatchObject({
      id: "spot-1",
      latitude: 40.7128,
      longitude: -74.006,
      streetName: "Test Street",
      safetyScore: 80.0,
      tourismDensity: 70.0,
      meterStatus: "working",
      meterStatusConfidence: 0.9,
      reviewCount: 5,
    });
  });
});


// frontend/src/tests/integration/MapScreen.test.tsx
import React from "react";
import { render, waitFor } from "@testing-library/react-native";
import { MapScreen } from "../../screens/MapScreen/MapScreen";
import * as Location from "expo-location";

jest.mock("expo-location");
jest.mock("../../hooks/useParkingSpots", () => ({
  useParkingSpots: () => ({
    spots: [
      {
        id: "spot-1",
        latitude: 40.7128,
        longitude: -74.006,
        streetName: "Test Street",
        safetyScore: 80.0,
        tourismDensity: 70.0,
        meterStatus: "working",
        meterStatusConfidence: 0.9,
        reviewCount: 5,
        lastUpdatedAt: "2024-01-01T12:00:00Z",
      },
    ],
    isLoading: false,
    fetchSpotsForRegion: jest.fn(),
    applyFilters: jest.fn(),
  }),
}));

describe("MapScreen Integration", () => {
  beforeEach(() => {
    (Location.requestForegroundPermissionsAsync as jest.Mock).mockResolvedValue({
      status: "granted",
    });

    (Location.getCurrentPositionAsync as jest.Mock).mockResolvedValue({
      coords: {
        latitude: 40.7128,
        longitude: -74.006,
      },
    });
  });

  it("renders map screen with components", async () => {
    const { getByPlaceholderText, getByText } = render(<MapScreen />);

    await waitFor(() => {
      expect(getByPlaceholderText("Search destination (e.g. restaurant)")).toBeTruthy();
    });

    // Check for filter bar labels
    expect(getByText(/Min safety:/)).toBeTruthy();
  });

  it("renders map view", () => {
    const { UNSAFE_getByType } = render(<MapScreen />);
    const mapView = UNSAFE_getByType("MapView");
    expect(mapView).toBeTruthy();
  });

  it("handles location loading state", () => {
    (Location.requestForegroundPermissionsAsync as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    const { UNSAFE_getByType } = render(<MapScreen />);
    // Map should still render
    const mapView = UNSAFE_getByType("MapView");
    expect(mapView).toBeTruthy();
  });
});


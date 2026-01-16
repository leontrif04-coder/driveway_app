// frontend/src/tests/components/ParkingSpotMarker.test.tsx
import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import { ParkingSpotMarker } from "../../components/ParkingSpotMarker";
import type { ParkingSpot } from "../../domain/models";

const mockSpot: ParkingSpot = {
  id: "spot-1",
  latitude: 40.7128,
  longitude: -74.006,
  streetName: "Test Street",
  maxDurationMinutes: 120,
  pricePerHourUsd: 4.0,
  safetyScore: 80.0,
  tourismDensity: 70.0,
  meterStatus: "working",
  meterStatusConfidence: 0.9,
  distanceToUserM: 100.0,
  distanceToDestinationM: 500.0,
  reviewCount: 5,
  lastUpdatedAt: "2024-01-01T12:00:00Z",
};

describe("ParkingSpotMarker", () => {
  it("renders marker with correct coordinates", () => {
    const { UNSAFE_getByType } = render(
      <ParkingSpotMarker spot={mockSpot} />
    );
    
    const marker = UNSAFE_getByType("Marker");
    expect(marker.props.coordinate).toEqual({
      latitude: mockSpot.latitude,
      longitude: mockSpot.longitude,
    });
  });

  it("uses red color for broken meter", () => {
    const brokenSpot: ParkingSpot = {
      ...mockSpot,
      meterStatus: "broken",
    };
    
    const { UNSAFE_getByType } = render(
      <ParkingSpotMarker spot={brokenSpot} />
    );
    
    const marker = UNSAFE_getByType("Marker");
    expect(marker.props.pinColor).toBe("#f97373");
  });

  it("uses green color for safe spots (safety >= 70)", () => {
    const safeSpot: ParkingSpot = {
      ...mockSpot,
      meterStatus: "working",
      safetyScore: 80.0,
    };
    
    const { UNSAFE_getByType } = render(
      <ParkingSpotMarker spot={safeSpot} />
    );
    
    const marker = UNSAFE_getByType("Marker");
    expect(marker.props.pinColor).toBe("#22c55e");
  });

  it("uses yellow color for medium safety spots", () => {
    const mediumSpot: ParkingSpot = {
      ...mockSpot,
      meterStatus: "working",
      safetyScore: 60.0,
    };
    
    const { UNSAFE_getByType } = render(
      <ParkingSpotMarker spot={mediumSpot} />
    );
    
    const marker = UNSAFE_getByType("Marker");
    expect(marker.props.pinColor).toBe("#facc15");
  });

  it("calls onPressDetails when callout is pressed", () => {
    const onPressDetails = jest.fn();
    const { getByText } = render(
      <ParkingSpotMarker spot={mockSpot} onPressDetails={onPressDetails} />
    );
    
    const callout = getByText("Tap for details").parent;
    if (callout) {
      fireEvent.press(callout);
      expect(onPressDetails).toHaveBeenCalledWith(mockSpot.id);
    }
  });

  it("displays street name in callout", () => {
    const { getByText } = render(<ParkingSpotMarker spot={mockSpot} />);
    expect(getByText("Test Street")).toBeTruthy();
  });

  it("displays distance to destination when available", () => {
    const { getByText } = render(<ParkingSpotMarker spot={mockSpot} />);
    expect(getByText(/Walk: 0.50 km/)).toBeTruthy();
  });

  it("does not display distance when not available", () => {
    const spotWithoutDistance: ParkingSpot = {
      ...mockSpot,
      distanceToDestinationM: undefined,
    };
    
    const { queryByText } = render(
      <ParkingSpotMarker spot={spotWithoutDistance} />
    );
    
    expect(queryByText(/Walk:/)).toBeNull();
  });

  it("displays meter status and confidence", () => {
    const { getByText } = render(<ParkingSpotMarker spot={mockSpot} />);
    expect(getByText(/Meter: working/)).toBeTruthy();
    expect(getByText(/90%/)).toBeTruthy();
  });
});


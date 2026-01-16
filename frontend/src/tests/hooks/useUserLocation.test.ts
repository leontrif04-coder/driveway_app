// frontend/src/tests/hooks/useUserLocation.test.ts
import { renderHook, waitFor } from "@testing-library/react-native";
import * as Location from "expo-location";
import { useUserLocation } from "../../hooks/useUserLocation";

jest.mock("expo-location");

describe("useUserLocation", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("requests location permission and gets location", async () => {
    (Location.requestForegroundPermissionsAsync as jest.Mock).mockResolvedValue({
      status: "granted",
    });

    (Location.getCurrentPositionAsync as jest.Mock).mockResolvedValue({
      coords: {
        latitude: 40.7128,
        longitude: -74.006,
      },
    });

    const { result } = renderHook(() => useUserLocation());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.location).toEqual({
      latitude: 40.7128,
      longitude: -74.006,
    });
    expect(result.current.error).toBeNull();
  });

  it("handles permission denial", async () => {
    (Location.requestForegroundPermissionsAsync as jest.Mock).mockResolvedValue({
      status: "denied",
    });

    const { result } = renderHook(() => useUserLocation());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.location).toBeNull();
    expect(result.current.error).toBe("Location permission not granted");
  });

  it("handles location error", async () => {
    (Location.requestForegroundPermissionsAsync as jest.Mock).mockResolvedValue({
      status: "granted",
    });

    (Location.getCurrentPositionAsync as jest.Mock).mockRejectedValue(
      new Error("Location error")
    );

    const { result } = renderHook(() => useUserLocation());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.location).toBeNull();
  });

  it("starts with loading state", () => {
    (Location.requestForegroundPermissionsAsync as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    const { result } = renderHook(() => useUserLocation());

    expect(result.current.isLoading).toBe(true);
  });
});


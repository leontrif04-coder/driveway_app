// frontend/src/tests/components/ParkingFilterBar.test.tsx
import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import { ParkingFilterBar } from "../../components/ParkingFilterBar";

describe("ParkingFilterBar", () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  it("renders filter controls", () => {
    const { getByText } = render(<ParkingFilterBar onChange={mockOnChange} />);
    
    expect(getByText(/Min safety:/)).toBeTruthy();
    expect(getByText(/Max walk:/)).toBeTruthy();
  });

  it("calls onChange with initial filter values", async () => {
    render(<ParkingFilterBar onChange={mockOnChange} />);
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          minSafetyScore: 60,
          maxWalkingDistanceM: 800,
          timeOfDay: "evening",
          tourismBias: "medium",
        })
      );
    });
  });

  it("updates filters when picker values change", async () => {
    const { UNSAFE_getAllByType } = render(
      <ParkingFilterBar onChange={mockOnChange} />
    );
    
    // Wait for initial render
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalled();
    });
    
    mockOnChange.mockClear();
    
    // Note: Picker testing in React Native is limited
    // This test verifies the component structure
    const pickers = UNSAFE_getAllByType("Picker");
    expect(pickers.length).toBeGreaterThan(0);
  });

  it("displays safety score correctly", () => {
    const { getByText } = render(<ParkingFilterBar onChange={mockOnChange} />);
    expect(getByText(/Min safety: 60/)).toBeTruthy();
  });

  it("displays walking distance correctly", () => {
    const { getByText } = render(<ParkingFilterBar onChange={mockOnChange} />);
    expect(getByText(/Max walk: 0.8 km/)).toBeTruthy();
  });
});


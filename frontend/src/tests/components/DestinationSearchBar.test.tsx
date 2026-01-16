// frontend/src/tests/components/DestinationSearchBar.test.tsx
import React from "react";
import { render, fireEvent, getByPlaceholderText } from "@testing-library/react-native";
import { DestinationSearchBar } from "../../components/DestinationSearchBar";

describe("DestinationSearchBar", () => {
  const mockOnDestinationSelected = jest.fn();

  beforeEach(() => {
    mockOnDestinationSelected.mockClear();
  });

  it("renders search input and button", () => {
    const { getByPlaceholderText, getByText } = render(
      <DestinationSearchBar onDestinationSelected={mockOnDestinationSelected} />
    );
    
    expect(getByPlaceholderText("Search destination (e.g. restaurant)")).toBeTruthy();
    expect(getByText("Go")).toBeTruthy();
  });

  it("updates query when text is entered", () => {
    const { getByPlaceholderText } = render(
      <DestinationSearchBar onDestinationSelected={mockOnDestinationSelected} />
    );
    
    const input = getByPlaceholderText("Search destination (e.g. restaurant)");
    fireEvent.changeText(input, "Central Park");
    
    expect(input.props.value).toBe("Central Park");
  });

  it("calls onDestinationSelected when Go button is pressed", () => {
    const { getByText } = render(
      <DestinationSearchBar onDestinationSelected={mockOnDestinationSelected} />
    );
    
    const goButton = getByText("Go");
    fireEvent.press(goButton);
    
    expect(mockOnDestinationSelected).toHaveBeenCalledWith({
      latitude: 40.7128,
      longitude: -74.006,
    });
  });

  it("calls onDestinationSelected with fixed coordinates", () => {
    const { getByText } = render(
      <DestinationSearchBar onDestinationSelected={mockOnDestinationSelected} />
    );
    
    fireEvent.press(getByText("Go"));
    
    expect(mockOnDestinationSelected).toHaveBeenCalledWith({
      latitude: 40.7128,
      longitude: -74.006,
    });
  });
});


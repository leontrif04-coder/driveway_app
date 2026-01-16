# Testing Guide - Smart Parking Assistant

Comprehensive testing guide for the Smart Parking Assistant application.

## Quick Start

### Backend Tests
```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

### Frontend Tests
```bash
cd frontend
npm install
npm test
```

---

## Backend Testing (pytest)

### Test Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_geo.py              # Geospatial unit tests
│   ├── test_scoring.py          # Scoring algorithm unit tests
│   ├── test_review_parser.py    # Review parser unit tests
│   ├── test_spots_api.py        # Spots API integration tests
│   └── test_reviews_api.py      # Reviews API integration tests
├── pytest.ini                   # Pytest configuration
└── requirements-dev.txt         # Test dependencies
```

### Setup

```bash
cd backend

# Install dependencies
pip install -r requirements-dev.txt

# Or install individually
pip install pytest pytest-asyncio pytest-cov httpx
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_geo.py

# Run specific test class
pytest tests/test_scoring.py::TestComputeSpotScore

# Run specific test
pytest tests/test_geo.py::TestHaversineDistance::test_same_point

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Run with markers
pytest -m unit          # Only unit tests
pytest -m integration   # Only integration tests

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

### Test Coverage

The project aims for >80% code coverage. Coverage reports are generated automatically:

```bash
# Generate coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing

# Coverage thresholds are configured in pytest.ini
# Tests will fail if coverage drops below 80%
```

### Writing Backend Tests

#### Unit Tests

Unit tests focus on testing individual functions in isolation:

```python
# tests/test_geo.py
import pytest
from app.services.geo import haversine_distance_m

def test_same_point():
    """Distance from a point to itself should be 0."""
    point = (40.7128, -74.0060)
    distance = haversine_distance_m(point, point)
    assert distance == pytest.approx(0.0, abs=0.1)
```

#### Integration Tests

Integration tests test API endpoints end-to-end:

```python
# tests/test_spots_api.py
def test_list_spots_near_location(client):
    """Test finding spots near a location."""
    # Setup
    spot = create_test_spot(...)
    
    # Execute
    response = client.get("/api/v1/spots?lat=40.7128&lng=-74.0060&radius_m=1000")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
```

#### Fixtures

Shared test data is defined in `conftest.py`:

```python
@pytest.fixture
def sample_spot() -> ParkingSpot:
    """Create a sample parking spot for testing."""
    return ParkingSpot(...)

@pytest.fixture
def client():
    """Create a test client for FastAPI."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)
```

### Test Files

#### test_geo.py
Tests for geospatial calculations:
- Haversine distance calculations
- Edge cases (same point, antipodes, equator crossing, poles)
- Distance accuracy for various scenarios

#### test_scoring.py
Tests for scoring algorithms:
- Score computation with 0, 1, 10, 100, 1000 reviews
- Logarithmic scaling verification
- Score capping at 100

#### test_review_parser.py
Tests for review text parsing:
- Meter status detection (working/broken/unknown)
- Keyword matching (case-insensitive)
- Ambiguous text handling
- Confidence calculation

#### test_spots_api.py
Integration tests for spots endpoints:
- GET /api/v1/spots (radius filtering, sorting, limit)
- GET /api/v1/spots/{spot_id}
- POST /api/v1/spots
- Error handling (404, 422)

#### test_reviews_api.py
Integration tests for reviews endpoints:
- GET /api/v1/spots/{spot_id}/reviews
- POST /api/v1/spots/{spot_id}/reviews
- Score recalculation after review creation
- Meter status updates
- Review count increments

---

## Frontend Testing (Jest + React Native Testing Library)

### Test Structure

```
frontend/src/tests/
├── setupTests.ts                    # Test setup and mocks
├── __mocks__/
│   └── react-native-maps.ts         # Map component mocks
├── mocks/
│   ├── server.ts                    # MSW server setup
│   └── handlers.ts                  # API request handlers
├── components/
│   ├── ParkingSpotMarker.test.tsx
│   ├── ParkingFilterBar.test.tsx
│   └── DestinationSearchBar.test.tsx
├── hooks/
│   ├── useParkingSpots.test.ts
│   └── useUserLocation.test.ts
├── services/
│   └── parkingService.test.ts
└── integration/
    └── MapScreen.test.tsx
```

### Setup

```bash
cd frontend

# Install dependencies
npm install

# Test dependencies are included in package.json devDependencies:
# - @testing-library/react-native
# - @testing-library/jest-native
# - jest
# - jest-expo
# - msw (Mock Service Worker)
```

### Running Tests

```bash
# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run tests for CI (no watch mode)
npm run test:ci

# Run specific test file
npm test -- ParkingSpotMarker.test.tsx

# Run tests matching a pattern
npm test -- --testNamePattern="renders"
```

### Test Configuration

Configuration is in `jest.config.js`:
- Uses `jest-expo` preset
- Sets up MSW for API mocking
- Configures coverage thresholds (70%)
- Mocks react-native-maps and expo-location

### Writing Frontend Tests

#### Component Tests

```typescript
// tests/components/ParkingSpotMarker.test.tsx
import { render, fireEvent } from "@testing-library/react-native";
import { ParkingSpotMarker } from "../../components/ParkingSpotMarker";

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
});
```

#### Hook Tests

```typescript
// tests/hooks/useParkingSpots.test.ts
import { renderHook, act, waitFor } from "@testing-library/react-native";
import { useParkingSpots } from "../../hooks/useParkingSpots";

describe("useParkingSpots", () => {
  it("fetches spots for region", async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
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
  });
});
```

#### API Mocking with MSW

API requests are mocked using Mock Service Worker (MSW):

```typescript
// tests/mocks/handlers.ts
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get(`${API_BASE_URL}/api/v1/spots`, () => {
    return HttpResponse.json([...mockSpots]);
  }),
];
```

### Test Files

#### Component Tests
- **ParkingSpotMarker.test.tsx**: Tests marker rendering, color selection, callout interactions
- **ParkingFilterBar.test.tsx**: Tests filter controls and onChange callbacks
- **DestinationSearchBar.test.tsx**: Tests search input and destination selection

#### Hook Tests
- **useParkingSpots.test.ts**: Tests data fetching, filtering, loading states, error handling
- **useUserLocation.test.ts**: Tests location permission, location updates, error states

#### Service Tests
- **parkingService.test.ts**: Tests API client, request/response mapping, error handling

#### Integration Tests
- **MapScreen.test.tsx**: Tests full user flow, component integration, state management

---

## Continuous Integration

### GitHub Actions Workflow

The project includes a GitHub Actions workflow (`.github/workflows/test.yml`) that:
- Runs backend tests on Python 3.10 and 3.11
- Runs frontend tests on Node.js 18
- Generates coverage reports
- Uploads coverage to Codecov

The workflow runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

### Local CI Simulation

```bash
# Run tests like CI
cd backend
pytest --cov=app --cov-report=xml

cd ../frontend
npm run test:ci
```

---

## Test Coverage Goals

### Backend
- **Target**: >80% code coverage
- **Critical paths**: 100% coverage
- **Coverage includes**:
  - All service functions
  - All API endpoints
  - Error handling paths
  - Edge cases

### Frontend
- **Target**: >70% code coverage
- **Coverage includes**:
  - All components
  - All hooks
  - All services
  - User interaction flows

---

## Best Practices

### Test Organization
1. **Arrange-Act-Assert**: Structure tests clearly
2. **Descriptive names**: Test names should describe what they test
3. **One assertion per test**: Focus each test on one behavior
4. **Independent tests**: Tests should not depend on each other
5. **Fast tests**: Unit tests should complete in <100ms

### Test Data
1. **Fixtures**: Use pytest fixtures for reusable test data
2. **Factories**: Create test data factories for complex objects
3. **Mocks**: Mock external dependencies (APIs, databases, etc.)
4. **Cleanup**: Reset state between tests (autouse fixtures)

### Test Quality
1. **Test edge cases**: Test boundaries, null values, error conditions
2. **Test error paths**: Verify error handling and validation
3. **Test integration**: Test how components work together
4. **Test user flows**: Test complete user journeys

---

## Troubleshooting

### Backend Tests

#### Import Errors
```bash
# Ensure you're in the backend directory
cd backend

# Install dependencies
pip install -r requirements-dev.txt

# Verify Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Storage Not Resetting
- The `reset_storage` fixture in `conftest.py` should automatically clear storage
- Ensure tests use the `client` fixture which resets storage

#### Coverage Not Generating
```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Run with coverage flags
pytest --cov=app --cov-report=html
```

### Frontend Tests

#### Module Resolution Errors
```bash
# Clear Jest cache
npx jest --clearCache

# Reinstall dependencies
rm -rf node_modules
npm install
```

#### MSW Not Working
- Ensure `setupTests.ts` is configured correctly
- Check that handlers are defined in `tests/mocks/handlers.ts`
- Verify API_BASE_URL matches in handlers

#### React Native Maps Not Mocked
- Ensure `__mocks__/react-native-maps.ts` exists
- Check `jest.config.js` transformIgnorePatterns

#### Test Timeouts
```typescript
// Increase timeout for slow tests
jest.setTimeout(10000);
```

---

## Common Test Patterns

### Testing Async Functions
```typescript
// Frontend
await act(async () => {
  await asyncFunction();
});
await waitFor(() => {
  expect(result).toBeDefined();
});
```

```python
# Backend
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Testing Error Cases
```typescript
// Frontend
await expect(asyncFunction()).rejects.toThrow("Error message");
```

```python
# Backend
with pytest.raises(ValueError, match="Error message"):
    function_that_raises()
```

### Testing API Endpoints
```python
# Backend
def test_endpoint(client):
    response = client.get("/api/v1/spots")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

### Testing Hooks
```typescript
// Frontend
const { result } = renderHook(() => useHook());
act(() => {
  result.current.someAction();
});
expect(result.current.state).toBe(expected);
```

---

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [React Native Testing Library](https://callstack.github.io/react-native-testing-library/)
- [MSW Documentation](https://mswjs.io/)
- [Testing Best Practices](https://testingjavascript.com/)

---

## Quick Reference

### Backend Commands
```bash
pytest                           # Run all tests
pytest -v                        # Verbose output
pytest --cov=app                 # With coverage
pytest tests/test_geo.py         # Specific file
pytest -m unit                   # Run marked tests
```

### Frontend Commands
```bash
npm test                         # Run all tests
npm run test:watch               # Watch mode
npm run test:coverage            # With coverage
npm test -- ParkingSpotMarker    # Specific file
```

---

## Questions?

For questions or issues with tests, please:
1. Check this guide
2. Review test examples in the codebase
3. Check error messages and stack traces
4. Consult testing documentation

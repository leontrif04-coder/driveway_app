I need you to implement a complete testing suite for my Smart Parking Assistant application. Act as a senior QA engineer with expertise in Python testing, React Native testing, and TDD practices.

CONTEXT:
- Backend: FastAPI with in-memory storage (will migrate to PostgreSQL)
- Frontend: React Native with Expo, TypeScript
- Key features: geospatial queries, review scoring, meter status parsing

REQUIREMENTS:

BACKEND TESTING (pytest):
1. Unit Tests:
   - app/services/geo.py: Test haversine_distance_m with edge cases (same point, antipodes, equator crossing, poles)
   - app/services/scoring.py: Test compute_spot_score with various review counts (0, 1, 10, 100, 1000)
   - app/utils/review_parser.py: Test parse_meter_status with ambiguous text, mixed keywords, no keywords
   
2. Integration Tests:
   - GET /api/v1/spots: Test radius filtering, sorting, limit parameter
   - POST /api/v1/spots/{spot_id}/reviews: Test score recalculation, meter status updates
   - Test 404 errors for non-existent spots
   
3. Test Fixtures:
   - Create reusable fixtures for parking spots, reviews, locations
   - Mock storage operations
   
4. Coverage:
   - Aim for >80% code coverage
   - Generate coverage reports

FRONTEND TESTING (Jest + React Native Testing Library):
1. Component Tests:
   - ParkingSpotMarker: Test rendering with different spot states
   - ParkingFilterBar: Test filter interactions
   - DestinationSearchBar: Test search input and submission
   
2. Hook Tests:
   - useParkingSpots: Test data fetching, filtering, error states
   - useUserLocation: Test permission handling, location updates
   
3. Integration Tests:
   - MapScreen: Test user flow from loading to selecting a spot
   - Test API service mocking with MSW

DELIVERABLES:
- Create test files in proper directory structure (tests/ folder)
- Include conftest.py for pytest fixtures
- Add jest.config.js for frontend
- Include GitHub Actions workflow (.github/workflows/test.yml)
- Add test commands to package.json and requirements-dev.txt
- Write a TESTING.md guide with test running instructions

CONSTRAINTS:
- Follow existing code style and patterns
- Use type hints in Python tests
- Use TypeScript for frontend tests
- Tests should be independent and idempotent
- Include both happy path and error scenarios

Please implement this comprehensively with production-grade quality.
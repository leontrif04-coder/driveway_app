# Smart Parking Assistant - Project Architecture

## Project Overview
A full-stack smart parking assistant application with a FastAPI backend and React Native (Expo) frontend. The application helps users find parking spots with reviews and scoring.

## Technology Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React Native with Expo, TypeScript
- **Maps**: react-native-maps
- **Location**: expo-location

---

## Project Structure

```
smart-assistant-park/
├── backend/                    # FastAPI backend application
│   ├── app/                    # Main application package
│   │   ├── __init__.py         # Package initialization
│   │   ├── config.py           # Application configuration
│   │   ├── routers/            # API route handlers
│   │   │   ├── __init__.py     # Routers package init
│   │   │   ├── reviews.py       # Review-related endpoints
│   │   │   └── spots.py        # Parking spot endpoints
│   │   ├── schemas/            # Pydantic data models
│   │   │   ├── __init__.py     # Schemas package init
│   │   │   ├── parking.py      # Parking spot schemas
│   │   │   └── review.py       # Review schemas
│   │   ├── services/           # Business logic services
│   │   │   ├── __init__.py     # Services package init
│   │   │   ├── geo.py          # Geospatial/geographic services
│   │   │   └── scoring.py      # Parking spot scoring logic
│   │   └── utils/              # Utility functions
│   │       ├── __init__.py     # Utils package init
│   │       └── review_parser.py # Review parsing utilities
│   ├── main.py                 # FastAPI application entry point
│   └── requirements.txt        # Python dependencies
│
└── frontend/                   # React Native frontend application
    ├── app.json                # Expo configuration
    ├── App.tsx                 # Main application component
    ├── package.json            # Node.js dependencies and scripts
    ├── tsconfig.json           # TypeScript configuration
    └── src/                    # Source code directory
        ├── app/                # Application-level code
        │   └── navigation/     # Navigation setup
        │       └── RootNavigator.tsx  # Root navigation component
        ├── components/         # Reusable UI components
        │   ├── DestinationSearchBar.tsx  # Search bar for destinations
        │   ├── ParkingFilterBar.tsx     # Filter controls for parking
        │   └── ParkingSpotMarker.tsx    # Map marker for parking spots
        ├── config/             # Configuration files
        │   └── env.ts          # Environment variables
        ├── domain/             # Domain models/types
        │   └── models.ts       # TypeScript type definitions
        ├── hooks/              # Custom React hooks
        │   ├── useParkingSpots.ts  # Hook for parking spots data
        │   └── useUserLocation.ts  # Hook for user location
        ├── screens/            # Screen components
        │   └── MapScreen/      # Map screen directory
        │       └── MapScreen.tsx  # Main map screen component
        ├── services/           # API service layer
        │   ├── parkingService.ts  # Parking spots API client
        │   └── reviewService.ts   # Reviews API client
        └── utils/              # Utility functions
            └── filters.ts      # Filtering utilities
```

---

## Backend Architecture

### Entry Point
- **`backend/main.py`**: FastAPI application initialization
  - Sets up CORS middleware
  - Registers routers for spots and reviews endpoints
  - API prefix: `/api/v1/`

### API Routes (`backend/app/routers/`)
- **`spots.py`**: Parking spot endpoints
  - Handles parking spot CRUD operations
  - Route prefix: `/api/v1/spots`
- **`reviews.py`**: Review endpoints
  - Handles review operations for parking spots
  - Route prefix: `/api/v1/spots` (nested under spots)

### Data Schemas (`backend/app/schemas/`)
- **`parking.py`**: Pydantic models for parking spots
- **`review.py`**: Pydantic models for reviews

### Business Logic (`backend/app/services/`)
- **`geo.py`**: Geospatial calculations and location services
- **`scoring.py`**: Parking spot scoring algorithm

### Utilities (`backend/app/utils/`)
- **`review_parser.py`**: Review text parsing and processing

### Configuration
- **`backend/app/config.py`**: Application settings and configuration

---

## Frontend Architecture

### Entry Point
- **`frontend/App.tsx`**: Root component that renders MapScreen

### Navigation (`frontend/src/app/navigation/`)
- **`RootNavigator.tsx`**: Main navigation setup and routing

### Components (`frontend/src/components/`)
- **`DestinationSearchBar.tsx`**: Search input for destination addresses
- **`ParkingFilterBar.tsx`**: UI controls for filtering parking spots
- **`ParkingSpotMarker.tsx`**: Custom marker component for map display

### Screens (`frontend/src/screens/`)
- **`MapScreen/MapScreen.tsx`**: Main map view with parking spots

### Custom Hooks (`frontend/src/hooks/`)
- **`useParkingSpots.ts`**: Manages parking spots data fetching and state
- **`useUserLocation.ts`**: Manages user location tracking

### Services (`frontend/src/services/`)
- **`parkingService.ts`**: API client for parking spots endpoints
- **`reviewService.ts`**: API client for reviews endpoints

### Domain Models (`frontend/src/domain/`)
- **`models.ts`**: TypeScript interfaces and types for domain entities

### Configuration (`frontend/src/config/`)
- **`env.ts`**: Environment variables and API endpoints

### Utilities (`frontend/src/utils/`)
- **`filters.ts`**: Helper functions for filtering parking data

---

## Key Dependencies

### Backend (`requirements.txt`)
- `fastapi>=0.104.0` - Web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `pydantic>=1.10.0,<2.0.0` - Data validation

### Frontend (`package.json`)
- `expo ~51.0.0` - React Native framework
- `react 18.2.0` - UI library
- `react-native 0.74.0` - Mobile framework
- `react-native-maps 1.18.0` - Map component
- `expo-location ~17.0.1` - Location services
- `@react-native-picker/picker 2.7.5` - Picker component
- `typescript ^5.1.3` - Type checking

---

## API Structure

### Base URL
- Backend API: `/api/v1/`

### Endpoints
- **Spots**: `/api/v1/spots/*`
- **Reviews**: `/api/v1/spots/*` (nested under spots)

---

## File Count Summary

### Backend
- Python files: 11
- Configuration files: 2 (requirements.txt, config.py)

### Frontend
- TypeScript/TSX files: 13
- Configuration files: 3 (package.json, tsconfig.json, app.json)

---

## Architecture Patterns

1. **Backend**: 
   - FastAPI with router-based architecture
   - Separation of concerns: routers, schemas, services, utils
   - Pydantic for data validation

2. **Frontend**:
   - React Native with Expo
   - Component-based architecture
   - Custom hooks for state management
   - Service layer for API communication
   - Domain models for type safety

---

## Notes
- CORS is currently set to allow all origins (`*`) - should be tightened in production
- Frontend uses TypeScript for type safety
- Backend uses Pydantic for request/response validation
- Map-based UI with location services integration

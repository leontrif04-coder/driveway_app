# Smart Parking Assistant - Complete Codebase Overview

## Executive Summary

The Smart Parking Assistant is a full-stack geolocation-based mobile application that helps users discover, evaluate, and review parking spots in real-time. The system consists of a FastAPI Python backend with machine learning recommendation capabilities and a React Native (Expo) frontend with real-time map-based visualization. The application uses geospatial calculations, user-generated reviews, ML-powered recommendations, and WebSocket-based real-time occupancy updates.

---

## 1. Technology Stack

### Backend
- **Framework**: FastAPI 0.104.0+ (Python 3.x)
- **ASGI Server**: Uvicorn
- **Data Validation**: Pydantic 1.10.0-2.0.0
- **Machine Learning**: scikit-learn 1.3.0+, pandas 2.0.0+, numpy 1.24.0+
- **Storage**: In-memory dictionaries (development/prototype - designed for PostgreSQL migration)
- **WebSocket**: Native FastAPI WebSocket support

### Frontend
- **Framework**: React Native with Expo ~51.0.0
- **Language**: TypeScript 5.1.3+
- **Maps**: react-native-maps 1.18.0
- **Location Services**: expo-location ~17.0.1
- **React**: 18.2.0
- **React Native**: 0.74.0
- **Testing**: Jest, React Native Testing Library, MSW (Mock Service Worker)

### Testing & Development
- **Backend Testing**: pytest, pytest-asyncio, pytest-cov, httpx
- **Frontend Testing**: Jest, jest-expo, @testing-library/react-native, MSW

---

## 2. Project Structure

```
driveway_app/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py           # Application configuration (Pydantic settings)
│   │   ├── storage.py           # In-memory data store (singleton pattern)
│   │   ├── websocket_manager.py # WebSocket connection management
│   │   ├── routers/             # API route handlers
│   │   │   ├── spots.py         # Parking spot CRUD endpoints
│   │   │   ├── reviews.py       # Review management endpoints
│   │   │   ├── occupancy.py     # Real-time occupancy tracking
│   │   │   ├── recommendations.py # ML-powered recommendations
│   │   │   └── websocket.py     # WebSocket endpoint handler
│   │   ├── schemas/             # Pydantic data models
│   │   │   ├── parking.py       # ParkingSpot, ParkingSpotCreate schemas
│   │   │   ├── review.py        # Review, ReviewCreate schemas
│   │   │   ├── occupancy.py     # OccupancyEvent, SpotAvailabilityUpdate
│   │   │   └── user_behavior.py # UserParkingEvent, UserPreferences
│   │   ├── services/            # Business logic layer
│   │   │   ├── geo.py           # Geospatial calculations (haversine distance)
│   │   │   ├── scoring.py       # Review-based scoring algorithms
│   │   │   ├── availability_predictor.py # Occupancy prediction
│   │   │   └── ml/              # Machine learning services
│   │   │       ├── ab_testing.py # A/B testing framework
│   │   │       ├── feature_engineering.py # Feature extraction for ML
│   │   │       └── recommender.py # ML recommendation engine
│   │   └── utils/               # Utility functions
│   │       └── review_parser.py # Text analysis for meter status detection
│   ├── main.py                  # FastAPI application entry point
│   ├── train_model.py           # ML model training script
│   ├── requirements.txt         # Production dependencies
│   ├── requirements-dev.txt     # Development dependencies
│   ├── pytest.ini               # Pytest configuration
│   └── tests/                   # Backend test suite
│       ├── conftest.py          # Shared pytest fixtures
│       ├── test_geo.py          # Geospatial unit tests
│       ├── test_scoring.py      # Scoring algorithm tests
│       ├── test_review_parser.py # Review parser tests
│       ├── test_spots_api.py    # Spots API integration tests
│       └── test_reviews_api.py  # Reviews API integration tests
│
├── frontend/                    # React Native frontend application
│   ├── App.tsx                  # Root application component
│   ├── app.json                 # Expo configuration
│   ├── package.json             # Node.js dependencies and scripts
│   ├── tsconfig.json            # TypeScript configuration
│   ├── jest.config.js           # Jest testing configuration
│   └── src/
│       ├── app/
│       │   └── navigation/
│       │       └── RootNavigator.tsx # Navigation setup
│       ├── components/          # Reusable UI components
│       │   ├── DestinationSearchBar.tsx
│       │   ├── ParkingFilterBar.tsx
│       │   └── ParkingSpotMarker.tsx
│       ├── screens/             # Screen components
│       │   └── MapScreen/
│       │       └── MapScreen.tsx # Main map view
│       ├── hooks/               # Custom React hooks
│       │   ├── useParkingSpots.ts # Parking spots data management
│       │   └── useUserLocation.ts # User location tracking
│       ├── services/            # API client layer
│       │   ├── parkingService.ts # HTTP client for spots
│       │   ├── reviewService.ts  # HTTP client for reviews
│       │   └── websocketService.ts # WebSocket client
│       ├── domain/              # Domain models/types
│       │   └── models.ts        # TypeScript interfaces
│       ├── config/              # Configuration
│       │   └── env.ts           # Environment variables (API_BASE_URL)
│       ├── utils/               # Utility functions
│       │   └── filters.ts       # Client-side filtering
│       └── tests/               # Frontend test suite
│           ├── setupTests.ts
│           ├── __mocks__/
│           │   └── react-native-maps.ts
│           ├── mocks/
│           │   ├── server.ts    # MSW server setup
│           │   └── handlers.ts  # API request handlers
│           ├── components/      # Component tests
│           ├── hooks/           # Hook tests
│           ├── services/        # Service tests
│           └── integration/     # Integration tests
│
├── agents/                      # AI agent prompts/contexts
│   ├── backend-architect.md
│   └── frontend-expert.md
│
├── prompts/                     # Development prompt templates
│   ├── backend-endpoint.md
│   ├── bug-fix.md
│   ├── database-migration.md
│   ├── frontend-component.md
│   ├── geospatial-expert.md
│   └── test-suite.md
│
├── skills/                      # Expert skill definitions
│   ├── ml-recommender-expert.md
│   └── testing-expert.md
│
├── workflows/                   # Development workflows
│   └── feature-development.md
│
├── examples/                    # Code examples
│   └── complete-feature-example.md
│
├── README.md                    # Project documentation
├── ARCHITECTURE.md              # Detailed architecture documentation
├── ML_SYSTEM.md                 # ML recommendation system docs
├── TESTING.md                   # Testing guide
└── cursor-rules.md              # Cursor IDE rules
```

---

## 3. Backend Architecture

### 3.1 Application Entry Point (`backend/main.py`)

- **FastAPI App Initialization**: Creates FastAPI application instance
- **CORS Configuration**: Currently allows all origins (`*`) - should be restricted in production
- **Router Registration**:
  - Spots: `/api/v1/spots`
  - Reviews: `/api/v1/spots` (nested)
  - Occupancy: `/api/v1/spots` (nested)
  - Recommendations: `/api/v1/recommendations`
  - WebSocket: `/api/v1/ws`
- **Startup Event**: Calls `seed_data()` to populate 10 fake parking spots (NYC area: 40.7128, -74.0060)

### 3.2 Data Storage Layer (`backend/app/storage.py`)

**Pattern**: In-memory storage using Python dictionaries (singleton pattern)

**Storage Structures**:
- `_spots: Dict[str, ParkingSpot]` - All parking spots by ID
- `_reviews: Dict[str, List[Review]]` - Reviews by spot_id
- `_occupancy_history: Dict[str, List[OccupancyEvent]]` - Occupancy events by spot_id
- `_user_parking_history: Dict[str, List[UserParkingEvent]]` - User events by user_id
- `_user_preferences: Dict[str, UserPreferences]` - User preferences by user_id

**Key Functions**:
- `get_all_spots()`, `get_spot(id)`, `create_spot()`, `update_spot()`
- `get_reviews(spot_id)`, `add_review(spot_id, review)`
- `add_occupancy_event()`, `get_occupancy_history()`, `clear_occupancy_history()`
- `add_user_parking_event()`, `get_user_parking_history()`, `get_all_user_parking_events()`
- `save_user_preferences()`, `get_user_preferences()`
- `seed_data()` - Initializes 10 fake parking spots on startup

**Design Decision**: In-memory storage is suitable for development/prototyping. Production should use PostgreSQL with PostGIS for geospatial queries.

### 3.3 API Routes (`backend/app/routers/`)

#### Spots Router (`spots.py`)
**Base Path**: `/api/v1/spots`

**Endpoints**:
1. **GET `/api/v1/spots?lat={lat}&lng={lng}&radius_m={radius}&limit={limit}`**
   - Find parking spots near a geographic point
   - Uses haversine distance calculation
   - Filters spots within radius, computes scores, sorts by distance
   - Returns `List[ParkingSpot]` with computed `score` and `distance_to_user_m`

2. **GET `/api/v1/spots/{spot_id}`**
   - Retrieve specific parking spot by ID
   - Returns `ParkingSpot` with computed `score`
   - 404 if spot not found

3. **POST `/api/v1/spots`**
   - Create new parking spot (dev/testing)
   - Request: `ParkingSpotCreate` schema
   - Returns: `ParkingSpot` with generated ID and score
   - ID format: `spot-{8-char-hex}`

#### Reviews Router (`reviews.py`)
**Base Path**: `/api/v1/spots`

**Endpoints**:
1. **GET `/api/v1/spots/{spot_id}/reviews`**
   - Get all reviews for a parking spot
   - Returns: `List[Review]`
   - 404 if spot not found

2. **POST `/api/v1/spots/{spot_id}/reviews`**
   - Add review and update spot metadata
   - Request: `ReviewCreate` (`rating: int, text: str`)
   - Side Effects:
     - Increments `review_count`
     - Recomputes `score` using logarithmic scaling
     - Updates `meter_status` via text analysis
     - Updates `meter_status_confidence`
     - Updates `last_updated_at`
   - Returns: Created `Review`
   - ID format: `rev-{8-char-hex}`

#### Occupancy Router (`occupancy.py`)
**Base Path**: `/api/v1/spots`

**Endpoints**:
- Tracks real-time parking spot occupancy
- Updates availability status
- Broadcasts updates via WebSocket

#### Recommendations Router (`recommendations.py`)
**Base Path**: `/api/v1/recommendations`

**Endpoints**:
1. **GET `/api/v1/recommendations?lat={lat}&lng={lng}&user_id={id}&destination_type={type}&radius_m={radius}&limit={limit}`**
   - ML-powered personalized recommendations
   - Uses Gradient Boosting Regressor model
   - Returns ranked spots with match scores and reasons

#### WebSocket Router (`websocket.py`)
**Endpoint**: `/api/v1/ws`

- Real-time availability updates
- Connection management via `ConnectionManager`
- Supports geographic subscription bounds

### 3.4 Data Models (`backend/app/schemas/`)

#### ParkingSpot Schema
```python
{
    id: str
    latitude: float
    longitude: float
    street_name: str
    max_duration_minutes: Optional[int]
    price_per_hour_usd: Optional[float]
    safety_score: float              # 0-100
    tourism_density: float           # 0-100
    meter_status: MeterStatus        # "working" | "broken" | "unknown"
    meter_status_confidence: float   # 0-1
    distance_to_user_m: Optional[float]
    distance_to_destination_m: Optional[float]
    review_count: int
    last_updated_at: datetime
    composite_score: Optional[float]  # Legacy composite scoring
    score: Optional[float]            # Review-based score (0-100)
    is_occupied?: bool                # Real-time availability
    estimated_availability_time?: datetime
}
```

#### Review Schema
```python
{
    id: str
    spot_id: str
    rating: int              # 1-5 scale
    text: str               # Used for meter status parsing
    created_at: datetime
}
```

#### UserParkingEvent Schema
Tracks user behavior for ML training:
```python
{
    user_id: str
    spot_id: str
    timestamp: datetime
    time_of_day: str
    day_of_week: int
    duration_minutes: Optional[int]
    price_paid_usd: Optional[float]
    final_destination_type: Optional[str]
    user_rating: Optional[int]
    safety_score_at_time: float
    distance_to_destination_m: Optional[float]
}
```

### 3.5 Business Logic Services (`backend/app/services/`)

#### Geospatial Service (`geo.py`)
- **Function**: `haversine_distance_m(a: Tuple[float, float], b: Tuple[float, float]) -> float`
- **Algorithm**: Haversine formula for great-circle distance
- **Earth Radius**: 6,371,000 meters
- **Use Cases**: Radius filtering, distance sorting, proximity calculations

#### Scoring Service (`scoring.py`)
- **Function**: `compute_spot_score(spot_id: str) -> float`
- **Algorithm**: 
  ```
  score = avg_rating * (1 + log10(review_count + 1)) * 20
  score = min(score, 100.0)  # Cap at 100
  ```
- **Rationale**: Logarithmic scaling prevents gaming, rewards reliability
- **Advanced Scoring**: `score_and_filter_spots()` - composite scoring with safety, tourism, time of day, meter status

#### Review Parser (`utils/review_parser.py`)
- **Function**: `parse_meter_status(reviews: List[str]) -> tuple[MeterStatus, float]`
- **Algorithm**: Keyword matching (case-insensitive)
  - **Broken indicators**: "broken", "doesn't work", "out of order", "error"
  - **Working indicators**: "works", "working fine", "no issues", "all good"
- **Status Determination**: Majority rule
- **Confidence**: `max(broken_count, working_count) / total_matches`

#### ML Services (`services/ml/`)
- **Feature Engineering**: Extracts 28 features per spot-user combination
  - User features (price tolerance, duration preferences, time preferences)
  - Contextual features (hour, day, destination type)
  - Spot features (price, safety, distance, reviews, meter status)
- **Recommender**: Gradient Boosting Regressor (scikit-learn)
- **A/B Testing**: Framework for comparing algorithms (distance-only vs ML-powered)
- **Cold Start**: Handles new users with default features and fallback ranking

#### Availability Predictor (`availability_predictor.py`)
- Predicts parking spot availability
- Uses occupancy history patterns
- Estimates availability times

### 3.6 WebSocket Manager (`websocket_manager.py`)

**Class**: `ConnectionManager`
- **Active Connections**: `Set[WebSocket]`
- **Client Subscriptions**: Geographic bounds for filtering updates
- **Methods**:
  - `connect()`: Accept new connection
  - `disconnect()`: Remove connection
  - `set_subscription()`: Set geographic bounds for client
  - `broadcast_update()`: Broadcast availability updates to subscribed clients
  - `send_personal_message()`: Send message to specific client
- **Message Format**: JSON with `type` and `data` fields

---

## 4. Frontend Architecture

### 4.1 Application Structure

**Entry Point**: `App.tsx` - Renders `MapScreen`

### 4.2 Screens

#### MapScreen (`screens/MapScreen/MapScreen.tsx`)
- Main map view with parking spots
- Uses `react-native-maps` for map rendering
- Displays markers for parking spots
- Integrates user location tracking
- Handles map region changes to fetch spots

### 4.3 Components

#### DestinationSearchBar (`components/DestinationSearchBar.tsx`)
- Search input for destination addresses
- Geocoding integration (future)

#### ParkingFilterBar (`components/ParkingFilterBar.tsx`)
- UI controls for filtering parking spots
- Filters: safety score, walking distance, tourism bias, time of day

#### ParkingSpotMarker (`components/ParkingSpotMarker.tsx`)
- Custom marker component for map display
- Color-coded based on spot status/score
- Callout with spot information

### 4.4 Custom Hooks

#### useParkingSpots (`hooks/useParkingSpots.ts`)
- Manages parking spots state
- Fetches spots for map region
- Handles filtering and data transformation
- Loading and error states

#### useUserLocation (`hooks/useUserLocation.ts`)
- Manages user location tracking
- Handles geolocation permissions
- Updates location on map movement
- Error handling for location services

### 4.5 Services Layer

#### parkingService (`services/parkingService.ts`)
- HTTP client for spots endpoints
- `fetchSpots(region, filters)` - Fetches spots with filters
- Maps backend response to frontend models (camelCase conversion)

#### reviewService (`services/reviewService.ts`)
- HTTP client for reviews endpoints
- Submit reviews, fetch reviews for spots

#### websocketService (`services/websocketService.ts`)
- WebSocket client for real-time updates
- Connects to `/api/v1/ws`
- Handles availability updates
- Manages connection lifecycle

### 4.6 Domain Models (`domain/models.ts`)

**TypeScript Interfaces**:
```typescript
interface ParkingSpot {
    id: string
    latitude: number
    longitude: number
    streetName: string
    maxDurationMinutes?: number
    pricePerHourUsd?: number
    safetyScore: number      // 0-100
    tourismDensity: number   // 0-100
    meterStatus: MeterStatus // "working" | "broken" | "unknown"
    meterStatusConfidence: number
    distanceToUserM?: number
    distanceToDestinationM?: number
    reviewCount: number
    lastUpdatedAt: string
    compositeScore?: number
    isOccupied?: boolean
    estimatedAvailabilityTime?: string
}

interface ParkingFilters {
    minSafetyScore?: number
    maxWalkingDistanceM?: number
    tourismBias?: "low" | "medium" | "high"
    timeOfDay?: "morning" | "afternoon" | "evening" | "night"
}
```

### 4.7 Configuration

#### Environment (`config/env.ts`)
- `API_BASE_URL`: Backend API URL
  - iOS simulator: `http://127.0.0.1:8000`
  - Android emulator: `http://10.0.2.2:8000`
  - Configurable via `EXPO_PUBLIC_API_BASE_URL`

---

## 5. Key Features & Functionality

### 5.1 Core Features

1. **Map-Based Parking Discovery**
   - Interactive map with parking spot markers
   - Real-time user location tracking
   - Region-based spot fetching

2. **Geospatial Search**
   - Radius-based filtering
   - Distance calculations using haversine formula
   - Proximity sorting

3. **Review System**
   - User-generated reviews (1-5 star ratings)
   - Text reviews with meter status parsing
   - Review-based scoring algorithm

4. **Scoring & Ranking**
   - Review-based scores with logarithmic scaling
   - Composite scoring (safety, tourism, time, meter status)
   - ML-powered personalized recommendations

5. **Real-Time Updates**
   - WebSocket-based availability updates
   - Occupancy tracking
   - Estimated availability times

6. **Filtering & Search**
   - Safety score filtering
   - Walking distance limits
   - Tourism density preferences
   - Time-of-day adjustments

7. **Machine Learning Recommendations**
   - Personalized spot recommendations
   - Gradient Boosting Regressor model
   - 28 features per recommendation
   - A/B testing framework

### 5.2 Data Flow

```
User Interaction (Map Movement)
    ↓
Frontend Hook (useParkingSpots)
    ↓
Service Layer (parkingService)
    ↓
HTTP Request (GET /api/v1/spots)
    ↓
Backend Router (spots.py)
    ↓
Storage Layer (get_all_spots)
    ↓
Geospatial Filtering (geo.py)
    ↓
Score Computation (scoring.py)
    ↓
Response (JSON List[ParkingSpot])
    ↓
Frontend State Update
    ↓
Map Re-render (Markers)
```

### 5.3 Review Submission Flow

```
User Submits Review
    ↓
Frontend Service (reviewService)
    ↓
HTTP POST /api/v1/spots/{spot_id}/reviews
    ↓
Reviews Router
    ↓
Create Review Object
    ↓
Storage.add_review()
    ↓
Get All Reviews for Spot
    ↓
compute_spot_score() → Scoring Service
    ↓
parse_meter_status() → Review Parser
    ↓
Update Spot Metadata
    ↓
Storage.update_spot()
    ↓
Return Review Object
```

---

## 6. API Specifications

### 6.1 Base URL
- Development: `http://127.0.0.1:8000` (iOS) or `http://10.0.2.2:8000` (Android)
- Production: Configurable via environment variable

### 6.2 API Version
- All endpoints prefixed with `/api/v1/`

### 6.3 Request/Response Format
- Content-Type: `application/json`
- All requests and responses use JSON

### 6.4 Authentication
- **Current State**: None (development)
- **Production**: Should implement JWT-based authentication

### 6.5 CORS
- **Current State**: Allows all origins (`*`)
- **Production**: Should whitelist specific origins

---

## 7. Algorithms & Business Logic

### 7.1 Haversine Distance Calculation

**Formula**: `R * 2 * atan2(√h, √(1-h))`

Where:
- `h = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)`
- `R = 6,371,000 meters` (Earth radius)

**Use Cases**:
- Finding spots within radius
- Calculating walking distance
- Sorting by proximity

### 7.2 Review-Based Scoring

**Formula**:
```
avg_rating = sum(ratings) / count
review_bonus = log10(review_count + 1)
score = avg_rating * (1 + review_bonus) * 20
score = min(score, 100.0)
```

**Examples**:
- 5.0 rating, 1 review: `5.0 * (1 + log10(2)) * 20 = 130.1 → 100.0`
- 4.5 rating, 10 reviews: `4.5 * (1 + log10(11)) * 20 = 183.69 → 100.0`
- 4.0 rating, 100 reviews: `4.0 * (1 + log10(101)) * 20 = 240.32 → 100.0`

**Rationale**: Logarithmic scaling prevents single high ratings from dominating, rewards spots with more reviews.

### 7.3 Composite Scoring (Legacy)

**Factors**:
- Base safety score
- Tourism density (with bias weight)
- Time of day adjustment
- Meter status penalty (broken meters)

**Formula**:
```
composite = base_score + (tourism * tour_weight) + time_component + meter_penalty
```

### 7.4 Meter Status Detection

**Algorithm**:
1. Scan review texts for keywords (case-insensitive)
2. Count "broken" vs "working" indicators
3. Determine status: majority rule
4. Calculate confidence: `max(counts) / total_matches`

**Keywords**:
- Broken: "broken", "doesn't work", "out of order", "error"
- Working: "works", "working fine", "no issues", "all good"

---

## 8. Machine Learning System

### 8.1 Model Architecture

- **Algorithm**: Gradient Boosting Regressor (scikit-learn)
- **Hyperparameters**:
  - `n_estimators`: 100
  - `max_depth`: 5
  - `learning_rate`: 0.1
- **Output**: Probability score (0-1) converted to 0-100 scale

### 8.2 Feature Engineering

**28 Features** (per spot-user combination):

**User Features** (from parking history):
- `avg_price_tolerance`
- `preferred_duration_minutes`
- `morning_preference`, `afternoon_preference`, `evening_preference`
- `avg_safety_score`
- `avg_walking_distance_m`
- `has_history` (cold start flag)

**Contextual Features**:
- `hour_of_day` (normalized 0-1)
- `is_weekend`
- `day_of_week` (normalized 0-1)
- `destination_type_*` (one-hot encoded)

**Spot Features**:
- `price_per_hour` (normalized)
- `safety_score` (normalized 0-1)
- `tourism_density` (normalized 0-1)
- `distance_to_user_km`
- `review_score` (normalized 0-1)
- `meter_status_working`, `meter_status_broken` (binary)
- `is_occupied`

### 8.3 Training Pipeline

1. Generate/collect training data from user parking events
2. Extract features for each training sample
3. Train on 80% of data, validate on 20%
4. 5-fold cross-validation
5. Save model as pickle file (`models/parking_recommender.pkl`)

**Training Script**: `backend/train_model.py`

### 8.4 Cold Start Problem

**Handling**:
1. Default features based on general population
2. User preference-based features (if set)
3. Fallback to distance-based ranking
4. Gradual learning as user history accumulates

### 8.5 A/B Testing

**Frameworks**:
- Distance-only ranking
- ML-powered ranking
- Hybrid approach

**Assignment**: Consistent user assignment based on `user_id` hash

**Metrics**: Conversion rate (spots selected / spots recommended)

---

## 9. Testing Strategy

### 9.1 Backend Testing (pytest)

**Test Structure**:
- Unit tests for services, utilities
- Integration tests for API endpoints
- Fixtures in `conftest.py`

**Coverage Goal**: >80%

**Test Files**:
- `test_geo.py`: Haversine distance calculations, edge cases
- `test_scoring.py`: Score computation with various review counts
- `test_review_parser.py`: Meter status detection, keyword matching
- `test_spots_api.py`: API endpoints, radius filtering, sorting
- `test_reviews_api.py`: Review creation, score updates, meter status updates

**Running Tests**:
```bash
cd backend
pytest                    # Run all tests
pytest --cov=app          # With coverage
pytest tests/test_geo.py  # Specific file
```

### 9.2 Frontend Testing (Jest)

**Test Structure**:
- Component tests (rendering, interactions)
- Hook tests (state management, side effects)
- Service tests (API mocking)
- Integration tests (user flows)

**Coverage Goal**: >70%

**Test Files**:
- Component tests: `ParkingSpotMarker`, `ParkingFilterBar`, `DestinationSearchBar`
- Hook tests: `useParkingSpots`, `useUserLocation`
- Service tests: `parkingService`
- Integration tests: `MapScreen`

**API Mocking**: Mock Service Worker (MSW)

**Running Tests**:
```bash
cd frontend
npm test                  # Run all tests
npm run test:watch        # Watch mode
npm run test:coverage     # With coverage
```

---

## 10. Configuration & Environment

### 10.1 Backend Configuration

**File**: `backend/app/config.py`
- Pydantic BaseSettings for configuration
- Loads from `.env` file
- Settings: `app_name`, `debug`

**Dependencies**:
- `requirements.txt`: Production dependencies
- `requirements-dev.txt`: Development dependencies (pytest, coverage tools)

**Pytest Configuration**: `pytest.ini`
- Test discovery patterns
- Coverage thresholds
- Markers for test categorization

### 10.2 Frontend Configuration

**Expo Config**: `app.json`
- Expo SDK version
- App metadata

**TypeScript Config**: `tsconfig.json`
- Compiler options
- Module resolution

**Jest Config**: `jest.config.js`
- Test environment (jest-expo)
- Transform patterns
- Coverage thresholds
- Mock setup

**Environment Variables**: `src/config/env.ts`
- `API_BASE_URL`: Backend API endpoint
- Configurable via `EXPO_PUBLIC_API_BASE_URL`

---

## 11. Development Workflow

### 11.1 Setup

**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements-dev.txt
```

**Frontend**:
```bash
cd frontend
npm install
```

### 11.2 Running Development Servers

**Backend**:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd frontend
npm start  # or `expo start`
```

### 11.3 Testing

**Backend**:
```bash
cd backend
pytest --cov=app --cov-report=html
```

**Frontend**:
```bash
cd frontend
npm test
```

### 11.4 ML Model Training

```bash
cd backend
python train_model.py
```

---

## 12. Key Design Decisions & Rationale

### 12.1 In-Memory Storage

**Why**: Rapid prototyping, simplicity, easy testing

**Trade-off**: Data lost on restart, not production-ready

**Migration Path**: Designed for easy migration to PostgreSQL with PostGIS

### 12.2 FastAPI

**Why**: High performance, async support, automatic OpenAPI docs, Pydantic integration

**Benefits**: Type safety, validation, modern Python features

### 12.3 React Native + Expo

**Why**: Cross-platform (iOS/Android), rapid development, built-in tooling

**Benefits**: Single codebase, hot reloading, map integration

### 12.4 Haversine Formula

**Why**: Accurate for short distances, simple, no external dependencies

**Trade-off**: Assumes perfect sphere (good enough for most use cases)

### 12.5 Logarithmic Scoring

**Why**: Prevents gaming, rewards reliability, smooth scaling

**Trade-off**: May underweight new spots with few reviews

### 12.6 ML Gradient Boosting

**Why**: Handles non-linear relationships, feature importance, good accuracy

**Trade-off**: Requires training data, longer training time than simpler models

---

## 13. Future Enhancements & Considerations

### 13.1 Storage Migration

**Current**: In-memory dictionaries  
**Future**: PostgreSQL with PostGIS

**Benefits**:
- Persistent data
- Geospatial indexing (faster radius queries)
- Complex SQL queries
- Transaction support

### 13.2 Authentication & Authorization

**Current**: None  
**Future**: JWT-based authentication

**Features**:
- User accounts
- User-specific reviews
- Favorite spots
- Rate limiting

### 13.3 Real-Time Features

**Current**: WebSocket for availability  
**Future**:
- Real-time spot creation
- Live occupancy updates
- Push notifications
- Collaborative filtering

### 13.4 Advanced ML Features

**Future Enhancements**:
- Deep learning models
- Online learning from feedback
- Multi-objective optimization
- Time-based price predictions
- Multi-destination optimization

### 13.5 Performance Optimizations

**Future**:
- Database indexing on coordinates
- Redis caching for frequently accessed spots
- Pagination for large result sets
- Background jobs for score recalculation
- CDN for static assets

### 13.6 Production Readiness

**Security**:
- Restrict CORS origins
- Input sanitization
- Rate limiting
- HTTPS enforcement
- API key management

**Monitoring**:
- Structured logging
- Error tracking (Sentry)
- Metrics (Prometheus/Grafana)
- Health check endpoints

**Deployment**:
- Docker containers
- CI/CD pipelines
- Environment-specific configs
- Database migrations

---

## 14. Key Files Reference

### Backend Critical Files
- `backend/main.py`: Application entry point
- `backend/app/storage.py`: Data storage layer
- `backend/app/routers/spots.py`: Spots API endpoints
- `backend/app/routers/reviews.py`: Reviews API endpoints
- `backend/app/services/geo.py`: Geospatial calculations
- `backend/app/services/scoring.py`: Scoring algorithms
- `backend/app/services/ml/recommender.py`: ML recommendation engine
- `backend/app/websocket_manager.py`: WebSocket connection management

### Frontend Critical Files
- `frontend/App.tsx`: Root component
- `frontend/src/screens/MapScreen/MapScreen.tsx`: Main map view
- `frontend/src/hooks/useParkingSpots.ts`: Parking spots data management
- `frontend/src/services/parkingService.ts`: API client
- `frontend/src/domain/models.ts`: TypeScript type definitions

### Configuration Files
- `backend/requirements.txt`: Backend dependencies
- `frontend/package.json`: Frontend dependencies
- `backend/pytest.ini`: Pytest configuration
- `frontend/jest.config.js`: Jest configuration
- `cursor-rules.md`: Cursor IDE development rules

### Documentation Files
- `README.md`: Project overview
- `ARCHITECTURE.md`: Detailed architecture documentation
- `ML_SYSTEM.md`: ML recommendation system documentation
- `TESTING.md`: Testing guide

---

## 15. Common Development Patterns

### 15.1 Adding a New API Endpoint

1. Define Pydantic schema in `app/schemas/`
2. Create route handler in appropriate router file
3. Implement business logic in service layer
4. Add integration tests in `tests/`
5. Update API documentation

### 15.2 Adding a New Frontend Component

1. Create component in `src/components/`
2. Define TypeScript interfaces in `domain/models.ts`
3. Add service methods if API calls needed
4. Write component tests
5. Integrate into screen/hook

### 15.3 Adding ML Features

1. Extract features in `services/ml/feature_engineering.py`
2. Update training script `train_model.py`
3. Add inference logic in `services/ml/recommender.py`
4. Add endpoint in `routers/recommendations.py`
5. Update frontend to consume recommendations

### 15.4 Testing New Features

**Backend**:
1. Write unit tests for services/utils
2. Write integration tests for API endpoints
3. Run `pytest --cov=app` to check coverage

**Frontend**:
1. Write component/hook tests
2. Mock API calls with MSW
3. Write integration tests for user flows
4. Run `npm test` to check coverage

---

## 16. Known Limitations & Technical Debt

### 16.1 Current Limitations

1. **Storage**: In-memory only (data lost on restart)
2. **Authentication**: None (all endpoints public)
3. **CORS**: Allows all origins (security risk)
4. **Rate Limiting**: None (vulnerable to abuse)
5. **Input Validation**: Basic Pydantic validation only
6. **Error Handling**: Basic HTTP exceptions
7. **Logging**: Basic Python logging
8. **Monitoring**: None

### 16.2 Technical Debt

1. **Database Migration**: Need to implement PostgreSQL migration
2. **API Versioning**: No versioning strategy yet
3. **Documentation**: Some endpoints lack OpenAPI docs
4. **Type Safety**: Some areas use `Any` types
5. **Error Messages**: Generic error messages
6. **Testing Coverage**: Some edge cases not covered

---

## 17. Dependencies Summary

### Backend Production Dependencies
- `fastapi>=0.104.0`
- `uvicorn[standard]>=0.24.0`
- `pydantic>=1.10.0,<2.0.0`
- `scikit-learn>=1.3.0`
- `pandas>=2.0.0`
- `numpy>=1.24.0`

### Backend Development Dependencies
- `pytest`
- `pytest-asyncio`
- `pytest-cov`
- `httpx`

### Frontend Dependencies
- `expo ~51.0.0`
- `react 18.2.0`
- `react-native 0.74.0`
- `react-native-maps 1.18.0`
- `expo-location ~17.0.1`
- `@react-native-picker/picker 2.7.5`
- `typescript ^5.1.3`

### Frontend Dev Dependencies
- `jest ^29.7.0`
- `jest-expo ~51.0.0`
- `@testing-library/react-native ^12.0.0`
- `msw ^2.0.0`

---

## 18. Quick Reference

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/spots` | List spots near location |
| GET | `/api/v1/spots/{id}` | Get specific spot |
| POST | `/api/v1/spots` | Create new spot |
| GET | `/api/v1/spots/{id}/reviews` | Get spot reviews |
| POST | `/api/v1/spots/{id}/reviews` | Add review |
| GET | `/api/v1/recommendations` | Get ML recommendations |
| WS | `/api/v1/ws` | WebSocket connection |

### Key Commands

**Backend**:
```bash
uvicorn main:app --reload    # Run server
pytest                       # Run tests
python train_model.py        # Train ML model
```

**Frontend**:
```bash
npm start                    # Start Expo
npm test                     # Run tests
```

### Key Algorithms

- **Haversine Distance**: Geospatial distance calculation
- **Logarithmic Scoring**: `avg_rating * (1 + log10(review_count + 1)) * 20`
- **Meter Status Detection**: Keyword-based text analysis
- **ML Recommendation**: Gradient Boosting Regressor with 28 features

---

## 19. Support & Resources

### Documentation
- `ARCHITECTURE.md`: Detailed system architecture
- `ML_SYSTEM.md`: ML recommendation system details
- `TESTING.md`: Testing guide and examples

### Development Resources
- `agents/`: AI agent prompts for development
- `prompts/`: Development prompt templates
- `workflows/`: Development workflow guides
- `examples/`: Code examples

---

This overview provides a comprehensive understanding of the Smart Parking Assistant codebase, its architecture, features, and development patterns. Use this as a reference when working with Claude AI or other development assistants.


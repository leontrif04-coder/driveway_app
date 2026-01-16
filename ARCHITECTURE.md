# Smart Parking Assistant - System Architecture Documentation

## Executive Summary

The Smart Parking Assistant is a full-stack geolocation-based application designed to help users discover, evaluate, and review parking spots. The system consists of a FastAPI REST backend and a React Native mobile frontend, utilizing geospatial calculations and user-generated reviews to provide intelligent parking recommendations.

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Native Frontend                     │
│  (Expo ~51.0.0, TypeScript, react-native-maps, expo-location)  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Screens    │  │  Components  │  │    Hooks     │          │
│  │  MapScreen   │  │  SearchBar   │  │ useParking   │          │
│  │              │  │  FilterBar   │  │ useLocation  │          │
│  │              │  │   Markers    │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                 │                 │                    │
│         └─────────────────┴─────────────────┘                    │
│                            │                                     │
│                   ┌────────▼────────┐                            │
│                   │   Services      │                            │
│                   │  parkingService │                            │
│                   │  reviewService  │                            │
│                   └────────┬────────┘                            │
└────────────────────────────┼─────────────────────────────────────┘
                             │ HTTP/REST
                             │ JSON
┌────────────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend                                │
│              (Python 3.x, FastAPI 0.104+)                        │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Routers    │  │   Services   │  │   Storage    │          │
│  │    spots     │  │     geo      │  │  (In-Memory) │          │
│  │   reviews    │  │   scoring    │  │   _spots     │          │
│  │              │  │              │  │  _reviews    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                 │                 │                    │
│         └─────────────────┴─────────────────┘                    │
│                            │                                     │
│                   ┌────────▼────────┐                            │
│                   │    Schemas      │                            │
│                   │  Pydantic Models│                            │
│                   └─────────────────┘                            │
└───────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

**Backend:**
- **Framework**: FastAPI 0.104.0+
- **Language**: Python 3.x
- **ASGI Server**: Uvicorn
- **Validation**: Pydantic 1.10.0-2.0.0
- **Storage**: In-memory dictionaries (development/prototype)

**Frontend:**
- **Framework**: React Native with Expo ~51.0.0
- **Language**: TypeScript 5.1.3+
- **Maps**: react-native-maps 1.18.0
- **Location**: expo-location ~17.0.1
- **React**: 18.2.0
- **React Native**: 0.74.0

---

## 2. Backend Architecture

### 2.1 Application Structure

The backend follows a layered architecture pattern with clear separation of concerns:

```
backend/
├── main.py                    # Application entry point, CORS config, startup events
├── app/
│   ├── storage.py             # In-memory data store (singleton pattern)
│   ├── config.py              # Application configuration
│   ├── routers/               # HTTP endpoint handlers
│   │   ├── spots.py           # Parking spot CRUD operations
│   │   └── reviews.py         # Review management
│   ├── schemas/               # Pydantic data models (request/response validation)
│   │   ├── parking.py         # ParkingSpot, ParkingSpotCreate
│   │   └── review.py          # Review, ReviewCreate
│   ├── services/              # Business logic layer
│   │   ├── geo.py             # Geospatial calculations
│   │   └── scoring.py         # Ranking and scoring algorithms
│   └── utils/                 # Utility functions
│       └── review_parser.py   # Text analysis for meter status
```

### 2.2 Data Storage Layer (`app/storage.py`)

**Pattern**: In-memory storage using Python dictionaries (singleton pattern)

**Storage Structure:**
```python
_spots: Dict[str, ParkingSpot]          # spot_id -> ParkingSpot
_reviews: Dict[str, List[Review]]       # spot_id -> List[Review]
```

**Key Functions:**
- `get_all_spots() -> List[ParkingSpot]`: Retrieve all parking spots
- `get_spot(spot_id: str) -> Optional[ParkingSpot]`: Get single spot
- `create_spot(spot: ParkingSpot) -> ParkingSpot`: Create new spot
- `update_spot(spot: ParkingSpot) -> ParkingSpot`: Update existing spot
- `get_reviews(spot_id: str) -> List[Review]`: Get reviews for a spot
- `add_review(spot_id: str, review: Review) -> Review`: Add review to spot
- `seed_data()`: Initialize 10 fake parking spots on startup

**Design Decision**: In-memory storage is suitable for development/prototyping. For production, this should be replaced with a persistent database (PostgreSQL, MongoDB, etc.).

### 2.3 API Layer (`app/routers/`)

#### 2.3.1 Spots Router (`routers/spots.py`)

**Base Path**: `/api/v1/spots`

**Endpoints:**

1. **GET `/api/v1/spots?lat={lat}&lng={lng}&radius_m={radius}&limit={limit}`**
   - **Purpose**: Find parking spots near a geographic point
   - **Parameters**:
     - `lat` (required, float): Center latitude
     - `lng` (required, float): Center longitude
     - `radius_m` (optional, float, default: 1000): Search radius in meters
     - `limit` (optional, int, default: 50): Maximum results
   - **Algorithm**:
     1. Retrieve all spots from storage
     2. Calculate haversine distance from center point to each spot
     3. Filter spots within radius
     4. Compute score for each spot (from reviews)
     5. Sort by distance (ascending)
     6. Apply limit
   - **Returns**: `List[ParkingSpot]` with computed `score` and `distance_to_user_m`

2. **GET `/api/v1/spots/{spot_id}`**
   - **Purpose**: Retrieve a specific parking spot by ID
   - **Returns**: `ParkingSpot` with computed `score`
   - **Errors**: 404 if spot not found

3. **POST `/api/v1/spots`**
   - **Purpose**: Create a new parking spot (development/testing)
   - **Request Body**: `ParkingSpotCreate` schema
   - **Returns**: `ParkingSpot` with generated ID and computed `score`
   - **ID Generation**: `spot-{8-char-hex}`

#### 2.3.2 Reviews Router (`routers/reviews.py`)

**Base Path**: `/api/v1/spots`

**Endpoints:**

1. **GET `/api/v1/spots/{spot_id}/reviews`**
   - **Purpose**: Get all reviews for a parking spot
   - **Returns**: `List[Review]`
   - **Errors**: 404 if spot not found

2. **POST `/api/v1/spots/{spot_id}/reviews`**
   - **Purpose**: Add a review and update spot metadata
   - **Request Body**: `ReviewCreate` schema (`rating: int, text: str`)
   - **Side Effects**:
     1. Creates and stores review
     2. Updates spot's `review_count`
     3. Recomputes spot's `score` using scoring algorithm
     4. Updates `meter_status` and `meter_status_confidence` via text analysis
     5. Updates `last_updated_at` timestamp
   - **Returns**: Created `Review` object
   - **Errors**: 404 if spot not found
   - **ID Generation**: `rev-{8-char-hex}`

### 2.4 Data Models (`app/schemas/`)

#### 2.4.1 ParkingSpot Schema

```python
class ParkingSpot(BaseModel):
    # Identity
    id: str
    
    # Location
    latitude: float
    longitude: float
    street_name: str
    
    # Pricing & Duration
    max_duration_minutes: Optional[int]
    price_per_hour_usd: Optional[float]
    
    # Attributes
    safety_score: float              # 0-100 scale
    tourism_density: float           # 0-100 scale
    meter_status: MeterStatus        # "working" | "broken" | "unknown"
    meter_status_confidence: float   # 0-1 scale
    
    # Computed distances (added at runtime)
    distance_to_user_m: Optional[float]
    distance_to_destination_m: Optional[float]
    
    # Review metadata
    review_count: int
    last_updated_at: datetime
    
    # Computed scores
    composite_score: Optional[float]  # Legacy composite scoring
    score: Optional[float]            # Review-based score (0-100)
```

**Key Fields:**
- `score`: Computed from reviews using logarithmic scaling (see scoring algorithm)
- `composite_score`: Legacy field for advanced filtering (not currently used in main endpoint)
- `meter_status_confidence`: Confidence level of meter status determination

#### 2.4.2 Review Schema

```python
class Review(BaseModel):
    id: str
    spot_id: str
    rating: int              # 1-5 scale
    text: str               # Review text (used for meter status parsing)
    created_at: datetime

class ReviewCreate(BaseModel):
    rating: int
    text: str
```

### 2.5 Business Logic Layer (`app/services/`)

#### 2.5.1 Geospatial Service (`services/geo.py`)

**Haversine Distance Calculation:**

```python
def haversine_distance_m(a: Tuple[float, float], b: Tuple[float, float]) -> float
```

**Algorithm:**
- Uses haversine formula to calculate great-circle distance between two points
- Earth radius: 6,371,000 meters
- Returns distance in meters
- Formula: `R * 2 * atan2(√h, √(1-h))` where `h = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)`

**Use Cases:**
- Finding spots within radius of user location
- Calculating walking distance to destination
- Sorting results by proximity

#### 2.5.2 Scoring Service (`services/scoring.py`)

**Review-Based Score Calculation:**

```python
def compute_spot_score(spot_id: str) -> float
```

**Algorithm:**
1. Retrieve all reviews for the spot
2. Calculate average rating: `avg_rating = sum(ratings) / count`
3. Apply logarithmic scaling: `score = avg_rating * (1 + log10(review_count + 1))`
4. Normalize to 0-100 scale: `score * 20` (assuming 1-5 rating scale)
5. Cap at 100: `min(score, 100.0)`

**Rationale:**
- Logarithmic scaling prevents spots with few reviews from dominating
- Rewards spots with more reviews (indicating reliability)
- Example: 5.0 rating with 10 reviews scores higher than 5.0 with 1 review

**Advanced Scoring (Legacy - for future use):**

The service also includes `score_and_filter_spots()` which calculates a composite score considering:
- Base safety score
- Tourism density (with bias weights)
- Time of day adjustments
- Meter status penalties

### 2.6 Utility Layer (`app/utils/`)

#### 2.6.1 Review Parser (`utils/review_parser.py`)

**Meter Status Detection:**

```python
def parse_meter_status(reviews: List[str]) -> tuple[MeterStatus, float]
```

**Algorithm:**
1. Scans review texts for keywords:
   - **Broken indicators**: "broken", "doesn't work", "out of order", "error", etc.
   - **Working indicators**: "works", "working fine", "no issues", "all good"
2. Counts occurrences of each category
3. Determines status:
   - If broken > working → "broken"
   - If working > broken → "working"
   - If no matches → "unknown"
4. Calculates confidence: `max(broken, working) / total_matches`

**Use Case:**
- Automatically updates meter status when new reviews are added
- Provides confidence metric for status reliability

### 2.7 Application Entry Point (`main.py`)

**Configuration:**
- CORS: Enabled for all origins (`*`) - suitable for Expo development
- API Version: `/api/v1/`
- Router Registration:
  - Spots router: `/api/v1/spots`
  - Reviews router: `/api/v1/spots` (nested)

**Startup Event:**
- Calls `seed_data()` to populate 10 fake parking spots
- Default location: NYC (40.7128, -74.0060)
- Spots distributed in ~1km radius

---

## 3. Frontend Architecture

### 3.1 Application Structure

```
frontend/
├── App.tsx                       # Root component
├── src/
│   ├── app/navigation/          # Navigation setup
│   │   └── RootNavigator.tsx
│   ├── screens/                 # Screen components
│   │   └── MapScreen/
│   │       └── MapScreen.tsx    # Main map view
│   ├── components/              # Reusable UI components
│   │   ├── DestinationSearchBar.tsx
│   │   ├── ParkingFilterBar.tsx
│   │   └── ParkingSpotMarker.tsx
│   ├── hooks/                   # Custom React hooks
│   │   ├── useParkingSpots.ts   # Parking data management
│   │   └── useUserLocation.ts   # Location tracking
│   ├── services/                # API client layer
│   │   ├── parkingService.ts    # HTTP client for spots
│   │   └── reviewService.ts     # HTTP client for reviews
│   ├── domain/                  # Type definitions
│   │   └── models.ts            # TypeScript interfaces
│   ├── config/                  # Configuration
│   │   └── env.ts               # Environment variables
│   └── utils/                   # Utility functions
│       └── filters.ts           # Client-side filtering
```

### 3.2 Architecture Patterns

**1. Component-Based Architecture**
- React Native components organized by responsibility
- Separation of presentational and container components

**2. Custom Hooks Pattern**
- `useParkingSpots`: Manages parking spots state, fetching, filtering
- `useUserLocation`: Handles geolocation permissions and tracking

**3. Service Layer Pattern**
- Abstracted HTTP client layer
- Centralized API endpoint configuration
- Error handling and response transformation

**4. Domain-Driven Design**
- TypeScript interfaces in `domain/models.ts` represent core entities
- Type safety across application layers

### 3.3 Data Flow

```
User Interaction
    │
    ▼
Components (UI Layer)
    │
    ▼
Custom Hooks (State Management)
    │
    ▼
Service Layer (API Clients)
    │
    │ HTTP/REST
    ▼
Backend API
    │
    ▼
Response Transformation
    │
    ▼
State Update (React State)
    │
    ▼
UI Re-render
```

---

## 4. API Specifications

### 4.1 API Design Principles

- **RESTful**: Resource-based URLs, HTTP methods for actions
- **Versioned**: `/api/v1/` prefix
- **JSON**: All requests and responses use JSON
- **Pydantic Validation**: Request/response validation on backend
- **Type Safety**: TypeScript types on frontend

### 4.2 Request/Response Examples

#### GET /api/v1/spots?lat=40.7128&lng=-74.0060&radius_m=1000&limit=10

**Request:**
```
Query Parameters:
  lat: 40.7128
  lng: -74.0060
  radius_m: 1000
  limit: 10
```

**Response:**
```json
[
  {
    "id": "spot-1",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "street_name": "Broadway",
    "max_duration_minutes": 120,
    "price_per_hour_usd": 4.0,
    "safety_score": 80.0,
    "tourism_density": 70.0,
    "meter_status": "working",
    "meter_status_confidence": 0.9,
    "distance_to_user_m": 0.0,
    "review_count": 0,
    "last_updated_at": "2024-01-01T12:00:00Z",
    "score": 0.0
  }
]
```

#### POST /api/v1/spots/{spot_id}/reviews

**Request:**
```json
{
  "rating": 5,
  "text": "Great spot! Meter works fine, easy to park."
}
```

**Response:**
```json
{
  "id": "rev-abc12345",
  "spot_id": "spot-1",
  "rating": 5,
  "text": "Great spot! Meter works fine, easy to park.",
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Side Effects:**
- Spot's `review_count` incremented
- Spot's `score` recalculated
- Spot's `meter_status` potentially updated to "working"
- Spot's `meter_status_confidence` recalculated

---

## 5. Key Algorithms and Business Logic

### 5.1 Spot Ranking Algorithm

**Primary Ranking (GET /spots endpoint):**
- Sorted by distance (ascending)
- No composite scoring applied

**Future Enhancement:**
- Could use `composite_score` for multi-factor ranking
- Factors: safety, tourism density, time of day, meter status

### 5.2 Review-Based Scoring

**Formula:**
```
score = avg_rating * (1 + log10(review_count + 1)) * 20
score = min(score, 100.0)  // Cap at 100
```

**Examples:**
- 5.0 rating, 1 review: `5.0 * (1 + log10(2)) * 20 = 5.0 * 1.301 * 20 = 130.1 → 100.0`
- 4.5 rating, 10 reviews: `4.5 * (1 + log10(11)) * 20 = 4.5 * 2.041 * 20 = 183.69 → 100.0`
- 4.0 rating, 100 reviews: `4.0 * (1 + log10(101)) * 20 = 4.0 * 3.004 * 20 = 240.32 → 100.0`

### 5.3 Meter Status Detection

**Keyword Matching:**
- Case-insensitive text matching
- Multiple keywords per category
- Confidence based on match ratio

**Status Determination:**
- Majority rule: More "broken" keywords → "broken", more "working" keywords → "working"
- No matches → "unknown"
- Confidence: `count_of_winning_category / total_matches`

---

## 6. Data Flow Diagrams

### 6.1 Adding a Review Flow

```
User submits review
    │
    ▼
POST /api/v1/spots/{spot_id}/reviews
    │
    ▼
Reviews Router (reviews.py)
    │
    ├─→ Validate spot exists
    │
    ├─→ Create Review object
    │
    ├─→ Storage.add_review()
    │
    ├─→ Get all reviews for spot
    │
    ├─→ compute_spot_score() ──→ Scoring Service
    │                              │
    │                              └─→ Calculate avg_rating
    │                              └─→ Apply log scaling
    │                              └─→ Normalize to 0-100
    │
    ├─→ parse_meter_status() ──→ Review Parser
    │                              │
    │                              └─→ Keyword matching
    │                              └─→ Status determination
    │
    ├─→ Update spot metadata
    │   ├─ review_count
    │   ├─ score
    │   ├─ meter_status
    │   ├─ meter_status_confidence
    │   └─ last_updated_at
    │
    └─→ Storage.update_spot()
    │
    └─→ Return Review object
```

### 6.2 Finding Nearby Spots Flow

```
User requests nearby spots
    │
    ▼
GET /api/v1/spots?lat=X&lng=Y&radius_m=Z
    │
    ▼
Spots Router (spots.py)
    │
    ├─→ Storage.get_all_spots()
    │
    ├─→ For each spot:
    │   ├─→ haversine_distance_m(center, spot_location)
    │   ├─→ Filter if distance <= radius_m
    │   └─→ Add distance_to_user_m
    │
    ├─→ For each filtered spot:
    │   └─→ compute_spot_score() ──→ Scoring Service
    │
    ├─→ Sort by distance (ascending)
    │
    ├─→ Apply limit
    │
    └─→ Return List[ParkingSpot]
```

---

## 7. Design Patterns and Principles

### 7.1 Patterns Used

1. **Layered Architecture**
   - Routers (Presentation) → Services (Business Logic) → Storage (Data Access)
   - Clear separation of concerns

2. **Repository Pattern (Implicit)**
   - Storage module acts as repository abstraction
   - Easy to swap in-memory storage for database

3. **Service Layer Pattern**
   - Business logic encapsulated in services
   - Reusable across different routes

4. **Schema Validation Pattern**
   - Pydantic models for request/response validation
   - Type safety and automatic documentation

5. **Singleton Pattern (Storage)**
   - Single instance of storage dictionaries
   - Global state management

### 7.2 SOLID Principles

- **Single Responsibility**: Each module has one clear purpose
- **Open/Closed**: Services extensible without modifying routers
- **Dependency Inversion**: Routers depend on service abstractions

### 7.3 Code Organization Principles

- **Separation of Concerns**: UI, business logic, data access separated
- **DRY (Don't Repeat Yourself)**: Reusable services and utilities
- **Type Safety**: TypeScript + Pydantic ensure type correctness

---

## 8. Key Technical Decisions

### 8.1 Why In-Memory Storage?

- **Development Speed**: Rapid prototyping without database setup
- **Simplicity**: No migration scripts, ORM configuration
- **Testing**: Easy to reset state between tests

**Trade-off**: Data is lost on server restart. Production requires persistent storage.

### 8.2 Why FastAPI?

- **Performance**: High-performance async framework
- **Type Safety**: Pydantic integration
- **Auto Documentation**: OpenAPI/Swagger generation
- **Modern Python**: Async/await support

### 8.3 Why React Native + Expo?

- **Cross-Platform**: Single codebase for iOS and Android
- **Rapid Development**: Expo provides development tools
- **Map Integration**: react-native-maps for geospatial features
- **Type Safety**: TypeScript prevents runtime errors

### 8.4 Why Haversine Formula?

- **Accuracy**: Provides great-circle distance (most accurate for short distances)
- **Simplicity**: Single formula, no external dependencies
- **Performance**: Computationally efficient

**Trade-off**: Assumes perfect sphere. For extreme precision, consider Vincenty's formula.

### 8.5 Why Logarithmic Scoring?

- **Prevents Gaming**: Single high rating doesn't dominate
- **Rewards Reliability**: More reviews indicate real-world usage
- **Smooth Scaling**: Logarithm provides smooth increase in weight

---

## 9. Future Enhancements and Scalability

### 9.1 Storage Migration

**Current**: In-memory dictionaries  
**Future**: PostgreSQL with PostGIS extension

**Benefits:**
- Persistent data
- Geospatial indexing for faster queries
- SQL queries for complex filtering
- Transaction support

### 9.2 Caching Strategy

- Redis cache for frequently accessed spots
- Cache invalidation on review updates
- Geospatial indexing for radius queries

### 9.3 Authentication & Authorization

- User authentication (JWT tokens)
- User-specific reviews and favorites
- Rate limiting on review submissions

### 9.4 Advanced Features

- Real-time updates (WebSockets)
- Parking availability prediction
- Price optimization recommendations
- Multi-factor ranking (safety, price, distance, reviews)

### 9.5 Performance Optimizations

- Database indexing on coordinates
- Pagination for large result sets
- Background jobs for score recalculation
- CDN for static assets

---

## 10. Testing Strategy

### 10.1 Backend Testing

**Unit Tests:**
- Geospatial calculations (haversine)
- Scoring algorithms
- Review parsing logic

**Integration Tests:**
- API endpoint testing
- End-to-end request/response flows
- Storage operations

**Test Tools:**
- pytest
- httpx (async HTTP client)
- pytest-asyncio

### 10.2 Frontend Testing

**Unit Tests:**
- Component rendering
- Custom hooks logic
- Utility functions

**Integration Tests:**
- API service layer
- User interaction flows

**Test Tools:**
- Jest
- React Native Testing Library
- MSW (Mock Service Worker) for API mocking

---

## 11. Deployment Considerations

### 11.1 Backend Deployment

- **Containerization**: Docker container
- **Server**: Uvicorn with multiple workers
- **Environment Variables**: API keys, database URLs
- **CORS**: Restrict origins in production

### 11.2 Frontend Deployment

- **Expo Build**: EAS Build for native apps
- **App Stores**: Apple App Store, Google Play Store
- **OTA Updates**: Expo Updates for JavaScript changes
- **Environment Config**: Different API endpoints for dev/staging/prod

### 11.3 Monitoring and Logging

- **Logging**: Structured logging (JSON format)
- **Error Tracking**: Sentry or similar
- **Metrics**: Prometheus + Grafana
- **Health Checks**: `/health` endpoint

---

## 12. Security Considerations

### 12.1 Current State

- CORS enabled for all origins (development)
- No authentication/authorization
- No input sanitization for review text
- No rate limiting

### 12.2 Production Requirements

- **CORS**: Whitelist specific origins
- **Authentication**: JWT-based user authentication
- **Input Validation**: Sanitize review text, prevent XSS
- **Rate Limiting**: Prevent spam reviews
- **HTTPS**: Enforce SSL/TLS
- **API Keys**: Rate limiting per API key
- **SQL Injection**: Use parameterized queries (when migrating to DB)

---

## 13. Glossary

- **Haversine Formula**: Mathematical formula to calculate distance between two points on a sphere
- **Composite Score**: Multi-factor score combining safety, tourism, time, meter status
- **Review Score**: Score computed from user ratings and review count
- **Meter Status**: Classification of parking meter functionality (working/broken/unknown)
- **Radius Query**: Geospatial query finding points within a specified distance
- **Geospatial Indexing**: Database optimization for location-based queries

---

## 14. Summary

The Smart Parking Assistant is a well-structured full-stack application following modern software architecture principles. The backend uses a layered architecture with clear separation between API routes, business logic, and data storage. The frontend follows React Native best practices with component-based architecture and custom hooks for state management.

**Key Strengths:**
- Clean code organization
- Type safety (TypeScript + Pydantic)
- Extensible architecture
- Clear separation of concerns

**Areas for Enhancement:**
- Persistent storage migration
- Authentication/authorization
- Production-ready security measures
- Comprehensive test coverage
- Performance optimizations

This architecture document provides a comprehensive understanding of the system's design, enabling effective development, maintenance, and future enhancements.


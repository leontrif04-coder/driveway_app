# backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import spots, reviews, occupancy, recommendations
from app.routers.websocket import websocket_endpoint
from app.database.config import lifespan_db_manager

# Use lifespan context manager for database initialization
@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager combining database and other startup tasks."""
    async with lifespan_db_manager(app):
        # Additional startup tasks can go here
        yield

app = FastAPI(
    title="Smart Parking API",
    version="0.1.0",
    lifespan=lifespan
)

origins = ["*"]  # tighten in production

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(spots.router, prefix="/api/v1/spots", tags=["spots"])
app.include_router(reviews.router, prefix="/api/v1/spots", tags=["reviews"])
app.include_router(occupancy.router, prefix="/api/v1/spots", tags=["occupancy"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["recommendations"])

# WebSocket endpoint (registered directly, not via router)
app.websocket("/api/v1/ws")(websocket_endpoint)

# Note: Database initialization and migrations are handled by lifespan_db_manager
# Seed data is now in the database migrations (002_seed_data.sql)



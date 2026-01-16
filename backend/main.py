# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import spots, reviews, occupancy, recommendations
from app.routers.websocket import websocket_endpoint
from app.storage import seed_data

app = FastAPI(title="Smart Parking API", version="0.1.0")

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

@app.on_event("startup")
async def startup_event():
    """Seed fake data on startup."""
    seed_data()



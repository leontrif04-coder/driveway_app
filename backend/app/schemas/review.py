# backend/app/schemas/review.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class Review(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    spot_id: str
    rating: int
    text: str
    created_at: datetime

class ReviewCreate(BaseModel):
  rating: int
  text: str



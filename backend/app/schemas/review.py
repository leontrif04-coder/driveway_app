# backend/app/schemas/review.py
from pydantic import BaseModel
from datetime import datetime

class Review(BaseModel):
  id: str
  spot_id: str
  rating: int
  text: str
  created_at: datetime

  class Config:
    orm_mode = True

class ReviewCreate(BaseModel):
  rating: int
  text: str



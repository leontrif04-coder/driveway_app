# backend/app/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Smart Parking API"
    debug: bool = True

    class Config:
        env_file = ".env"

settings = Settings()


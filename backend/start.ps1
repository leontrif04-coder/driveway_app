# Startup script for Smart Parking Assistant Backend
# Sets environment variables and starts the server

Write-Host "Setting up environment variables..." -ForegroundColor Green

# Database Configuration
$env:DATABASE_URL="postgresql://parking_app:dev_password_123@localhost:5432/parking_assistant"
$env:DATABASE_POOL_SIZE="5"
$env:DATABASE_MAX_OVERFLOW="10"
$env:RUN_MIGRATIONS="false"
$env:DB_ECHO="false"

Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "Database URL: $env:DATABASE_URL" -ForegroundColor Yellow

# Start the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000


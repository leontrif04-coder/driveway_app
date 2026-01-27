# Fix: Database User "parking_app" Does Not Exist

## Problem

The error shows:
```
FATAL: role "parking_app" não existe
```

This means the PostgreSQL user/role "parking_app" doesn't exist in your database.

## Solution

### Option 1: Run the PowerShell Setup Script (Recommended)

```powershell
cd backend
.\setup_database.ps1
```

This will:
- Create the `parking_app` user
- Grant all necessary permissions
- Enable PostGIS extension

### Option 2: Manual Setup via Docker

Connect to your PostgreSQL container and create the user:

```powershell
# Connect to PostgreSQL as superuser
docker exec -it parking-db psql -U postgres

# Then run these SQL commands:
CREATE USER parking_app WITH PASSWORD 'dev_password_123';
GRANT ALL PRIVILEGES ON DATABASE parking_assistant TO parking_app;

# Connect to the database
\c parking_assistant

# Grant schema privileges
GRANT ALL ON SCHEMA public TO parking_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO parking_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO parking_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO parking_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO parking_app;

# Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

# Exit
\q
```

### Option 3: One-Line Command

```powershell
docker exec -i parking-db psql -U postgres -c "CREATE USER parking_app WITH PASSWORD 'dev_password_123';" && docker exec -i parking-db psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE parking_assistant TO parking_app;"
```

## Verify the Fix

After creating the user, test the connection:

```powershell
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should now see:
```
[DEBUG] Step 3: ✓ Connection established
[DEBUG] Step 4: ✓ Encoding set to UTF8
[DEBUG] Step 5: ✓ Query successful!
✓ All connection tests passed!
Database connection successful
```

## Why This Happened

Your Docker container was created with the environment variables:
- `POSTGRES_USER=parking_app`
- `POSTGRES_PASSWORD=dev_password_123`
- `POSTGRES_DB=parking_assistant`

However, if the container was created before these were set, or if the database was initialized differently, the user might not exist.

The error message was in Portuguese because your Docker container's locale is set to Portuguese, which caused the encoding issue when psycopg2 tried to decode it.


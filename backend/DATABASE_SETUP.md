# Database Setup Guide

## Docker Container Connection

Your PostgreSQL + PostGIS database is running in a Docker container with the following configuration:

- **Container Name**: `parking-db`
- **Host**: `localhost` (or `127.0.0.1`)
- **Port**: `5432`
- **Database**: `parking_assistant`
- **Username**: `parking_app`
- **Password**: `dev_password_123`
- **PostGIS Version**: 3.3.4

## Step 1: Create `.env` File

Create a file named `.env` in the `backend/` directory with the following content:

```env
# Database Configuration
# PostgreSQL + PostGIS connection string for Docker container
DATABASE_URL=postgresql://parking_app:dev_password_123@localhost:5432/parking_assistant

# Connection Pool Settings
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Run migrations on startup (set to "true" to enable automatic migrations)
RUN_MIGRATIONS=false

# Database echo (set to "true" to log all SQL queries for debugging)
DB_ECHO=false
```

**Important**: Make sure the `.env` file is saved with UTF-8 encoding to avoid encoding errors.

## Step 2: Verify Docker Container is Running

Check that your database container is running:

```powershell
docker ps | findstr parking-db
```

Or:

```powershell
docker ps -a --filter "name=parking-db"
```

## Step 3: Test Database Connection

You can test the connection manually:

```powershell
# Using psql (if installed)
psql -h localhost -p 5432 -U parking_app -d parking_assistant

# Or using Docker exec
docker exec -it parking-db psql -U parking_app -d parking_assistant
```

## Step 4: Run Database Migrations

### Option A: Automatic (on startup)

Set `RUN_MIGRATIONS=true` in your `.env` file, then start the app:

```powershell
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option B: Manual (recommended for first time)

Run migrations manually using Python:

```powershell
cd backend
python -c "from app.database.config import run_migrations; run_migrations()"
```

### Option C: Using psql directly

Connect to the database and run the SQL files:

```powershell
# Connect to database
docker exec -i parking-db psql -U parking_app -d parking_assistant < app/database/migrations/001_initial_schema.sql
docker exec -i parking-db psql -U parking_app -d parking_assistant < app/database/migrations/002_seed_data.sql
```

## Step 5: Verify PostGIS Extension

After running migrations, verify PostGIS is enabled:

```powershell
docker exec -it parking-db psql -U parking_app -d parking_assistant -c "SELECT PostGIS_Version();"
```

You should see output like:
```
            postgis_version
---------------------------------
 3.3 USE_GEOS=1 USE_PROJ=1 ...
```

## Troubleshooting

### Connection Refused

If you get "connection refused" errors:

1. **Check container is running**:
   ```powershell
   docker ps | findstr parking-db
   ```

2. **Check port mapping**:
   ```powershell
   docker port parking-db
   ```
   Should show: `5432/tcp -> 0.0.0.0:5432`

3. **Restart container if needed**:
   ```powershell
   docker restart parking-db
   ```

### Encoding Errors

If you see UTF-8 encoding errors:

1. Make sure `.env` file is saved with UTF-8 encoding (not UTF-8 with BOM)
2. In VS Code: File → Save with Encoding → UTF-8
3. In Notepad++: Encoding → Convert to UTF-8 → Save

### Database Doesn't Exist

If the database doesn't exist, create it:

```powershell
docker exec -it parking-db psql -U parking_app -c "CREATE DATABASE parking_assistant;"
```

### PostGIS Extension Not Found

Enable PostGIS extension:

```powershell
docker exec -it parking-db psql -U parking_app -d parking_assistant -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

## Connection String Format

The connection string format is:
```
postgresql://[username]:[password]@[host]:[port]/[database]
```

For your setup:
```
postgresql://parking_app:dev_password_123@localhost:5432/parking_assistant
```

## Next Steps

Once the database is connected:

1. ✅ Start the FastAPI server: `python -m uvicorn main:app --reload`
2. ✅ Verify connection in startup logs
3. ✅ Test API endpoints that use the database
4. ✅ Check that geospatial queries work correctly


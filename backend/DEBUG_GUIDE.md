# Debugging Database Connection Issues

## Enable Debug Mode

To see detailed logs about where the connection is failing, set the `DB_DEBUG` environment variable:

```powershell
$env:DB_DEBUG="true"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

This will show:
- When settings are being loaded
- The database URL being used (password masked)
- Each step of the connection process
- Full stack traces for any errors

## Run Debug Script

For a comprehensive diagnostic, run:

```powershell
python debug_db_connection.py
```

This will test:
1. Environment variables
2. .env file reading with different encodings
3. Settings loading
4. Engine creation
5. Database connection

## Common Issues and Solutions

### Issue 1: Encoding Error in .env File

**Symptom**: `'utf-8' codec can't decode byte 0xe3`

**Solution**: Run the encoding fix script:
```powershell
python fix_env_encoding.py
```

### Issue 2: Database Not Running

**Symptom**: Connection timeout or "connection refused"

**Check**:
```powershell
docker ps | findstr parking-db
```

**Fix**: Start the container:
```powershell
docker start parking-db
```

### Issue 3: Wrong Connection String

**Symptom**: Authentication failed or database doesn't exist

**Check**: Verify your DATABASE_URL matches Docker container:
- User: `parking_app`
- Password: `dev_password_123`
- Database: `parking_assistant`
- Host: `localhost`
- Port: `5432`

### Issue 4: PostGIS Not Enabled

**Symptom**: PostGIS functions fail

**Fix**:
```powershell
docker exec -it parking-db psql -U parking_app -d parking_assistant -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

## Viewing Full Error Details

If you need to see the complete error traceback, the debug mode will show it. You can also check the uvicorn logs for more details.

## Next Steps

1. Run `python debug_db_connection.py` to identify the exact issue
2. Enable `DB_DEBUG=true` to see detailed logs
3. Fix the identified issue using the solutions above


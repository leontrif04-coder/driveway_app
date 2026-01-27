# Fix UTF-8 Encoding Error

## Quick Fix: Use Environment Variables Directly

Instead of using the `.env` file (which has encoding issues), set the environment variable directly in PowerShell:

### Option 1: Set for Current Session

```powershell
$env:DATABASE_URL="postgresql://parking_app:dev_password_123@localhost:5432/parking_assistant"
$env:DATABASE_POOL_SIZE="5"
$env:DATABASE_MAX_OVERFLOW="10"
$env:RUN_MIGRATIONS="false"
$env:DB_ECHO="false"

# Then start the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Fix the .env File Encoding

1. **Delete the existing .env file** (it has encoding issues)

2. **Create a new .env file** with UTF-8 encoding:

   In PowerShell:
   ```powershell
   @"
   DATABASE_URL=postgresql://parking_app:dev_password_123@localhost:5432/parking_assistant
   DATABASE_POOL_SIZE=5
   DATABASE_MAX_OVERFLOW=10
   RUN_MIGRATIONS=false
   DB_ECHO=false
   "@ | Out-File -FilePath .env -Encoding utf8 -NoNewline
   ```

   Or manually:
   - Open Notepad
   - Paste the content:
     ```
     DATABASE_URL=postgresql://parking_app:dev_password_123@localhost:5432/parking_assistant
     DATABASE_POOL_SIZE=5
     DATABASE_MAX_OVERFLOW=10
     RUN_MIGRATIONS=false
     DB_ECHO=false
     ```
   - Save As → Choose "UTF-8" encoding (NOT UTF-8 with BOM)
   - Save as `.env` in the `backend/` directory

3. **In VS Code**:
   - Open the .env file
   - Click the encoding indicator in the bottom right
   - Select "Save with Encoding" → "UTF-8"

### Option 3: Use a Startup Script

Create `backend/start.ps1`:

```powershell
# Set environment variables
$env:DATABASE_URL="postgresql://parking_app:dev_password_123@localhost:5432/parking_assistant"
$env:DATABASE_POOL_SIZE="5"
$env:DATABASE_MAX_OVERFLOW="10"
$env:RUN_MIGRATIONS="false"
$env:DB_ECHO="false"

# Start the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then run:
```powershell
.\start.ps1
```

## Why This Happens

The error `'utf-8' codec can't decode byte 0xe3` means:
- The .env file was saved with a different encoding (likely Windows-1252 or UTF-8 with BOM)
- Byte 0xe3 is part of a multi-byte UTF-8 sequence that's been corrupted
- pydantic-settings tries to read it as UTF-8 and fails

## Verification

After setting the environment variable, test the connection:

```powershell
python test_db_connection.py
```

You should see:
```
✓ Database connection successful!
```


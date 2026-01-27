# Solution Plan: Fix UTF-8 Encoding Error

## Problem Analysis

The error `'utf-8' codec can't decode byte 0xe3 in position 89` is happening when:
1. **pydantic-settings** tries to read the `.env` file
2. The `.env` file has incorrect encoding (likely Windows-1252 or UTF-8 with BOM)
3. Even with environment variables set, the error persists because pydantic-settings still tries to read `.env` first

## Root Cause

The `DatabaseSettings` class from pydantic-settings automatically tries to read `.env` file on initialization, and if it has encoding issues, it fails before we can use environment variables.

## Solution Strategy

### Step 1: Fix .env File Encoding (Permanent Fix)
Run the provided script to fix the encoding:
```powershell
cd backend
python fix_env_encoding.py
```

This will:
- Read your existing .env file with encoding fallbacks
- Create a backup
- Rewrite it with proper UTF-8 encoding

### Step 2: Make DatabaseSettings Skip .env on Error
Update the code to skip .env file if it has encoding issues and use environment variables instead.

### Step 3: Add Better Error Handling
Improve error handling in database connection to catch encoding errors from psycopg2.

## Implementation Steps

1. ✅ Created `fix_env_encoding.py` script
2. ✅ Updated error handling in `check_db_connection()`
3. ⏳ Update `DatabaseSettings` to handle encoding errors gracefully
4. ⏳ Test the fix

## Quick Fix Commands

```powershell
# Option 1: Fix .env file encoding (RECOMMENDED)
cd backend
python fix_env_encoding.py

# Option 2: Delete .env and let it use environment variables
# (But you'd need to set them each time)

# Option 3: Use the startup script (temporary workaround)
.\start.ps1
```


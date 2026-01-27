# Quick Debug Guide

## See Detailed Logs

The debug mode is now **enabled by default**. When you start the server, you'll see detailed step-by-step logs:

```powershell
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You'll see output like:
```
[DEBUG] Step 1: Getting database settings...
[DEBUG] Step 1: ✓ Settings loaded. URL: ...@localhost:5432/parking_assistant
[DEBUG] Step 2: Creating database engine...
[DEBUG] Step 2: ✓ Engine created successfully
[DEBUG] Step 3: Attempting database connection...
```

If there's an error, you'll see exactly which step failed and a full stack trace.

## Run Comprehensive Diagnostic

For a full diagnostic, run:

```powershell
python debug_db_connection.py
```

This will test each component separately and show you exactly where the problem is.

## Fix .env File Encoding

If the diagnostic shows the .env file has encoding issues:

```powershell
python fix_env_encoding.py
```

This will:
- Read your .env file with encoding fallbacks
- Create a backup
- Rewrite it with proper UTF-8 encoding

## What to Look For

When you run the server, look for:

1. **Step 1 errors**: Settings loading issue (likely .env file encoding)
2. **Step 2 errors**: Engine creation issue (connection string problem)
3. **Step 3 errors**: Database connection issue (database not running or wrong credentials)

The debug output will show you the exact step that fails and why.


#!/usr/bin/env python3
"""
Test database connection script.

Run this to verify your database connection is working correctly.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.database.config import (
        get_settings,
        check_db_connection,
        check_postgis_extension,
        get_sync_engine,
    )
    from sqlalchemy import text
    
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    
    # Load settings
    print("\n1. Loading database settings...")
    try:
        settings = get_settings()
        print(f"   ✓ Settings loaded successfully")
        print(f"   - Database URL: {settings.sync_url if hasattr(settings, 'sync_url') else 'N/A'}")
    except Exception as e:
        print(f"   ✗ Error loading settings: {e}")
        sys.exit(1)
    
    # Test connection
    print("\n2. Testing database connection...")
    if check_db_connection():
        print("   ✓ Database connection successful!")
    else:
        print("   ✗ Database connection failed")
        print("\n   Troubleshooting:")
        print("   - Check that Docker container 'parking-db' is running")
        print("   - Verify DATABASE_URL in .env file is correct")
        print("   - Check that port 5432 is accessible")
        sys.exit(1)
    
    # Test PostGIS
    print("\n3. Checking PostGIS extension...")
    try:
        if check_postgis_extension():
            print("   ✓ PostGIS extension is available")
        else:
            print("   ⚠ PostGIS extension not found (may need to enable it)")
    except Exception as e:
        print(f"   ⚠ PostGIS check failed: {e}")
    
    # Test basic query
    print("\n4. Testing basic SQL query...")
    try:
        engine = get_sync_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"   ✓ PostgreSQL version: {version[:50]}...")
    except Exception as e:
        print(f"   ✗ Query failed: {e}")
        sys.exit(1)
    
    # Check if tables exist
    print("\n5. Checking database schema...")
    try:
        engine = get_sync_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            if tables:
                print(f"   ✓ Found {len(tables)} table(s): {', '.join(tables)}")
            else:
                print("   ⚠ No tables found - you may need to run migrations")
    except Exception as e:
        print(f"   ⚠ Schema check failed: {e}")
    
    print("\n" + "=" * 60)
    print("✓ All connection tests passed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run migrations: python -c \"from app.database.config import run_migrations; run_migrations()\"")
    print("2. Start the server: python -m uvicorn main:app --reload")
    
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're in the backend directory and dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


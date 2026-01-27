#!/usr/bin/env python3
"""
Debug database connection issues.

This script will help identify where the encoding error is occurring.
"""

import os
import sys
import traceback
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("Database Connection Debug Tool")
print("=" * 70)
print()

# Step 1: Check environment variables
print("\n1. Checking Environment Variables:")
print("-" * 70)
db_url = os.getenv('DATABASE_URL')
if db_url:
    print(f"   ✓ DATABASE_URL is set: {db_url[:60]}...")
else:
    print("   ✗ DATABASE_URL is not set")
print(f"   DATABASE_POOL_SIZE: {os.getenv('DATABASE_POOL_SIZE', 'not set')}")
print(f"   DATABASE_MAX_OVERFLOW: {os.getenv('DATABASE_MAX_OVERFLOW', 'not set')}")

# Step 2: Check .env file
print("\n2. Checking .env File:")
print("-" * 70)
env_path = Path(".env")
if env_path.exists():
    print(f"   ✓ .env file exists: {env_path.absolute()}")
    print(f"   File size: {env_path.stat().st_size} bytes")
    
    # Try to read with different encodings
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    for encoding in encodings:
        try:
            with open(env_path, 'r', encoding=encoding, errors='strict') as f:
                content = f.read()
            print(f"   ✓ Can read with {encoding} encoding")
            # Check for DATABASE_URL in content
            if 'DATABASE_URL' in content:
                lines = [l for l in content.splitlines() if 'DATABASE_URL' in l and not l.strip().startswith('#')]
                if lines:
                    print(f"   ✓ Found DATABASE_URL in file: {lines[0][:60]}...")
            break
        except UnicodeDecodeError as e:
            print(f"   ✗ Cannot read with {encoding} encoding: {e}")
        except Exception as e:
            print(f"   ✗ Error reading with {encoding}: {e}")
else:
    print("   ✗ .env file does not exist")

# Step 3: Try to load settings
print("\n3. Testing Settings Loading:")
print("-" * 70)
try:
    from app.database.config import get_settings
    print("   Attempting to load settings...")
    settings = get_settings()
    print(f"   ✓ Settings loaded successfully")
    print(f"   Database URL: {settings.sync_url[:60]}...")
except UnicodeDecodeError as e:
    print(f"   ✗ UnicodeDecodeError: {e}")
    print(f"   Position: {e.start if hasattr(e, 'start') else 'unknown'}")
    traceback.print_exc()
except Exception as e:
    print(f"   ✗ Error loading settings: {e}")
    traceback.print_exc()

# Step 4: Try to create engine
print("\n4. Testing Engine Creation:")
print("-" * 70)
try:
    from app.database.config import get_sync_engine
    print("   Attempting to create engine...")
    engine = get_sync_engine()
    print(f"   ✓ Engine created successfully")
    print(f"   Engine URL: {str(engine.url)[:60]}...")
except UnicodeDecodeError as e:
    print(f"   ✗ UnicodeDecodeError creating engine: {e}")
    print(f"   Position: {e.start if hasattr(e, 'start') else 'unknown'}")
    traceback.print_exc()
except Exception as e:
    print(f"   ✗ Error creating engine: {e}")
    traceback.print_exc()

# Step 5: Try to connect
print("\n5. Testing Database Connection:")
print("-" * 70)
try:
    from app.database.config import get_sync_engine
    from sqlalchemy import text
    
    engine = get_sync_engine()
    print("   Attempting to connect...")
    with engine.connect() as conn:
        print("   ✓ Connection established")
        print("   Executing test query...")
        result = conn.execute(text("SELECT 1"))
        value = result.scalar()
        print(f"   ✓ Query successful: {value}")
        print("   ✓ Database connection is working!")
except UnicodeDecodeError as e:
    print(f"   ✗ UnicodeDecodeError during connection: {e}")
    print(f"   Position: {e.start if hasattr(e, 'start') else 'unknown'}")
    if hasattr(e, 'object'):
        obj = e.object
        if isinstance(obj, bytes):
            print(f"   Problematic bytes: {obj[e.start-10:e.start+10]}")
    traceback.print_exc()
except Exception as e:
    print(f"   ✗ Connection error: {e}")
    print(f"   Error type: {type(e).__name__}")
    traceback.print_exc()

print("\n" + "=" * 70)
print("Debug complete")
print("=" * 70)


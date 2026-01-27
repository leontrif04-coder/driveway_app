#!/usr/bin/env python3
"""
Fix .env file encoding issues.

This script will:
1. Read the existing .env file with encoding fallbacks
2. Create a new .env file with proper UTF-8 encoding
3. Preserve all existing settings
"""

import sys
from pathlib import Path

def fix_env_file():
    """Fix .env file encoding."""
    # Find .env file
    env_path = Path(".env")
    if not env_path.exists():
        env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print("No .env file found. Creating a new one...")
        create_new_env_file(env_path)
        return
    
    print(f"Reading existing .env file: {env_path}")
    
    # Try to read with different encodings
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    content = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            with open(env_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            used_encoding = encoding
            print(f"Successfully read file with {encoding} encoding")
            break
        except Exception as e:
            continue
    
    if not content:
        print("ERROR: Could not read .env file with any encoding. Creating new one...")
        create_new_env_file(env_path)
        return
    
    # Backup old file
    backup_path = env_path.with_suffix('.env.backup')
    try:
        import shutil
        shutil.copy2(env_path, backup_path)
        print(f"Backed up original file to: {backup_path}")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")
    
    # Write new file with UTF-8 encoding
    try:
        with open(env_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        print(f"✓ Successfully rewrote .env file with UTF-8 encoding")
        print(f"  Original encoding: {used_encoding}")
        print(f"  New encoding: UTF-8")
    except Exception as e:
        print(f"ERROR: Could not write new .env file: {e}")
        sys.exit(1)


def create_new_env_file(env_path: Path):
    """Create a new .env file with default settings."""
    default_content = """# Database Configuration
# PostgreSQL + PostGIS connection string for Docker container
DATABASE_URL=postgresql://parking_app:dev_password_123@localhost:5432/parking_assistant

# Connection Pool Settings
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Run migrations on startup (set to "true" to enable automatic migrations)
RUN_MIGRATIONS=false

# Database echo (set to "true" to log all SQL queries for debugging)
DB_ECHO=false
"""
    
    try:
        with open(env_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(default_content)
        print(f"✓ Created new .env file at: {env_path}")
        print("  Please update DATABASE_URL if needed")
    except Exception as e:
        print(f"ERROR: Could not create .env file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("Fix .env File Encoding")
    print("=" * 60)
    print()
    
    try:
        fix_env_file()
        print()
        print("=" * 60)
        print("✓ Done! Your .env file should now work correctly.")
        print("=" * 60)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


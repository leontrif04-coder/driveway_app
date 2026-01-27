"""
Smart Parking Assistant - Database Configuration
=================================================

Database connection management with support for:
- PostgreSQL + PostGIS (production)
- SQLite with SpatiaLite (testing/development fallback)
- Connection pooling
- Session management

Environment Variables:
    DATABASE_URL: Full connection string
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD: Individual components
    DB_POOL_SIZE: Connection pool size (default: 5)
    DB_MAX_OVERFLOW: Max overflow connections (default: 10)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager, contextmanager
from functools import lru_cache
from typing import AsyncGenerator, Generator, Optional

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


# ============================================================================
# Configuration
# ============================================================================

class DatabaseSettings(BaseSettings):
    """Database configuration from environment variables."""
    
    # Full connection string (preferred)
    database_url: Optional[str] = None
    
    # Individual components (fallback)
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "parking_app"
    db_user: str = "postgres"
    db_password: str = ""
    
    # Connection pool settings
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800  # 30 minutes
    
    # Testing mode
    testing: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Ignore errors when reading .env file
        case_sensitive = False
    
    @property
    def sync_url(self) -> str:
        """Get synchronous database URL."""
        if self.database_url:
            url = self.database_url
            # Ensure it's not async URL
            return url.replace("postgresql+asyncpg://", "postgresql://")
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def async_url(self) -> str:
        """Get asynchronous database URL."""
        if self.database_url:
            url = self.database_url
            # Ensure it uses asyncpg
            if "postgresql://" in url and "asyncpg" not in url:
                return url.replace("postgresql://", "postgresql+asyncpg://")
            return url
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


@lru_cache()
def get_settings() -> DatabaseSettings:
    """Get cached database settings."""
    import os
    
    # First, try to create DatabaseSettings without .env file if it has encoding issues
    # We'll manually handle .env reading if pydantic fails
    
    # Check if DATABASE_URL is set in environment (bypasses .env file)
    if os.getenv('DATABASE_URL'):
        try:
            # Try to create settings from environment variables only
            # Temporarily disable .env file reading
            class EnvOnlySettings(BaseSettings):
                database_url: Optional[str] = None
                db_host: str = "localhost"
                db_port: int = 5432
                db_name: str = "parking_app"
                db_user: str = "postgres"
                db_password: str = ""
                db_pool_size: int = 5
                db_max_overflow: int = 10
                db_pool_timeout: int = 30
                db_pool_recycle: int = 1800
                testing: bool = False
                
                class Config:
                    env_file = None  # Skip .env file
                    case_sensitive = False
                
                @property
                def sync_url(self) -> str:
                    if self.database_url:
                        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")
                    return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
                
                @property
                def async_url(self) -> str:
                    if self.database_url:
                        url = self.database_url
                        if "postgresql://" in url and "asyncpg" not in url:
                            return url.replace("postgresql://", "postgresql+asyncpg://")
                        return url
                    return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
            
            return EnvOnlySettings()
        except Exception:
            pass
    
    # Try normal loading
    try:
        return DatabaseSettings()
    except (UnicodeDecodeError, UnicodeError) as e:
        # Catch encoding errors specifically
        print(f"Warning: Encoding error reading .env file: {e}")
        print("Attempting to load settings from environment variables and manual .env parsing...")
        return _load_settings_manually()
    except Exception as e:
        # If pydantic-settings fails for other reasons, try manual .env reading
        error_msg = str(e)
        if "utf-8" in error_msg.lower() or "codec" in error_msg.lower() or "decode" in error_msg.lower():
            print(f"Warning: Encoding issue loading .env file: {e}")
            print("Attempting to load settings manually...")
            return _load_settings_manually()
        # For other errors, still try manual loading as fallback
        print(f"Warning: Error loading settings with pydantic-settings: {e}")
        print("Falling back to manual settings loading...")
        return _load_settings_manually()


def _load_settings_manually() -> DatabaseSettings:
    """Manually load settings from .env file with encoding fallbacks."""
    import os
    from pathlib import Path
    
    # Try to find .env file (check multiple locations)
    base_dir = Path(__file__).parent.parent.parent  # backend directory
    env_path = None
    
    # Try different locations
    possible_paths = [
        base_dir / ".env",
        Path(".env"),  # Current directory
        Path.cwd() / ".env",  # Current working directory
    ]
    
    for path in possible_paths:
        if path.exists():
            env_path = path
            break
    
    settings_dict = {}
    
    if env_path and env_path.exists():
        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open(env_path, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()
                break
            except Exception:
                continue
        
        if content:
            # Parse .env file manually
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    # Convert to uppercase and replace - with _
                    env_key = key.upper().replace('-', '_')
                    settings_dict[env_key] = value
    
    # Also check environment variables
    settings_dict['database_url'] = os.getenv('DATABASE_URL') or settings_dict.get('DATABASE_URL')
    settings_dict['db_host'] = os.getenv('DB_HOST') or settings_dict.get('DB_HOST', 'localhost')
    settings_dict['db_port'] = int(os.getenv('DB_PORT') or settings_dict.get('DB_PORT', '5432'))
    settings_dict['db_name'] = os.getenv('DB_NAME') or settings_dict.get('DB_NAME', 'parking_app')
    settings_dict['db_user'] = os.getenv('DB_USER') or settings_dict.get('DB_USER', 'postgres')
    settings_dict['db_password'] = os.getenv('DB_PASSWORD') or settings_dict.get('DB_PASSWORD', '')
    settings_dict['db_pool_size'] = int(os.getenv('DATABASE_POOL_SIZE') or settings_dict.get('DATABASE_POOL_SIZE', '5'))
    settings_dict['db_max_overflow'] = int(os.getenv('DATABASE_MAX_OVERFLOW') or settings_dict.get('DATABASE_MAX_OVERFLOW', '10'))
    
    # Create settings object manually
    class ManualDatabaseSettings:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        @property
        def sync_url(self) -> str:
            if self.database_url:
                url = self.database_url
                return url.replace("postgresql+asyncpg://", "postgresql://")
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        
        @property
        def async_url(self) -> str:
            if self.database_url:
                url = self.database_url
                if "postgresql://" in url and "asyncpg" not in url:
                    return url.replace("postgresql://", "postgresql+asyncpg://")
                return url
            return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    return ManualDatabaseSettings(**settings_dict)


# ============================================================================
# Engine Factory
# ============================================================================

def create_sync_engine(settings: Optional[DatabaseSettings] = None) -> Engine:
    """Create synchronous SQLAlchemy engine."""
    if settings is None:
        try:
            settings = get_settings()
        except Exception as e:
            # If settings can't be loaded, use defaults
            print(f"Warning: Could not load database settings: {e}")
            settings = DatabaseSettings()
    
    if settings.testing:
        # Use SQLite for testing (with spatialite if available)
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    
    # Get database URL, with fallback if not configured
    try:
        db_url = settings.sync_url
    except Exception as e:
        # If there's an error getting the URL, use a default that will fail gracefully
        print(f"Warning: Could not construct database URL: {e}")
        db_url = "postgresql://localhost/parking_assistant"
    
    # Add encoding parameter to connect_args for PostgreSQL to handle encoding issues
    connect_args = {}
    if "postgresql" in db_url:
        connect_args = {
            "connect_timeout": 5,
            # Force UTF-8 encoding for connection
            "client_encoding": "UTF8",
        }
    
    return create_engine(
        db_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,  # Verify connections before use
        echo=os.getenv("DB_ECHO", "false").lower() == "true",
        connect_args=connect_args,
    )


def create_async_engine_instance(settings: Optional[DatabaseSettings] = None):
    """Create asynchronous SQLAlchemy engine."""
    if settings is None:
        settings = get_settings()
    
    if settings.testing:
        # Use aiosqlite for async testing
        from sqlalchemy.ext.asyncio import create_async_engine
        return create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    
    return create_async_engine(
        settings.async_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,
        echo=os.getenv("DB_ECHO", "false").lower() == "true",
    )


# ============================================================================
# Session Management
# ============================================================================

# Global engines (lazily initialized)
_sync_engine: Optional[Engine] = None
_async_engine = None

# Session factories
_sync_session_factory: Optional[sessionmaker] = None
_async_session_factory: Optional[async_sessionmaker] = None


def get_sync_engine() -> Engine:
    """Get or create the synchronous engine."""
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_sync_engine()
    return _sync_engine


def get_async_engine():
    """Get or create the asynchronous engine."""
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine_instance()
    return _async_engine


def get_sync_session_factory() -> sessionmaker:
    """Get or create the synchronous session factory."""
    global _sync_session_factory
    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(
            bind=get_sync_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _sync_session_factory


def get_async_session_factory() -> async_sessionmaker:
    """Get or create the asynchronous session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _async_session_factory


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for synchronous database sessions.
    
    Usage:
        with get_db_session() as session:
            spots = session.query(ParkingSpot).all()
    """
    session = get_sync_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    
    Usage:
        async with get_async_db_session() as session:
            result = await session.execute(select(ParkingSpot))
            spots = result.scalars().all()
    """
    session = get_async_session_factory()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for synchronous database sessions.
    
    Usage:
        @app.get("/spots")
        def get_spots(db: Session = Depends(get_db)):
            return db.query(ParkingSpot).all()
    """
    session = get_sync_session_factory()()
    try:
        yield session
    finally:
        session.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for asynchronous database sessions.
    
    Usage:
        @app.get("/spots")
        async def get_spots(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(ParkingSpot))
            return result.scalars().all()
    """
    async with get_async_db_session() as session:
        yield session


# ============================================================================
# Database Initialization
# ============================================================================

def init_db(drop_existing: bool = False) -> None:
    """
    Initialize database tables.
    
    Args:
        drop_existing: If True, drop all tables before creating
    """
    from .models import Base
    
    engine = get_sync_engine()
    
    if drop_existing:
        Base.metadata.drop_all(bind=engine)
    
    Base.metadata.create_all(bind=engine)


async def init_db_async(drop_existing: bool = False) -> None:
    """Asynchronous database initialization."""
    from .models import Base
    
    engine = get_async_engine()
    
    async with engine.begin() as conn:
        if drop_existing:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


def _safe_decode_error(error: Exception) -> str:
    """Safely decode error messages, handling encoding issues."""
    try:
        if isinstance(error, (UnicodeDecodeError, UnicodeError)):
            # Try to decode the problematic bytes with different encodings
            if hasattr(error, 'object') and isinstance(error.object, bytes):
                # Try different encodings for error messages (common: latin-1, cp1252, utf-8)
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1', 'utf-8']:
                    try:
                        decoded = error.object.decode(encoding, errors='replace')
                        # Extract the actual error message (usually after "FATAL:")
                        if 'FATAL:' in decoded:
                            fatal_part = decoded.split('FATAL:')[-1].strip()
                            return f"Database error: {fatal_part}"
                        return f"Database error: {decoded}"
                    except Exception:
                        continue
            return f"Encoding error: {error.reason if hasattr(error, 'reason') else str(error)}"
        
        error_msg = str(error)
        
        # If error has args with bytes, try to decode them with multiple encodings
        if hasattr(error, 'args') and error.args:
            for arg in error.args:
                if isinstance(arg, bytes):
                    # Try multiple encodings
                    for encoding in ['latin-1', 'cp1252', 'iso-8859-1', 'utf-8']:
                        try:
                            decoded = arg.decode(encoding, errors='replace')
                            if decoded and len(decoded) > 0:
                                # Extract meaningful error message
                                if 'FATAL:' in decoded:
                                    fatal_part = decoded.split('FATAL:')[-1].strip()
                                    return f"Database error: {fatal_part}"
                                error_msg = decoded
                                break
                        except Exception:
                            continue
        
        return error_msg
    except Exception:
        return "Database connection error (unable to decode error message)"


def check_db_connection() -> bool:
    """
    Verify database connection is working.
    
    Returns:
        True if connection is successful, False otherwise
    """
    import traceback
    import os
    
    # Enable debug mode if DB_DEBUG is set (always show errors in detail)
    debug_mode = os.getenv("DB_DEBUG", "true").lower() == "true"  # Default to true for now
    
    try:
        if debug_mode:
            print("[DEBUG] Step 1: Getting database settings...")
        try:
            settings = get_settings()
            if debug_mode:
                safe_url = settings.sync_url.split('@')[-1] if '@' in settings.sync_url else settings.sync_url[:50]
                print(f"[DEBUG] Step 1: ✓ Settings loaded. URL: ...@{safe_url}")
        except Exception as settings_error:
            if debug_mode:
                print(f"[DEBUG] Step 1: ✗ Error loading settings:")
                traceback.print_exc()
            error_msg = _safe_decode_error(settings_error)
            print(f"Database connection failed: Error loading settings - {error_msg}")
            return False
        
        if debug_mode:
            print("[DEBUG] Step 2: Creating database engine...")
        try:
            engine = get_sync_engine()
            if debug_mode:
                print(f"[DEBUG] Step 2: ✓ Engine created successfully")
        except Exception as engine_error:
            if debug_mode:
                print(f"[DEBUG] Step 2: ✗ Error creating engine:")
                traceback.print_exc()
            error_msg = _safe_decode_error(engine_error)
            print(f"Database connection failed: Error creating engine - {error_msg}")
            return False
        
        if debug_mode:
            print("[DEBUG] Step 3: Attempting database connection...")
        
        # Use a more robust connection test with explicit encoding handling
        try:
            with engine.connect() as conn:
                if debug_mode:
                    print("[DEBUG] Step 3: ✓ Connection established")
                    print("[DEBUG] Step 4: Setting client encoding...")
                # Set client encoding explicitly to avoid encoding issues
                try:
                    conn.execute(text("SET client_encoding TO 'UTF8'"))
                    if debug_mode:
                        print("[DEBUG] Step 4: ✓ Encoding set to UTF8")
                except Exception as e:
                    if debug_mode:
                        print(f"[DEBUG] Step 4: ⚠ Could not set encoding (may already be set): {e}")
                
                if debug_mode:
                    print("[DEBUG] Step 5: Executing test query...")
                conn.execute(text("SELECT 1"))
                
                if debug_mode:
                    print("[DEBUG] Step 5: ✓ Query successful!")
                    print("[DEBUG] ✓ All connection tests passed!")
            return True
        except Exception as conn_error:
            # Handle connection errors with proper encoding
            if debug_mode:
                print(f"[DEBUG] Step 3/4/5: ✗ Connection error occurred:")
                traceback.print_exc()
            error_msg = _safe_decode_error(conn_error)
            print(f"Database connection failed: {error_msg}")
            if debug_mode:
                print(f"[DEBUG] Error details:")
                print(f"  Error type: {type(conn_error).__name__}")
                print(f"  Error args: {conn_error.args}")
                if hasattr(conn_error, '__cause__') and conn_error.__cause__:
                    print(f"  Caused by: {type(conn_error.__cause__).__name__}: {conn_error.__cause__}")
            return False
    except (UnicodeDecodeError, UnicodeError) as e:
        # Handle UTF-8 decoding errors at the engine level
        if debug_mode:
            print(f"[DEBUG] ✗ Unicode error occurred:")
            traceback.print_exc()
        error_msg = _safe_decode_error(e)
        print(f"Database connection failed: Encoding error - {error_msg}")
        if debug_mode:
            print(f"[DEBUG] Unicode error details:")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Position: {e.start if hasattr(e, 'start') else 'unknown'}")
            if hasattr(e, 'object') and isinstance(e.object, bytes):
                start = e.start if hasattr(e, 'start') else 0
                end = min(start + 20, len(e.object))
                print(f"  Problematic bytes: {e.object[max(0, start-10):end]}")
        return False
    except Exception as e:
        # Handle other errors
        if debug_mode:
            print(f"[DEBUG] ✗ Unexpected error occurred:")
            traceback.print_exc()
        error_msg = _safe_decode_error(e)
        print(f"Database connection failed: {error_msg}")
        if debug_mode:
            print(f"[DEBUG] Error details:")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Error args: {e.args}")
        return False


def check_postgis_extension() -> bool:
    """
    Verify PostGIS extension is installed.
    
    Returns:
        True if PostGIS is available, False otherwise
    """
    try:
        engine = get_sync_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT PostGIS_Version()"))
            version = result.scalar()
            print(f"PostGIS version: {version}")
            return True
    except Exception as e:
        print(f"PostGIS not available: {e}")
        return False


def run_sql_migration(migration_file: str) -> None:
    """
    Run a SQL migration file.
    
    Args:
        migration_file: Path to SQL migration file
    """
    import os
    from pathlib import Path
    
    engine = get_sync_engine()
    
    # Read SQL file with proper encoding handling
    sql_path = Path(migration_file)
    if not sql_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_file}")
    
    try:
        with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
            sql_content = f.read()
    except UnicodeDecodeError as e:
        # Try with different encoding if UTF-8 fails
        try:
            with open(sql_path, 'r', encoding='latin-1', errors='replace') as f:
                sql_content = f.read()
        except Exception:
            raise ValueError(f"Could not read migration file {migration_file}: {e}")
    
    # Execute SQL
    with engine.connect() as conn:
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        for statement in statements:
            if statement:
                conn.execute(text(statement))
        conn.commit()
    
    print(f"Migration completed: {migration_file}")


def run_migrations(migrations_dir: str = None) -> None:
    """
    Run all SQL migrations in order.
    
    Args:
        migrations_dir: Directory containing migration files (defaults to app/database/migrations)
    """
    import os
    from pathlib import Path
    
    if migrations_dir is None:
        # Default to app/database/migrations
        base_dir = Path(__file__).parent
        migrations_dir = base_dir / "migrations"
    else:
        migrations_dir = Path(migrations_dir)
    
    if not migrations_dir.exists():
        print(f"Migrations directory not found: {migrations_dir}")
        return
    
    # Get all SQL files and sort them
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("No migration files found")
        return
    
    print(f"Running {len(migration_files)} migration(s)...")
    for migration_file in migration_files:
        print(f"Running migration: {migration_file.name}")
        run_sql_migration(str(migration_file))
    
    print("All migrations completed")


# ============================================================================
# Testing Utilities
# ============================================================================

class TestingSessionManager:
    """
    Manages test database sessions with automatic cleanup.
    
    Usage:
        @pytest.fixture
        def db_session():
            with TestingSessionManager() as session:
                yield session
    """
    
    def __init__(self, seed_data: bool = True):
        self.seed_data = seed_data
        self._engine: Optional[Engine] = None
        self._session: Optional[Session] = None
    
    def __enter__(self) -> Session:
        from .models import Base
        
        # Create in-memory SQLite engine
        self._engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
        
        # Enable foreign key support for SQLite
        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        # Create tables
        Base.metadata.create_all(bind=self._engine)
        
        # Create session
        session_factory = sessionmaker(bind=self._engine)
        self._session = session_factory()
        
        if self.seed_data:
            self._seed_test_data()
        
        return self._session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            self._session.close()
        if self._engine:
            self._engine.dispose()
    
    def _seed_test_data(self) -> None:
        """Seed minimal test data."""
        from .models import User, ParkingSpot, MeterStatus
        from uuid import uuid4
        from decimal import Decimal
        
        # Create test user
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="test_user",
        )
        self._session.add(user)
        
        # Create test spots (Note: Without PostGIS, location column won't work)
        # For SQLite testing, we skip the geometry column
        spot = ParkingSpot(
            id=uuid4(),
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060"),
            street_name="Test Street",
            street_number="123",
            city="New York",
            state="NY",
            safety_score=80,
            tourism_density=60,
            meter_status=MeterStatus.WORKING,
        )
        # Note: For SQLite, you'd need to handle the geometry differently
        
        self._session.commit()


def create_test_engine(echo: bool = False) -> Engine:
    """
    Create an in-memory SQLite engine for testing.
    
    Note: This doesn't support PostGIS functions.
    For full geospatial testing, use a real PostgreSQL database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=echo,
    )
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    return engine


def create_test_session(engine: Engine) -> Session:
    """Create a session bound to the test engine."""
    from .models import Base
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


# ============================================================================
# Connection Pool Monitoring
# ============================================================================

def get_pool_status() -> dict:
    """
    Get current connection pool status.
    
    Returns:
        Dictionary with pool statistics
    """
    engine = get_sync_engine()
    pool = engine.pool
    
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalidatedcount() if hasattr(pool, 'invalidatedcount') else None,
    }


# ============================================================================
# Cleanup
# ============================================================================

def dispose_engines() -> None:
    """Dispose of all database engines (for shutdown)."""
    global _sync_engine, _async_engine
    
    if _sync_engine:
        _sync_engine.dispose()
        _sync_engine = None
    
    if _async_engine:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_async_engine.dispose())
        except RuntimeError:
            # No running loop, create one
            asyncio.run(_async_engine.dispose())
        _async_engine = None


# ============================================================================
# FastAPI Lifespan Integration
# ============================================================================

@asynccontextmanager
async def lifespan_db_manager(app):
    """
    FastAPI lifespan context manager for database.
    
    Usage:
        from fastapi import FastAPI
        from database.config import lifespan_db_manager
        
        app = FastAPI(lifespan=lifespan_db_manager)
    """
    # Startup
    print("Initializing database connection...")
    try:
        if check_db_connection():
            print("Database connection successful")
            try:
                if check_postgis_extension():
                    print("PostGIS extension verified")
            except Exception as e:
                print(f"PostGIS check failed (continuing): {e}")
            
            # Run migrations if enabled
            import os
            if os.getenv("RUN_MIGRATIONS", "false").lower() == "true":
                print("Running database migrations...")
                try:
                    run_migrations()
                except Exception as e:
                    print(f"Migration error (continuing anyway): {e}")
        else:
            print("WARNING: Database connection failed - some features may not work")
            print("NOTE: Make sure PostgreSQL is running and DATABASE_URL is set correctly")
    except Exception as e:
        # Catch any encoding or other errors during initialization
        error_msg = str(e)
        if isinstance(e, UnicodeDecodeError):
            error_msg = f"Encoding error: {e}. Check .env file encoding or database configuration."
        print(f"WARNING: Database initialization error: {error_msg}")
        print("Application will continue but database features will be unavailable")
    
    yield
    
    # Shutdown
    print("Closing database connections...")
    try:
        dispose_engines()
        print("Database connections closed")
    except Exception:
        pass  # Ignore errors during shutdown

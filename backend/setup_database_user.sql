-- Setup database user and permissions
-- Run this in your PostgreSQL Docker container

-- Create the user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'parking_app') THEN
        CREATE USER parking_app WITH PASSWORD 'dev_password_123';
        RAISE NOTICE 'User parking_app created';
    ELSE
        RAISE NOTICE 'User parking_app already exists';
    END IF;
END
$$;

-- Grant privileges on the database
GRANT ALL PRIVILEGES ON DATABASE parking_assistant TO parking_app;

-- Connect to the database and grant schema privileges
\c parking_assistant

-- Grant privileges on the public schema
GRANT ALL ON SCHEMA public TO parking_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO parking_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO parking_app;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO parking_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO parking_app;

-- Enable PostGIS extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS postgis;


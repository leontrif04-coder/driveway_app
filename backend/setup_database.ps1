# PowerShell script to setup database user and permissions
# Run this to create the database user in your Docker container

Write-Host "Setting up database user 'parking_app'..." -ForegroundColor Green

# Create the user
docker exec -i parking-db psql -U postgres -c @"
DO `$`$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'parking_app') THEN
        CREATE USER parking_app WITH PASSWORD 'dev_password_123';
        RAISE NOTICE 'User parking_app created';
    ELSE
        RAISE NOTICE 'User parking_app already exists';
    END IF;
END
`$`$;
"@

# Grant privileges on the database
docker exec -i parking-db psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE parking_assistant TO parking_app;"

Write-Host "Granting schema privileges..." -ForegroundColor Green

# Grant schema privileges
docker exec -i parking-db psql -U postgres -d parking_assistant -c "GRANT ALL ON SCHEMA public TO parking_app;"
docker exec -i parking-db psql -U postgres -d parking_assistant -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO parking_app;"
docker exec -i parking-db psql -U postgres -d parking_assistant -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO parking_app;"
docker exec -i parking-db psql -U postgres -d parking_assistant -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO parking_app;"
docker exec -i parking-db psql -U postgres -d parking_assistant -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO parking_app;"

# Enable PostGIS extension
docker exec -i parking-db psql -U postgres -d parking_assistant -c "CREATE EXTENSION IF NOT EXISTS postgis;"

Write-Host "✓ Database setup complete!" -ForegroundColor Green


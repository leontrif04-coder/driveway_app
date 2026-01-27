-- Smart Parking Assistant - Seed Data
-- NYC test data matching the in-memory seed_data() function

-- Insert 10 parking spots around NYC (40.7128, -74.0060)
INSERT INTO parking_spots (
    id,
    latitude,
    longitude,
    street_name,
    max_duration_minutes,
    price_per_hour_usd,
    safety_score,
    tourism_density,
    meter_status,
    meter_status_confidence,
    is_active
) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 40.7128, -74.0060, 'Broadway', 120, 4.0, 80, 70, 'working', 0.9, TRUE),
    ('550e8400-e29b-41d4-a716-446655440002', 40.7138, -74.0030, 'Church St', 60, 3.0, 60, 50, 'broken', 0.8, TRUE),
    ('550e8400-e29b-41d4-a716-446655440003', 40.7118, -74.0090, 'Park Pl', 90, 3.5, 75, 60, 'working', 0.85, TRUE),
    ('550e8400-e29b-41d4-a716-446655440004', 40.7148, -74.0000, 'Canal St', 120, 5.0, 70, 80, 'working', 0.95, TRUE),
    ('550e8400-e29b-41d4-a716-446655440005', 40.7108, -74.0120, 'Vesey St', 180, 2.5, 85, 40, 'working', 0.9, TRUE),
    ('550e8400-e29b-41d4-a716-446655440006', 40.7158, -74.0040, 'Lafayette St', 60, 3.0, 65, 55, 'unknown', 0.5, TRUE),
    ('550e8400-e29b-41d4-a716-446655440007', 40.7098, -74.0150, 'West St', 240, 2.0, 90, 30, 'working', 0.92, TRUE),
    ('550e8400-e29b-41d4-a716-446655440008', 40.7168, -74.0010, 'Mulberry St', 60, 6.0, 55, 90, 'broken', 0.75, TRUE),
    ('550e8400-e29b-41d4-a716-446655440009', 40.7088, -74.0180, 'Greenwich St', 120, 3.5, 78, 45, 'working', 0.88, TRUE),
    ('550e8400-e29b-41d4-a716-446655440010', 40.7178, -74.0020, 'Mott St', 90, 4.5, 68, 75, 'working', 0.82, TRUE);

-- Note: The location geometry will be automatically set by the trigger
-- Note: Review stats (review_count, avg_rating, computed_score) will be NULL until reviews are added


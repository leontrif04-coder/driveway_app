-- Smart Parking Assistant - Initial Database Schema
-- PostgreSQL + PostGIS
-- Run this migration to create all tables, indexes, triggers, and functions

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- Enums
-- ============================================================================

CREATE TYPE meter_status AS ENUM ('working', 'broken', 'unknown');
CREATE TYPE destination_type AS ENUM ('restaurant', 'shopping', 'office', 'entertainment', 'medical', 'residential', 'other');
CREATE TYPE time_of_day AS ENUM ('morning', 'afternoon', 'evening', 'night');
CREATE TYPE ab_test_variant AS ENUM ('control', 'ml_powered', 'hybrid');

-- ============================================================================
-- Users Table
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE,
    username VARCHAR(100),
    last_active_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    total_reviews INTEGER NOT NULL DEFAULT 0,
    total_parkings INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_last_active ON users(last_active_at) WHERE is_active = TRUE;

-- ============================================================================
-- User Preferences Table
-- ============================================================================

CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    preferred_max_price_usd NUMERIC(6, 2),
    preferred_max_walk_distance_m INTEGER,
    preferred_min_safety_score INTEGER,
    tourism_preference VARCHAR(20),
    avg_parking_duration_min INTEGER,
    avg_price_tolerance_usd NUMERIC(6, 2),
    morning_preference_score NUMERIC(3, 2),
    afternoon_preference_score NUMERIC(3, 2),
    evening_preference_score NUMERIC(3, 2),
    night_preference_score NUMERIC(3, 2),
    ab_test_variant ab_test_variant NOT NULL DEFAULT 'control',
    notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT check_safety_score_range CHECK (preferred_min_safety_score BETWEEN 0 AND 100),
    CONSTRAINT check_tourism_preference CHECK (tourism_preference IN ('low', 'medium', 'high'))
);

-- ============================================================================
-- Parking Spots Table
-- ============================================================================

CREATE TABLE parking_spots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location GEOMETRY(POINT, 4326) NOT NULL,
    latitude NUMERIC(10, 8) NOT NULL,
    longitude NUMERIC(11, 8) NOT NULL,
    street_name VARCHAR(255) NOT NULL,
    street_number VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(2) NOT NULL DEFAULT 'US',
    max_duration_minutes INTEGER,
    price_per_hour_usd NUMERIC(6, 2),
    spot_type VARCHAR(50) NOT NULL DEFAULT 'street',
    safety_score INTEGER NOT NULL DEFAULT 50,
    tourism_density INTEGER NOT NULL DEFAULT 50,
    meter_status meter_status NOT NULL DEFAULT 'unknown',
    meter_status_confidence NUMERIC(3, 2) NOT NULL DEFAULT 0,
    meter_last_verified_at TIMESTAMPTZ,
    review_count INTEGER NOT NULL DEFAULT 0,
    avg_rating NUMERIC(3, 2),
    computed_score NUMERIC(5, 2),
    is_occupied BOOLEAN NOT NULL DEFAULT FALSE,
    last_occupancy_change TIMESTAMPTZ,
    estimated_available_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    spot_metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_coordinates CHECK (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180),
    CONSTRAINT check_safety_range CHECK (safety_score BETWEEN 0 AND 100),
    CONSTRAINT check_tourism_range CHECK (tourism_density BETWEEN 0 AND 100),
    CONSTRAINT check_rating_range CHECK (avg_rating BETWEEN 1 AND 5),
    CONSTRAINT check_score_range CHECK (computed_score BETWEEN 0 AND 100),
    CONSTRAINT check_confidence_range CHECK (meter_status_confidence BETWEEN 0 AND 1)
);

-- PostGIS spatial index for location
CREATE INDEX idx_spots_location_gist ON parking_spots USING GIST(location);

-- Other indexes
CREATE INDEX idx_spots_safety ON parking_spots(safety_score) WHERE is_active = TRUE;
CREATE INDEX idx_spots_price ON parking_spots(price_per_hour_usd) WHERE is_active = TRUE;
CREATE INDEX idx_spots_score ON parking_spots(computed_score DESC NULLS LAST) WHERE is_active = TRUE;
CREATE INDEX idx_spots_active_score ON parking_spots(is_active, computed_score DESC NULLS LAST);

-- Trigger to update location geometry from lat/lng
CREATE OR REPLACE FUNCTION update_spot_location()
RETURNS TRIGGER AS $$
BEGIN
    NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_spot_location
    BEFORE INSERT OR UPDATE OF latitude, longitude ON parking_spots
    FOR EACH ROW
    EXECUTE FUNCTION update_spot_location();

-- ============================================================================
-- Reviews Table
-- ============================================================================

CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spot_id UUID NOT NULL REFERENCES parking_spots(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    rating SMALLINT NOT NULL,
    review_text TEXT,
    detected_meter_status meter_status,
    sentiment_score NUMERIC(3, 2),
    extracted_keywords TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_visible BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT check_review_rating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT check_sentiment_range CHECK (sentiment_score BETWEEN -1 AND 1),
    CONSTRAINT unique_user_spot_day UNIQUE (user_id, spot_id, (created_at::date))
);

CREATE INDEX idx_reviews_spot ON reviews(spot_id, created_at DESC) WHERE is_visible = TRUE;
CREATE INDEX idx_reviews_user ON reviews(user_id, created_at DESC) WHERE is_visible = TRUE;
CREATE INDEX idx_reviews_rating ON reviews(spot_id, rating) WHERE is_visible = TRUE;

-- ============================================================================
-- Trigger: Update Spot Review Stats
-- ============================================================================

CREATE OR REPLACE FUNCTION update_spot_review_stats()
RETURNS TRIGGER AS $$
DECLARE
    v_review_count INTEGER;
    v_avg_rating NUMERIC(3, 2);
    v_computed_score NUMERIC(5, 2);
BEGIN
    -- Calculate review stats for the spot
    SELECT 
        COUNT(*)::INTEGER,
        AVG(rating)::NUMERIC(3, 2)
    INTO v_review_count, v_avg_rating
    FROM reviews
    WHERE spot_id = COALESCE(NEW.spot_id, OLD.spot_id)
      AND is_visible = TRUE;
    
    -- Update parking_spots table
    UPDATE parking_spots
    SET 
        review_count = COALESCE(v_review_count, 0),
        avg_rating = v_avg_rating,
        computed_score = CASE
            WHEN v_avg_rating IS NULL OR v_review_count = 0 THEN NULL
            ELSE LEAST(v_avg_rating * (1 + LOG(v_review_count + 1)) * 20, 100.0)
        END,
        updated_at = NOW()
    WHERE id = COALESCE(NEW.spot_id, OLD.spot_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_spot_review_stats
    AFTER INSERT OR UPDATE OR DELETE ON reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_spot_review_stats();

-- ============================================================================
-- Occupancy Events Table
-- ============================================================================

CREATE TABLE occupancy_events (
    id UUID NOT NULL,
    spot_id UUID NOT NULL REFERENCES parking_spots(id) ON DELETE CASCADE,
    event_type VARCHAR(20) NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(50) NOT NULL DEFAULT 'user_report',
    reported_by UUID REFERENCES users(id),
    confidence NUMERIC(3, 2) NOT NULL DEFAULT 1.0,
    event_metadata JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (id, event_time),
    CONSTRAINT check_event_type CHECK (event_type IN ('occupied', 'available', 'unknown')),
    CONSTRAINT check_occupancy_confidence CHECK (confidence BETWEEN 0 AND 1)
);

CREATE INDEX idx_occupancy_spot_time ON occupancy_events(spot_id, event_time DESC);

-- Trigger: Update spot occupancy status
CREATE OR REPLACE FUNCTION update_spot_occupancy()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE parking_spots
    SET 
        is_occupied = (NEW.event_type = 'occupied'),
        last_occupancy_change = NEW.event_time,
        updated_at = NOW()
    WHERE id = NEW.spot_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_spot_occupancy
    AFTER INSERT ON occupancy_events
    FOR EACH ROW
    EXECUTE FUNCTION update_spot_occupancy();

-- ============================================================================
-- User Parking Events Table (ML Training Data)
-- ============================================================================

CREATE TABLE user_parking_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    spot_id UUID NOT NULL REFERENCES parking_spots(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    duration_minutes INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN ended_at IS NOT NULL THEN 
                EXTRACT(EPOCH FROM (ended_at - started_at)) / 60
            ELSE NULL
        END
    ) STORED,
    time_of_day time_of_day NOT NULL,
    day_of_week SMALLINT NOT NULL,
    destination_type destination_type,
    distance_to_dest_m INTEGER,
    price_paid_usd NUMERIC(6, 2),
    spot_safety_score INTEGER NOT NULL,
    spot_tourism_density INTEGER NOT NULL,
    spot_price_per_hour NUMERIC(6, 2),
    user_rating SMALLINT,
    would_return BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT check_day_of_week CHECK (day_of_week BETWEEN 0 AND 6),
    CONSTRAINT check_parking_rating CHECK (user_rating BETWEEN 1 AND 5)
);

CREATE INDEX idx_parking_events_user ON user_parking_events(user_id, started_at DESC);
CREATE INDEX idx_parking_events_spot ON user_parking_events(spot_id, started_at DESC);
CREATE INDEX idx_parking_events_ml ON user_parking_events(user_id, time_of_day, day_of_week);

-- ============================================================================
-- User Favorite Spots Table
-- ============================================================================

CREATE TABLE user_favorite_spots (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    spot_id UUID NOT NULL REFERENCES parking_spots(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    nickname VARCHAR(100),
    PRIMARY KEY (user_id, spot_id)
);

-- ============================================================================
-- ML Models Table
-- ============================================================================

CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    accuracy NUMERIC(5, 4),
    precision_score NUMERIC(5, 4),
    recall NUMERIC(5, 4),
    f1_score NUMERIC(5, 4),
    training_samples INTEGER,
    feature_count INTEGER,
    hyperparameters JSONB NOT NULL DEFAULT '{}',
    artifact_path VARCHAR(500),
    trained_at TIMESTAMPTZ NOT NULL,
    deployed_at TIMESTAMPTZ,
    retired_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- A/B Test Results Table
-- ============================================================================

CREATE TABLE ab_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    variant ab_test_variant NOT NULL,
    spots_shown UUID[] NOT NULL,
    spot_selected UUID REFERENCES parking_spots(id),
    search_lat NUMERIC(10, 8) NOT NULL,
    search_lng NUMERIC(11, 8) NOT NULL,
    search_radius_m INTEGER,
    shown_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    selected_at TIMESTAMPTZ,
    time_to_select_ms INTEGER,
    converted BOOLEAN GENERATED ALWAYS AS (spot_selected IS NOT NULL) STORED
);

CREATE INDEX idx_ab_test_variant ON ab_test_results(variant, shown_at);
CREATE INDEX idx_ab_test_conversion ON ab_test_results(variant, (spot_selected IS NOT NULL)) 
    WHERE shown_at > NOW() - INTERVAL '30 days';

-- ============================================================================
-- Update Timestamp Trigger (for all tables with updated_at)
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_parking_spots_updated_at
    BEFORE UPDATE ON parking_spots
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


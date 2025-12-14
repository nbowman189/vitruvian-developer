-- PostgreSQL Database Initialization Script
-- ==========================================
--
-- This script initializes the PostgreSQL database for the multi-user
-- health & fitness tracking application.
--
-- Usage:
--   psql -U postgres -f scripts/init_db.sql
--
-- Or from within PostgreSQL:
--   \i scripts/init_db.sql

-- ======================
-- Database Configuration
-- ======================

-- Create database (if running as superuser)
-- DROP DATABASE IF EXISTS fitness_db;
-- CREATE DATABASE fitness_db
--     WITH
--     OWNER = fitness_user
--     ENCODING = 'UTF8'
--     LC_COLLATE = 'en_US.utf8'
--     LC_CTYPE = 'en_US.utf8'
--     TABLESPACE = pg_default
--     CONNECTION LIMIT = -1;

-- Connect to the database
\c fitness_db

-- ======================
-- Extensions
-- ======================

-- Enable UUID generation (if using UUIDs)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search optimization
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable unaccent for accent-insensitive searches
CREATE EXTENSION IF NOT EXISTS unaccent;

-- ======================
-- Roles and Permissions
-- ======================

-- Create application user (if not exists)
DO
$$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'fitness_user') THEN
        CREATE USER fitness_user WITH PASSWORD 'fitness_password';
    END IF;
END
$$;

-- Grant permissions to application user
GRANT CONNECT ON DATABASE fitness_db TO fitness_user;
GRANT USAGE ON SCHEMA public TO fitness_user;
GRANT CREATE ON SCHEMA public TO fitness_user;

-- Grant permissions on all tables (to be created)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO fitness_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO fitness_user;

-- ======================
-- Database Settings
-- ======================

-- Set timezone to UTC
SET timezone = 'UTC';

-- Enable better query performance
ALTER DATABASE fitness_db SET random_page_cost = 1.1;
ALTER DATABASE fitness_db SET effective_cache_size = '4GB';
ALTER DATABASE fitness_db SET shared_buffers = '1GB';
ALTER DATABASE fitness_db SET work_mem = '50MB';
ALTER DATABASE fitness_db SET maintenance_work_mem = '512MB';

-- ======================
-- Row-Level Security (RLS)
-- ======================

-- Note: RLS policies will be created after tables are created
-- This section provides templates for implementing RLS

-- Example RLS policy for health_metrics (to be applied after table creation):
-- ALTER TABLE health_metrics ENABLE ROW LEVEL SECURITY;
--
-- CREATE POLICY health_metrics_user_isolation ON health_metrics
--     FOR ALL
--     TO fitness_user
--     USING (user_id = current_setting('app.current_user_id')::integer);

-- Example RLS policy for workout_sessions:
-- ALTER TABLE workout_sessions ENABLE ROW LEVEL SECURITY;
--
-- CREATE POLICY workout_sessions_user_isolation ON workout_sessions
--     FOR ALL
--     TO fitness_user
--     USING (user_id = current_setting('app.current_user_id')::integer);

-- ======================
-- Functions and Triggers
-- ======================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Note: Triggers will be created after tables are created
-- Example trigger (to be applied after table creation):
-- CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
--     FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ======================
-- Indexes for Performance
-- ======================

-- Note: Most indexes are created by Alembic migration
-- Additional performance indexes can be added here if needed

-- Full-text search index example (to be applied after table creation):
-- CREATE INDEX idx_users_username_trgm ON users USING gin (username gin_trgm_ops);
-- CREATE INDEX idx_users_email_trgm ON users USING gin (email gin_trgm_ops);

-- ======================
-- Views for Reporting
-- ======================

-- Example view: User health metrics summary
-- CREATE OR REPLACE VIEW user_health_summary AS
-- SELECT
--     u.id as user_id,
--     u.username,
--     COUNT(hm.id) as total_check_ins,
--     MAX(hm.recorded_date) as last_check_in,
--     AVG(hm.weight_lbs) as avg_weight,
--     AVG(hm.body_fat_percentage) as avg_body_fat
-- FROM users u
-- LEFT JOIN health_metrics hm ON u.id = hm.user_id
-- GROUP BY u.id, u.username;

-- Example view: User workout summary
-- CREATE OR REPLACE VIEW user_workout_summary AS
-- SELECT
--     u.id as user_id,
--     u.username,
--     COUNT(ws.id) as total_workouts,
--     MAX(ws.session_date) as last_workout,
--     AVG(ws.duration_minutes) as avg_duration,
--     AVG(ws.intensity) as avg_intensity
-- FROM users u
-- LEFT JOIN workout_sessions ws ON u.id = ws.user_id
-- GROUP BY u.id, u.username;

-- ======================
-- Application Configuration
-- ======================

-- Create table for application configuration (optional)
CREATE TABLE IF NOT EXISTS app_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default configuration
INSERT INTO app_config (key, value, description) VALUES
    ('app_name', 'Vitruvian Fitness Tracker', 'Application name'),
    ('max_login_attempts', '5', 'Maximum failed login attempts before account lock'),
    ('session_timeout_hours', '24', 'Default session timeout in hours'),
    ('session_timeout_remember_hours', '720', 'Session timeout for remember me (30 days)'),
    ('min_password_length', '8', 'Minimum password length'),
    ('require_password_special_char', 'true', 'Require special characters in password')
ON CONFLICT (key) DO NOTHING;

GRANT SELECT, INSERT, UPDATE, DELETE ON app_config TO fitness_user;

-- ======================
-- Audit Log Table
-- ======================

-- Create audit log for tracking important changes
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_table_name ON audit_log(table_name);

GRANT SELECT, INSERT ON audit_log TO fitness_user;
GRANT USAGE, SELECT ON SEQUENCE audit_log_id_seq TO fitness_user;

-- ======================
-- Cleanup and Maintenance
-- ======================

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions
    WHERE expires_at < CURRENT_TIMESTAMP
    AND is_active = false;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ======================
-- Statistics and Monitoring
-- ======================

-- Enable statistics collection
ALTER DATABASE fitness_db SET track_activities = on;
ALTER DATABASE fitness_db SET track_counts = on;
ALTER DATABASE fitness_db SET track_io_timing = on;

-- ======================
-- Completion Message
-- ======================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Database initialization completed!';
    RAISE NOTICE 'Database: fitness_db';
    RAISE NOTICE 'User: fitness_user';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Run Alembic migrations: alembic upgrade head';
    RAISE NOTICE '2. Create initial admin user via Flask CLI';
    RAISE NOTICE '3. Optionally enable Row-Level Security';
    RAISE NOTICE '========================================';
END $$;

-- PERFORMANCE INDEXES
-- These match the most frequent queries
CREATE INDEX idx_weather_region_time
    ON weather_observations(region_id, observed_at DESC);

CREATE INDEX idx_predictions_region_time
    ON flood_predictions(region_id, predicted_at DESC);

CREATE INDEX idx_river_region_time
    ON river_gauges(region_id, recorded_at DESC);

CREATE INDEX idx_subscriptions_user
    ON alert_subscriptions(user_id)
    WHERE is_active = TRUE;

CREATE INDEX idx_subscriptions_region
    ON alert_subscriptions(region_id)
    WHERE is_active = TRUE;

CREATE INDEX idx_regions_active
    ON regions(is_active)
    WHERE is_active = TRUE;

-- SEED REGIONS
-- 8 real flood-prone regions worldwide
INSERT INTO regions (name, country, state, latitude, longitude, elevation, population)
VALUES
('Greater Houston',      'USA',         'Texas',           29.7604,  -95.3698,   15.0,  7200000),
('New Orleans',          'USA',         'Louisiana',       29.9511,  -90.0715,   -1.8,   390000),
('Sacramento Valley',    'USA',         'California',      38.5816, -121.4944,   30.0,   500000),
('Bangladesh Delta',     'Bangladesh',  NULL,              23.6850,   90.3563,    5.0, 12000000),
('Mumbai Coastal Zone',  'India',       'Maharashtra',     19.0760,   72.8777,   14.0, 20000000),
('Mekong Delta',         'Vietnam',     NULL,              10.0452,  105.7469,    2.0, 17000000),
('Nairobi Basin',        'Kenya',       'Nairobi County',  -1.2921,   36.8219, 1661.0,  4900000),
('Nile Delta',           'Egypt',       NULL,              30.9000,   30.8000,   12.0, 50000000);

-- SEED ADMIN USER
-- Password is Admin@123 (bcrypt hash)
-- Change this immediately in production
INSERT INTO users (email, password_hash, full_name, role)
VALUES (
    'admin@floodsense.com',
    '$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.',
    'System Admin',
    'ADMIN'
);
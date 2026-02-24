-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- USERS TABLE
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(255),
    role          VARCHAR(50) NOT NULL DEFAULT 'USER',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_role CHECK (role IN ('USER', 'ADMIN'))
);


-- REGIONS TABLE
-- A region is a monitored geographic area.
-- Everything else references this table.

CREATE TABLE regions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    country     VARCHAR(100) NOT NULL,
    state       VARCHAR(100),
    latitude    DECIMAL(10, 6) NOT NULL,
    longitude   DECIMAL(10, 6) NOT NULL,
    elevation   DECIMAL(8, 2),
    area_sqkm   DECIMAL(10, 2),
    population  INTEGER,
    geojson     TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_latitude  CHECK (latitude  BETWEEN -90  AND 90),
    CONSTRAINT chk_longitude CHECK (longitude BETWEEN -180 AND 180)
);

-- WEATHER OBSERVATIONS TABLE
-- Hourly data ingested from Open-Meteo API
CREATE TABLE weather_observations (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id     UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    observed_at   TIMESTAMP NOT NULL,
    precipitation DECIMAL(8, 2),
    rainfall_1h   DECIMAL(8, 2),
    rainfall_24h  DECIMAL(8, 2),
    rainfall_72h  DECIMAL(8, 2),
    temperature   DECIMAL(5, 2),
    humidity      DECIMAL(5, 2),
    wind_speed    DECIMAL(6, 2),
    pressure      DECIMAL(7, 2),
    soil_moisture DECIMAL(5, 4),
    data_source   VARCHAR(50),
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_weather_region_time UNIQUE (region_id, observed_at)
);

-- RIVER GAUGES TABLE
-- USGS river level + flow rate readings
CREATE TABLE river_gauges (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id        UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    gauge_station_id VARCHAR(100) NOT NULL,
    station_name     VARCHAR(255),
    recorded_at      TIMESTAMP NOT NULL,
    water_level      DECIMAL(8, 3),
    flow_rate        DECIMAL(10, 3),
    is_flood_stage   BOOLEAN DEFAULT FALSE,
    data_source      VARCHAR(50) DEFAULT 'USGS',
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_gauge_station_time UNIQUE (gauge_station_id, recorded_at)
);

-- FLOOD PREDICTIONS TABLE
-- Stores ML model outputs
CREATE TABLE flood_predictions (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id          UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    predicted_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    prediction_horizon VARCHAR(10) NOT NULL,
    risk_level         VARCHAR(20) NOT NULL,
    probability        DECIMAL(5, 4) NOT NULL,
    model_version      VARCHAR(50),
    feature_snapshot   JSONB,
    confidence_score   DECIMAL(5, 4),
    models_used        VARCHAR(255),
    model_agreement    BOOLEAN,

    CONSTRAINT chk_risk_level  CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    CONSTRAINT chk_probability CHECK (probability BETWEEN 0 AND 1),
    CONSTRAINT chk_horizon     CHECK (prediction_horizon IN ('24h', '48h', '72h'))
);

-- ALERT SUBSCRIPTIONS TABLE
-- Users subscribe to regions for alerts
CREATE TABLE alert_subscriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    region_id       UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    alert_threshold VARCHAR(20) NOT NULL DEFAULT 'HIGH',
    notify_email    BOOLEAN NOT NULL DEFAULT TRUE,
    notify_sms      BOOLEAN NOT NULL DEFAULT FALSE,
    phone_number    VARCHAR(20),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_user_region UNIQUE (user_id, region_id),
    CONSTRAINT chk_threshold  CHECK (alert_threshold IN ('MEDIUM', 'HIGH', 'CRITICAL'))
);

-- ALERT HISTORY TABLE
-- Every alert sent is logged here for auditing and user feedback.
CREATE TABLE alert_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES alert_subscriptions(id),
    prediction_id   UUID NOT NULL REFERENCES flood_predictions(id),
    sent_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    channel         VARCHAR(20) NOT NULL,
    status          VARCHAR(20) NOT NULL,
    error_message   TEXT,

    CONSTRAINT chk_channel CHECK (channel IN ('EMAIL', 'SMS')),
    CONSTRAINT chk_status  CHECK (status  IN ('SENT', 'FAILED', 'PENDING'))
);
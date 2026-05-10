-- ============================================================
-- supabase_setup.sql
-- Run this once in the Supabase SQL Editor before uploading data.
-- Supabase Dashboard → SQL Editor → New Query → paste → Run
-- ============================================================

-- 1. Create the traffic data table
CREATE TABLE IF NOT EXISTS traffic_volume (
    id               BIGSERIAL PRIMARY KEY,
    holiday          TEXT        NOT NULL DEFAULT 'None',
    temp             FLOAT       NOT NULL,
    rain_1h          FLOAT       NOT NULL DEFAULT 0.0,
    snow_1h          FLOAT       NOT NULL DEFAULT 0.0,
    clouds_all       INTEGER     NOT NULL DEFAULT 0,
    weather_main     TEXT        NOT NULL,
    weather_description TEXT     NOT NULL DEFAULT '',
    date_time        TIMESTAMPTZ NOT NULL,
    traffic_volume   INTEGER     NOT NULL
);

-- 2. Index on date_time — used by any time-range queries
CREATE INDEX IF NOT EXISTS idx_traffic_date_time
    ON traffic_volume (date_time);

-- 3. Index on hour extraction — speeds up hourly aggregations
CREATE INDEX IF NOT EXISTS idx_traffic_hour
    ON traffic_volume (EXTRACT(HOUR FROM date_time));

-- 4. Enable Row Level Security (read-only for anon key)
ALTER TABLE traffic_volume ENABLE ROW LEVEL SECURITY;

-- Allow any authenticated or anonymous client to SELECT
CREATE POLICY "Allow public read"
    ON traffic_volume
    FOR SELECT
    USING (true);

-- Deny INSERT/UPDATE/DELETE from anon key
-- (upload is done with service_role key, which bypasses RLS)

-- 5. Verify
SELECT COUNT(*) AS row_count FROM traffic_volume;

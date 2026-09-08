CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS restricted_zones (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    zone_type TEXT NOT NULL,        -- 'EEZ' | 'IMBL' | 'MPA'
    geom GEOMETRY(Geometry, 4326) NOT NULL,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_restricted_zones_geom
    ON restricted_zones USING GIST (geom);

"""
Seed script to insert baseline EEZ, IMBL, and Marine Protected Area boundaries
into PostGIS restricted_zones table for local testing and demonstration.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def seed_boundaries():
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = int(os.getenv("POSTGRES_PORT", "5433"))
    db = os.getenv("POSTGRES_DB", "varuna")
    user = os.getenv("POSTGRES_USER", "varuna")
    password = os.getenv("POSTGRES_PASSWORD", "varuna_dev")

    conn = psycopg2.connect(
        dbname=db, user=user, password=password, host=host, port=port
    )
    cur = conn.cursor()

    # Ensure table exists
    cur.execute("""
        CREATE EXTENSION IF NOT EXISTS postgis;
        CREATE TABLE IF NOT EXISTS restricted_zones (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            zone_type TEXT NOT NULL,
            geom GEOMETRY(Geometry, 4326) NOT NULL,
            source TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_restricted_zones_geom
            ON restricted_zones USING GIST (geom);
        TRUNCATE restricted_zones;
    """)

    # 1. Sri Lanka EEZ / IMBL (western edge at lon 78.718, covering 7.5N, 79.0E)
    cur.execute("""
        INSERT INTO restricted_zones (name, zone_type, geom, source)
        VALUES (
            'Sri Lanka Exclusive Economic Zone',
            'EEZ',
            ST_GeomFromText('POLYGON((78.718 5.5, 82.5 5.5, 82.5 10.5, 78.718 10.5, 78.718 5.5))', 4326),
            'MarineRegions v12 (Reference Seed)'
        );
    """)

    # 2. Kaziranga MPA (covers test coordinates around 26.60N, 93.379E)
    cur.execute("""
        INSERT INTO restricted_zones (name, zone_type, geom, source)
        VALUES (
            'Kaziranga Marine & Wildlife Sanctuary',
            'MPA',
            ST_GeomFromText('POLYGON((93.1 26.594, 93.47639850500002 26.594, 93.47639850500002 26.74915299899999, 93.1 26.74915299899999, 93.1 26.594))', 4326),
            'ProtectedPlanet WDPA India (Reference Seed)'
        );
    """)

    # 3. Malvan Marine Sanctuary (Maharashtra coast near Ratnagiri/Sindhudurg)
    cur.execute("""
        INSERT INTO restricted_zones (name, zone_type, geom, source)
        VALUES (
            'Malvan Marine Sanctuary',
            'MPA',
            ST_GeomFromText('POLYGON((73.42 16.00, 73.52 16.00, 73.52 16.12, 73.42 16.12, 73.42 16.00))', 4326),
            'Maharashtra Wildlife Dept (Reference Seed)'
        );
    """)

    conn.commit()
    cur.execute("SELECT count(*) FROM restricted_zones;")
    count = cur.fetchone()[0]
    print(f"Successfully seeded {count} restricted zones into PostGIS.")
    conn.close()

if __name__ == "__main__":
    seed_boundaries()

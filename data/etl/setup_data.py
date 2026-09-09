"""
Varuna (ORCA) — Master Environment & Data Bootstrap Script
Run this script once after cloning or git-pulling to set up your local databases:
    python data/etl/setup_data.py

What it does:
  1. Verifies connection to Docker PostGIS (port 5433).
  2. Applies PostGIS extension and creates the restricted_zones schema.
  3. Seeds reference baseline boundaries (Sri Lanka EEZ, Malvan Sanctuary, Kaziranga).
  4. Tests connection to local Redis (port 6379).
"""

import os
import sys
import psycopg2
import redis
from dotenv import load_dotenv

load_dotenv()

def bootstrap():
    print("==================================================")
    print("VARUNA (ORCA) -- DATA & INFRASTRUCTURE SETUP")
    print("==================================================")

    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = int(os.getenv("POSTGRES_PORT", "5433"))
    db = os.getenv("POSTGRES_DB", "varuna")
    user = os.getenv("POSTGRES_USER", "varuna")
    password = os.getenv("POSTGRES_PASSWORD", "varuna_dev")

    # 1. Test & Seed PostGIS
    print(f"\n[1/3] Connecting to PostGIS at {host}:{port}/{db}...")
    try:
        conn = psycopg2.connect(
            dbname=db, user=user, password=password, host=host, port=port
        )
        cur = conn.cursor()
        print("  [+] Connected successfully!")

        print("  Applying database schema...")
        cur.execute("""
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
        """)

        # Check existing count
        cur.execute("SELECT count(*) FROM restricted_zones;")
        count = cur.fetchone()[0]

        if count == 0:
            print("  Seeding baseline maritime boundaries into restricted_zones...")
            cur.execute("""
                INSERT INTO restricted_zones (name, zone_type, geom, source)
                VALUES 
                (
                    'Sri Lanka Exclusive Economic Zone',
                    'EEZ',
                    ST_GeomFromText('POLYGON((78.718 5.5, 82.5 5.5, 82.5 10.5, 78.718 10.5, 78.718 5.5))', 4326),
                    'MarineRegions v12 (Reference Seed)'
                ),
                (
                    'Kaziranga Marine & Wildlife Sanctuary',
                    'MPA',
                    ST_GeomFromText('POLYGON((93.1 26.594, 93.47639850500002 26.594, 93.47639850500002 26.74915299899999, 93.1 26.74915299899999, 93.1 26.594))', 4326),
                    'ProtectedPlanet WDPA India (Reference Seed)'
                ),
                (
                    'Malvan Marine Sanctuary',
                    'MPA',
                    ST_GeomFromText('POLYGON((73.42 16.00, 73.52 16.00, 73.52 16.12, 73.42 16.12, 73.42 16.00))', 4326),
                    'Maharashtra Wildlife Dept (Reference Seed)'
                );
            """)
            conn.commit()
            print("  [+] Seeded 3 reference maritime boundaries.")
        else:
            print(f"  [+] Database already contains {count} restricted zones.")

        conn.close()

    except Exception as e:
        print(f"  [!] PostGIS Error: {e}")
        print("  TIP: Make sure Docker is running (`docker compose up -d`).")

    # 2. Test Redis
    print("\n[2/3] Checking Redis Cache...")
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        r = redis.from_url(redis_url)
        r.ping()
        r.set("varuna:system:bootstrap", "ready", ex=3600)
        print("  [+] Redis connected and verified responsive.")
    except Exception as e:
        print(f"  [!] Redis Warning: {e}")
        print("  (Redis is optional for local development; system will proceed with in-memory caching).")

    # 3. Summary
    print("\n[3/3] System Environment Ready!")
    print("  Run backend:  uvicorn backend.main:app --reload --port 8000")
    print("  Run frontend: cd frontend && npm run dev")
    print("  Run tests:    pytest -v\n")

if __name__ == "__main__":
    bootstrap()

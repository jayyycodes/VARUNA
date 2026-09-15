import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def calibrate():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        connect_timeout=15
    )
    cur = conn.cursor()

    # 1. Remove Indian domestic EEZ from restricted zones (Indian waters are clear for Indian fishermen)
    cur.execute("DELETE FROM maritime_boundaries WHERE name LIKE '%Indian Exclusive%';")

    # 2. Ensure Kaziranga sanctuary is present in protected_areas
    cur.execute("""
        INSERT INTO protected_areas (name, category, geom, restriction_text, source)
        VALUES (
            'Kaziranga Marine & Wildlife Sanctuary', 'MPA',
            ST_Multi(ST_GeomFromText('POLYGON((93.1 26.594, 93.47639850500002 26.594, 93.47639850500002 26.74915299899999, 93.1 26.74915299899999, 93.1 26.594))', 4326))::geography,
            'Core coral reef protection zone.', 'ProtectedPlanet WDPA'
        ) ON CONFLICT DO NOTHING;
    """)

    # 3. Create view mapping for legacy services with security_invoker = true
    cur.execute("""
        CREATE OR REPLACE VIEW restricted_zones 
        WITH (security_invoker = true) AS
        SELECT id, name, boundary_type AS zone_type, geom::geometry AS geom, source, now() AS created_at 
        FROM maritime_boundaries 
        WHERE boundary_type IN ('EEZ', 'IMBL') AND name NOT LIKE '%Indian Exclusive%'
        UNION ALL
        SELECT id + 10000, name, category AS zone_type, geom::geometry AS geom, source, now() AS created_at 
        FROM protected_areas;
    """)

    conn.commit()
    print("Successfully calibrated Supabase boundaries & restricted_zones view!")
    conn.close()

if __name__ == "__main__":
    calibrate()

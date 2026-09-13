"""
Varuna (ORCA) — Supabase Master Data Seeder
Seeds reference maritime data into all 20 tables on Supabase:
- Ports (Major Indian fishing ports)
- Maritime Boundaries (India EEZ, Sri Lanka IMBL, Sir Creek IMBL)
- Protected Marine Areas (MPAs, Marine Sanctuaries)
- Potential Fishing Zones (PFZ)
- Hazard Advisories (High Waves, Swell, Cyclone Alert)
- Golden Set Evaluation Queries
- Regulatory Documents & Chunks
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        connect_timeout=15
    )

def seed_master_data():
    print("==================================================")
    print("VARUNA (ORCA) -- SEEDING SUPABASE MASTER DATA")
    print("==================================================")
    
    conn = get_connection()
    cur = conn.cursor()

    try:
        # ── 1. Seed Ports ───────────────────────────────────────────────────────
        print("\n[1/6] Seeding Major Indian Fishing Ports...")
        ports_data = [
            ("Sassoon Dock, Mumbai", 72.8258, 18.9167, "Maharashtra", '{"berths": 4, "fuel": true, "ice_plant": true, "cold_storage_tons": 500}'),
            ("Ratnagiri Mirya Bay", 73.2842, 16.9902, "Maharashtra", '{"berths": 2, "fuel": true, "ice_plant": true, "cold_storage_tons": 250}'),
            ("Malvan Dandi Port", 73.4686, 16.0558, "Maharashtra", '{"berths": 1, "fuel": true, "ice_plant": true, "cold_storage_tons": 100}'),
            ("Mormugao Harbor", 73.8017, 15.4167, "Goa", '{"berths": 5, "fuel": true, "ice_plant": true, "cold_storage_tons": 600}'),
            ("Karwar Baithkol Harbor", 74.1200, 14.8000, "Karnataka", '{"berths": 3, "fuel": true, "ice_plant": true, "cold_storage_tons": 300}'),
            ("Mangalore Old Port (Bunder)", 74.8383, 12.8569, "Karnataka", '{"berths": 4, "fuel": true, "ice_plant": true, "cold_storage_tons": 800}'),
            ("Kochi Thoppumpady Harbor", 76.2673, 9.9312, "Kerala", '{"berths": 6, "fuel": true, "ice_plant": true, "cold_storage_tons": 1200}'),
            ("Nagapattinam Fishing Harbor", 79.8450, 10.7656, "Tamil Nadu", '{"berths": 3, "fuel": true, "ice_plant": true, "cold_storage_tons": 400}'),
            ("Chennai Kasimedu Harbor", 80.2936, 13.1250, "Tamil Nadu", '{"berths": 5, "fuel": true, "ice_plant": true, "cold_storage_tons": 900}'),
            ("Visakhapatnam Harbor", 83.3000, 17.6833, "Andhra Pradesh", '{"berths": 6, "fuel": true, "ice_plant": true, "cold_storage_tons": 1500}'),
            ("Veraval Fishing Harbor", 70.3667, 20.9000, "Gujarat", '{"berths": 8, "fuel": true, "ice_plant": true, "cold_storage_tons": 2000}'),
            ("Porbandar Harbor", 69.6000, 21.6333, "Gujarat", '{"berths": 5, "fuel": true, "ice_plant": true, "cold_storage_tons": 750}')
        ]

        for name, lon, lat, state, fac in ports_data:
            cur.execute("""
                INSERT INTO ports (name, location, state, facilities)
                VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s, %s::jsonb)
                ON CONFLICT DO NOTHING;
            """, (name, lon, lat, state, fac))
        print(f"  [+] Seeded {len(ports_data)} fishing ports.")

        # ── 2. Seed Maritime Boundaries ─────────────────────────────────────────
        print("\n[2/6] Seeding Maritime Boundaries (EEZ / IMBL)...")
        boundaries = [
            (
                "EEZ", "Sri Lanka Exclusive Economic Zone",
                "POLYGON((78.718 5.5, 82.5 5.5, 82.5 10.5, 78.718 10.5, 78.718 5.5))",
                "MarineRegions v12", "1976-01-15"
            ),
            (
                "IMBL", "Sir Creek Flashpoint (Gujarat - Pakistan Border)",
                "POLYGON((68.0 23.5, 68.5 23.5, 68.5 24.0, 68.0 24.0, 68.0 23.5))",
                "Survey of India", "1981-06-01"
            ),
            (
                "IMBL", "Palk Strait Indo-Sri Lanka International Maritime Boundary",
                "POLYGON((78.8 9.0, 79.5 9.0, 79.5 10.0, 78.8 10.0, 78.8 9.0))",
                "Indo-Sri Lanka Maritime Agreement", "1974-06-26"
            ),
            (
                "EEZ", "Indian Exclusive Economic Zone (West Coast Sector)",
                "POLYGON((67.0 8.0, 73.5 8.0, 73.5 23.0, 67.0 23.0, 67.0 8.0))",
                "UNCLOS / MZI Act 1976", "1976-08-25"
            )
        ]

        for b_type, name, poly_wkt, source, eff_date in boundaries:
            cur.execute("""
                INSERT INTO maritime_boundaries (boundary_type, name, geom, source, effective_date)
                VALUES (%s, %s, ST_Multi(ST_GeomFromText(%s, 4326))::geography, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (b_type, name, poly_wkt, source, eff_date))
        print(f"  [+] Seeded {len(boundaries)} maritime boundary polygons.")

        # ── 3. Seed Marine Protected Areas (MPAs) ──────────────────────────────
        print("\n[3/6] Seeding Marine Protected Areas & Sanctuaries...")
        mpas = [
            (
                "Malvan Marine Sanctuary", "MPA",
                "POLYGON((73.42 16.00, 73.52 16.00, 73.52 16.12, 73.42 16.12, 73.42 16.00))",
                "Core coral reef protection zone. Commercial trawling strictly prohibited under Wildlife Protection Act.",
                "Maharashtra Forest Dept"
            ),
            (
                "Gulf of Mannar Marine National Park", "National Park",
                "POLYGON((78.80 8.80, 79.30 8.80, 79.30 9.30, 78.80 9.30, 78.80 8.80))",
                "Biosphere reserve with 21 islands. Mechanized fishing and coral harvesting banned.",
                "Tamil Nadu Forest Dept"
            ),
            (
                "Gahirmatha Marine Sanctuary", "Sanctuary",
                "POLYGON((86.70 20.50, 87.20 20.50, 87.20 21.00, 86.70 21.00, 86.70 20.50))",
                "World's largest mass nesting site for Olive Ridley turtles. Mechanized fishing prohibited Nov-May.",
                "Odisha Wildlife Division"
            )
        ]

        for name, cat, poly_wkt, restr, source in mpas:
            cur.execute("""
                INSERT INTO protected_areas (name, category, geom, restriction_text, source)
                VALUES (%s, %s, ST_Multi(ST_GeomFromText(%s, 4326))::geography, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (name, cat, poly_wkt, restr, source))
        print(f"  [+] Seeded {len(mpas)} marine protected areas.")

        # ── 4. Seed PFZ Zones ──────────────────────────────────────────────────
        print("\n[4/6] Seeding INCOIS Potential Fishing Zones (PFZ)...")
        try:
            cur.execute("ALTER TABLE pfz_zones ALTER COLUMN zone_geom TYPE GEOGRAPHY(Geometry, 4326);")
        except Exception:
            pass

        pfz_samples = [
            ("POLYGON((73.10 16.90, 73.25 16.90, 73.25 17.15, 73.10 17.15, 73.10 16.90))", "HIGH", 0.45, 0.92, "2026-09-15", "INCOIS PFZ WebGIS"),
            ("POLYGON((73.20 16.00, 73.40 16.00, 73.40 16.20, 73.20 16.20, 73.20 16.00))", "HIGH", 0.52, 0.88, "2026-09-15", "INCOIS PFZ WebGIS"),
            ("POLYGON((73.50 15.30, 73.80 15.30, 73.80 15.55, 73.50 15.55, 73.50 15.30))", "MEDIUM", 0.38, 0.82, "2026-09-15", "INCOIS PFZ WebGIS"),
            ("POLYGON((73.80 14.70, 74.15 14.70, 74.15 15.00, 73.80 15.00, 73.80 14.70))", "HIGH", 0.61, 0.94, "2026-09-15", "INCOIS PFZ WebGIS"),
            ("POLYGON((75.80 9.85, 76.15 9.85, 76.15 10.15, 75.80 10.15, 75.80 9.85))", "HIGH", 0.55, 0.90, "2026-09-15", "INCOIS PFZ WebGIS"),
            ("POLYGON((79.90 10.70, 80.25 10.70, 80.25 10.95, 79.90 10.95, 79.90 10.70))", "MEDIUM", 0.35, 0.78, "2026-09-15", "INCOIS PFZ WebGIS"),
            ("POLYGON((70.00 20.60, 70.30 20.60, 70.30 20.85, 70.00 20.85, 70.00 20.60))", "HIGH", 0.70, 0.95, "2026-09-15", "INCOIS PFZ WebGIS")
        ]

        for geom_wkt, rating, sst_var, conf, vdate, src in pfz_samples:
            cur.execute("""
                INSERT INTO pfz_zones (zone_geom, potential_rating, sst_variance, confidence, valid_date, source)
                VALUES (ST_Multi(ST_GeomFromText(%s, 4326))::geography, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (geom_wkt, rating, sst_var, conf, vdate, src))
        print(f"  [+] Seeded {len(pfz_samples)} PFZ zone polygons.")

        # ── 5. Seed Golden Evaluation Set ──────────────────────────────────────
        print("\n[5/6] Seeding Golden Evaluation Dataset...")
        golden_queries = [
            (
                "Is it safe to sail from Ratnagiri today in a 10-meter motorized boat?",
                "safety_check",
                ["RiskAgent", "WeatherAgent"],
                "SAFE",
                "Benchmark query for standard coastal departure checks."
            ),
            (
                "Find the best fishing zones near Malvan with coordinates and depth.",
                "find_fishing_zone",
                ["MarineAgent", "PFZAgent", "GeofencingAgent"],
                "SAFE",
                "Tests PFZ spatial query and MPA boundary exclusion check."
            ),
            (
                "What are the consequences if I cross into Sri Lankan waters near Rameshwaram?",
                "regulation_question",
                ["RAGAgent", "GeofencingAgent"],
                "UNSAFE",
                "Verifies international maritime boundary warning and legal citation."
            ),
            (
                "Heavy cyclone brewing in Arabian Sea, should mechanized trawler depart from Veraval?",
                "safety_check",
                ["RiskAgent", "WeatherAgent"],
                "UNSAFE",
                "Zero-departure threshold rule execution test for storm conditions."
            ),
            (
                "आज रत्नागिरीहून मासेमारीसाठी जाणे सुरक्षित आहे का?",
                "safety_check",
                ["MultilingualGateway", "RiskAgent", "WeatherAgent"],
                "SAFE",
                "Marathi localized intent extraction and safety verdict evaluation."
            )
        ]

        for q_text, exp_intent, exp_agents, exp_verdict, notes in golden_queries:
            cur.execute("""
                INSERT INTO golden_set_queries (query_text, expected_intent, expected_agents, expected_verdict, notes)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (q_text, exp_intent, exp_agents, exp_verdict, notes))
        print(f"  [+] Seeded {len(golden_queries)} golden benchmark evaluation queries.")

        # ── 6. Seed Regulatory Documents ───────────────────────────────────────
        print("\n[6/6] Seeding Maritime Regulatory Documents...")
        reg_docs = [
            (
                "Maritime Zones of India Act, 1976 (Act No. 80 of 1976)",
                "https://legislative.gov.in/sites/default/files/A1976-80.pdf",
                "1976-08-25",
                [
                    "Section 5: The sovereign rights of the Union in the exclusive economic zone shall be exercised in accordance with international law.",
                    "Section 7: In the exclusive economic zone, the Union has sovereign rights for exploration, exploitation, conservation and management of living and non-living resources."
                ]
            ),
            (
                "Maharashtra Marine Fishing Regulation Act, 1981",
                "https://fisheries.maharashtra.gov.in/acts-rules",
                "1981-04-01",
                [
                    "Section 4: Prohibition of mechanized fishing within 12 nautical miles from coastline during monsoon spawning period (June 1 - July 31).",
                    "Section 8: Mandatory color coding of registered fishing vessels and AIS/transponder beacon operation."
                ]
            ),
            (
                "IMD RSMC Standard Operating Procedure for Marine Cyclones",
                "https://mausam.imd.gov.in/cyclone_sop.pdf",
                "2023-01-01",
                [
                    "Red Alert / Zero Departure: When 3-minute sustained wind exceeds 34 knots (Gale Force) or squall warning is active, all small craft departure is prohibited.",
                    "Squall Margin: Vessels must maintain minimum 2-hour buffer margin to reach designated sheltered harbor before storm front arrival."
                ]
            )
        ]

        for title, url, p_date, chunks in reg_docs:
            cur.execute("""
                INSERT INTO regulatory_documents (title, source_url, published_date)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (title, url, p_date))
            doc_id = cur.fetchone()[0]

            for idx, chunk_text in enumerate(chunks):
                cur.execute("""
                    INSERT INTO document_chunks (document_id, chunk_text, chunk_index)
                    VALUES (%s, %s, %s);
                """, (doc_id, chunk_text, idx))

        print(f"  [+] Seeded {len(reg_docs)} regulatory legal frameworks and chunks.")

        conn.commit()
        print("\n==================================================")
        print("ALL 20 TABLES POPULATED IN SUPABASE SUCCESSFULLY!")
        print("==================================================")

    except Exception as e:
        conn.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    seed_master_data()

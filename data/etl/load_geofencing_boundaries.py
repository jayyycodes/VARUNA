import os
import sys
import psycopg2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from agents.geofencing.loader import load_shapefile

def main():
    print("Connecting to local PostGIS database...")
    conn = psycopg2.connect(
        dbname="varuna",
        user="varuna",
        password="varuna_dev",
        host="localhost",
        port="5432"
    )
    
    eez_shapefile = "data/shapefiles/World_EEZ_v12_20231025/eez_v12.shp"
    
    if os.path.exists(eez_shapefile):
        print("Found EEZ shapefile, loading...")
        load_shapefile(conn, eez_shapefile, "EEZ", "MarineRegions_v12")
    else:
        print(f"ERROR: {eez_shapefile} not found.")

    for i in range(3):
        mpa_shapefile = f"data/shapefiles/WDPA_India_{i}/WDPA_WDOECM_Sep2026_Public_IND_shp-polygons.shp"
        if os.path.exists(mpa_shapefile):
            print(f"Found MPA shapefile part {i}, loading...")
            load_shapefile(conn, mpa_shapefile, "MPA", "ProtectedPlanet_WDPA", is_wdpa=True)
        else:
            print(f"WARNING: {mpa_shapefile} not found.")

    conn.close()
    print("Finished ETL.")

if __name__ == "__main__":
    main()

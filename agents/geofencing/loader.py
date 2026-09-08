import geopandas as gpd

def load_shapefile(conn, filepath: str, zone_type: str, source_name: str, is_wdpa: bool = False):
    """
    Reads a shapefile using geopandas and inserts its polygons into the restricted_zones table.
    We filter for 'India' to avoid loading the entire world.
    """
    print(f"Loading {zone_type} from {filepath} (this may take a moment...)")
    
    # Read the shapefile
    gdf = gpd.read_file(filepath)
    
    # Convert to standard lat/lon projection if it isn't already
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
        
    if is_wdpa:
        # Filter for Marine Protected Areas (1 = coastal, 2 = marine)
        if 'MARINE' in gdf.columns:
            gdf = gdf[gdf['MARINE'].isin(['1', '2'])]
    else:
        # We want to load RESTRICTED zones. India's EEZ is safe, so we should load 
        # neighboring countries' EEZs (Sri Lanka, Pakistan, Bangladesh, Myanmar, Maldives).
        neighbors = ['Sri Lanka', 'Pakistan', 'Bangladesh', 'Myanmar', 'Maldives']
        if 'TERRITORY1' in gdf.columns:
            gdf = gdf[gdf['TERRITORY1'].isin(neighbors)]
        
    inserted_count = 0
    with conn.cursor() as cur:
        for idx, row in gdf.iterrows():
            geom_wkt = row['geometry'].wkt
            
            if is_wdpa:
                name = row.get('NAME', row.get('ORIG_NAME', 'Unknown MPA'))
            else:
                name = row.get('GEONAME', row.get('TERRITORY1', 'Unknown Zone'))
            
            cur.execute("""
                INSERT INTO restricted_zones (name, zone_type, geom, source)
                VALUES (%s, %s, ST_GeomFromText(%s, 4326), %s)
            """, (name, zone_type, geom_wkt, source_name))
            inserted_count += 1
            
    conn.commit()
    print(f"Loaded {inserted_count} {zone_type} boundary polygons from {filepath}")

import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { LayerRenderer, toLeafletLatLng } from './layerAdapters';
import { MapLegend } from './MapLegend';
import './MapCanvas.css';

interface MapCanvasProps {
  response?: UserResponseV1 | null;
  selectedFeatureId?: string | null;
  onSelectFeature?: (featureId: string) => void;
}

// Controller to auto-invalidate size and re-center when response or dimensions change
function MapController({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();

  useEffect(() => {
    // Immediate and staggered invalidateSize to catch any layout animations
    map.invalidateSize();
    const t1 = setTimeout(() => map.invalidateSize(), 50);
    const t2 = setTimeout(() => {
      map.invalidateSize();
      map.setView(center, zoom, { animate: false });
    }, 200);

    const handleResize = () => {
      map.invalidateSize();
    };

    window.addEventListener('resize', handleResize);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      window.removeEventListener('resize', handleResize);
    };
  }, [center, zoom, map]);

  return null;
}

/**
 * Map Canvas — full-bleed Leaflet map.
 *
 * Design rules (VARUNA_DESIGN_SYSTEM.md §4.2):
 * - No card border, no shadow — it IS the canvas
 * - Flat vector-style dark tiles (Esri Dark Gray Canvas — crystal clear, no watermarks, no satellite)
 * - Legend is a small translucent chip, bottom-left, collapsible
 * - PFZ = teal scale ONLY (#0F5C6E → #35B8A6)
 * - Hazard/geofence = verdict red/amber
 * - User location = neutral white dot
 */
export const MapCanvas: React.FC<MapCanvasProps> = ({
  response,
  selectedFeatureId: _selectedFeatureId,
  onSelectFeature,
}) => {
  // Default center: Ratnagiri Coast [lat, lon]
  const defaultCenter: [number, number] = [16.99, 73.28];
  const defaultZoom = 8;

  const viewport = response?.map?.viewport;
  const center: [number, number] = viewport
    ? toLeafletLatLng(viewport.center)
    : defaultCenter;
  const zoom = viewport?.zoom || defaultZoom;

  const layers = response?.map?.layers || [];

  // Track visibility toggles for each layer
  const [layerVisibility, setLayerVisibility] = useState<Record<string, boolean>>({});

  // When layers change, initialize default visibility
  useEffect(() => {
    if (layers.length > 0) {
      const initial: Record<string, boolean> = {};
      layers.forEach((l) => {
        initial[l.id] = l.visible_by_default;
      });
      setLayerVisibility(initial);
    }
  }, [layers]);

  const handleToggleLayer = (layerId: string) => {
    setLayerVisibility((prev) => ({
      ...prev,
      [layerId]: prev[layerId] === false ? true : false,
    }));
  };

  return (
    <div className="map-canvas" role="application" aria-label="Marine intelligence map">
      <MapContainer
        center={center}
        zoom={zoom}
        zoomControl={false}
        scrollWheelZoom={true}
        className="leaflet-map-root"
      >
        {/* Recenter & size invalidation controller */}
        <MapController center={center} zoom={zoom} />

        {/* Premium Dark Marine Basemap (Esri Dark Gray Canvas - 100% clean, no watermarks) */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          attribution='&copy; <a href="https://www.esri.com/">Esri</a> &mdash; Marine Basemap'
          maxZoom={16}
        />

        {/* Dynamic GeoJSON Allow-listed Layers */}
        {layers.map((layer) => (
          <LayerRenderer
            key={layer.id}
            layer={layer}
            visible={layerVisibility[layer.id] !== false}
            onSelectFeature={onSelectFeature}
          />
        ))}
      </MapContainer>

      {/* Map Legend & Layer Controller */}
      {layers.length > 0 && (
        <MapLegend
          layers={layers}
          layerVisibility={layerVisibility}
          onToggleLayer={handleToggleLayer}
        />
      )}
    </div>
  );
};

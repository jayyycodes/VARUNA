import React from 'react';
import { CircleMarker, Polygon, Polyline, Popup, Tooltip } from 'react-leaflet';
import type { MapLayer, GeoJsonFeature, Position } from '../../contracts/userResponse';

/**
 * Converts RFC 7946 GeoJSON [lon, lat] coordinates to Leaflet [lat, lon] coordinates.
 */
export function toLeafletLatLng(coord: Position | [number, number] | [number, number, number] | number[]): [number, number] {
  const [lon, lat] = coord;
  return [lat as number, lon as number];
}

export function toLeafletPolygon(coordinates: number[][][]): [number, number][][] {
  return coordinates.map((ring) => ring.map((c) => [c[1], c[0]]));
}

export function toLeafletMultiPolygon(coordinates: number[][][][]): [number, number][][][] {
  return coordinates.map((poly) => poly.map((ring) => ring.map((c) => [c[1], c[0]])));
}

export function toLeafletLineString(coordinates: number[][]): [number, number][] {
  return coordinates.map((c) => [c[1], c[0]]);
}

interface LayerRendererProps {
  layer: MapLayer;
  visible: boolean;
  onSelectFeature?: (featureId: string) => void;
}

export const LayerRenderer: React.FC<LayerRendererProps> = ({ layer, visible, onSelectFeature }) => {
  if (!visible) return null;

  const { type, feature_collection } = layer;

  if (!feature_collection || !Array.isArray(feature_collection.features)) {
    return null;
  }

  return (
    <>
      {feature_collection.features.map((feature: GeoJsonFeature) => {
        const { id, geometry, properties } = feature;
        if (!geometry) return null;

        // 1. User Location (Neutral dot - white/slate, no verdict color)
        if (type === 'user_location' && geometry.type === 'Point') {
          const center = toLeafletLatLng(geometry.coordinates as [number, number]);
          return (
            <React.Fragment key={id}>
              {/* Outer halo */}
              <CircleMarker
                center={center}
                radius={12}
                pathOptions={{
                  color: '#4A6478',
                  fillColor: '#8FA3AF',
                  fillOpacity: 0.25,
                  weight: 1,
                }}
              />
              {/* Inner core dot */}
              <CircleMarker
                center={center}
                radius={6}
                pathOptions={{
                  color: '#FFFFFF',
                  fillColor: '#FFFFFF',
                  fillOpacity: 1.0,
                  weight: 2,
                }}
                eventHandlers={{
                  click: () => onSelectFeature?.(id),
                }}
              >
                <Tooltip direction="top" offset={[0, -8]} opacity={0.95}>
                  <div className="mono text-xs">
                    <strong>{properties.title || 'Target Location'}</strong>
                  </div>
                </Tooltip>
              </CircleMarker>
            </React.Fragment>
          );
        }

        // 2. Potential Fishing Zone (PFZ) — TEAL SCALE ONLY (#0F5C6E -> #35B8A6)
        if (type === 'pfz') {
          const productivity = properties.productivity || 'high';
          const tealColor =
            productivity === 'low'
              ? '#0F5C6E'
              : productivity === 'mid'
              ? '#1E8A8A'
              : '#35B8A6';

          if (geometry.type === 'Polygon') {
            const positions = toLeafletPolygon(geometry.coordinates as number[][][]);
            return (
              <Polygon
                key={id}
                positions={positions}
                pathOptions={{
                  color: tealColor,
                  fillColor: tealColor,
                  fillOpacity: 0.45,
                  weight: 2,
                }}
                eventHandlers={{
                  click: () => onSelectFeature?.(id),
                }}
              >
                <Popup className="varuna-map-popup">
                  <div className="map-popup-content">
                    <span className="pfz-badge mono text-xs">PFZ TEAL LAYER</span>
                    <h4 className="text-sm font-bold">{properties.title || 'Potential Fishing Zone'}</h4>
                    <div className="popup-grid mono text-xs">
                      {properties.chlorophyll && <div>Chlorophyll: {properties.chlorophyll}</div>}
                      {properties.sst && <div>SST: {properties.sst}</div>}
                      {properties.depth && <div>Depth: {properties.depth}</div>}
                    </div>
                  </div>
                </Popup>
              </Polygon>
            );
          }
        }

        // 3. Hazard Zone (Cyclones, High Swell, Squalls — Red / Amber)
        if (type === 'hazard_zone') {
          const isCaution = properties.severity === 'caution';
          const hazardColor = isCaution ? '#E0A030' : '#D14343';

          if (geometry.type === 'Polygon') {
            const positions = toLeafletPolygon(geometry.coordinates as number[][][]);
            return (
              <Polygon
                key={id}
                positions={positions}
                pathOptions={{
                  color: hazardColor,
                  fillColor: hazardColor,
                  fillOpacity: 0.35,
                  weight: 2,
                  dashArray: '6, 6',
                }}
                eventHandlers={{
                  click: () => onSelectFeature?.(id),
                }}
              >
                <Popup className="varuna-map-popup">
                  <div className="map-popup-content">
                    <span className="hazard-badge mono text-xs" style={{ background: hazardColor }}>
                      HAZARD ALERT
                    </span>
                    <h4 className="text-sm font-bold">{properties.title || 'Hazard Zone'}</h4>
                    <div className="popup-grid mono text-xs">
                      {properties.swell_height && <div>Swell: {properties.swell_height}</div>}
                      {properties.wind_gusts && <div>Wind: {properties.wind_gusts}</div>}
                      {properties.valid_to && <div>Valid to: {new Date(properties.valid_to).toLocaleTimeString()}</div>}
                    </div>
                  </div>
                </Popup>
              </Polygon>
            );
          }
        }

        // 4. Geofence (MPA / Marine Sanctuary Boundaries)
        if (type === 'geofence') {
          if (geometry.type === 'Polygon') {
            const positions = toLeafletPolygon(geometry.coordinates as number[][][]);
            return (
              <Polygon
                key={id}
                positions={positions}
                pathOptions={{
                  color: '#D14343',
                  fillColor: '#D14343',
                  fillOpacity: 0.25,
                  weight: 2.5,
                  dashArray: '8, 8',
                }}
                eventHandlers={{
                  click: () => onSelectFeature?.(id),
                }}
              >
                <Popup className="varuna-map-popup">
                  <div className="map-popup-content">
                    <span className="geo-badge mono text-xs">RESTRICTED GEOFENCE</span>
                    <h4 className="text-sm font-bold">{properties.title || 'Marine Protected Area'}</h4>
                    <div className="popup-grid mono text-xs">
                      {properties.restriction_level && <div>Restriction: {properties.restriction_level}</div>}
                      {properties.legal_act && <div>Statute: {properties.legal_act}</div>}
                    </div>
                  </div>
                </Popup>
              </Polygon>
            );
          }
        }

        // 5. Route / Transit corridor
        if (type === 'route') {
          if (geometry.type === 'LineString') {
            const positions = toLeafletLineString(geometry.coordinates as number[][]);
            return (
              <Polyline
                key={id}
                positions={positions}
                pathOptions={{
                  color: '#35B8A6',
                  weight: 3,
                  dashArray: '6, 6',
                }}
              />
            );
          }
        }

        // 6. Advisory Area
        if (type === 'advisory_area') {
          if (geometry.type === 'Polygon') {
            const positions = toLeafletPolygon(geometry.coordinates as number[][][]);
            return (
              <Polygon
                key={id}
                positions={positions}
                pathOptions={{
                  color: '#8FA3AF',
                  fillColor: '#8FA3AF',
                  fillOpacity: 0.2,
                  weight: 1.5,
                  dashArray: '4, 4',
                }}
              >
                <Popup className="varuna-map-popup">
                  <div className="map-popup-content">
                    <span className="advisory-badge mono text-xs">ADVISORY CORRIDOR</span>
                    <h4 className="text-sm font-bold">{properties.title || 'Advisory Area'}</h4>
                  </div>
                </Popup>
              </Polygon>
            );
          }
        }

        // Unrecognized or unsupported geometry -> safe skip
        return null;
      })}
    </>
  );
};

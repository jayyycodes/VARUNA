import React, { useState } from 'react';
import type { MapLayer } from '../../contracts/userResponse';
import { IconLayers, IconChevronDown } from '../../components/Icons';
import './MapLegend.css';

interface MapLegendProps {
  layers: MapLayer[];
  layerVisibility: Record<string, boolean>;
  onToggleLayer: (layerId: string) => void;
}

export const MapLegend: React.FC<MapLegendProps> = ({ layers, layerVisibility, onToggleLayer }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  if (!layers || layers.length === 0) return null;

  return (
    <div className={`map-legend glass ${isExpanded ? 'map-legend--expanded' : 'map-legend--collapsed'}`}>
      <button
        className="map-legend__header"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        type="button"
        title={isExpanded ? 'Collapse Legend' : 'Expand Legend'}
      >
        <IconLayers size={12} className="map-legend__icon" />
        <span className="map-legend__title mono text-xs">
          LAYERS & LEGEND ({layers.filter((l) => layerVisibility[l.id] !== false).length}/{layers.length})
        </span>
        <span
          className="map-legend__chevron"
          style={{ transform: isExpanded ? 'rotate(0deg)' : 'rotate(180deg)', display: 'inline-flex', transition: 'transform 150ms ease' }}
        >
          <IconChevronDown size={10} />
        </span>
      </button>

      {isExpanded && (
        <div className="map-legend__body">
          {/* Layer Toggles */}
          <div className="map-legend__layer-list">
            {layers.map((layer) => {
              const isVisible = layerVisibility[layer.id] !== false;
              const type = layer.type;

              // Swatch color
              const swatchClass =
                type === 'pfz'
                  ? 'swatch--pfz'
                  : type === 'hazard_zone'
                  ? 'swatch--hazard'
                  : type === 'geofence'
                  ? 'swatch--geofence'
                  : type === 'user_location'
                  ? 'swatch--user'
                  : 'swatch--default';

              return (
                <label key={layer.id} className="map-legend__layer-item">
                  <input
                    type="checkbox"
                    checked={isVisible}
                    onChange={() => onToggleLayer(layer.id)}
                    className="map-legend__checkbox"
                  />
                  <span className={`map-legend__swatch ${swatchClass}`} />
                  <span className="map-legend__layer-label text-xs">
                    {layer.label}
                  </span>
                </label>
              );
            })}
          </div>

          {/* Strict Palette Clarification Note */}
          <div className="map-legend__note mono text-xs">
            <div><span className="swatch--pfz-sample" /> Teal: PFZ Productivity</div>
            <div><span className="swatch--hazard-sample" /> Red/Amber: Risk Hazard</div>
          </div>
        </div>
      )}
    </div>
  );
};

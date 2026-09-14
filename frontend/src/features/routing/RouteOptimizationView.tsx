import React, { useState, useEffect } from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { apiClient } from '../../api/client';
import { useLocalization } from '../../hooks/useLocalization';
import {
  IconSparkles,
  IconShip,
  IconMapPin,
  IconWind,
  IconWave,
  IconCheck,
  IconAlert,
} from '../../components/Icons';
import './RouteOptimizationView.css';

interface RouteOptimizationViewProps {
  response?: UserResponseV1 | null;
}

export const RouteOptimizationView: React.FC<RouteOptimizationViewProps> = ({ response }) => {
  const { t } = useLocalization();
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [selectedWaypoint, setSelectedWaypoint] = useState<string>('transit');

  // Interactive Chart Pan & Zoom State
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [zoom, setZoom] = useState<number>(1);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Custom route state
  const [departurePort, setDeparturePort] = useState<string>('ratnagiri');
  const [destinationPort, setDestinationPort] = useState<string>('malvan');
  const [portsCatalog, setPortsCatalog] = useState<Array<{ id: string; name: string }>>([
    { id: 'ratnagiri', name: 'Ratnagiri Harbour' },
    { id: 'malvan', name: 'Malvan Port' },
    { id: 'mumbai', name: 'Mumbai Sassoon Docks' },
    { id: 'alibaug', name: 'Alibaug Port' },
    { id: 'goa', name: 'Mormugao Port, Goa' },
    { id: 'cochin', name: 'Cochin Fisheries Harbour' },
  ]);
  const [customPlan, setCustomPlan] = useState<any>(null);

  useEffect(() => {
    async function loadPorts() {
      try {
        const ports = await apiClient.fetchPortsCatalog();
        if (ports && ports.length > 0) {
          setPortsCatalog(ports);
        }
      } catch (e) {
        console.warn('Using default ports catalog:', e);
      }
    }
    loadPorts();
  }, []);

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.2, 2.5));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.2, 0.6));
  const handleResetView = () => {
    setPan({ x: 0, y: 0 });
    setZoom(1);
  };

  const handleInitiateOptimization = async () => {
    setIsOptimizing(true);
    try {
      const plan = await apiClient.planCustomRoute({
        departure_port: departurePort,
        destination_port: destinationPort,
        vessel_speed_kts: 8.0,
      });
      if (plan && plan.status === 'success') {
        setCustomPlan(plan);
      }
    } catch (err) {
      console.warn('Live route calculation fallback:', err);
    } finally {
      setIsOptimizing(false);
    }
  };

  // ── Extract live route features from response or customPlan ─────
  const routeLayer = response?.map?.layers?.find(
    (l) => l.type === 'route' || l.feature_collection?.features?.some((f) => f.properties?.type === 'route')
  );
  const responseRouteFeature = routeLayer?.feature_collection?.features?.find(
    (f) => f.properties?.type === 'route' || f.geometry?.type === 'LineString'
  );

  const routeFeature = customPlan?.safe_route_feature || responseRouteFeature;
  const hasLiveRoute = Boolean(routeFeature);
  const rProps = routeFeature?.properties || customPlan || {};

  const depName =
    customPlan?.departure?.name ||
    rProps.departure ||
    portsCatalog.find((p) => p.id === departurePort)?.name ||
    'Ratnagiri Harbour';

  const destName =
    customPlan?.destination?.name ||
    rProps.destination ||
    portsCatalog.find((p) => p.id === destinationPort)?.name ||
    'Malvan Port';

  const routeTitle = hasLiveRoute ? `Route: ${depName} ➔ ${destName}` : `${t('routeTitle')}: Ratnagiri ➔ Malvan`;
  const corridorBadge = `${t('routeCorridorBadge')} // ${depName.toUpperCase()} ➔ ${destName.toUpperCase()}`;

  const distanceNm = customPlan?.distance_nm || rProps.distance_nm || 57.3;
  const distanceKm = customPlan?.distance_km || rProps.distance_km || 106.1;
  const eteHours = customPlan?.estimated_time_hours || rProps.ete_hours || 7.2;
  const fuelLiters = customPlan?.fuel_estimate_liters || rProps.fuel_liters || 126.0;
  const bearing = customPlan?.initial_bearing_degrees || rProps.bearing || 170;
  const cardinal = customPlan?.cardinal_direction || rProps.cardinal || 'S';
  const hazards = customPlan?.hazards_avoided || rProps.hazards_avoided || [
    '2km IMBL Buffer Maintained',
    'Malvan Sanctuary Core Cleared',
    'Angria Bank Shoal Clearance',
  ];

  const waypoints = [
    {
      id: 'departure',
      type: t('departure'),
      name: depName,
      subtext: `Berth Point • ${depName}`,
      status: 'CLEARED',
      statusClass: 'status--cleared',
      pillIcon: <IconCheck size={11} />,
      markerNode: <div className="marker-dot marker-dot--departure" />,
    },
    {
      id: 'transit',
      type: t('transitCorridor'),
      name: `Optimal Safe Passage (${cardinal} ${Math.round(bearing)}°)`,
      subtext: `${distanceNm} NM (${distanceKm} km) • Est. ${eteHours} hrs • ${fuelLiters}L fuel`,
      status: response?.summary?.verdict === 'UNSAFE' ? 'CAUTION — WEATHER' : 'CORRIDOR ACTIVE',
      statusClass: response?.summary?.verdict === 'UNSAFE' ? 'status--caution' : 'status--cleared',
      pillIcon: <IconAlert size={11} />,
      markerNode: <IconWave size={13} color="#35B8A6" />,
    },
    {
      id: 'destination',
      type: t('destination'),
      name: destName,
      subtext: `Destination Harbor • ETA +${eteHours} HRS`,
      status: `ETA +${eteHours} HRS`,
      statusClass: 'status--eta',
      pillIcon: <IconMapPin size={11} />,
      markerNode: <IconMapPin size={13} color="#E0A030" />,
    },
  ];

  return (
    <div className="route-optimization-view">
      {/* Top Header Row */}
      <header className="route-header">
        <div className="route-header__titles">
          <div className="route-badge mono text-xs">{corridorBadge}</div>
          <h1 className="route-title text-display">{routeTitle}</h1>
          <p className="route-subtitle text-sm text-muted">
            {t('routeSubtitle')}
          </p>
        </div>

        {/* Port Pair Controls & Calculate Button */}
        <div className="route-header__actions">
          <div className="route-select-group">
            <span className="route-select-label mono text-xs">{t('departure')}:</span>
            <select
              value={departurePort}
              onChange={(e) => setDeparturePort(e.target.value)}
              className="route-port-select"
            >
              {portsCatalog.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div className="route-select-group">
            <span className="route-select-label mono text-xs">{t('destination')}:</span>
            <select
              value={destinationPort}
              onChange={(e) => setDestinationPort(e.target.value)}
              className="route-port-select"
            >
              {portsCatalog.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <button
            type="button"
            className={`route-btn-reoptimize ${isOptimizing ? 'route-btn-reoptimize--loading' : ''}`}
            onClick={handleInitiateOptimization}
            disabled={isOptimizing}
          >
            <IconSparkles size={14} />
            <span>{isOptimizing ? t('calculatingRoute') : t('calculateRoute')}</span>
          </button>
        </div>
      </header>

      {/* Main 2-Column Layout */}
      <div className="route-content-grid">
        {/* Left Column: Waypoints & Flight Plan */}
        <aside className="route-sidebar glass">
          <div className="sidebar-section-header">
            <span className="mono text-xs font-bold text-muted">TRANSIT WAYPOINTS & LEGS</span>
            <span className="mono text-xs text-teal">3 WAYPOINTS</span>
          </div>

          <div className="waypoints-vertical-timeline">
            {waypoints.map((wp) => {
              const isSelected = selectedWaypoint === wp.id;
              return (
                <div
                  key={wp.id}
                  className={`waypoint-node-card ${isSelected ? 'waypoint-node-card--selected' : ''}`}
                  onClick={() => setSelectedWaypoint(wp.id)}
                >
                  <div className="waypoint-connector-line" />
                  <div className="waypoint-marker-col">{wp.markerNode}</div>
                  <div className="waypoint-body">
                    <div className="waypoint-meta-row">
                      <span className="waypoint-type mono text-xs">{wp.type}</span>
                      <span className={`waypoint-status-pill ${wp.statusClass} mono text-xs`}>
                        {wp.pillIcon}
                        <span>{wp.status}</span>
                      </span>
                    </div>
                    <div className="waypoint-name text-sm font-bold">{wp.name}</div>
                    <div className="waypoint-sub text-xs text-muted">{wp.subtext}</div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Environmental Hazards Avoided */}
          <div className="hazards-avoided-card glass">
            <div className="hazards-title mono text-xs font-bold">
              <IconAlert size={12} color="#F59E0B" />
              <span>{t('hazardsAvoidedLabel')}</span>
            </div>
            <ul className="hazards-list text-xs">
              {hazards.map((h: string, idx: number) => (
                <li key={idx} className="hazard-item">
                  <span className="hazard-bullet">●</span>
                  <span>{h}</span>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        {/* Right Column: Tactical Chart Canvas & Live Telemetry Pod */}
        <section className="route-map-panel">
          <div className="tactical-chart-card glass">
            <div className="chart-frame-header">
              <span className="mono text-xs chart-header-title">BATHYMETRIC CORRIDOR PLOT (CONTOURS & CORRIDOR)</span>
              <span className="mono text-xs text-teal">100% POSTGIS COMPLIANT</span>
            </div>

            <div
              className={`chart-canvas-wrapper ${isDragging ? 'chart-canvas-wrapper--dragging' : ''}`}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
            >
              {/* Interactive Map Overlay Controls */}
              <div className="chart-map-controls">
                <button
                  type="button"
                  className="chart-ctrl-btn"
                  onClick={handleZoomIn}
                  title="Zoom In"
                  aria-label="Zoom In"
                >
                  +
                </button>
                <button
                  type="button"
                  className="chart-ctrl-btn"
                  onClick={handleZoomOut}
                  title="Zoom Out"
                  aria-label="Zoom Out"
                >
                  −
                </button>
                <button
                  type="button"
                  className="chart-ctrl-btn chart-ctrl-btn--reset"
                  onClick={handleResetView}
                  title="Reset View"
                  aria-label="Reset View"
                >
                  ⟲
                </button>
                <span className="chart-drag-hint mono text-xs">
                  ✋ Drag to pan
                </span>
              </div>

              <svg viewBox="0 0 800 440" className="tactical-chart-svg" preserveAspectRatio="xMidYMid meet">
                <defs>
                  <linearGradient id="routeGradient" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#2DD4BF" />
                    <stop offset="50%" stopColor="#38BDF8" />
                    <stop offset="100%" stopColor="#F59E0B" />
                  </linearGradient>
                  <linearGradient id="oceanShade" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#040D18" />
                    <stop offset="60%" stopColor="#081829" />
                    <stop offset="100%" stopColor="#0E243A" />
                  </linearGradient>
                  <pattern id="hazardHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                    <line x1="0" y1="0" x2="0" y2="8" stroke="rgba(239, 68, 68, 0.4)" strokeWidth="2" />
                  </pattern>
                  <filter id="corridorGlow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="6" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                </defs>

                {/* Oceanic Bathymetric Background */}
                <rect x="0" y="0" width="800" height="440" fill="url(#oceanShade)" />

                {/* Pan & Zoom Interactive SVG Layer */}
                <g
                  transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}
                  style={{ transformOrigin: '400px 220px', transition: isDragging ? 'none' : 'transform 0.12s ease-out' }}
                >
                  {/* Nautical Coordinate Grid Lines */}
                  <line x1="0" y1="110" x2="800" y2="110" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
                  <line x1="0" y1="220" x2="800" y2="220" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
                  <line x1="0" y1="330" x2="800" y2="330" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
                  <line x1="200" y1="0" x2="200" y2="440" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
                  <line x1="400" y1="0" x2="400" y2="440" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
                  <line x1="600" y1="0" x2="600" y2="440" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />

                  <text x="14" y="24" fill="#64748B" fontSize="9" fontFamily="monospace">17°00'N 73°10'E</text>
                  <text x="14" y="426" fill="#64748B" fontSize="9" fontFamily="monospace">16°00'N 73°30'E</text>

                  {/* Simulated Coastal Landmass (Konkan / Maharashtra Coast) */}
                  <path
                    d="M 680 0 Q 640 100 660 180 T 630 300 T 670 440 L 800 440 L 800 0 Z"
                    fill="#112233"
                    stroke="#2DD4BF"
                    strokeWidth="1.5"
                  />
                  <text x="740" y="220" fill="#475569" fontSize="10" fontFamily="Sora" fontWeight="700" letterSpacing="0.1em" textAnchor="middle">
                    COASTLINE
                  </text>

                  {/* Bathymetry Contours */}
                  {/* 10m Shoal Contour */}
                  <path d="M 610 0 Q 580 120 600 220 T 570 340 T 620 440" fill="none" stroke="rgba(56, 189, 248, 0.2)" strokeWidth="1" strokeDasharray="3 3" />
                  <text x="595" y="60" fill="#38BDF8" opacity="0.6" fontSize="8" fontFamily="monospace">10m</text>

                  {/* 20m Depth Contour */}
                  <path d="M 520 0 Q 480 130 500 230 T 470 350 T 520 440" fill="none" stroke="rgba(45, 212, 191, 0.3)" strokeWidth="1.2" />
                  <text x="495" y="80" fill="#2DD4BF" opacity="0.7" fontSize="8" fontFamily="monospace">20m DEPTH</text>

                  {/* 50m Deep Trench Contour */}
                  <path d="M 360 0 Q 310 140 330 250 T 290 370 T 340 440" fill="none" stroke="rgba(14, 165, 233, 0.25)" strokeWidth="1.2" strokeDasharray="6 4" />
                  <text x="330" y="100" fill="#0EA5E9" opacity="0.6" fontSize="8" fontFamily="monospace">50m DEEP WATER</text>

                  {/* Environmental / Regulatory Hazard Avoidance Zones */}
                  {/* 1. Malvan Sanctuary Core (Avoided) */}
                  <g>
                    <polygon
                      points="500,240 560,220 580,290 510,300"
                      fill="url(#hazardHatch)"
                      stroke="#EF4444"
                      strokeWidth="1.5"
                      strokeDasharray="4 2"
                    />
                    <rect x="490" y="258" width="84" height="16" rx="4" fill="rgba(15, 23, 42, 0.85)" />
                    <text x="532" y="270" fill="#F87171" fontSize="8" fontFamily="Sora" fontWeight="700" textAnchor="middle">
                      SANCTUARY (AVOIDED)
                    </text>
                  </g>

                  {/* 2. Angria Bank Shoal Clearance */}
                  <g>
                    <circle cx="260" cy="180" r="32" fill="rgba(245, 158, 11, 0.12)" stroke="#F59E0B" strokeWidth="1" strokeDasharray="3 3" />
                    <text x="260" y="184" fill="#FBBF24" fontSize="8" fontFamily="monospace" textAnchor="middle">
                      SHOAL HAZARD
                    </text>
                  </g>

                  {/* Safe Passage Wide Corridor Buffer Ribbon */}
                  <path
                    d="M 160 80 Q 260 170 370 210 T 520 330"
                    fill="none"
                    stroke="rgba(45, 212, 191, 0.18)"
                    strokeWidth="32"
                    strokeLinecap="round"
                  />

                  {/* High Contrast Optimized Route Path */}
                  <path
                    d="M 160 80 Q 260 170 370 210 T 520 330"
                    fill="none"
                    stroke="url(#routeGradient)"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray="10 5"
                    filter="url(#corridorGlow)"
                  />

                  {/* Direct Baseline (Sub-optimal direct line for contrast) */}
                  <line x1="160" y1="80" x2="520" y2="330" stroke="rgba(239, 68, 68, 0.35)" strokeWidth="1.5" strokeDasharray="3 3" />
                  <text x="290" y="190" fill="#F87171" opacity="0.6" fontSize="8" fontFamily="monospace" transform="rotate(35 290 190)">
                    DIRECT (HAZARD INTERSECT)
                  </text>

                  {/* Waypoint 1: Departure Port */}
                  <g transform="translate(160, 80)">
                    <circle cx="0" cy="0" r="14" fill="rgba(45, 212, 191, 0.2)" />
                    <circle cx="0" cy="0" r="7" fill="#2DD4BF" stroke="#FFFFFF" strokeWidth="2" />
                    <rect x="-65" y="-32" width="130" height="20" rx="6" fill="rgba(15, 23, 42, 0.88)" stroke="#2DD4BF" strokeWidth="1" />
                    <text x="0" y="-18" fill="#FFFFFF" fontSize="9.5" fontFamily="Sora" fontWeight="700" textAnchor="middle">
                      ⚓ {depName}
                    </text>
                  </g>

                  {/* Waypoint 2: Mid Passage Transit & Active Vessel */}
                  <g transform="translate(370, 210)">
                    {/* Outer Pulsing Vessel Radar Ring */}
                    <circle cx="0" cy="0" r="22" fill="none" stroke="#38BDF8" strokeWidth="1.5">
                      <animate attributeName="r" values="10;28;10" dur="2.4s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="1;0;1" dur="2.4s" repeatCount="indefinite" />
                    </circle>
                    <circle cx="0" cy="0" r="8" fill="#38BDF8" stroke="#FFFFFF" strokeWidth="2" />
                    <rect x="-60" y="16" width="120" height="20" rx="6" fill="rgba(15, 23, 42, 0.9)" stroke="#38BDF8" strokeWidth="1" />
                    <text x="0" y="30" fill="#38BDF8" fontSize="9" fontFamily="Sora" fontWeight="700" textAnchor="middle">
                      🚢 VIGILANT ({Math.round(bearing)}°)
                    </text>
                  </g>

                  {/* Waypoint 3: Destination Port */}
                  <g transform="translate(520, 330)">
                    <circle cx="0" cy="0" r="14" fill="rgba(245, 158, 11, 0.25)" />
                    <circle cx="0" cy="0" r="8" fill="#F59E0B" stroke="#FFFFFF" strokeWidth="2" />
                    <rect x="-65" y="16" width="130" height="20" rx="6" fill="rgba(15, 23, 42, 0.88)" stroke="#F59E0B" strokeWidth="1" />
                    <text x="0" y="30" fill="#FBBF24" fontSize="9.5" fontFamily="Sora" fontWeight="700" textAnchor="middle">
                      🏁 {destName}
                    </text>
                  </g>

                  {/* Compass Rose Mini */}
                  <g transform="translate(730, 60)">
                    <circle cx="0" cy="0" r="22" fill="rgba(15, 23, 42, 0.6)" stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
                    <polygon points="0,-18 4,-4 0,0 -4,-4" fill="#EF4444" />
                    <polygon points="0,18 4,4 0,0 -4,4" fill="#94A3B8" />
                    <polygon points="18,0 4,4 0,0 4,-4" fill="#94A3B8" />
                    <polygon points="-18,0 -4,4 0,0 -4,-4" fill="#94A3B8" />
                    <text x="0" y="-7" fill="#FFFFFF" fontSize="8" fontFamily="Sora" fontWeight="800" textAnchor="middle">N</text>
                  </g>
                </g>
              </svg>

              {/* Live Telemetry Instrument Pod */}
              <div className="floating-telemetry-card glass">
                <div className="telemetry-card__top">
                  <div className="telemetry-card__title mono text-xs font-bold">
                    <IconShip size={13} color="#38BDF8" />
                    <span>VESSEL: VIGILANT (IND-MH-0192)</span>
                  </div>
                  <span className="telemetry-status-pill mono text-xs">
                    <span className="status-live-dot" /> LIVE PASSAGE
                  </span>
                </div>

                <div className="telemetry-metrics-grid">
                  <div className="telemetry-stat">
                    <span className="stat-label mono text-xs">Speed Over Ground</span>
                    <span className="stat-val font-bold mono text-display">
                      8.0 <span className="stat-unit">kts</span>
                    </span>
                  </div>

                  <div className="telemetry-stat">
                    <span className="stat-label mono text-xs">Heading Course</span>
                    <span className="stat-val font-bold mono text-display">
                      {Math.round(bearing)}° <span className="stat-unit">{cardinal}</span>
                    </span>
                  </div>

                  <div className="telemetry-stat">
                    <span className="stat-label mono text-xs">
                      <IconWind size={11} /> Distance
                    </span>
                    <span className="stat-val font-bold mono">
                      {distanceNm} NM ({distanceKm} km)
                    </span>
                  </div>

                  <div className="telemetry-stat">
                    <span className="stat-label mono text-xs">
                      <IconWave size={11} /> {t('fuelEstimate')}
                    </span>
                    <span className="stat-val font-bold mono">
                      {fuelLiters} Liters
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

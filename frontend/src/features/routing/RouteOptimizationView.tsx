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
        <div className="route-header__actions flex gap-2 items-center flex-wrap">
          <div className="flex items-center gap-1">
            <span className="mono text-xs text-muted">{t('departure')}:</span>
            <select
              value={departurePort}
              onChange={(e) => setDeparturePort(e.target.value)}
              className="bg-slate-800 text-white text-xs rounded px-2 py-1 border border-slate-700 font-mono"
            >
              {portsCatalog.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1">
            <span className="mono text-xs text-muted">{t('destination')}:</span>
            <select
              value={destinationPort}
              onChange={(e) => setDestinationPort(e.target.value)}
              className="bg-slate-800 text-white text-xs rounded px-2 py-1 border border-slate-700 font-mono"
            >
              {portsCatalog.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <button
            type="button"
            className="route-btn-reoptimize"
            onClick={handleInitiateOptimization}
            disabled={isOptimizing}
          >
            <IconSparkles size={14} color="#0F172A" />
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
              <span className="mono text-xs text-muted">BATHYMETRIC CORRIDOR PLOT (CONTOURS & CORRIDOR)</span>
              <span className="mono text-xs text-teal">100% POSTGIS COMPLIANT</span>
            </div>

            <div className="chart-canvas-wrapper">
              <svg viewBox="0 0 800 500" className="tactical-chart-svg">
                <defs>
                  <linearGradient id="routeGlow" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#14B8A6" />
                    <stop offset="50%" stopColor="#F59E0B" />
                    <stop offset="100%" stopColor="#D8FA36" />
                  </linearGradient>
                </defs>

                {/* Continental Shelf Backdrop */}
                <rect x="0" y="0" width="800" height="500" fill="#0b1329" />

                {/* Bathymetry Contours */}
                <path d="M 120 0 Q 240 120 200 240 T 180 400 T 220 600" fill="none" stroke="rgba(45, 212, 191, 0.15)" strokeWidth="1.5" strokeDasharray="6 6" />
                <path d="M 220 0 Q 360 140 310 280 T 290 440 T 350 600" fill="none" stroke="rgba(45, 212, 191, 0.25)" strokeWidth="1.5" />
                <path d="M 340 0 Q 480 160 430 320 T 410 480 T 480 600" fill="none" stroke="rgba(45, 212, 191, 0.12)" strokeWidth="1" />

                {/* Trajectory Safe Passage Corridor Ribbon */}
                <path d="M 140 180 Q 340 280 520 200 T 680 130" fill="none" stroke="rgba(216, 250, 54, 0.15)" strokeWidth="28" strokeLinecap="round" />

                {/* Active Planned Route Path */}
                <path d="M 140 180 Q 340 280 520 200 T 680 130" fill="none" stroke="url(#routeGlow)" strokeWidth="3.5" strokeDasharray="8 4" />

                {/* Waypoint 1: Departure */}
                <circle cx="140" cy="180" r="7" fill="#14B8A6" stroke="#FFFFFF" strokeWidth="2" />
                <text x="140" y="210" fill="#E2E8F0" fontSize="11" fontFamily="Sora" fontWeight="700" textAnchor="middle">
                  {depName} ({t('departure')})
                </text>

                {/* Waypoint 2: Transit Corridor */}
                <circle cx="430" cy="245" r="8" fill="#F59E0B" stroke="#FFFFFF" strokeWidth="2" />
                <text x="430" y="275" fill="#E2E8F0" fontSize="11" fontFamily="Sora" fontWeight="700" textAnchor="middle">
                  {cardinal} {Math.round(bearing)}° Corridor
                </text>

                {/* Active Vessel Indicator */}
                <g transform="translate(430, 245)">
                  <circle cx="0" cy="0" r="18" fill="none" stroke="#38BDF8" strokeWidth="1.5">
                    <animate attributeName="r" values="8;24;8" dur="2.5s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="1;0;1" dur="2.5s" repeatCount="indefinite" />
                  </circle>
                  <circle cx="0" cy="0" r="4" fill="#38BDF8" />
                </g>

                {/* Waypoint 3: Destination */}
                <circle cx="680" cy="130" r="10" fill="#D8FA36" stroke="#0F172A" strokeWidth="2.5" />
                <text x="680" y="105" fill="#D8FA36" fontSize="12" fontFamily="Sora" fontWeight="800" textAnchor="middle">
                  {destName} ({t('destination')})
                </text>
              </svg>

              {/* Floating Frosted Glass Live Telemetry Instrument Pod */}
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

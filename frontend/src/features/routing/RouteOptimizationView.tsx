import React, { useState } from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
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

export const RouteOptimizationView: React.FC<RouteOptimizationViewProps> = ({ response: _response }) => {
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [selectedWaypoint, setSelectedWaypoint] = useState<string>('transit');

  const handleInitiateOptimization = () => {
    setIsOptimizing(true);
    setTimeout(() => {
      setIsOptimizing(false);
    }, 1200);
  };

  const waypoints = [
    {
      id: 'departure',
      type: 'DEPARTURE',
      name: 'Ratnagiri Harbour',
      subtext: 'Berth 4, Terminal East • 17.02° N, 73.18° E',
      status: 'CLEARED',
      statusClass: 'status--cleared',
      pillIcon: <IconCheck size={11} />,
      markerNode: <div className="marker-dot marker-dot--departure" />,
    },
    {
      id: 'transit',
      type: 'TRANSIT CORRIDOR',
      name: 'Sindhudurg Waters',
      subtext: 'Expected swells 1.2m - 2.4m • Minor wave surge near bay mouth',
      status: 'CAUTION — SWELL',
      statusClass: 'status--caution',
      pillIcon: <IconAlert size={11} />,
      markerNode: <IconWave size={13} color="#D97706" />,
    },
    {
      id: 'destination',
      type: 'DESTINATION',
      name: 'Zone Alpha-7 (PFZ Prime)',
      subtext: 'Deep Sea Sector 42A • 12 NM off Mirya Bay • High Chlorophyll Front',
      status: 'ETA +4 HRS',
      statusClass: 'status--eta',
      pillIcon: <IconMapPin size={11} />,
      markerNode: <IconMapPin size={13} color="#64748B" />,
    },
  ];

  return (
    <div className="route-opt-view">
      {/* 1. Header Bar */}
      <header className="route-opt-header">
        <div>
          <div className="route-opt-badge mono text-xs">
            SAFE PASSAGE CORRIDOR // RATNAGIRI ➔ ZONE ALPHA-7
          </div>
          <h1 className="route-opt-title text-display">Route to Zone Alpha-7</h1>
          <p className="route-opt-subtitle text-sm text-muted">
            Active Multi-Domain Route Optimization & Safe Navigation Trajectory
          </p>
        </div>

        <button
          type="button"
          className={`route-opt-btn ${isOptimizing ? 'route-opt-btn--loading' : ''}`}
          onClick={handleInitiateOptimization}
          disabled={isOptimizing}
        >
          <IconSparkles size={15} />
          <span>{isOptimizing ? 'COMPUTING CORRIDOR...' : 'INITIATE ROUTE OPTIMIZATION'}</span>
        </button>
      </header>

      {/* 2. Main Two-Column Layout */}
      <div className="route-opt-grid">
        {/* Left Column: Navigation Sequence Cards */}
        <section className="nav-sequence-column">
          <div className="nav-sequence-card">
            <h3 className="nav-sequence-title">Navigation Sequence</h3>

            <div className="sequence-timeline">
              <div className="sequence-timeline__spine" />

              {waypoints.map((wp) => {
                const isSelected = selectedWaypoint === wp.id;
                return (
                  <div
                    key={wp.id}
                    className={`sequence-step ${isSelected ? 'sequence-step--selected' : ''}`}
                    onClick={() => setSelectedWaypoint(wp.id)}
                  >
                    <div className="sequence-step__marker">
                      {wp.markerNode}
                    </div>

                    <article className="sequence-step__content">
                      <div className="sequence-step__header">
                        <span className="sequence-step__type mono text-xs">{wp.type}</span>
                        <span className={`sequence-step__pill mono text-xs ${wp.statusClass}`}>
                          {wp.pillIcon}
                          <span>{wp.status}</span>
                        </span>
                      </div>

                      <h4 className="sequence-step__name">{wp.name}</h4>
                      <p className="sequence-step__desc text-xs">{wp.subtext}</p>
                    </article>
                  </div>
                );
              })}
            </div>

            {/* Safety Clearance Summary Box */}
            <div className="route-safety-summary">
              <div className="route-safety-summary__header">
                <span className="mono text-xs font-bold text-safe">CORRIDOR CLEARANCE: 99.4%</span>
                <span className="mono text-xs text-muted">SWAN Model v1.2</span>
              </div>
              <p className="route-safety-summary__text text-xs">
                Optimal routing holds course 214° SW to bypass nearshore shallow swell reef. Favorable chlorophyll density gradient expected at waypoint 3.
              </p>
            </div>
          </div>
        </section>

        {/* Right Column: Tactical Hydrographic Map Card */}
        <section className="tactical-map-column">
          <div className="tactical-map-card">
            {/* SVG Tactical Bathymetric Chart Visualizer */}
            <div className="tactical-map-canvas">
              <svg className="tactical-svg" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice">
                <defs>
                  <linearGradient id="oceanGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#0B1321" />
                    <stop offset="50%" stopColor="#091829" />
                    <stop offset="100%" stopColor="#062038" />
                  </linearGradient>

                  <linearGradient id="routeGlow" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#2DD4BF" />
                    <stop offset="50%" stopColor="#38BDF8" />
                    <stop offset="100%" stopColor="#D8FA36" />
                  </linearGradient>
                </defs>

                {/* Ocean Background */}
                <rect width="100%" height="100%" fill="url(#oceanGrad)" />

                {/* Grid Lines */}
                <line x1="100" y1="0" x2="100" y2="600" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
                <line x1="300" y1="0" x2="300" y2="600" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
                <line x1="500" y1="0" x2="500" y2="600" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
                <line x1="700" y1="0" x2="700" y2="600" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
                <line x1="0" y1="150" x2="800" y2="150" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
                <line x1="0" y1="350" x2="800" y2="350" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
                <line x1="0" y1="500" x2="800" y2="500" stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />

                {/* Coastline Silhouette */}
                <path
                  d="M 50 0 Q 180 80 140 180 T 110 320 T 160 480 T 90 600 L 0 600 L 0 0 Z"
                  fill="#111B29"
                  stroke="#1E2F46"
                  strokeWidth="2"
                />

                {/* Bathymetry Contours */}
                <path
                  d="M 120 0 Q 240 120 200 240 T 180 400 T 220 600"
                  fill="none"
                  stroke="rgba(45, 212, 191, 0.15)"
                  strokeWidth="1.5"
                  strokeDasharray="6 6"
                />
                <path
                  d="M 220 0 Q 360 140 310 280 T 290 440 T 350 600"
                  fill="none"
                  stroke="rgba(45, 212, 191, 0.25)"
                  strokeWidth="1.5"
                />
                <path
                  d="M 340 0 Q 480 160 430 320 T 410 480 T 480 600"
                  fill="none"
                  stroke="rgba(45, 212, 191, 0.12)"
                  strokeWidth="1"
                />

                {/* Trajectory Safe Passage Corridor Ribbon */}
                <path
                  d="M 140 180 Q 340 280 520 200 T 680 130"
                  fill="none"
                  stroke="rgba(216, 250, 54, 0.15)"
                  strokeWidth="28"
                  strokeLinecap="round"
                />

                {/* Active Planned Route Path */}
                <path
                  d="M 140 180 Q 340 280 520 200 T 680 130"
                  fill="none"
                  stroke="url(#routeGlow)"
                  strokeWidth="3.5"
                  strokeDasharray="8 4"
                />

                {/* Waypoint 1: Departure Ratnagiri */}
                <circle cx="140" cy="180" r="7" fill="#14B8A6" stroke="#FFFFFF" strokeWidth="2" />
                <text x="140" y="210" fill="#E2E8F0" fontSize="11" fontFamily="Sora" fontWeight="700" textAnchor="middle">
                  Ratnagiri (Departure)
                </text>

                {/* Waypoint 2: Sindhudurg Transit */}
                <circle cx="430" cy="245" r="8" fill="#F59E0B" stroke="#FFFFFF" strokeWidth="2" />
                <text x="430" y="275" fill="#E2E8F0" fontSize="11" fontFamily="Sora" fontWeight="700" textAnchor="middle">
                  Sindhudurg Waters
                </text>

                {/* Active Vessel Indicator */}
                <g transform="translate(430, 245)">
                  <circle cx="0" cy="0" r="18" fill="none" stroke="#38BDF8" strokeWidth="1.5">
                    <animate attributeName="r" values="8;24;8" dur="2.5s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="1;0;1" dur="2.5s" repeatCount="indefinite" />
                  </circle>
                  <circle cx="0" cy="0" r="4" fill="#38BDF8" />
                </g>

                {/* Waypoint 3: Zone Alpha-7 PFZ */}
                <circle cx="680" cy="130" r="10" fill="#D8FA36" stroke="#0F172A" strokeWidth="2.5" />
                <text x="680" y="105" fill="#D8FA36" fontSize="12" fontFamily="Sora" fontWeight="800" textAnchor="middle">
                  Zone Alpha-7 (PFZ Prime)
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
                    <span className="status-live-dot" /> LIVE SYNC
                  </span>
                </div>

                <div className="telemetry-metrics-grid">
                  <div className="telemetry-stat">
                    <span className="stat-label mono text-xs">Speed Over Ground</span>
                    <span className="stat-val font-bold mono text-display">8.4 <span className="stat-unit">kts</span></span>
                  </div>

                  <div className="telemetry-stat">
                    <span className="stat-label mono text-xs">Heading Course</span>
                    <span className="stat-val font-bold mono text-display">214° <span className="stat-unit">SW</span></span>
                  </div>

                  <div className="telemetry-stat">
                    <span className="stat-label mono text-xs">
                      <IconWind size={11} /> Wind Speed
                    </span>
                    <span className="stat-val font-bold mono">12 kts NW</span>
                  </div>

                  <div className="telemetry-stat">
                    <span className="stat-label mono text-xs">
                      <IconWave size={11} /> Wave Swell
                    </span>
                    <span className="stat-val font-bold mono">1.2 m (11.4s)</span>
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

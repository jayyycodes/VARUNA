import React, { useState, useEffect } from 'react';
import historicalFallback from '../../fixtures/historical_trends.json';
import { apiClient } from '../../api/client';
import { useLocalization } from '../../hooks/useLocalization';
import { IconAlert, IconSearch } from '../../components/Icons';
import './HistoricalTrendsView.css';

export const HistoricalTrendsView: React.FC = () => {
  const { t } = useLocalization();
  const [activeMetric, setActiveMetric] = useState<'sst' | 'chlorophyll'>('sst');
  const [data, setData] = useState<any>(historicalFallback);
  const [isLive, setIsLive] = useState<boolean>(false);
  const [selectedMonth, setSelectedMonth] = useState<string>('May');

  useEffect(() => {
    let isMounted = true;
    async function loadTrends() {
      try {
        const live = await apiClient.fetchHistoricalTrends();
        if (isMounted && live) {
          setData(live);
          setIsLive(true);
        }
      } catch (err) {
        console.warn('Using historical trends fallback:', err);
      }
    }
    loadTrends();
    return () => {
      isMounted = false;
    };
  }, []);

  const {
    sector,
    monitoring_period,
    productivity_index,
    primary_causes = [],
    months = [],
    sst_baseline_celsius = [],
    sst_observed_celsius = [],
    chlorophyll_baseline_mg_m3 = [],
    chlorophyll_observed_mg_m3 = [],
    statutory_reference = {},
    sources = [],
  } = data;

  const [hoveredIdx, setHoveredIdx] = useState<number | null>(7); // Default May peak

  // Chart coordinate mapping
  const width = 580;
  const height = 210;
  const padLeft = 45;
  const padRight = 20;
  const padTop = 24;
  const padBottom = 32;
  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  const getPointsObj = (values: number[], minVal: number, maxVal: number) => {
    if (!values || values.length === 0) return [];
    return values.map((val, idx) => {
      const x = padLeft + (idx / Math.max(values.length - 1, 1)) * plotW;
      const y = padTop + plotH - ((val - minVal) / Math.max(maxVal - minVal, 0.001)) * plotH;
      return { x, y, val };
    });
  };

  const sstMin = 25.0;
  const sstMax = 31.5;
  const sstBaselineObjs = getPointsObj(sst_baseline_celsius, sstMin, sstMax);
  const sstObservedObjs = getPointsObj(sst_observed_celsius, sstMin, sstMax);

  const chlMin = 0.2;
  const chlMax = 0.8;
  const chlBaselineObjs = getPointsObj(chlorophyll_baseline_mg_m3, chlMin, chlMax);
  const chlObservedObjs = getPointsObj(chlorophyll_observed_mg_m3, chlMin, chlMax);

  // Smooth Bezier Curve generator (Cubic Splines)
  const getSmoothPath = (pts: { x: number; y: number }[]) => {
    if (pts.length === 0) return '';
    let d = `M ${pts[0].x.toFixed(1)},${pts[0].y.toFixed(1)}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i];
      const p1 = pts[i + 1];
      const cp1x = p0.x + (p1.x - p0.x) / 2;
      const cp1y = p0.y;
      const cp2x = p0.x + (p1.x - p0.x) / 2;
      const cp2y = p1.y;
      d += ` C ${cp1x.toFixed(1)},${cp1y.toFixed(1)} ${cp2x.toFixed(1)},${cp2y.toFixed(1)} ${p1.x.toFixed(1)},${p1.y.toFixed(1)}`;
    }
    return d;
  };

  const getAreaPath = (pts: { x: number; y: number }[], bottomY: number) => {
    const pathD = getSmoothPath(pts);
    if (!pathD) return '';
    const firstX = pts[0].x.toFixed(1);
    const lastX = pts[pts.length - 1].x.toFixed(1);
    return `${pathD} L ${lastX},${bottomY.toFixed(1)} L ${firstX},${bottomY.toFixed(1)} Z`;
  };

  const currentObservedObjs = activeMetric === 'sst' ? sstObservedObjs : chlObservedObjs;
  const currentBaselineObjs = activeMetric === 'sst' ? sstBaselineObjs : chlBaselineObjs;

  const observedPathD = getSmoothPath(currentObservedObjs);
  const baselinePathD = getSmoothPath(currentBaselineObjs);
  const areaPathD = getAreaPath(currentObservedObjs, padTop + plotH);

  const actTitle = typeof statutory_reference === 'object' ? statutory_reference.act : String(statutory_reference);
  const actSection = typeof statutory_reference === 'object' ? statutory_reference.section : '';
  const actNote = typeof statutory_reference === 'object' ? statutory_reference.regulatory_note : '';

  return (
    <div className="trends-view bento-container">
      {/* 1. Header Section */}
      <header className="trends-header">
        <div className="trends-badge mono text-xs">
          {t('sihQuery7')} {isLive && <span className="ml-2 text-safe">● LIVE API</span>}
        </div>
        <h1 className="trends-title text-display">
          {t('trendsTitle')}
        </h1>
        <p className="trends-subtitle text-sm text-muted">
          {t('trendsSubtitle')}
        </p>
      </header>

      {/* 2. Top Summary Row */}
      <div className="bento-top-row">
        <div className="bento-card bento-card--sector">
          <div className="sector-info">
            <span className="sector-name font-bold">{sector}</span>
            <span className="sector-period mono text-xs">{monitoring_period}</span>
          </div>
          <div className="decline-pill mono font-bold">
            {productivity_index}
          </div>
        </div>

        <div className="bento-card bento-card--drivers">
          <div className="causes-title mono text-xs">
            <IconAlert size={14} color="var(--status-caution)" />
            <span>PRIMARY ENVIRONMENTAL DRIVERS IDENTIFIED</span>
          </div>
          <ul className="causes-list">
            {primary_causes.map((cause: string, i: number) => (
              <li key={i} className="cause-item text-xs">
                <span className="cause-bullet">●</span>
                <span>{cause}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* 3. Main Bento 3-Column Layout */}
      <div className="bento-grid">
        {/* ================= COLUMN 1: Left Column ================= */}
        <div className="bento-col bento-col--left">
          {/* Card 1: Today's Focus Sector Card */}
          <div className="bento-card bento-card--focus">
            <div className="card-top-head">
              <span className="card-subtitle text-xs font-bold text-muted">Active Sector Focus</span>
              <span className="card-more">•••</span>
            </div>
            
            <div className="focus-body">
              <div className="focus-avatar-pod">
                <IconSearch size={18} color="#4F8BF9" />
              </div>
              <div className="focus-details">
                <h3 className="focus-title text-sm font-bold">Ratnagiri Fishery Zone</h3>
                <div className="focus-meta mono text-xs text-muted">
                  <span>31 Vessels</span> • <span>50 min lag</span> • <span>12 Lessons</span>
                </div>
              </div>
            </div>

            <div className="focus-progress-area">
              <div className="progress-labels mono text-xs">
                <span className="font-bold">80% Anomaly Index</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: '80%' }} />
              </div>
              <div className="focus-actions">
                <button type="button" className="btn-secondary text-xs">Skip</button>
                <button type="button" className="btn-primary text-xs">Explore Sector</button>
              </div>
            </div>
          </div>

          {/* Card 2: Statutory Regulation Card (Pastel Amber) */}
          <div className="bento-card bento-card--governance">
            <div className="card-top-head">
              <span className="governance-badge mono text-xs">GOVERNANCE</span>
              <button type="button" className="bento-arrow-btn" aria-label="Explore Governance">↗</button>
            </div>
            <div className="governance-body">
              <h4 className="governance-title text-sm font-bold">{actTitle}</h4>
              <p className="governance-desc text-xs">{actSection}: {actNote}</p>
            </div>
          </div>
        </div>

        {/* ================= COLUMN 2: Center Column (Dark Hero Telemetry Observation Card) ================= */}
        <div className="bento-col bento-col--center">
          {/* Main Dark Hero Card (Telemetry SVG Chart) */}
          <div className="bento-card bento-card--hero-dark">
            <div className="hero-dark-header">
              <div className="hero-title-area">
                <h3 className="hero-title">Telemetry Observation</h3>
                <span className="hero-more">•••</span>
              </div>

              <div className="chart-tabs" role="tablist">
                <button
                  type="button"
                  role="tab"
                  aria-selected={activeMetric === 'sst'}
                  className={`chart-tab ${activeMetric === 'sst' ? 'chart-tab--active' : ''}`}
                  onClick={() => setActiveMetric('sst')}
                >
                  Sea Surface Temp (SST)
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={activeMetric === 'chlorophyll'}
                  className={`chart-tab ${activeMetric === 'chlorophyll' ? 'chart-tab--active' : ''}`}
                  onClick={() => setActiveMetric('chlorophyll')}
                >
                  Chlorophyll-a
                </button>
              </div>
            </div>

            {/* SVG Chart Container */}
            <div className="chart-svg-container" style={{ position: 'relative' }}>
              <svg viewBox={`0 0 ${width} ${height}`} className="trends-svg">
                <defs>
                  {/* SST Area Gradient (Red) */}
                  <linearGradient id="sstAreaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#FF4D4D" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#FF4D4D" stopOpacity="0.0" />
                  </linearGradient>

                  {/* Chlorophyll Area Gradient (Mint) */}
                  <linearGradient id="chlAreaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#00E676" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#00E676" stopOpacity="0.0" />
                  </linearGradient>

                  {/* Diagonal Hatch Pattern (Matching Reference Image 2) */}
                  <pattern id="diagonalHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                    <line x1="0" y1="0" x2="0" y2="8" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1.5" />
                  </pattern>

                  {/* Glow Filter */}
                  <filter id="glowFilter" x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor={activeMetric === 'sst' ? '#FF4D4D' : '#00E676'} floodOpacity="0.5" />
                  </filter>
                </defs>

                {/* Horizontal Grid lines */}
                {[0, 0.25, 0.5, 0.75, 1].map((ratio, idx) => {
                  const y = padTop + plotH * ratio;
                  const labelVal =
                    activeMetric === 'sst'
                      ? (sstMax - ratio * (sstMax - sstMin)).toFixed(1) + '°C'
                      : (chlMax - ratio * (chlMax - chlMin)).toFixed(1) + ' mg';
                  return (
                    <g key={idx}>
                      <line
                        x1={padLeft}
                        y1={y}
                        x2={width - padRight}
                        y2={y}
                        stroke="rgba(255, 255, 255, 0.06)"
                        strokeDasharray="4 4"
                      />
                      <text
                        x={padLeft - 10}
                        y={y + 3}
                        fill="rgba(255, 255, 255, 0.5)"
                        fontSize="9.5"
                        textAnchor="end"
                        fontFamily="monospace"
                        fontWeight="500"
                      >
                        {labelVal}
                      </text>
                    </g>
                  );
                })}

                {/* Gradient Fill under Observed Curve */}
                <path
                  d={areaPathD}
                  fill={activeMetric === 'sst' ? 'url(#sstAreaGrad)' : 'url(#chlAreaGrad)'}
                />
                <path
                  d={areaPathD}
                  fill="url(#diagonalHatch)"
                />

                {/* Baseline Curved Path (Dashed) */}
                <path
                  d={baselinePathD}
                  fill="none"
                  stroke="rgba(148, 163, 184, 0.45)"
                  strokeWidth="2"
                  strokeDasharray="6 5"
                />

                {/* Observed Curved Path (Solid Smooth) */}
                <path
                  d={observedPathD}
                  fill="none"
                  stroke={activeMetric === 'sst' ? '#FF4D4D' : '#00E676'}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  filter="url(#glowFilter)"
                />

                {/* Active / Hovered Vertical Guide Line & Node Points */}
                {hoveredIdx !== null && currentObservedObjs[hoveredIdx] && (
                  <g key="hover-guide">
                    <line
                      x1={currentObservedObjs[hoveredIdx].x}
                      y1={padTop}
                      x2={currentObservedObjs[hoveredIdx].x}
                      y2={padTop + plotH}
                      stroke="rgba(255, 255, 255, 0.3)"
                      strokeDasharray="3 3"
                    />
                    {/* Baseline Node */}
                    <circle
                      cx={currentBaselineObjs[hoveredIdx].x}
                      cy={currentBaselineObjs[hoveredIdx].y}
                      r="4"
                      fill="#64748B"
                      stroke="#0B0E17"
                      strokeWidth="2"
                    />
                    {/* Observed Node */}
                    <circle
                      cx={currentObservedObjs[hoveredIdx].x}
                      cy={currentObservedObjs[hoveredIdx].y}
                      r="6"
                      fill={activeMetric === 'sst' ? '#FF4D4D' : '#00E676'}
                      stroke="#FFFFFF"
                      strokeWidth="2.5"
                    />
                  </g>
                )}

                {/* Month Labels & Interactive Hover Triggers */}
                {months.map((m: string, idx: number) => {
                  const x = padLeft + (idx / Math.max(months.length - 1, 1)) * plotW;
                  const isHovered = hoveredIdx === idx;
                  return (
                    <g
                      key={m}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredIdx(idx)}
                      onClick={() => setHoveredIdx(idx)}
                    >
                      {/* Transparent Hover Hitbox */}
                      <rect
                        x={x - plotW / Math.max(months.length * 2, 1)}
                        y={padTop}
                        width={plotW / Math.max(months.length, 1)}
                        height={plotH + padBottom}
                        fill="transparent"
                      />
                      <text
                        x={x}
                        y={height - 8}
                        fill={isHovered ? '#FFFFFF' : 'rgba(255, 255, 255, 0.45)'}
                        fontSize="10"
                        fontWeight={isHovered ? '700' : '500'}
                        textAnchor="middle"
                        fontFamily="monospace"
                      >
                        {m}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* Telemetry Driver Metrics Section */}
            <div className="hero-activity-section">
              <h4 className="activity-title">Telemetry Driver Metrics</h4>
              <div className="activity-list">
                <div className="activity-row">
                  <span className="activity-label">Positive SST Thermal Anomaly</span>
                  <div className="activity-bar-wrap">
                    <div className="activity-bar activity-bar--coral" style={{ width: '80%' }} />
                  </div>
                  <span className="activity-pct mono font-bold">80%</span>
                </div>

                <div className="activity-row">
                  <span className="activity-label">Chlorophyll Peak Suppression</span>
                  <div className="activity-bar-wrap">
                    <div className="activity-bar activity-bar--sage" style={{ width: '60%' }} />
                  </div>
                  <span className="activity-pct mono font-bold">60%</span>
                </div>

                <div className="activity-row">
                  <span className="activity-label">Thermal Stratification Index</span>
                  <div className="activity-bar-wrap">
                    <div className="activity-bar activity-bar--cyan" style={{ width: '85%' }} />
                  </div>
                  <span className="activity-pct mono font-bold">85%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sub-row cards in center column */}
          <div className="bento-subrow">
            <div className="bento-card bento-card--pastel-mint">
              <div className="card-top-head">
                <span className="pastel-label text-xs font-bold">Upwelling Status</span>
                <button type="button" className="bento-arrow-btn" aria-label="Explore Upwelling">↗</button>
              </div>
              <h4 className="pastel-title text-sm font-bold">Seasonal Upwelling Delay</h4>
              <p className="pastel-desc text-xs text-muted">Warm surface cap delays cold nutrient-rich subsurface water mixing.</p>
            </div>

            <div className="bento-card bento-card--pastel-sage">
              <div className="card-top-head">
                <span className="pastel-label text-xs font-bold">Fisheries Advisory</span>
                <button type="button" className="bento-arrow-btn" aria-label="Explore Advisory">↗</button>
              </div>
              <h4 className="pastel-title text-sm font-bold">Monsoon Trawl Ban</h4>
              <p className="pastel-desc text-xs text-muted">Strict enforcement active across 12-nautical-mile territorial limits.</p>
            </div>
          </div>
        </div>

        {/* ================= COLUMN 3: Right Column ================= */}
        <div className="bento-col bento-col--right">
          {/* Card 1: Calendar / Timeline Widget (Dark) */}
          <div className="bento-card bento-card--calendar">
            <div className="calendar-header">
              <span className="calendar-nav-btn">‹</span>
              <span className="calendar-title text-xs font-bold mono">2025–2026 Timeline</span>
              <span className="calendar-nav-btn">›</span>
            </div>

            <div className="calendar-month-grid">
              {['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'].map((m) => {
                const isSel = m === selectedMonth;
                return (
                  <button
                    key={m}
                    type="button"
                    className={`month-cell ${isSel ? 'month-cell--active' : ''}`}
                    onClick={() => setSelectedMonth(m)}
                  >
                    {m}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Card 2: Anomaly Quick Filter Tags (Pastel Rose) */}
          <div className="bento-card bento-card--tags">
            <h4 className="tags-title text-sm font-bold">Anomaly Drivers</h4>
            <p className="tags-subtitle text-xs text-muted">Most active environmental parameters on board</p>

            <div className="tags-cloud">
              <span className="tag-pill tag-pill--active">SST Anomaly</span>
              <span className="tag-pill">Chlorophyll-a</span>
              <span className="tag-pill">Upwelling</span>
              <span className="tag-pill">Monsoon Ban</span>
              <span className="tag-pill">Stratification</span>
              <span className="tag-pill">Trawl Limits</span>
            </div>

            <div className="tags-explore-link text-xs font-bold">
              <span>Explore Telemetry Records</span>
              <button type="button" className="bento-arrow-btn bento-arrow-btn--sm" aria-label="Explore Records">↗</button>
            </div>
          </div>

          {/* Card 3: Metrics Callout Card (White) */}
          <div className="bento-card bento-card--stat-callout">
            <div className="stat-num-area">
              <span className="stat-number text-display font-bold">450+</span>
              <span className="stat-icon">🏆</span>
            </div>
            <p className="stat-label text-xs text-muted">Satellite Telemetry Data Points Processed</p>
          </div>
        </div>
      </div>

      {/* 4. Telemetry Sources Footer */}
      <footer className="trends-footer mono text-xs text-muted">
        <div className="footer-title">Authoritative Telemetry Sources:</div>
        <div className="footer-sources-row">
          {sources.map((s: string, idx: number) => (
            <span key={idx} className="footer-source-pill">
              ✓ {s}
            </span>
          ))}
        </div>
      </footer>
    </div>
  );
};

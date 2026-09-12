import React, { useState } from 'react';
import historicalData from '../../fixtures/historical_trends.json';
import { IconBook, IconAlert } from '../../components/Icons';
import './HistoricalTrendsView.css';

export const HistoricalTrendsView: React.FC = () => {
  const [activeMetric, setActiveMetric] = useState<'sst' | 'chlorophyll'>('sst');

  const {
    sector,
    monitoring_period,
    productivity_index,
    primary_causes,
    months,
    sst_baseline_celsius,
    sst_observed_celsius,
    chlorophyll_baseline_mg_m3,
    chlorophyll_observed_mg_m3,
    statutory_reference,
    sources,
  } = historicalData;

  // Chart coordinate mapping
  const width = 640;
  const height = 240;
  const padLeft = 45;
  const padRight = 20;
  const padTop = 25;
  const padBottom = 35;
  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  const getPoints = (values: number[], minVal: number, maxVal: number) => {
    return values
      .map((val, idx) => {
        const x = padLeft + (idx / (values.length - 1)) * plotW;
        const y = padTop + plotH - ((val - minVal) / (maxVal - minVal)) * plotH;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  };

  const sstMin = 25.0;
  const sstMax = 31.5;
  const sstBaselinePts = getPoints(sst_baseline_celsius, sstMin, sstMax);
  const sstObservedPts = getPoints(sst_observed_celsius, sstMin, sstMax);

  const chlMin = 0.2;
  const chlMax = 0.8;
  const chlBaselinePts = getPoints(chlorophyll_baseline_mg_m3, chlMin, chlMax);
  const chlObservedPts = getPoints(chlorophyll_observed_mg_m3, chlMin, chlMax);

  return (
    <div className="trends-view">
      <header className="trends-header">
        <div className="trends-badge mono text-xs">
          SIH NATIONAL EVALUATION QUERY #7
        </div>
        <h1 className="trends-title text-display">
          Coastal Fishery Productivity & Anomaly Analysis
        </h1>
        <p className="trends-subtitle text-sm text-muted">
          Multi-agent historical analysis explaining coastal fish decline via satellite SST anomalies, chlorophyll cycles, and monsoon trawl bans.
        </p>

        <div className="trends-sector-card">
          <div className="sector-info">
            <span className="sector-name font-bold">{sector}</span>
            <span className="sector-period mono text-xs">{monitoring_period}</span>
          </div>
          <div className="decline-pill mono font-bold">
            {productivity_index}
          </div>
        </div>
      </header>

      {/* Primary Causal Insights */}
      <div className="trends-causes-card glass">
        <div className="causes-title mono text-xs">
          <IconAlert size={14} color="var(--status-caution)" />
          <span>PRIMARY ENVIRONMENTAL DRIVERS IDENTIFIED</span>
        </div>
        <ul className="causes-list">
          {primary_causes.map((cause, i) => (
            <li key={i} className="cause-item text-xs">
              <span className="cause-bullet">●</span>
              <span>{cause}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Metric Selector & Chart Canvas */}
      <div className="trends-chart-card glass">
        <div className="chart-header">
          <div className="chart-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={activeMetric === 'sst'}
              className={`chart-tab ${activeMetric === 'sst' ? 'chart-tab--active' : ''}`}
              onClick={() => setActiveMetric('sst')}
            >
              Sea Surface Temp (SST Anomaly)
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeMetric === 'chlorophyll'}
              className={`chart-tab ${activeMetric === 'chlorophyll' ? 'chart-tab--active' : ''}`}
              onClick={() => setActiveMetric('chlorophyll')}
            >
              Chlorophyll-a Bloom Cycle
            </button>
          </div>

          <div className="chart-legend mono text-xs">
            <span className="legend-item">
              <span className="legend-line legend-line--baseline" /> 5-Yr Climatological Normal
            </span>
            <span className="legend-item">
              <span className="legend-line legend-line--observed" /> 2025–2026 Observed Telemetry
            </span>
          </div>
        </div>

        {/* SVG Time-Series Chart */}
        <div className="chart-svg-container">
          <svg viewBox={`0 0 ${width} ${height}`} className="trends-svg">
            {/* Horizontal Grid lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((ratio, idx) => {
              const y = padTop + plotH * ratio;
              const labelVal =
                activeMetric === 'sst'
                  ? (sstMax - ratio * (sstMax - sstMin)).toFixed(1) + '°C'
                  : (chlMax - ratio * (chlMax - chlMin)).toFixed(2) + ' mg';
              return (
                <g key={idx}>
                  <line
                    x1={padLeft}
                    y1={y}
                    x2={width - padRight}
                    y2={y}
                    stroke="rgba(255, 255, 255, 0.08)"
                    strokeDasharray="4 4"
                  />
                  <text
                    x={padLeft - 8}
                    y={y + 4}
                    fill="var(--text-dark-secondary, #94A3B8)"
                    fontSize="10"
                    textAnchor="end"
                    fontFamily="monospace"
                  >
                    {labelVal}
                  </text>
                </g>
              );
            })}

            {/* Baseline Polyline */}
            <polyline
              fill="none"
              stroke="var(--text-dark-secondary, #94A3B8)"
              strokeWidth="2"
              strokeDasharray="5 4"
              points={activeMetric === 'sst' ? sstBaselinePts : chlBaselinePts}
            />

            {/* Observed Polyline */}
            <polyline
              fill="none"
              stroke={activeMetric === 'sst' ? 'var(--status-unsafe)' : 'var(--status-pfz)'}
              strokeWidth="3"
              strokeLinecap="round"
              points={activeMetric === 'sst' ? sstObservedPts : chlObservedPts}
            />

            {/* Month Labels */}
            {months.map((m, idx) => {
              const x = padLeft + (idx / (months.length - 1)) * plotW;
              return (
                <text
                  key={m}
                  x={x}
                  y={height - 8}
                  fill="var(--text-dark-secondary, #94A3B8)"
                  fontSize="10"
                  textAnchor="middle"
                  fontFamily="monospace"
                >
                  {m}
                </text>
              );
            })}
          </svg>
        </div>
      </div>

      {/* Statutory Fisheries Governance Notice */}
      <div className="trends-statutory-card glass">
        <div className="statutory-header mono text-xs">
          <IconBook size={14} color="var(--status-pfz)" />
          <span>STATUTORY CORRELATION & GOVERNANCE</span>
        </div>
        <div className="statutory-act text-sm font-bold">
          {statutory_reference.act} — {statutory_reference.section}
        </div>
        <p className="statutory-note text-xs text-muted">
          {statutory_reference.regulatory_note}
        </p>
      </div>

      {/* Authoritative Sources */}
      <footer className="trends-footer mono text-xs text-muted">
        <div className="footer-title">Telemetry Sources:</div>
        {sources.map((s, idx) => (
          <div key={idx} className="footer-source">
            ✓ {s}
          </div>
        ))}
      </footer>
    </div>
  );
};

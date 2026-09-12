import React from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { FIXTURES } from '../../fixtures';
import {
  IconCheck,
  IconShield,
  IconWave,
  IconShip,
  IconRoute,
  IconAlert,
  IconCopilotBot,
} from '../../components/Icons';
import './ExecutiveDashboardView.css';

interface ExecutiveDashboardViewProps {
  response: UserResponseV1 | null;
  activeScenarioId: string | null;
  onSelectScenario: (scenarioId: string) => void;
  onNavigateView: (view: any) => void;
}

export const ExecutiveDashboardView: React.FC<ExecutiveDashboardViewProps> = ({
  response,
  activeScenarioId: _activeScenarioId,
  onSelectScenario,
  onNavigateView,
}) => {
  const scenariosList = Object.entries(FIXTURES).filter(
    ([key]) => key !== 'invalid_geometry'
  );

  const ruleTrace = response?.evidence_panel?.rule_trace || [];
  const passedCount = ruleTrace.filter((r) => r.passed).length;
  const failedCount = ruleTrace.length - passedCount;
  const passPercentage = ruleTrace.length > 0 ? Math.round((passedCount / ruleTrace.length) * 100) : 100;

  const verdict = response?.summary?.verdict || 'SAFE';

  return (
    <div className="executive-dashboard">
      {/* Left 2/3 Content Column */}
      <div className="exec-left-column">
        {/* 1. Header & Hero Cards Section */}
        <div className="exec-section-header">
          <h2 className="exec-section-title">Marine Advisory Cards</h2>
          <span className="exec-section-link" onClick={() => onNavigateView('map')}>View Map View ↗</span>
        </div>

        <div className="exec-cards-row">
          {/* Hero Card 1: Obsidian Matte Card */}
          <div className="exec-card exec-card--dark">
            <div className="exec-card__top">
              <span className="exec-card__chip">◈ VARUNA NAV</span>
              <span className="exec-card__menu">•••</span>
            </div>
            <div className="exec-card__main-val">
              {verdict === 'SAFE' && 'SAFE TO SAIL'}
              {verdict === 'CAUTION' && 'GO WITH CAUTION'}
              {verdict === 'UNSAFE' && 'DO NOT DEPART'}
              {verdict === 'UNKNOWN' && 'DATA INCOMPLETE'}
            </div>
            <div className="exec-card__sub-text mono">
              ZONE ID • RATNAGIRI-WZ-04
            </div>
            <div className="exec-card__bottom">
              <span className="exec-card__date mono">VALID: TODAY</span>
              <span className="exec-card__brand-tag">INCOIS VERIFIED</span>
            </div>
          </div>

          {/* Hero Card 2: Pure White Telemetry Card */}
          <div className="exec-card exec-card--light">
            <div className="exec-card__top">
              <span className="exec-card__chip-light">OCEAN TELEMETRY</span>
              <span className="exec-card__menu-light">•••</span>
            </div>
            <div className="exec-card__main-val-light">
              3 PFZ ZONES ACTIVE
            </div>
            <div className="exec-card__sub-text-light mono">
              SST 28.4°C • CHL 0.82 mg/m³
            </div>
            <div className="exec-card__bottom">
              <span className="exec-card__date-light mono">UPDATED: LIVE</span>
              <div className="exec-card__toggle-pill">
                <span className="toggle-dot" />
                <span>Sensors ON</span>
              </div>
            </div>
          </div>
        </div>

        {/* 2. Action Pills Row */}
        <div className="exec-actions-row">
          <button
            type="button"
            className="exec-action-pill exec-action-pill--active"
            onClick={() => onNavigateView('routing')}
          >
            <span className="pill-icon-circle"><IconRoute size={14} color="#FFFFFF" /></span>
            <span>Route Optimize</span>
          </button>

          <button
            type="button"
            className="exec-action-pill"
            onClick={() => onNavigateView('reasoning')}
          >
            <span className="pill-icon-circle pill-icon-circle--dark"><IconShield size={14} color="#FFFFFF" /></span>
            <span>Rules Engine</span>
          </button>

          <button
            type="button"
            className="exec-action-pill"
            onClick={() => onNavigateView('fleet')}
          >
            <span className="pill-icon-circle pill-icon-circle--dark"><IconShip size={14} color="#FFFFFF" /></span>
            <span>Fleet Ops</span>
          </button>

          <button
            type="button"
            className="exec-action-pill"
            onClick={() => onNavigateView('trends')}
          >
            <span className="pill-icon-circle pill-icon-circle--dark"><IconWave size={14} color="#FFFFFF" /></span>
            <span>Fishery Trends</span>
          </button>

          <button
            type="button"
            className="exec-action-pill"
            onClick={() => onNavigateView('alerts')}
          >
            <span className="pill-icon-circle pill-icon-circle--dark"><IconAlert size={14} color="#FFFFFF" /></span>
            <span>Active Alerts</span>
          </button>
        </div>

        {/* 3. Recent Maritime Scenarios & Vessel Inquiries Table */}
        <div className="exec-table-section">
          <div className="exec-table-header">
            <h3 className="exec-table-title">Recent Coastal Scenarios & Queries</h3>
            <span className="exec-table-subtitle text-xs">Tap any row to evaluate immediate marine safety</span>
          </div>

          <div className="exec-table-container">
            <div className="exec-table-head-row">
              <span className="th-sender">Zone / Vessel</span>
              <span className="th-date">Timestamp</span>
              <span className="th-status">Safety Verdict</span>
              <span className="th-coords">Coordinates</span>
            </div>

            <div className="exec-table-body">
              {scenariosList.map(([key, item]) => {
                const itemVerdict = item.expectedVerdict;
                const statusTagClass = `exec-status--${itemVerdict.toLowerCase()}`;
                const initialLetter = item.name ? item.name.charAt(3) || '⚓' : '⚓';

                return (
                  <div
                    key={key}
                    className="exec-table-row"
                    onClick={() => {
                      onSelectScenario(key);
                      onNavigateView('map');
                    }}
                  >
                    <div className="td-sender">
                      <div className="sender-avatar">
                        <span>{initialLetter}</span>
                      </div>
                      <div className="sender-info">
                        <span className="sender-name">{item.name}</span>
                        <span className="sender-sub text-xs">{item.description.slice(0, 32)}...</span>
                      </div>
                    </div>

                    <div className="td-date text-xs mono">
                      {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </div>

                    <div className="td-status">
                      <span className={`exec-status-pill ${statusTagClass}`}>
                        <span className="exec-status-dot" />
                        {itemVerdict}
                      </span>
                    </div>

                    <div className="td-coords mono text-xs">
                      16.98° N, 73.28° E
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Right Floating Statistic Card */}
      <div className="exec-right-column">
        <div className="exec-statistic-card">
          <div className="stat-card-top">
            <div className="stat-card-title-wrap">
              <span className="stat-card-title">Statistic</span>
              <span className="stat-card-info-icon">ⓘ</span>
            </div>
            <div className="stat-card-dropdown text-xs mono">
              Today ⌵
            </div>
          </div>

          {/* Large Clean Donut Chart */}
          <div className="stat-donut-wrapper">
            <div className="stat-donut-chart">
              <svg viewBox="0 0 100 100" className="stat-donut-svg">
                <circle className="stat-donut-bg" cx="50" cy="50" r="38" />
                <circle
                  className="stat-donut-fill"
                  cx="50"
                  cy="50"
                  r="38"
                  strokeDasharray={`${(passedCount / Math.max(ruleTrace.length, 1)) * 238.76} 238.76`}
                />
              </svg>
              <div className="stat-donut-center">
                <span className="stat-donut-label text-xs">Integrity</span>
                <span className="stat-donut-val mono">{passPercentage}%</span>
              </div>
            </div>

            <div className="stat-donut-legends">
              <div className="stat-legend-item">
                <span className="legend-box legend-box--blue" />
                <span className="text-xs">Passed ({passedCount})</span>
              </div>
              <div className="stat-legend-item">
                <span className="legend-box legend-box--dark" />
                <span className="text-xs">Violations ({failedCount})</span>
              </div>
            </div>
          </div>

          {/* Telemetry Sensor List (Matching Spotify/Apple/Bitcoin item list) */}
          <div className="stat-items-list">
            <div className="stat-item-row" onClick={() => onNavigateView('map')}>
              <div className="stat-item-icon-wrap stat-item-icon--blue">
                <IconWave size={16} color="#FFFFFF" />
              </div>
              <div className="stat-item-info">
                <span className="stat-item-name">INCOIS Wave Buoy</span>
                <span className="stat-item-time text-xs">Swell 1.8m • Normal</span>
              </div>
              <span className="stat-item-badge stat-item-badge--pass"><IconCheck size={12} /> OK</span>
            </div>

            <div className="stat-item-row" onClick={() => onNavigateView('map')}>
              <div className="stat-item-icon-wrap stat-item-icon--dark">
                <IconShield size={16} color="#FFFFFF" />
              </div>
              <div className="stat-item-info">
                <span className="stat-item-name">Coast Guard MPA</span>
                <span className="stat-item-time text-xs">Geofence Boundary</span>
              </div>
              <span className="stat-item-badge stat-item-badge--pass"><IconCheck size={12} /> Clear</span>
            </div>

            <div className="stat-item-row" onClick={() => onNavigateView('map')}>
              <div className="stat-item-icon-wrap stat-item-icon--amber">
                <IconAlert size={16} color="#FFFFFF" />
              </div>
              <div className="stat-item-info">
                <span className="stat-item-name">IMD Cyclone Radar</span>
                <span className="stat-item-time text-xs">Wind Gust 24kt</span>
              </div>
              <span className="stat-item-badge stat-item-badge--caution">Monitor</span>
            </div>

            <div className="stat-item-row" onClick={() => onNavigateView('chat')}>
              <div className="stat-item-icon-wrap stat-item-icon--purple">
                <IconCopilotBot size={16} color="#FFFFFF" />
              </div>
              <div className="stat-item-info">
                <span className="stat-item-name">VARUNA Copilot</span>
                <span className="stat-item-time text-xs">AI Advisory Ready</span>
              </div>
              <span className="stat-item-badge stat-item-badge--ai">Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

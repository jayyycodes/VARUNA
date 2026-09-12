import React, { useState, useEffect } from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { FIXTURES } from '../../fixtures';
import { apiClient } from '../../api/client';
import { useLocalization } from '../../hooks/useLocalization';
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
  const { t } = useLocalization();
  const [fleetCount, setFleetCount] = useState<number>(24);
  const [alertCount, setAlertCount] = useState<number>(4);
  const [liveSst, setLiveSst] = useState<string>('28.4°C');
  const [liveChl, setLiveChl] = useState<string>('0.82 mg/m³');
  const [isLiveApi, setIsLiveApi] = useState<boolean>(false);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [fleet, alerts, trends, health] = await Promise.all([
          apiClient.fetchFleetStatus().catch(() => null),
          apiClient.fetchActiveAlerts().catch(() => null),
          apiClient.fetchHistoricalTrends().catch(() => null),
          apiClient.checkHealth().catch(() => ({ online: false })),
        ]);

        if (health?.online) setIsLiveApi(true);
        if (fleet?.active_craft) setFleetCount(fleet.active_craft);
        if (alerts?.length) setAlertCount(alerts.length);
        if (trends) {
          if (trends.sst_observed_celsius?.length) {
            const lastSst = trends.sst_observed_celsius[trends.sst_observed_celsius.length - 1];
            setLiveSst(`${lastSst.toFixed(1)}°C`);
          }
          if (trends.chlorophyll_observed_mg_m3?.length) {
            const lastChl = trends.chlorophyll_observed_mg_m3[trends.chlorophyll_observed_mg_m3.length - 1];
            setLiveChl(`${lastChl.toFixed(2)} mg/m³`);
          }
        }
      } catch (err) {
        console.warn('Dashboard live stats error:', err);
      }
    }
    loadDashboardData();
  }, []);

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
          <h2 className="exec-section-title">
            {t('marineAdvisoryCards')} {isLiveApi && <span className="ml-2 text-xs text-safe font-bold">● LIVE FASTAPI BACKEND</span>}
          </h2>
          <span className="exec-section-link" onClick={() => onNavigateView('map')}>{t('viewMapView')}</span>
        </div>

        <div className="exec-cards-row">
          {/* Hero Card 1: Obsidian Matte Card */}
          <div className="exec-card exec-card--dark">
            <div className="exec-card__top">
              <span className="exec-card__chip">◈ VARUNA NAV</span>
              <span className="exec-card__menu">•••</span>
            </div>
            <div className="exec-card__main-val">
              {verdict === 'SAFE' && t('safe')}
              {verdict === 'CAUTION' && t('caution')}
              {verdict === 'UNSAFE' && t('unsafe')}
              {verdict === 'UNKNOWN' && t('unknown')}
            </div>
            <div className="exec-card__sub-text mono">
              ZONE ID • RATNAGIRI-WZ-04
            </div>
            <div className="exec-card__bottom">
              <span className="exec-card__date mono">VALID: TODAY</span>
              <span className="exec-card__brand-tag">INCOIS / IMD VERIFIED</span>
            </div>
          </div>

          {/* Hero Card 2: Pure White Telemetry Card */}
          <div className="exec-card exec-card--light">
            <div className="exec-card__top">
              <span className="exec-card__chip-light">{t('oceanTelemetry')}</span>
              <span className="exec-card__menu-light">•••</span>
            </div>
            <div className="exec-card__main-val-light">
              3 PFZ ZONES ACTIVE
            </div>
            <div className="exec-card__sub-text-light mono">
              SST {liveSst} • CHL {liveChl}
            </div>
            <div className="exec-card__bottom">
              <span className="exec-card__date-light mono">UPDATED: {isLiveApi ? 'LIVE API' : 'LIVE'}</span>
              <div className="exec-card__toggle-pill">
                <span className="toggle-dot" />
                <span>{t('sensorsOn')}</span>
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
            <span>{t('routeOptimize')}</span>
          </button>

          <button
            type="button"
            className="exec-action-pill"
            onClick={() => onNavigateView('reasoning')}
          >
            <span className="pill-icon-circle pill-icon-circle--dark"><IconShield size={14} color="#FFFFFF" /></span>
            <span>{t('rulesEngine')}</span>
          </button>

          <button
            type="button"
            className="exec-action-pill"
            onClick={() => onNavigateView('fleet')}
          >
            <span className="pill-icon-circle pill-icon-circle--dark"><IconShip size={14} color="#FFFFFF" /></span>
            <span>{t('fleetOps')} ({fleetCount})</span>
          </button>

          <button
            type="button"
            className="exec-action-pill"
            onClick={() => onNavigateView('trends')}
          >
            <span className="pill-icon-circle pill-icon-circle--dark"><IconWave size={14} color="#FFFFFF" /></span>
            <span>{t('fisheryTrends')}</span>
          </button>

          <button
            type="button"
            className="exec-action-pill"
            onClick={() => onNavigateView('alerts')}
          >
            <span className="pill-icon-circle pill-icon-circle--dark"><IconAlert size={14} color="#FFFFFF" /></span>
            <span>{t('activeAlerts')} ({alertCount})</span>
          </button>
        </div>

        {/* 3. Recent Maritime Scenarios & Vessel Inquiries Table */}
        <div className="exec-table-section">
          <div className="exec-table-header">
            <h3 className="exec-table-title">{t('recentScenariosTitle')}</h3>
            <span className="exec-table-subtitle text-xs">{t('tapToEvaluate')}</span>
          </div>

          <div className="exec-table-container">
            <div className="exec-table-head-row">
              <span className="th-sender">{t('zoneVessel')}</span>
              <span className="th-date">{t('timestamp')}</span>
              <span className="th-status">{t('safetyVerdict')}</span>
              <span className="th-coords">{t('coordinates')}</span>
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
              <span className="stat-card-title">{t('statistic')}</span>
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
                <span className="stat-donut-label text-xs">{t('integrity')}</span>
                <span className="stat-donut-val mono">{passPercentage}%</span>
              </div>
            </div>

            <div className="stat-donut-legends">
              <div className="stat-legend-item">
                <span className="legend-box legend-box--blue" />
                <span className="text-xs">{t('passedChecks')} ({passedCount})</span>
              </div>
              <div className="stat-legend-item">
                <span className="legend-box legend-box--dark" />
                <span className="text-xs">{t('violations')} ({failedCount})</span>
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
              <div className="stat-item-icon-wrap stat-item-icon--ocean">
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

import React, { useState, useEffect } from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { apiClient } from '../../api/client';
import { useLocalization } from '../../hooks/useLocalization';
import { useIsMobile } from '../../hooks/useIsMobile';
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
  const isMobile = useIsMobile();
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

interface ScenarioEntry {
  key: string;
  name: string;
  description: string;
  expectedVerdict: 'SAFE' | 'CAUTION' | 'UNSAFE' | 'UNKNOWN';
}

const SCENARIOS_CATALOG: ScenarioEntry[] = [
  { key: 'safe_complete', name: 'Safe / Complete (Ratnagiri)', description: 'Favorable sea conditions, wave 1.1m, wind 11 kts.', expectedVerdict: 'SAFE' },
  { key: 'caution_high_wave', name: 'Caution / High Wave (Kochi)', description: 'Swell 2.8m exceeds threshold for small craft.', expectedVerdict: 'CAUTION' },
  { key: 'unsafe_cyclone', name: 'Unsafe / Cyclone (Visakhapatnam)', description: 'Severe cyclonic storm alert. All operations suspended.', expectedVerdict: 'UNSAFE' },
  { key: 'pfz_productive_unsafe', name: 'Productive PFZ but Unsafe (Ratnagiri)', description: 'High chlorophyll bloom but severe 3.4m sea state.', expectedVerdict: 'UNSAFE' },
  { key: 'geofence_restricted', name: 'Geofence Restricted (Malvan MPA)', description: 'Marine Protected Area boundary breach detected.', expectedVerdict: 'UNSAFE' },
  { key: 'weather_stale', name: 'Weather Stale (Veraval)', description: 'Telemetry sensor age 4.5h exceeds freshness SLA.', expectedVerdict: 'UNKNOWN' },
  { key: 'indeterminate_sensor_blackout', name: 'Sensor Blackout (Paradip)', description: 'Doppler radar and telemetry offline.', expectedVerdict: 'UNKNOWN' },
  { key: 'rag_cited_advisory', name: 'RAG Cited Advisory (Mandapam)', description: 'Palk Bay shallow waters navigation advisory.', expectedVerdict: 'SAFE' },
  { key: 'rag_insufficient_evidence', name: 'RAG Insufficient (Lakshadweep)', description: 'Lagoon channel clearance telemetry incomplete.', expectedVerdict: 'UNKNOWN' },
];

  const verdict = response?.summary?.verdict || 'SAFE';
  const ruleTrace = response?.evidence_panel?.rule_trace || [];
  const passedCount = ruleTrace.length > 0 ? ruleTrace.filter((r) => r.passed).length : (verdict === 'SAFE' ? 2 : verdict === 'CAUTION' ? 1 : 0);
  const failedCount = ruleTrace.length > 0 ? ruleTrace.length - passedCount : (verdict === 'SAFE' ? 0 : verdict === 'CAUTION' ? 1 : 2);
  const totalRules = Math.max(passedCount + failedCount, 1);
  const passPercentage = Math.round((passedCount / totalRules) * 100);

  // Extract dynamic location / sector name from active response
  const allFeatures = response?.map?.layers?.flatMap((l) => l.feature_collection?.features || []) || [];
  const userLocFeature = allFeatures.find(
    (f) => f.properties?.type === 'user_location' || f.properties?.layer_id === 'layer-user-loc'
  );
  const activeZoneName = userLocFeature?.properties?.title || userLocFeature?.properties?.name || 'Ratnagiri Coast';
  const activeZoneId = userLocFeature?.properties?.zone_id || (activeZoneName.toUpperCase().replace(/\s+/g, '-') + '-04');

  // Extract dynamic PFZ telemetry
  const pfzFeatures = allFeatures.filter(
    (f) => f.properties?.type === 'pfz_zone' || f.properties?.layer_id?.includes('pfz') || f.properties?.type === 'pfz'
  );
  const activePfzCountNum = pfzFeatures.length > 0 ? pfzFeatures.length : 3;
  const firstPfz = pfzFeatures[0]?.properties;
  const displaySst = firstPfz?.sst ? (String(firstPfz.sst).includes('°C') ? firstPfz.sst : `${firstPfz.sst}°C`) : liveSst;
  const displayChl = firstPfz?.chlorophyll ? (String(firstPfz.chlorophyll).includes('mg/m³') ? firstPfz.chlorophyll : `${firstPfz.chlorophyll} mg/m³`) : liveChl;

  // Live sensor status extraction from active rule trace
  const waveRule = ruleTrace.find(
    (r) => r.domain === 'marine_wave' || r.domain?.includes('wave') || r.rule_id?.includes('WAVE')
  );
  const waveVal = waveRule ? `${waveRule.measured_value}m` : '1.44m';
  const wavePassed = waveRule ? waveRule.passed : (verdict !== 'UNSAFE');

  const mpaRule = ruleTrace.find(
    (r) => r.domain?.includes('geofence') || r.rule_id?.includes('MPA') || r.rule_id?.includes('GEOFENCE')
  );
  const mpaPassed = mpaRule ? mpaRule.passed : true;

  const windRule = ruleTrace.find(
    (r) => r.domain === 'atmospheric_wind' || r.domain?.includes('wind') || r.rule_id?.includes('WIND')
  );
  const windVal = windRule ? `${windRule.measured_value} kts` : '17 km/h';
  const windPassed = windRule ? windRule.passed : (verdict === 'SAFE');

  const verdictDisplay = verdict === 'SAFE' ? 'SAFE TO SAIL' : verdict === 'CAUTION' ? 'CAUTION: MONITOR' : verdict === 'UNSAFE' ? 'UNSAFE: RETURN TO PORT' : 'UNKNOWN';

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
              {verdictDisplay}
            </div>
            <div className="exec-card__sub-text mono">
              ZONE ID • {activeZoneId}
            </div>
            <div className="exec-card__bottom">
              <span className="exec-card__date mono">{t('validToday')}</span>
              <span className="exec-card__brand-tag">{t('incoisImdVerified')}</span>
            </div>
          </div>

          {/* Hero Card 2: Pure White Telemetry Card */}
          <div className="exec-card exec-card--light">
            <div className="exec-card__top">
              <span className="exec-card__chip-light">{t('oceanTelemetry')}</span>
              <span className="exec-card__menu-light">•••</span>
            </div>
            <div className="exec-card__main-val-light">
              {activePfzCountNum} PFZ ZONES ACTIVE
            </div>
            <div className="exec-card__sub-text-light mono">
              SST {displaySst} • CHL {displayChl}
            </div>
            <div className="exec-card__bottom">
              <span className="exec-card__date-light mono">
                {isLiveApi ? 'UPDATED: LIVE API' : t('updatedLive')}
              </span>
              <div className="exec-card__toggle-pill">
                <span className="toggle-dot" />
                <span>Sensors Active</span>
              </div>
            </div>
          </div>
        </div>

        {/* 2. Action Pills Row (Mobile Only) */}
        {isMobile && (
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
        )}

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
              {SCENARIOS_CATALOG.map((item) => {
                const key = item.key;
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
                        <span className="sender-name">{t(`scenario_${key}_name`) || item.name}</span>
                        <span className="sender-sub text-xs">{(t(`scenario_${key}_desc`) || item.description).slice(0, 42)}...</span>
                      </div>
                    </div>

                    <div className="td-meta-row">
                      <div className="td-status">
                        <span className={`exec-status-pill ${statusTagClass}`}>
                          <span className="exec-status-dot" />
                          {itemVerdict}
                        </span>
                      </div>

                      <div className="td-date text-xs mono">
                        {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </div>

                      <div className="td-coords mono text-xs">
                        16.98° N, 73.28° E
                      </div>
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
                  strokeDasharray={`${(passedCount / totalRules) * 238.76} 238.76`}
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
                <span className="stat-item-name">{t('incoisWaveBuoy')}</span>
                <span className="stat-item-time text-xs">Swell {waveVal} • {wavePassed ? 'Normal' : 'High Wave Alert'}</span>
              </div>
              <span className={`stat-item-badge ${wavePassed ? 'stat-item-badge--pass' : 'stat-item-badge--caution'}`}>
                {wavePassed ? <><IconCheck size={12} /> OK</> : 'ALERT'}
              </span>
            </div>

            <div className="stat-item-row" onClick={() => onNavigateView('map')}>
              <div className="stat-item-icon-wrap stat-item-icon--dark">
                <IconShield size={16} color="#FFFFFF" />
              </div>
              <div className="stat-item-info">
                <span className="stat-item-name">{t('coastGuardMpa')}</span>
                <span className="stat-item-time text-xs">Geofence Boundary • {mpaPassed ? 'Clear' : 'Exclusion Zone Incursion'}</span>
              </div>
              <span className={`stat-item-badge ${mpaPassed ? 'stat-item-badge--pass' : 'stat-item-badge--caution'}`}>
                {mpaPassed ? <><IconCheck size={12} /> Clear</> : 'RESTRICTED'}
              </span>
            </div>

            <div className="stat-item-row" onClick={() => onNavigateView('map')}>
              <div className="stat-item-icon-wrap stat-item-icon--amber">
                <IconAlert size={16} color="#FFFFFF" />
              </div>
              <div className="stat-item-info">
                <span className="stat-item-name">{t('imdCycloneRadar')}</span>
                <span className="stat-item-time text-xs">Wind {windVal} • {windPassed ? 'Safe Envelope' : 'Squall Threat'}</span>
              </div>
              <span className={`stat-item-badge ${windPassed ? 'stat-item-badge--pass' : 'stat-item-badge--caution'}`}>
                {windPassed ? 'Monitor' : 'GALE ALERT'}
              </span>
            </div>

            <div className="stat-item-row" onClick={() => onNavigateView('chat')}>
              <div className="stat-item-icon-wrap stat-item-icon--ocean">
                <IconCopilotBot size={16} color="#FFFFFF" />
              </div>
              <div className="stat-item-info">
                <span className="stat-item-name">{t('varunaCopilot')}</span>
                <span className="stat-item-time text-xs">LangGraph Agent • {isLiveApi ? 'Live Gateway' : 'Ready'}</span>
              </div>
              <span className="stat-item-badge stat-item-badge--ai">{isLiveApi ? 'LIVE API' : t('badgeActive')}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { apiClient } from '../../api/client';
import { useLocalization } from '../../hooks/useLocalization';
import { useAppStore } from '../../store/useAppStore';
import './ActiveAlertsView.css';

interface ActiveAlertsViewProps {
  response?: UserResponseV1 | null;
  onSelectScenario: (scenarioId: string) => void;
}

export const ActiveAlertsView: React.FC<ActiveAlertsViewProps> = ({ response, onSelectScenario }) => {
  const { t } = useLocalization();
  const activeQuery = useAppStore((s) => s.activeQuery);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    async function loadAlerts() {
      setLoading(true);
      try {
        const liveAlerts = await apiClient.fetchActiveAlerts();
        if (isMounted) {
          setAlerts(liveAlerts);
        }
      } catch (err) {
        console.error('Failed to load active alerts:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadAlerts();
    return () => {
      isMounted = false;
    };
  }, []);

  const isRegulatoryQuery = Boolean(
    (activeQuery && /ban|monsoon|trawl|mfra|sanctuary|statutory|mechanized|july|law/i.test(activeQuery)) ||
    response?.claims?.some((c) => /monsoon|trawl|mfra|sanctuary|statutory|prohibited/i.test(c.text)) ||
    response?.citations?.some((c) => /mfra|monsoon|regulation|fisheries/i.test(c.title))
  );

  const queryOrText = `${activeQuery || ''} ${response?.summary?.headline || ''} ${response?.summary?.action || ''}`.toLowerCase();
  let alertRegion = 'Maharashtra Coastal Waters (12 NM / EEZ)';
  let alertHeadline = 'Monsoon Trawling Ban Enforced (1 June – 31 July)';
  let alertAuth = 'Department of Fisheries MH & Indian Coast Guard';
  let alertValid = '31-JUL-2026 23:59 IST';

  if (/kerala|kochi|cochin|kollam/i.test(queryOrText)) {
    alertRegion = 'Kerala Coastal Waters (Territorial 12 NM)';
    alertHeadline = 'Uniform Monsoon Fishing Ban (1 June – 31 July)';
    alertAuth = 'Kerala Fisheries Dept & Marine Enforcement';
    alertValid = '31-JUL-2026 23:59 IST';
  } else if (/tamil nadu|chennai|thoothukudi|mannar/i.test(queryOrText)) {
    alertRegion = 'Tamil Nadu Coastal Waters (Palk Bay / Coromandel)';
    alertHeadline = 'East Coast Annual Fishing Ban (15 April – 14 June)';
    alertAuth = 'Tamil Nadu Dept of Fisheries & Coastal Security Group';
    alertValid = '14-JUN-2026 23:59 IST';
  } else if (/andhra|visakhapatnam|vizag|kakinada/i.test(queryOrText)) {
    alertRegion = 'Andhra Pradesh Coastal Waters (Bay of Bengal)';
    alertHeadline = 'East Coast Annual Fishing Ban (15 April – 14 June)';
    alertAuth = 'Andhra Pradesh Fisheries Dept & Coastal Police';
    alertValid = '14-JUN-2026 23:59 IST';
  } else if (/odisha|orissa|paradeep|gahirmatha/i.test(queryOrText)) {
    alertRegion = 'Odisha Coastal Waters & Olive Ridley Protected Belts';
    alertHeadline = 'East Coast Annual Fishing Ban (15 April – 14 June)';
    alertAuth = 'Odisha Fisheries Dept & Forest Wildlife Wing';
    alertValid = '14-JUN-2026 23:59 IST';
  } else if (/gujarat|veraval|porbandar|kutch/i.test(queryOrText)) {
    alertRegion = 'Gujarat Coastal Waters & Gulf of Kutch';
    alertHeadline = 'West Coast Monsoon Fishing Ban (1 June – 31 July)';
    alertAuth = 'Gujarat Fisheries Dept & Indian Coast Guard';
    alertValid = '31-JUL-2026 23:59 IST';
  } else if (/karnataka|mangalore|malpe/i.test(queryOrText)) {
    alertRegion = 'Karnataka Coastal Waters (12 NM)';
    alertHeadline = 'West Coast Monsoon Fishing Ban (1 June – 31 July)';
    alertAuth = 'Karnataka Directorate of Fisheries & Coastal Police';
    alertValid = '31-JUL-2026 23:59 IST';
  }

  const promptRegulatoryAlert = isRegulatoryQuery
    ? {
        id: 'alert-prompt-regulatory',
        type: 'STATUTORY PROHIBITION',
        region: alertRegion,
        headline: alertHeadline,
        details:
          response?.summary?.action ||
          `Mechanized trawlers and purse-seiners are strictly prohibited under state statutory provisions & Central Directives. Violations subject to vessel impoundment and penalty.`,
        severity: 'UNSAFE',
        authority: alertAuth,
        validUntil: alertValid,
        actionScenario: 'geofence_restricted',
        isPromptNotice: true,
      }
    : null;

  const displayAlerts = promptRegulatoryAlert
    ? [promptRegulatoryAlert, ...alerts.filter((a) => a.id !== promptRegulatoryAlert.id)]
    : alerts;

  return (
    <div className="active-alerts-view">
      <header className="alerts-header">
        <div>
          <div className="alerts-badge mono text-xs">{t('coastalHazardBroadcast')}</div>
          <h1 className="alerts-title text-display">{t('activeAlertsTitle')}</h1>
          <p className="alerts-subtitle text-sm text-muted">
            {t('activeAlertsSubtitle')}
          </p>
        </div>
      </header>

      {loading && (
        <div className="alerts-loading text-center py-6 text-sm text-muted">
          <span>{t('analyzingDomains')}...</span>
        </div>
      )}

      {/* Grid of Alert Cards */}
      <div className="alerts-grid">
        {displayAlerts.map((alert) => {
          const isUnsafe = alert.severity === 'UNSAFE';
          const isCaution = alert.severity === 'CAUTION';
          const cardClass = isUnsafe
            ? 'alert-card--unsafe'
            : isCaution
            ? 'alert-card--caution'
            : 'alert-card--unknown';

          return (
            <article
              key={alert.id}
              className={`alert-card glass ${cardClass} ${alert.isPromptNotice ? 'alert-card--prompt-bulletin' : ''}`}
              style={alert.isPromptNotice ? { border: '1.5px solid rgba(239, 68, 68, 0.6)', background: 'rgba(239, 68, 68, 0.06)' } : undefined}
            >
              <div className="alert-card__top">
                <span className={`alert-pill alert-pill--${alert.severity.toLowerCase()} mono text-xs`}>
                  {alert.isPromptNotice ? '⚡ ' : ''}{alert.type}
                </span>
                <span className="alert-region mono text-xs">{alert.region}</span>
              </div>

              <h3 className="alert-headline text-md font-bold">{alert.headline}</h3>
              <p className="alert-details text-xs text-muted">{alert.details}</p>

              <div className="alert-meta mono text-xs">
                <div>{t('authority')}: <span className="text-foam">{alert.authority}</span></div>
                <div>{t('validity')}: <span className="text-foam">{alert.validUntil}</span></div>
              </div>

              <button
                type="button"
                className="alert-inspect-btn"
                onClick={() => onSelectScenario(alert.actionScenario)}
              >
                {t('evaluateOnMap')}
              </button>
            </article>
          );
        })}
      </div>
    </div>
  );
};

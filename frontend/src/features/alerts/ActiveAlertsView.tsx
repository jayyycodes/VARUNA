import React, { useState, useEffect } from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { apiClient } from '../../api/client';
import { useLocalization } from '../../hooks/useLocalization';
import './ActiveAlertsView.css';

interface ActiveAlertsViewProps {
  response?: UserResponseV1 | null;
  onSelectScenario: (scenarioId: string) => void;
}

export const ActiveAlertsView: React.FC<ActiveAlertsViewProps> = ({ response: _response, onSelectScenario }) => {
  const { t } = useLocalization();
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
        {alerts.map((alert) => {
          const isUnsafe = alert.severity === 'UNSAFE';
          const isCaution = alert.severity === 'CAUTION';
          const cardClass = isUnsafe
            ? 'alert-card--unsafe'
            : isCaution
            ? 'alert-card--caution'
            : 'alert-card--unknown';

          return (
            <article key={alert.id} className={`alert-card glass ${cardClass}`}>
              <div className="alert-card__top">
                <span className={`alert-pill alert-pill--${alert.severity.toLowerCase()} mono text-xs`}>
                  {alert.type}
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

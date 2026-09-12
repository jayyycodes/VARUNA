import React, { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { useLocalization } from '../../hooks/useLocalization';
import './FleetOpsView.css';

export const FleetOpsView: React.FC = () => {
  const { t } = useLocalization();
  const [fleetData, setFleetData] = useState<any>({
    active_craft: 24,
    in_pfz_count: 14,
    weather_clear_pct: 88.5,
    vessels: [],
    isLive: false,
  });
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    async function loadFleet() {
      setLoading(true);
      try {
        const data = await apiClient.fetchFleetStatus();
        if (isMounted) {
          setFleetData(data);
        }
      } catch (e) {
        console.error('Failed to load fleet status:', e);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadFleet();
    return () => {
      isMounted = false;
    };
  }, []);

  const vessels = fleetData.vessels || [];

  return (
    <div className="fleet-ops-view">
      <header className="fleet-header">
        <div>
          <div className="fleet-badge mono text-xs">{t('fleetMonitorBadge')}</div>
          <h1 className="fleet-title text-display">{t('fleetTitle')}</h1>
          <p className="fleet-subtitle text-sm text-muted">
            {t('fleetSubtitle')}
          </p>
        </div>

        <div className="fleet-metrics-strip glass">
          <div className="metric-box">
            <span className="metric-label mono text-xs">{t('activeCraft')}</span>
            <span className="metric-num mono text-md font-bold text-teal">
              {fleetData.active_craft} Vessels
            </span>
          </div>
          <div className="metric-box">
            <span className="metric-label mono text-xs">{t('inPfzZones')}</span>
            <span className="metric-num mono text-md font-bold">
              {fleetData.in_pfz_count} Vessels
            </span>
          </div>
          <div className="metric-box">
            <span className="metric-label mono text-xs">{t('weatherClear')}</span>
            <span className="metric-num mono text-md font-bold text-safe">
              {fleetData.weather_clear_pct}%
            </span>
          </div>
        </div>
      </header>

      {loading && (
        <div className="text-center py-4 text-xs text-muted">
          <span>{t('analyzingDomains')}...</span>
        </div>
      )}

      {/* Vessels Table */}
      <div className="fleet-table-wrap glass">
        <table className="fleet-table">
          <thead>
            <tr>
              <th>{t('vesselIdName')}</th>
              <th>{t('vesselType')}</th>
              <th>{t('homePort')}</th>
              <th>{t('vesselCoords')}</th>
              <th>{t('operatingStatus')}</th>
              <th>{t('safetyState')}</th>
              <th>{t('aisRelay')}</th>
            </tr>
          </thead>
          <tbody>
            {vessels.map((v: any) => {
              const isSafe = (v.compliance || '').includes('SAFE');
              const isCaution = (v.compliance || '').includes('CAUTION');
              const pillClass = isSafe
                ? 'compliance--safe'
                : isCaution
                ? 'compliance--caution'
                : 'compliance--unsafe';

              return (
                <tr key={v.id}>
                  <td>
                    <div className="vessel-id mono font-bold text-foam">{v.name}</div>
                    <div className="vessel-code mono text-xs text-muted">{v.id}</div>
                  </td>
                  <td className="text-xs">{v.type}</td>
                  <td className="text-xs">{v.port}</td>
                  <td className="mono text-xs tabular-nums text-muted">{v.coordinates}</td>
                  <td className="text-xs font-bold">{v.status}</td>
                  <td>
                    <span className={`compliance-pill ${pillClass} mono text-xs font-bold`}>
                      {v.compliance}
                    </span>
                  </td>
                  <td className="mono text-xs text-teal">{v.ais_status || v.aisStatus || 'Active'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

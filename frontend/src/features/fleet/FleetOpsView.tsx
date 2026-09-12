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
          <div className="fleet-badge mono text-xs">
            {t('fleetMonitorBadge')} {fleetData.isLive && <span className="ml-2 text-safe font-bold">● LIVE FASTAPI BACKEND</span>}
          </div>
          <h1 className="fleet-title text-display">{t('fleetTitle')}</h1>
          <p className="fleet-subtitle text-sm text-muted">
            {t('fleetSubtitle')}
          </p>
        </div>

        <div className="fleet-metrics-strip glass">
          <div className="metric-box">
            <span className="metric-label mono text-xs">{t('activeCraft')}</span>
            <span className="metric-num mono text-md font-bold text-teal">
              {fleetData.active_craft || 24} Vessels
            </span>
          </div>
          <div className="metric-box">
            <span className="metric-label mono text-xs">{t('inPfzZones')}</span>
            <span className="metric-num mono text-md font-bold">
              {fleetData.in_pfz_count || 14} Vessels
            </span>
          </div>
          <div className="metric-box">
            <span className="metric-label mono text-xs">{t('weatherClear')}</span>
            <span className="metric-num mono text-md font-bold text-safe">
              {fleetData.weather_clear_pct || 88.5}%
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
              <th>Telemetry & Fuel</th>
              <th>{t('safetyState')}</th>
              <th>{t('aisRelay')}</th>
            </tr>
          </thead>
          <tbody>
            {(vessels.length > 0 ? vessels : [
              {
                id: "IND-MH-0192",
                name: "Matsya Sagar IV",
                type: "Mechanized Trawler (14m)",
                port: "Mirya Bay, Ratnagiri",
                coordinates: "17.02° N, 73.18° E",
                status: "Operating in PFZ Zone",
                compliance: "SAFE (All Clear)",
                severity: "safe",
                fuel: "74%",
                crew: 6,
                speed_kts: 6.8,
                ais_status: "Active (Class B AIS)",
              },
              {
                id: "IND-MH-5510",
                name: "Sindhudurg Star",
                type: "Artisanal Motor Craft (7.5m)",
                port: "Malvan Port",
                coordinates: "16.02° N, 73.42° E",
                status: "Transit near Sanctuary Buffer",
                compliance: "SAFE (Clear of MPA Core)",
                severity: "safe",
                fuel: "65%",
                crew: 3,
                speed_kts: 5.2,
                ais_status: "Active (VHF Ch 16)",
              },
              {
                id: "IND-KL-4081",
                name: "Samudra Jyoti",
                type: "Motorized Gillnetter (9.5m)",
                port: "Cochin Harbour",
                coordinates: "09.92° N, 76.15° E",
                status: "Returning to Harbor",
                compliance: "CAUTION (Wave Swell 2.6m)",
                severity: "caution",
                fuel: "42%",
                crew: 4,
                speed_kts: 7.4,
                ais_status: "Active",
              },
              {
                id: "IND-AP-8821",
                name: "Bay Queen III",
                type: "Deep Sea Longliner (16m)",
                port: "Visakhapatnam",
                coordinates: "17.65° N, 83.32° E",
                status: "Moored / Harbor Anchor",
                compliance: "UNSAFE (Port Signal #8 Active)",
                severity: "unsafe",
                fuel: "90%",
                crew: 8,
                speed_kts: 0.0,
                ais_status: "Harbour Transponder Standby",
              },
              {
                id: "IND-GJ-1104",
                name: "Saurashtra Shakti",
                type: "Wooden Trawler (12m)",
                port: "Veraval Port",
                coordinates: "20.90° N, 70.37° E",
                status: "Fishing in Continental Shelf",
                compliance: "SAFE (EEZ Verified)",
                severity: "safe",
                fuel: "58%",
                crew: 5,
                speed_kts: 6.1,
                ais_status: "Active",
              },
            ]).map((v: any) => {
              const isSafe = (v.compliance || '').includes('SAFE') || v.severity === 'safe';
              const isCaution = (v.compliance || '').includes('CAUTION') || v.severity === 'caution';
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
                  <td className="mono text-xs text-muted">
                    {v.speed_kts !== undefined ? `${v.speed_kts} kts` : '6.5 kts'} • Fuel {v.fuel || '75%'}
                  </td>
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

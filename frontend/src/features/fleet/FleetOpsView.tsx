import React from 'react';
import './FleetOpsView.css';

export const FleetOpsView: React.FC = () => {
  const vessels = [
    {
      id: 'IND-MH-0192',
      name: 'Matsya Sagar IV',
      type: 'Trawler (14m)',
      port: 'Mirya Bay, Ratnagiri',
      coordinates: '17.02° N, 73.18° E',
      status: 'Operating in PFZ',
      compliance: 'SAFE (All Clear)',
      fuel: '74%',
      crew: 6,
      aisStatus: 'Active (VHF Ch 16)',
    },
    {
      id: 'IND-KL-4081',
      name: 'Samudra Jyoti',
      type: 'Gillnetter (9.5m)',
      port: 'Cochin Harbour',
      coordinates: '09.92° N, 76.15° E',
      status: 'Returning to Port',
      compliance: 'CAUTION (Wave Swell)',
      fuel: '42%',
      crew: 4,
      aisStatus: 'Active',
    },
    {
      id: 'IND-AP-8821',
      name: 'Bay Queen III',
      type: 'Longliner (16m)',
      port: 'Visakhapatnam',
      coordinates: '17.65° N, 83.32° E',
      status: 'Moored / Standby',
      compliance: 'UNSAFE (Port Alert #8)',
      fuel: '90%',
      crew: 8,
      aisStatus: 'Harbour Anchor',
    },
    {
      id: 'IND-MH-5510',
      name: 'Sindhudurg Star',
      type: 'Artisanal Craft (7m)',
      port: 'Malvan Port',
      coordinates: '16.02° N, 73.42° E',
      status: 'Patrolling Buffer',
      compliance: 'SAFE (Clear of MPA)',
      fuel: '65%',
      crew: 3,
      aisStatus: 'Active',
    },
  ];

  return (
    <div className="fleet-ops-view">
      <header className="fleet-header">
        <div>
          <div className="fleet-badge mono text-xs">FLEET TELEMETRY & AIS MONITOR</div>
          <h1 className="fleet-title text-display">Coastal Fleet Operations</h1>
          <p className="fleet-subtitle text-sm text-muted">
            Live positioning, geofence compliance, safety advisories, and harbor moorings.
          </p>
        </div>

        <div className="fleet-metrics-strip glass">
          <div className="metric-box">
            <span className="metric-label mono text-xs">ACTIVE CRAFT</span>
            <span className="metric-num mono text-md font-bold text-teal">24 Vessels</span>
          </div>
          <div className="metric-box">
            <span className="metric-label mono text-xs">IN PFZ ZONES</span>
            <span className="metric-num mono text-md font-bold">14 Vessels</span>
          </div>
          <div className="metric-box">
            <span className="metric-label mono text-xs">WEATHER CLEAR</span>
            <span className="metric-num mono text-md font-bold text-safe">88% Compliance</span>
          </div>
        </div>
      </header>

      {/* Vessels Table */}
      <div className="fleet-table-wrap glass">
        <table className="fleet-table">
          <thead>
            <tr>
              <th>Vessel ID / Name</th>
              <th>Type</th>
              <th>Home Port</th>
              <th>Coordinates</th>
              <th>Operating Status</th>
              <th>Safety State</th>
              <th>AIS Relay</th>
            </tr>
          </thead>
          <tbody>
            {vessels.map((v) => {
              const isSafe = v.compliance.includes('SAFE');
              const isCaution = v.compliance.includes('CAUTION');
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
                  <td className="mono text-xs text-teal">{v.aisStatus}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

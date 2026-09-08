import React from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import './ActiveAlertsView.css';

interface ActiveAlertsViewProps {
  response?: UserResponseV1 | null;
  onSelectScenario: (scenarioId: string) => void;
}

export const ActiveAlertsView: React.FC<ActiveAlertsViewProps> = ({ response: _response, onSelectScenario }) => {
  const alerts = [
    {
      id: 'alert-cyclone-vizag',
      type: 'CYCLONE WARNING',
      severity: 'UNSAFE',
      region: 'Andhra Pradesh / North Bay of Bengal',
      headline: 'Severe Cyclonic Storm Warning — Port Warning Signal #8',
      details: 'Sustained winds 48 kts gusting 65 kts. Significant wave height 5.2 m. Total suspension of all artisanal and mechanized fishing.',
      authority: 'IMD Cyclone Warning Division & INCOIS',
      actionScenario: 'unsafe_cyclone',
      validUntil: '2026-09-09T18:00:00Z',
    },
    {
      id: 'alert-swell-kochi',
      type: 'HIGH SWELL / KALLAKKADAL',
      severity: 'CAUTION',
      region: 'Kerala Coast (Kochi to Vizhinjam)',
      headline: 'Swell Wave Alert 2.8m — Nearshore Surge',
      details: 'High period swell waves (14s) breaking near harbour mouths. Small craft advised to stay within 5 NM.',
      authority: 'INCOIS Coastal Hazard Warning Centre',
      actionScenario: 'caution_wave',
      validUntil: '2026-09-08T23:30:00Z',
    },
    {
      id: 'alert-mpa-malvan',
      type: 'REGULATORY RESTRICTION',
      severity: 'UNSAFE',
      region: 'Malvan Marine Sanctuary, Maharashtra',
      headline: 'Marine Protected Area Core Geofence Active',
      details: 'Total exclusion no-take zone under Wildlife Protection Act 1972. Fines and gear confiscation for incursions.',
      authority: 'Maharashtra Forest Dept / Coastal Police',
      actionScenario: 'geofence_restricted',
      validUntil: 'Permanent Statutory Notified Zone',
    },
    {
      id: 'alert-stale-telemetry',
      type: 'DEGRADED SENSOR WARNING',
      severity: 'UNKNOWN',
      region: 'Gujarat Coast / Saurashtra Sector',
      headline: 'Coastal Radar Packet Loss (>6h Data Age)',
      details: 'Weather observations stale. System clamps verdict to UNKNOWN to prevent reassuring false positives.',
      authority: 'VARUNA Telemetry Health Guard',
      actionScenario: 'weather_stale',
      validUntil: 'Until next buoy uplink sync',
    },
  ];

  return (
    <div className="active-alerts-view">
      <header className="alerts-header">
        <div>
          <div className="alerts-badge mono text-xs">COASTAL HAZARD BROADCAST</div>
          <h1 className="alerts-title text-display">Active Marine Alerts & Restrictions</h1>
          <p className="alerts-subtitle text-sm text-muted">
            Live emergency notices, INCOIS high wave bulletins, IMD cyclone warnings, and MPA boundary geofences.
          </p>
        </div>
      </header>

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
                <div>Authority: <span className="text-foam">{alert.authority}</span></div>
                <div>Validity: <span className="text-foam">{alert.validUntil}</span></div>
              </div>

              <button
                className="alert-inspect-btn"
                onClick={() => onSelectScenario(alert.actionScenario)}
              >
                Inspect on Map Canvas →
              </button>
            </article>
          );
        })}
      </div>
    </div>
  );
};

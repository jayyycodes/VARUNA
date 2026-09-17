import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { provenanceLogger } from '../utils/provenanceLogger';
import './DataProvenanceBadge.css';

/**
 * Dev-Only Data Provenance Badge & Inspector.
 * Adheres strictly to Phase 2:
 * - Surfaces source (live | fixture | cache), endpoint URL, query_run_id, HTTP status, and latency.
 * - Toggleable modal for deep inspection.
 * - Stripped / disabled in production builds (returns null if not DEV).
 * - Live badge bound to actual network request state, not a static prop.
 */
export const DataProvenanceBadge: React.FC = () => {
  // Strip completely in production builds
  if (!import.meta.env.DEV) {
    return null;
  }

  const { provenance, activeScenarioId } = useAppStore();
  const [modalOpen, setModalOpen] = useState(false);

  const isLive = provenance?.source === 'live';
  const isFixture = provenance?.source === 'fixture' || Boolean(activeScenarioId);

  const badgeClass = isLive
    ? 'data-provenance-badge--live'
    : isFixture
    ? 'data-provenance-badge--fixture'
    : 'data-provenance-badge--unknown';

  const label = isLive
    ? `Live API${provenance?.latencyMs ? ` • ${provenance.latencyMs.toFixed(0)}ms` : ''}`
    : isFixture
    ? 'Demo Mode'
    : 'Standby';

  const tooltipText = isLive
    ? `Live Ocean Telemetry (${provenance?.latencyMs ? `${provenance.latencyMs.toFixed(0)}ms` : 'Connected'}) - Click to inspect`
    : isFixture
    ? `Scenario: ${provenance?.fixtureName || activeScenarioId || 'mock'} - Click to inspect audit trail`
    : 'Standby - Click to inspect';

  const history = provenance?.query_run_id
    ? provenanceLogger.getHistory(provenance.query_run_id)
    : [];

  return (
    <div className="data-provenance-badge-container">
      <button
        type="button"
        className={`data-provenance-badge ${badgeClass}`}
        onClick={() => setModalOpen(true)}
        title={tooltipText}
      >
        <span className="data-provenance-pulse-dot" />
        <span>{label}</span>
      </button>

      {modalOpen && (
        <div
          className="data-provenance-modal-backdrop"
          onClick={() => setModalOpen(false)}
        >
          <div
            className="data-provenance-modal"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="provenance-title"
          >
            <div className="data-provenance-modal__header">
              <div id="provenance-title" className="data-provenance-modal__title">
                <span>Data Provenance Inspector</span>
                <span
                  style={{
                    fontSize: 10,
                    background: isLive ? '#059669' : '#D97706',
                    color: '#FFF',
                    padding: '1px 5px',
                    borderRadius: 3,
                  }}
                >
                  {isLive ? 'LIVE NETWORK' : 'MOCK FIXTURE'}
                </span>
              </div>
              <button
                type="button"
                className="data-provenance-modal__close-btn"
                onClick={() => setModalOpen(false)}
                aria-label="Close provenance inspector"
              >
                ✕
              </button>
            </div>

            <div className="data-provenance-modal__content">
              <div className="data-provenance-grid">
                <span className="data-provenance-label">Data Origin:</span>
                <span className="data-provenance-value" style={{ color: isLive ? '#34D399' : '#FBBF24', fontWeight: 'bold' }}>
                  {provenance?.source?.toUpperCase() || 'UNKNOWN'}
                </span>

                <span className="data-provenance-label">Endpoint URL:</span>
                <span className="data-provenance-value">{provenance?.endpoint || 'N/A'}</span>

                <span className="data-provenance-label">Query Run ID:</span>
                <span className="data-provenance-value">{provenance?.query_run_id || 'N/A'}</span>

                <span className="data-provenance-label">HTTP Status:</span>
                <span className="data-provenance-value">
                  {provenance?.httpStatus ? `${provenance.httpStatus} OK` : 'N/A'}
                </span>

                <span className="data-provenance-label">Round-Trip Latency:</span>
                <span className="data-provenance-value">
                  {provenance?.latencyMs ? `${provenance.latencyMs.toFixed(2)} ms` : 'N/A'}
                </span>

                <span className="data-provenance-label">Contract Validation:</span>
                <span
                  className="data-provenance-value"
                  style={{ color: provenance?.validationPassed ? '#34D399' : '#F87171' }}
                >
                  {provenance?.validationPassed ? '✓ PASSED (Zod UserResponseV1)' : '✗ FAILED SCHEMA'}
                </span>

                {provenance?.validationError && (
                  <>
                    <span className="data-provenance-label">Validation Error:</span>
                    <span className="data-provenance-value" style={{ color: '#F87171', fontSize: 11 }}>
                      {provenance.validationError}
                    </span>
                  </>
                )}

                <span className="data-provenance-label">Response Time:</span>
                <span className="data-provenance-value">
                  {provenance?.timestamp ? new Date(provenance.timestamp).toLocaleTimeString() : 'N/A'}
                </span>
              </div>

              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#94A3B8', marginBottom: 6, textTransform: 'uppercase' }}>
                  Structured Audit Trail ({provenance?.query_run_id || 'Current'})
                </div>
                <div className="data-provenance-history-box">
                  {history.length > 0 ? (
                    history.map((h, i) => (
                      <div key={i} className="data-provenance-history-item">
                        <span style={{ color: '#38BDF8' }}>[{h.stage}]</span>
                        <span style={{ color: '#64748B' }}>
                          {new Date(h.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div style={{ color: '#64748B', fontStyle: 'italic' }}>
                      No structured audit stages recorded for this query run ID yet.
                    </div>
                  )}
                </div>
              </div>

              <div style={{ fontSize: 10, color: '#64748B', textAlign: 'center' }}>
                VARUNA Security Policy: Credentials, auth headers, and backend stack traces are strictly filtered.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

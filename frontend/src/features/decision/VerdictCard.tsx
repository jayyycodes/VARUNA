import React from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { IconInfo, IconAlert } from '../../components/Icons';
import './VerdictCard.css';

interface VerdictCardProps {
  response?: UserResponseV1 | null;
  loading?: boolean;
  loadingMessage?: string;
  error?: string | null;
  onSelectReason?: (claimId: string, evidenceId?: string) => void;
  onRetry?: () => void;
}

export const VerdictCard: React.FC<VerdictCardProps> = ({
  response,
  loading = false,
  loadingMessage = 'Checking weather, marine conditions, and boundaries...',
  error = null,
  onSelectReason,
  onRetry,
}) => {
  // 1. Loading State
  if (loading) {
    return (
      <div
        className="verdict-card verdict-card--loading glass"
        role="status"
        aria-live="polite"
        aria-busy="true"
        aria-label="Evaluating marine safety conditions"
      >
        <div className="verdict-card__loading-header">
          <div className="verdict-card__pulse-spinner" />
          <span className="verdict-card__status-text text-sm mono">ANALYZING DOMAINS</span>
        </div>
        <p className="verdict-card__headline text-verdict">Assessing Maritime Risk...</p>
        <p className="verdict-card__action text-sm">{loadingMessage}</p>
        <div className="verdict-card__skeleton-bar" />
      </div>
    );
  }

  // 2. Error State
  if (error) {
    return (
      <div
        className="verdict-card verdict-card--error glass"
        role="alert"
        aria-live="assertive"
        data-verdict="UNKNOWN"
      >
        <div className="verdict-card__status">
          <span className="verdict-card__badge verdict-card__badge--unknown">SYSTEM ERROR</span>
        </div>
        <p className="verdict-card__headline text-verdict">Unable to Complete Assessment</p>
        <p className="verdict-card__action text-sm">{error}</p>
        {onRetry && (
          <button className="verdict-card__retry-btn" onClick={onRetry}>
            Retry Assessment
          </button>
        )}
      </div>
    );
  }

  // 3. Idle State (No query yet)
  if (!response) {
    return (
      <div
        className="verdict-card glass"
        role="status"
        aria-label="Safety verdict standby"
        aria-live="polite"
      >
        <div className="verdict-card__status">
          <div className="verdict-card__indicator verdict-card__indicator--idle" />
          <span className="verdict-card__label text-sm">System Ready</span>
        </div>
        <p className="verdict-card__headline text-verdict">Coastal Marine Intelligence</p>
        <p className="verdict-card__action text-sm">
          Select a coastal scenario or enter coordinates to evaluate weather, wave swell, and regulatory compliance.
        </p>
      </div>
    );
  }

  const { summary, decision_status, claims, degradation } = response;
  const verdict = summary.verdict;
  const isDegraded = decision_status === 'degraded' || decision_status === 'indeterminate';

  // Extract top 1-3 actionable claims for fast tapping
  const headlineClaims = claims.slice(0, 3);

  return (
    <div
      className={`verdict-card glass verdict-card--${verdict.toLowerCase()}`}
      role="region"
      aria-label={`Safety verdict: ${verdict}`}
      data-verdict={verdict}
      data-status={decision_status}
    >
      {/* 1. Hero Verdict Section */}
      <div className="verdict-card__hero-header">
        <div className="verdict-card__hero-left">
          <span
            className={`verdict-hero-icon verdict-hero-icon--${verdict.toLowerCase()}`}
            aria-hidden="true"
          >
            {verdict === 'SAFE' && '●'}
            {verdict === 'CAUTION' && '▲'}
            {verdict === 'UNSAFE' && '■'}
            {verdict === 'UNKNOWN' && '◇'}
          </span>
          <h1 className="verdict-card__hero-verdict">{verdict}</h1>
        </div>

        <div className="verdict-card__hero-meta">
          <span className="verdict-card__confidence-pill mono text-xs">
            CONFIDENCE: <span className="confidence-value">{summary.confidence_band.toUpperCase()}</span>
          </span>
          {isDegraded && (
            <span
              className="verdict-card__degraded-tag mono text-xs"
              title="Telemetry partially degraded"
            >
              {decision_status.toUpperCase()}
            </span>
          )}
        </div>
      </div>

      {/* 2. Headline Summary */}
      <p className="verdict-card__headline-sub text-sm">{summary.headline}</p>

      {/* 3. Operational Action / Directive Box */}
      <div className="verdict-card__action-box">
        <div className="verdict-card__action-label mono text-xs">DIRECTIVE</div>
        <p className="verdict-card__action text-sm">{summary.action}</p>
      </div>

      {/* 4. Confidence Explanation */}
      {summary.confidence_reason && (
        <div className="verdict-card__confidence-reason text-xs">
          <span className="verdict-card__reason-bullet">
            <IconInfo size={12} />
          </span>{' '}
          {summary.confidence_reason}
        </div>
      )}

      {/* 5. Tappable Headline Reasons (Linked directly to Rule Traces / Evidence) */}
      {headlineClaims.length > 0 && (
        <div className="verdict-card__reasons-section">
          <div className="verdict-card__reasons-label mono text-xs">KEY FACTORS (TAP TO INSPECT)</div>
          <div className="verdict-card__reasons-list">
            {headlineClaims.map((claim) => (
              <button
                key={claim.id}
                className="verdict-card__reason-chip"
                onClick={() => onSelectReason?.(claim.id, claim.evidence_ids[0])}
                title="View evidentiary rule trace in Evidence Panel"
              >
                <span className="verdict-card__reason-kind mono text-xs">
                  {claim.kind.replace('_', ' ').toUpperCase()}
                </span>
                <span className="verdict-card__reason-text text-xs">{claim.text}</span>
                <span className="verdict-card__reason-arrow">→</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 6. Degradation Notice Warning if active */}
      {degradation && degradation.is_degraded && (
        <div className="verdict-card__degradation-alert" role="note">
          <span className="degradation-icon">
            <IconAlert size={14} color="#F59E0B" />
          </span>
          <div className="degradation-content text-xs">
            <strong>Degraded Mode:</strong> {degradation.reason}
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState } from 'react';
import type {
  UserResponseV1,
  RuleTraceItem,
  DataFreshnessItem,
  MissingInputItem,
  Citation,
} from '../../contracts/userResponse';
import {
  IconShield,
  IconCheck,
  IconCross,
  IconAlert,
  IconExternalLink,
} from '../../components/Icons';
import { useLocalization } from '../../hooks/useLocalization';
import './EvidencePanelContent.css';

interface EvidencePanelContentProps {
  response?: UserResponseV1 | null;
  selectedEvidenceId?: string | null;
  selectedClaimId?: string | null;
  onSelectFeature?: (featureId: string) => void;
}

export const EvidencePanelContent: React.FC<EvidencePanelContentProps> = ({
  response,
  selectedEvidenceId,
  selectedClaimId: _selectedClaimId,
}) => {
  const [activeTab, setActiveTab] = useState<'rules' | 'freshness' | 'citations'>('rules');
  const { t } = useLocalization();

  if (!response) {
    return (
      <div className="evidence-empty-state">
        <div className="evidence-empty-icon">
          <IconShield size={36} color="#94A3B8" />
        </div>
        <p className="text-sm">{t('emptyEvidence')}</p>
      </div>
    );
  }

  const { evidence_panel, citations, claims, decision_status } = response;
  const { rule_trace, data_freshness, missing_inputs } = evidence_panel;

  const passedCount = rule_trace.filter((r) => r.passed).length;
  const failedCount = rule_trace.length - passedCount;
  const passPercentage = rule_trace.length > 0 ? Math.round((passedCount / rule_trace.length) * 100) : 100;

  // Check if any claim is unverified / insufficient evidence
  const unverifiedClaims = claims.filter(
    (c) => c.kind === 'regulation' && (!c.citation_ids || c.citation_ids.length === 0)
  );

  return (
    <div className="evidence-panel-inner">
      {/* Modern Statistic Donut Card (Matching Reference UI) */}
      <div className="evidence-donut-card">
        <div className="donut-card-header">
          <span className="donut-card-title">Safety Metric ⓘ</span>
          <span className="donut-card-period text-xs mono">Real-Time Evaluation</span>
        </div>
        <div className="donut-card-body">
          <div className="donut-chart-container">
            <svg className="donut-chart-svg" viewBox="0 0 100 100">
              <circle className="donut-ring-bg" cx="50" cy="50" r="38" />
              <circle
                className="donut-ring-progress"
                cx="50"
                cy="50"
                r="38"
                strokeDasharray={`${(passedCount / Math.max(rule_trace.length, 1)) * 238.76} 238.76`}
              />
            </svg>
            <div className="donut-chart-center">
              <span className="donut-center-label text-xs">Passed</span>
              <span className="donut-center-val mono">{passPercentage}%</span>
            </div>
          </div>
          <div className="donut-legend">
            <div className="donut-legend-item">
              <span className="donut-legend-dot donut-legend-dot--safe" />
              <span className="text-xs">{t('passed')}: {passedCount}</span>
            </div>
            <div className="donut-legend-item">
              <span className="donut-legend-dot donut-legend-dot--unsafe" />
              <span className="text-xs">{t('breach')}: {failedCount}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 1. Tab Navigation */}
      <nav className="evidence-nav" aria-label="Evidence categories">
        <button
          className={`evidence-nav__btn ${activeTab === 'rules' ? 'evidence-nav__btn--active' : ''}`}
          onClick={() => setActiveTab('rules')}
        >
          {t('rulesAndChecks')}
          {rule_trace.length > 0 && <span className="evidence-nav__badge">{rule_trace.length}</span>}
        </button>

        <button
          className={`evidence-nav__btn ${activeTab === 'freshness' ? 'evidence-nav__btn--active' : ''}`}
          onClick={() => setActiveTab('freshness')}
        >
          {t('freshness')}
          {data_freshness.length > 0 && <span className="evidence-nav__badge">{data_freshness.length}</span>}
        </button>

        <button
          className={`evidence-nav__btn ${activeTab === 'citations' ? 'evidence-nav__btn--active' : ''}`}
          onClick={() => setActiveTab('citations')}
        >
          {t('citations')}
          {citations.length > 0 && <span className="evidence-nav__badge">{citations.length}</span>}
        </button>
      </nav>

      <div className="evidence-scroll-area">
        {/* ==================== TAB 1: RULES & TRACES ==================== */}
        {activeTab === 'rules' && (
          <div className="evidence-section">
            <div className="evidence-section__header">
              <span className="mono text-xs text-muted">{t('deterministicEngine')}</span>
            </div>

            {rule_trace.length === 0 ? (
              <div className="evidence-note text-xs">
                {decision_status === 'indeterminate'
                  ? t('noRuleTracesIndeterminate')
                  : t('noRuleTraces')}
              </div>
            ) : (
              <div className="rule-trace-list">
                {rule_trace.map((item: RuleTraceItem) => {
                  const isHighlighted = selectedEvidenceId === item.id;
                  const isPassed = item.passed;
                  const severityClass = `rule-card--${item.severity || (isPassed ? 'safe' : 'unsafe')}`;

                  return (
                    <article
                      key={item.id}
                      id={`rule-${item.id}`}
                      className={`rule-card ${severityClass} ${isHighlighted ? 'rule-card--highlight' : ''}`}
                    >
                      <div className="rule-card__top">
                        <span className="rule-card__domain mono text-xs">{item.domain.toUpperCase()}</span>
                        <span
                          className={`rule-card__badge rule-card__badge--${isPassed ? 'pass' : 'fail'}`}
                        >
                          {isPassed ? (
                            <>
                              <IconCheck size={11} color="#FFFFFF" /> {t('passed')}
                            </>
                          ) : (
                            <>
                              <IconCross size={11} color="#FFFFFF" /> {t('breach')}
                            </>
                          )}
                        </span>
                      </div>

                      <h4 className="rule-card__title text-sm">{item.rule_name}</h4>

                      {/* Tabular Value Comparison */}
                      <div className="rule-card__table-wrapper">
                        <table className="rule-card__table">
                          <thead>
                            <tr>
                              <th>{t('measured')}</th>
                              <th>{t('op')}</th>
                              <th>{t('threshold')}</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <td className="mono tabular-nums text-sm font-bold">
                                {String(item.measured_value)} {item.unit}
                              </td>
                              <td className="mono text-muted text-center">{item.comparator}</td>
                              <td className="mono tabular-nums text-sm">
                                {String(item.threshold_value)} {item.unit}
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>

                      <p className="rule-card__explanation text-xs">{item.explanation}</p>

                      <div className="rule-card__footer mono text-xs text-muted">
                        <span>{t('rule')}: {item.rule_id}</span>
                        <span>{t('version')}: {item.threshold_version}</span>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}

            {/* Missing Inputs Disclosure */}
            {missing_inputs.length > 0 && (
              <div className="missing-inputs-box">
                <div className="missing-inputs-header">
                  <span className="missing-inputs-badge mono text-xs">
                    <IconAlert size={12} color="#FFFFFF" /> {t('missingInputs')} ({missing_inputs.length})
                  </span>
                </div>
                <div className="missing-inputs-list">
                  {missing_inputs.map((m: MissingInputItem, idx: number) => (
                    <div key={idx} className="missing-input-row text-xs">
                      <div className="missing-param font-bold mono">{m.parameter}</div>
                      <div className="missing-impact text-muted">{m.impact}</div>
                      {m.fallback_used && (
                        <div className="missing-fallback text-xs">{t('fallback')}: {m.fallback_used}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ==================== TAB 2: DATA FRESHNESS ==================== */}
        {activeTab === 'freshness' && (
          <div className="evidence-section">
            <div className="evidence-section__header">
              <span className="mono text-xs text-muted">{t('telemetrySources')}</span>
            </div>

            <div className="freshness-list">
              {data_freshness.map((item: DataFreshnessItem, idx: number) => {
                const status = item.status;
                const statusColor =
                  status === 'fresh'
                    ? 'status-pill--fresh'
                    : status === 'stale'
                    ? 'status-pill--stale'
                    : status === 'missing'
                    ? 'status-pill--missing'
                    : 'status-pill--unknown';

                return (
                  <div key={idx} className="freshness-card">
                    <div className="freshness-card__header">
                      <span className="freshness-source-name font-bold text-sm">{item.source_name}</span>
                      <span className={`status-pill ${statusColor} mono text-xs`}>
                        {status.toUpperCase()} ({item.age_minutes}m)
                      </span>
                    </div>

                    <div className="freshness-card__domain mono text-xs text-muted">
                      {t('domain')}: {item.domain}
                    </div>

                    <div className="freshness-card__timestamps mono text-xs">
                      <div>{t('observed')}: {new Date(item.observed_at).toLocaleTimeString()}</div>
                      <div>{t('retrieved')}: {new Date(item.retrieved_at).toLocaleTimeString()}</div>
                      {item.valid_to && <div>{t('validTo')}: {new Date(item.valid_to).toLocaleTimeString()}</div>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ==================== TAB 3: STATUTORY CITATIONS (RAG) ==================== */}
        {activeTab === 'citations' && (
          <div className="evidence-section">
            <div className="evidence-section__header">
              <span className="mono text-xs text-muted">{t('legalCitations')}</span>
            </div>

            {/* Unverified / Insufficient Evidence Fallback */}
            {unverifiedClaims.length > 0 && (
              <div className="unverified-citation-banner" role="alert">
                <div className="unverified-header">
                  <span className="unverified-tag mono text-xs">{t('notVerified')}</span>
                  <span className="text-xs text-muted">{t('ragGroundingGuard')}</span>
                </div>
                <p className="unverified-copy text-sm font-bold">
                  {t('unverifiedCopy')}
                </p>
                <p className="text-xs text-muted">
                  {t('unverifiedExplain')}
                </p>
              </div>
            )}

            {citations.length === 0 && unverifiedClaims.length === 0 ? (
              <div className="evidence-note text-xs">
                {t('noCitations')}
              </div>
            ) : (
              <div className="citations-list">
                {citations.map((c: Citation) => (
                  <article key={c.id} className="citation-card">
                    <div className="citation-card__publisher mono text-xs">{c.publisher.toUpperCase()}</div>
                    <h4 className="citation-card__title text-sm">{c.title}</h4>

                    {/* Excerpt with Source-Language vs Response-Language Differentiation */}
                    <div className="citation-card__excerpt-box">
                      {c.source_language && c.source_language !== 'en-IN' && (
                        <span className="lang-tag mono text-xs">
                          {t('original')} [{c.source_language.toUpperCase()}]
                        </span>
                      )}
                      <blockquote className="citation-excerpt text-xs font-italic">
                        "{c.excerpt}"
                      </blockquote>
                    </div>

                    <div className="citation-card__footer">
                      <span className="mono text-xs text-muted">
                        {t('published')}: {new Date(c.published_at).toLocaleDateString()}
                      </span>
                      {c.url && (
                        <a
                          href={c.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="citation-link text-xs mono"
                        >
                          {t('sourceDoc')} <IconExternalLink size={11} />
                        </a>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

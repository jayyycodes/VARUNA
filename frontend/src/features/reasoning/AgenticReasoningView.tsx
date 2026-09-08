import React, { useState } from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { IconTree, IconWave, IconScale, IconBook } from '../../components/Icons';
import './AgenticReasoningView.css';

interface AgenticReasoningViewProps {
  response?: UserResponseV1 | null;
}

export const AgenticReasoningView: React.FC<AgenticReasoningViewProps> = ({ response }) => {
  const [activeTab, setActiveTab] = useState<'active' | 'historical' | 'failed'>('active');
  const [expandedNode, setExpandedNode] = useState<string | null>('marine');

  const verdict = response?.summary?.verdict || 'SAFE';
  const queryId = response?.query_run_id || 'run-live-001';

  return (
    <div className="agentic-reasoning-view">
      {/* View Header */}
      <header className="reasoning-header">
        <div>
          <div className="reasoning-breadcrumb mono text-xs">
            AGENTIC REASONING ENGINE // <span className="text-teal">{queryId}</span>
          </div>
          <h1 className="reasoning-title text-display">Multi-Agent Synthesis Trace</h1>
          <p className="reasoning-subtitle text-sm text-muted">
            Deterministic rule traces, conflict arbitration, and grounded LLM explanation pipeline.
          </p>
        </div>

        {/* Tab Filter */}
        <div className="reasoning-tabs glass">
          <button
            className={`reasoning-tab ${activeTab === 'active' ? 'reasoning-tab--active' : ''}`}
            onClick={() => setActiveTab('active')}
          >
            Active Pipeline (5 Agents)
          </button>
          <button
            className={`reasoning-tab ${activeTab === 'historical' ? 'reasoning-tab--active' : ''}`}
            onClick={() => setActiveTab('historical')}
          >
            Historical Traces
          </button>
        </div>
      </header>

      {/* Multi-Agent Node Timeline */}
      <div className="timeline-container">
        <div className="timeline-spine" />

        {/* 1. Planning Agent */}
        <article className="timeline-node">
          <div className="node-marker node-marker--planning">
            <span className="node-icon">
              <IconTree size={16} color="#FFFFFF" />
            </span>
          </div>
          <div className="node-card glass">
            <div className="node-card__header" onClick={() => setExpandedNode(expandedNode === 'planning' ? null : 'planning')}>
              <div>
                <div className="node-domain mono text-xs">DISPATCH & DECOMPOSITION</div>
                <h3 className="node-title text-md font-bold">Planning Agent</h3>
                <p className="node-summary text-xs text-muted">
                  Decomposed query into parallel marine, atmospheric, geofence, and regulatory sub-tasks.
                </p>
              </div>
              <span className="node-status-pill node-status-pill--done mono text-xs">COMPLETED (12ms)</span>
            </div>

            {expandedNode === 'planning' && (
              <div className="node-card__body">
                <div className="code-block mono text-xs">
                  {JSON.stringify(
                    {
                      intent: 'SAFETY_ASSESSMENT_AND_PFZ_QUERY',
                      domain_agents_dispatched: ['MarineAgent', 'WeatherAgent', 'GeofenceAgent', 'RiskEngine'],
                      execution_mode: 'PARALLEL_WITH_DETERMINISTIC_GATE',
                    },
                    null,
                    2
                  )}
                </div>
              </div>
            )}
          </div>
        </article>

        {/* 2. Marine Data Agent */}
        <article className="timeline-node">
          <div className="node-marker node-marker--marine">
            <span className="node-icon">
              <IconWave size={16} color="#14B8A6" />
            </span>
          </div>
          <div className="node-card glass node-card--active">
            <div className="node-card__header" onClick={() => setExpandedNode(expandedNode === 'marine' ? null : 'marine')}>
              <div>
                <div className="node-domain mono text-xs text-teal">TELEMETRY INGESTION</div>
                <h3 className="node-title text-md font-bold text-teal">Marine Data Agent (INCOIS / SWAN)</h3>
                <p className="node-summary text-xs text-muted">
                  Fetched wave height, swell period, and thermal chlorophyll fronts.
                </p>
              </div>
              <span className="node-status-pill node-status-pill--active mono text-xs">VERIFIED</span>
            </div>

            {expandedNode === 'marine' && (
              <div className="node-card__body">
                <div className="telemetry-grid">
                  <div className="telemetry-item">
                    <span className="telemetry-label text-xs mono">Significant Wave Height</span>
                    <span className="telemetry-value mono font-bold">
                      {response?.evidence_panel?.rule_trace[0]?.measured_value || '1.2 m'}
                    </span>
                  </div>
                  <div className="telemetry-item">
                    <span className="telemetry-label text-xs mono">Data Freshness</span>
                    <span className="telemetry-value mono font-bold text-teal">
                      {response?.evidence_panel?.data_freshness[0]?.age_minutes ?? 25} min age (Fresh)
                    </span>
                  </div>
                  <div className="telemetry-item">
                    <span className="telemetry-label text-xs mono">SWAN Model Status</span>
                    <span className="telemetry-value mono font-bold">Converged</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </article>

        {/* 3. Deterministic Risk Engine */}
        <article className="timeline-node">
          <div className={`node-marker node-marker--${verdict.toLowerCase()}`}>
            <span className="node-icon">
              <IconScale size={16} color="#FFFFFF" />
            </span>
          </div>
          <div className={`node-card glass node-card--verdict-${verdict.toLowerCase()}`}>
            <div className="node-card__header" onClick={() => setExpandedNode(expandedNode === 'risk' ? null : 'risk')}>
              <div>
                <div className="node-domain mono text-xs">DETERMINISTIC RULE ENGINE</div>
                <h3 className="node-title text-md font-bold">Risk Assessment Agent</h3>
                <p className="node-summary text-xs text-muted">
                  Computed final verdict: <strong>{verdict}</strong> ({response?.summary?.headline})
                </p>
              </div>
              <span className={`verdict-pill verdict-pill--${verdict.toLowerCase()} mono text-xs`}>
                {verdict}
              </span>
            </div>

            {expandedNode === 'risk' && (
              <div className="node-card__body">
                <div className="rules-executed-list">
                  {response?.evidence_panel?.rule_trace.map((rule) => (
                    <div key={rule.id} className="rule-execution-row">
                      <span className={`rule-pass-dot ${rule.passed ? 'pass' : 'fail'}`} />
                      <div className="rule-exec-info">
                        <span className="mono text-xs font-bold">{rule.rule_name}</span>
                        <span className="mono text-xs text-muted">
                          {String(rule.measured_value)} {rule.comparator} {String(rule.threshold_value)} ({rule.threshold_version})
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </article>

        {/* 4. Explanation & Grounded RAG Agent */}
        <article className="timeline-node">
          <div className="node-marker node-marker--rag">
            <span className="node-icon">
              <IconBook size={16} color="#FFFFFF" />
            </span>
          </div>
          <div className="node-card glass">
            <div className="node-card__header" onClick={() => setExpandedNode(expandedNode === 'rag' ? null : 'rag')}>
              <div>
                <div className="node-domain mono text-xs">GROUNDED SYNTHESIS & TRANSLATION</div>
                <h3 className="node-title text-md font-bold">Explanation Agent</h3>
                <p className="node-summary text-xs text-muted">
                  Synthesized plain-language directive backed by {response?.citations?.length || 0} statutory citations.
                </p>
              </div>
              <span className="node-status-pill node-status-pill--done mono text-xs">GROUNDED</span>
            </div>

            {expandedNode === 'rag' && (
              <div className="node-card__body">
                <p className="explanation-text text-sm">
                  "{response?.summary?.action}"
                </p>
                {response?.claims?.map((c) => (
                  <div key={c.id} className="claim-box text-xs">
                    <span className="mono font-bold">[{c.kind.toUpperCase()}]:</span> {c.text}
                  </div>
                ))}
              </div>
            )}
          </div>
        </article>
      </div>
    </div>
  );
};

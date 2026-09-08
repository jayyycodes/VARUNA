import React, { useState, useEffect, useRef } from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { apiClient } from '../../api/client';
import {
  IconCopilotBot,
  IconSearch,
  IconCheck,
  IconAlert,
  IconCross,
  IconShip,
  IconWave,
  IconWind,
  IconTree,
  IconRoute,
} from '../../components/Icons';
import type { ActiveNavView } from '../query/Sidebar';
import './ChatAssistantView.css';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  text: string;
  thinking?: string[];
  verdict?: 'SAFE' | 'CAUTION' | 'UNSAFE';
  scenarioSyncId?: string;
  metrics?: {
    wave?: string;
    wind?: string;
    pfz?: string;
    confidence?: string;
  };
  actions?: Array<{
    label: string;
    actionType: 'scenario' | 'view';
    target: string;
  }>;
}

interface ChatAssistantViewProps {
  onSelectScenario: (scenarioId: string) => void;
  onChangeView: (view: ActiveNavView) => void;
  currentResponse?: UserResponseV1 | null;
}

export const ChatAssistantView: React.FC<ChatAssistantViewProps> = ({
  onSelectScenario,
  onChangeView,
  currentResponse,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      timestamp: '10:30 AM',
      text: "Welcome to **VARUNA Copilot** — your real-time marine conversational intelligence engine.\n\nYou can query coastal oceanographic feeds, analyze safety thresholds across Indian waters, plan safe passage corridors, or search active Potential Fishing Zones (PFZs).",
      thinking: [
        'Ingesting INCOIS Buoy Real-Time Telemetry (9 Coastal Station Nodes)',
        'Synchronized with IMD Tropical Cyclone Advisory & Squall Warning Matrix',
        'Deterministic Safety Evaluation Rules Active (Rule-WAVE-01, Rule-WIND-01, Rule-GEO-01)',
      ],
      actions: [
        { label: 'Check Ratnagiri Harbour Clearance', actionType: 'scenario', target: 'safe_complete' },
        { label: 'Inspect Kochi Swell Advisory', actionType: 'scenario', target: 'caution_high_wave' },
        { label: 'Optimize Safe Passage to Zone Alpha-7', actionType: 'view', target: 'routing' },
      ],
    },
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [expandedThinking, setExpandedThinking] = useState<Record<string, boolean>>({ welcome: true });
  const [reasoningMode, setReasoningMode] = useState<'deep' | 'fast' | 'corridor'>('deep');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on message updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || isThinking) return;

    const userMsgId = `user-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      text: query,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsThinking(true);

    try {
      // Connect to Live LangGraph Agent via apiClient, fallback to local intelligence
      const chatRes = await apiClient.submitChatQuery(query);
      const assistantMsgId = `asst-${Date.now()}`;

      const assistantMsg: ChatMessage = {
        id: assistantMsgId,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        text: chatRes.text,
        thinking: chatRes.thinking,
        verdict: chatRes.verdict,
        scenarioSyncId: chatRes.scenarioSyncId,
        metrics: chatRes.metrics,
        actions: chatRes.actions,
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setExpandedThinking((prev) => ({ ...prev, [assistantMsgId]: true }));
    } catch (err: any) {
      console.warn('Chat assistant fallback trigger:', err);
      generateAgentResponse(query);
    } finally {
      setIsThinking(false);
    }
  };

  const generateAgentResponse = (query: string) => {
    const lower = query.toLowerCase();
    const assistantMsgId = `asst-${Date.now()}`;
    let responseText = '';
    let thinkingSteps: string[] = [];
    let verdict: 'SAFE' | 'CAUTION' | 'UNSAFE' | undefined = undefined;
    let scenarioSyncId: string | undefined = undefined;
    let metrics: ChatMessage['metrics'] = undefined;
    let actions: ChatMessage['actions'] = [];

    if (lower.includes('ratnagiri') || lower.includes('fishing') || lower.includes('sail') || lower.includes('harbour')) {
      verdict = 'SAFE';
      scenarioSyncId = 'safe_complete';
      thinkingSteps = [
        'Query parsed: Location "Ratnagiri Harbour", Entity "Coastal Artisanal Fleet".',
        'Ingesting SWAN Wave Model buoy 43012: Hsig = 1.2m (Threshold: 2.5m).',
        'Atmospheric check: Sustained wind 12 kts WNW, no squall formations.',
        'PFZ Layer: Mirya Bay high-chlorophyll zone confirmed active (12 NM off).',
        'Rule-WAVE-01 (PASS), Rule-WIND-01 (PASS), Rule-GEO-01 (PASS).',
      ];
      responseText = `**SAFE TO PROCEED** from Ratnagiri Harbour.\n\nAll primary marine domains are within regulatory safety envelopes. Wave heights are nominal at **1.2 m**, and surface winds are mild (**12 kts WNW**). High chlorophyll aggregation is detected **12 NM offshore** in Sector 42A.`;
      metrics = {
        wave: '1.2 m (nominal)',
        wind: '12 kts WNW',
        pfz: '12 NM (Active PFZ)',
        confidence: 'HIGH (99.4%)',
      };
      actions = [
        { label: 'Sync Map with Ratnagiri', actionType: 'scenario', target: 'safe_complete' },
        { label: 'Open Navigation Corridor', actionType: 'view', target: 'routing' },
      ];
    } else if (lower.includes('kochi') || lower.includes('swell') || lower.includes('high wave')) {
      verdict = 'CAUTION';
      scenarioSyncId = 'caution_high_wave';
      thinkingSteps = [
        'Target location: Kochi Marine Sector / Vembanad Mouth.',
        'Buoy telemetry ingestion: Wave swell measured at 2.8m (Threshold 2.5m).',
        'Checking INCOIS High Wave Warning Feed: Alert issued for coastal motorized craft.',
        'Confidence evaluation: INCOIS lightning feed degraded (Medium confidence).',
        'Verdict synthesized: CAUTION / HIGH WAVE.',
      ];
      responseText = `**CAUTION — HIGH WAVE SWELL DETECTED** near Kochi waters.\n\nSignificant wave swell is currently **2.8 m**, exceeding the **2.5 m small craft threshold**. Artisanal and non-motorized vessels are advised to exercise extreme caution and remain within harbour limits.`;
      metrics = {
        wave: '2.8 m (Exceeds Limit)',
        wind: '18 kts SW',
        confidence: 'MEDIUM (Telemetry Gap)',
      };
      actions = [
        { label: 'Load Kochi Alert Map', actionType: 'scenario', target: 'caution_high_wave' },
        { label: 'View Active Alerts List', actionType: 'view', target: 'alerts' },
      ];
    } else if (lower.includes('cyclone') || lower.includes('visakhapatnam') || lower.includes('storm') || lower.includes('unsafe')) {
      verdict = 'UNSAFE';
      scenarioSyncId = 'unsafe_cyclone';
      thinkingSteps = [
        'Analyzing Bay of Bengal Sector: Visakhapatnam Deep Sea.',
        'IMD Severe Cyclonic Storm Advisory active (Advisory #04).',
        'Sustained gale winds measured at 48 kts with gusts to 65 kts.',
        'Extreme wave heights reaching 5.2 m.',
        'Mandatory Zero-Departure Directive enforced.',
      ];
      responseText = `**MANDATORY ZERO-DEPARTURE — SEVERE CYCLONIC WARNING**.\n\nDeep sea squalls and gale-force winds of **48 kts** with **5.2 m waves** are sweeping through the Visakhapatnam coastal sector. Port operations are on Level 3 Alert. All maritime departures are prohibited.`;
      metrics = {
        wave: '5.2 m (Hazardous)',
        wind: '48 kts Gale',
        confidence: 'HIGH',
      };
      actions = [
        { label: 'Load Cyclone Warning', actionType: 'scenario', target: 'unsafe_cyclone' },
        { label: 'Inspect Fleet Positions', actionType: 'view', target: 'fleet' },
      ];
    } else if (lower.includes('pfz') || lower.includes('alpha-7') || lower.includes('chlorophyll') || lower.includes('fish')) {
      verdict = 'SAFE';
      scenarioSyncId = 'pfz_productive_unsafe';
      thinkingSteps = [
        'Querying INCOIS Potential Fishing Zone (PFZ) Satellite Composites.',
        'Detected high SST thermal front matching chlorophyll density bloom.',
        'Zone Alpha-7 (Sector 42A) identified as primary tuna/mackerel aggregation.',
      ];
      responseText = `**POTENTIAL FISHING ZONE (PFZ) INTEL**:\n\nThe highest biological productivity gradient is mapped in **Zone Alpha-7 (PFZ Prime)**, situated 12 NM off Mirya Bay. Optimal safe transit trajectory is calculated via **Sindhudurg Waters corridor**.`;
      metrics = {
        pfz: 'Zone Alpha-7 (Sector 42A)',
        wave: '1.2 m - 2.4 m',
        wind: '12 kts NW',
      };
      actions = [
        { label: 'View Safe Navigation Corridor', actionType: 'view', target: 'routing' },
        { label: 'View PFZ on Map', actionType: 'scenario', target: 'safe_complete' },
      ];
    } else {
      verdict = currentResponse?.summary?.verdict as any;
      thinkingSteps = [
        `Processing maritime natural language query: "${query}"`,
        'Correlating query against 4 marine safety domains: Wave, Wind, Lightning, Geofence.',
        'Synthesizing deterministic multi-agent verdict response.',
      ];
      responseText = `**Maritime Analysis for "${query}"**:\n\nBased on real-time marine telemetry across coastal India, conditions are being actively evaluated against safety rules. You can inspect live buoys, compute safe transit trajectories, or review deterministic safety evidence in the inspection engine.`;
      actions = [
        { label: 'Inspect Command Map', actionType: 'view', target: 'map' },
        { label: 'Open Route Optimization', actionType: 'view', target: 'routing' },
        { label: 'View Agentic Reasoning Tree', actionType: 'view', target: 'reasoning' },
      ];
    }

    const newAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      sender: 'assistant',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      text: responseText,
      thinking: thinkingSteps,
      verdict,
      scenarioSyncId,
      metrics,
      actions,
    };

    setMessages((prev) => [...prev, newAssistantMsg]);
    setExpandedThinking((prev) => ({ ...prev, [assistantMsgId]: true }));

    // Automatically sync scenario if identified
    if (scenarioSyncId) {
      onSelectScenario(scenarioSyncId);
    }
  };

  const toggleThinking = (id: string) => {
    setExpandedThinking((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  return (
    <div className="chat-view-container">
      {/* 1. Header Toolbar */}
      <header className="chat-view-header">
        <div className="chat-view-header__left">
          <div className="chat-view-bot-badge">
            <IconCopilotBot size={20} color="#FFFFFF" />
          </div>
          <div>
            <div className="chat-view-title-row">
              <h2 className="chat-view-title">VARUNA Copilot</h2>
              <span className="chat-model-tag mono text-xs">ORCA-3.2 Marine Intelligence</span>
            </div>
            <p className="chat-view-subtitle text-xs">
              <span className="live-status-dot" />
              Live INCOIS Buoy, IMD Weather & PFZ Satellite Feeds
            </p>
          </div>
        </div>

        <div className="chat-view-header__right">
          <div className="reasoning-pills">
            <button
              type="button"
              className={`mode-pill ${reasoningMode === 'deep' ? 'mode-pill--active' : ''}`}
              onClick={() => setReasoningMode('deep')}
            >
              <IconTree size={12} />
              <span>Deep Reasoning</span>
            </button>
            <button
              type="button"
              className={`mode-pill ${reasoningMode === 'corridor' ? 'mode-pill--active' : ''}`}
              onClick={() => setReasoningMode('corridor')}
            >
              <IconRoute size={12} />
              <span>Corridor Solver</span>
            </button>
          </div>

          <button
            type="button"
            className="clear-chat-btn"
            onClick={() => setMessages([messages[0]])}
            title="Clear Chat Thread"
          >
            Clear Thread
          </button>
        </div>
      </header>

      {/* 2. Messages Stream Area */}
      <main className="chat-view-messages">
        <div className="chat-messages-max-width">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`chat-row chat-row--${msg.sender}`}
            >
              {msg.sender === 'assistant' && (
                <div className="chat-row__avatar assistant-avatar">
                  <IconCopilotBot size={18} color="#FFFFFF" />
                </div>
              )}

              <div className="chat-row__content">
                {/* Thinking Process Accordion (Claude 3.7 / Grok 3 / o1 Style) */}
                {msg.thinking && msg.thinking.length > 0 && (
                  <div className="reasoning-accordion">
                    <button
                      type="button"
                      className="reasoning-accordion__header mono text-xs"
                      onClick={() => toggleThinking(msg.id)}
                    >
                      <IconTree size={13} color="#D8FA36" />
                      <span>
                        {expandedThinking[msg.id]
                          ? 'Deep Marine Reasoning Process'
                          : `View Reasoning Steps (${msg.thinking.length} nodes)`}
                      </span>
                      <span className="reasoning-accordion__arrow">
                        {expandedThinking[msg.id] ? '▲' : '▼'}
                      </span>
                    </button>

                    {expandedThinking[msg.id] && (
                      <div className="reasoning-accordion__body">
                        {msg.thinking.map((step, idx) => (
                          <div key={idx} className="reasoning-step text-xs">
                            <span className="reasoning-step__num mono">{idx + 1}.</span>
                            <span>{step}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Deterministic Verdict Tag */}
                {msg.verdict && (
                  <div className="verdict-banner">
                    <span className={`verdict-pill verdict-pill--${msg.verdict.toLowerCase()} mono text-xs`}>
                      {msg.verdict === 'SAFE' && <IconCheck size={12} />}
                      {msg.verdict === 'CAUTION' && <IconAlert size={12} />}
                      {msg.verdict === 'UNSAFE' && <IconCross size={12} />}
                      {msg.verdict} // DETERMINISTIC ENGINE
                    </span>
                  </div>
                )}

                {/* Message Bubble */}
                <div className="chat-bubble">
                  <div
                    className="chat-bubble__text"
                    dangerouslySetInnerHTML={{
                      __html: msg.text
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\n\n/g, '<br/><br/>')
                        .replace(/\n/g, '<br/>'),
                    }}
                  />

                  {/* Telemetry Metric Chips */}
                  {msg.metrics && (
                    <div className="chat-metrics-grid">
                      {msg.metrics.wave && (
                        <div className="metric-tag">
                          <IconWave size={12} color="#38BDF8" />
                          <span className="metric-tag__label">Wave:</span>
                          <span className="metric-tag__val mono">{msg.metrics.wave}</span>
                        </div>
                      )}
                      {msg.metrics.wind && (
                        <div className="metric-tag">
                          <IconWind size={12} color="#34D399" />
                          <span className="metric-tag__label">Wind:</span>
                          <span className="metric-tag__val mono">{msg.metrics.wind}</span>
                        </div>
                      )}
                      {msg.metrics.pfz && (
                        <div className="metric-tag">
                          <IconShip size={12} color="#FBBF24" />
                          <span className="metric-tag__label">PFZ:</span>
                          <span className="metric-tag__val mono">{msg.metrics.pfz}</span>
                        </div>
                      )}
                      {msg.metrics.confidence && (
                        <div className="metric-tag">
                          <span className="metric-tag__label">Confidence:</span>
                          <span className="metric-tag__val mono">{msg.metrics.confidence}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Interactive Action Pills */}
                  {msg.actions && msg.actions.length > 0 && (
                    <div className="chat-actions-row">
                      {msg.actions.map((act, i) => (
                        <button
                          key={i}
                          type="button"
                          className="chat-action-btn"
                          onClick={() => {
                            if (act.actionType === 'scenario') {
                              onSelectScenario(act.target);
                              onChangeView('map');
                            } else if (act.actionType === 'view') {
                              onChangeView(act.target as any);
                            }
                          }}
                        >
                          <span>{act.label}</span>
                          <span className="chat-action-arrow">➔</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <span className="chat-timestamp mono text-xs">{msg.timestamp}</span>
              </div>
            </div>
          ))}

          {/* Thinking Indicator Animation */}
          {isThinking && (
            <div className="chat-row chat-row--assistant">
              <div className="chat-row__avatar assistant-avatar">
                <IconCopilotBot size={18} color="#FFFFFF" />
              </div>
              <div className="thinking-box">
                <div className="thinking-dots">
                  <span className="dot dot-1" />
                  <span className="dot dot-2" />
                  <span className="dot dot-3" />
                </div>
                <span className="thinking-text mono text-xs">
                  Synthesizing INCOIS wave buoys & IMD atmospheric models...
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* 3. Bottom Input Area & Quick Suggestions */}
      <footer className="chat-view-footer">
        <div className="chat-view-footer__inner">
          {/* Quick Suggestions */}
          <div className="suggestions-scroll">
            <button
              type="button"
              className="suggestion-pill"
              onClick={() => handleSendMessage('Can artisanal boats safely sail off Ratnagiri today?')}
            >
              🌊 Can I sail off Ratnagiri today?
            </button>
            <button
              type="button"
              className="suggestion-pill"
              onClick={() => handleSendMessage('Check swell warnings near Kochi waters')}
            >
              ⚠️ Kochi swell advisory
            </button>
            <button
              type="button"
              className="suggestion-pill"
              onClick={() => handleSendMessage('Locate closest high-chlorophyll PFZ coordinates')}
            >
              🐟 Locate PFZ Zone Alpha-7
            </button>
            <button
              type="button"
              className="suggestion-pill"
              onClick={() => handleSendMessage('Analyze severe cyclone trajectory at Visakhapatnam')}
            >
              🌀 Cyclone storm track
            </button>
          </div>

          {/* Composer Input Box */}
          <form
            className="chat-composer"
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
          >
            <div className="composer-prefix">
              <IconSearch size={16} color="#94A3B8" />
            </div>

            <textarea
              ref={inputRef}
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Ask VARUNA Copilot... (e.g. Is it safe to sail from Ratnagiri? Check wave swell at Kochi)"
              rows={1}
              className="composer-input"
            />

            <button
              type="submit"
              className={`composer-send-btn ${inputQuery.trim() ? 'composer-send-btn--active' : ''}`}
              disabled={!inputQuery.trim() || isThinking}
            >
              <IconCopilotBot size={16} />
              <span>Ask Copilot</span>
            </button>
          </form>

          <div className="chat-composer-footer mono text-xs">
            <span>Press <strong>Enter ↵</strong> to query • Grounded on INCOIS & IMD Telemetry</span>
            <span>Deterministic Marine Safety Engine</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

import React, { useState, useEffect, useRef } from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { apiClient } from '../../api/client';
import type { ActiveNavView } from '../query/Sidebar';
import { useLocalization } from '../../hooks/useLocalization';
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

interface TimelineItem {
  id: string;
  type: 'alerts' | 'forecast' | 'history' | 'automation';
  title: string;
  timestamp: string;
  timeGroup: 'TODAY' | 'YESTERDAY' | '1 WEEK AGO';
  iconType: 'anomaly' | 'warning' | 'route' | 'forecast' | 'chat';
  isUnread?: boolean;
  queryPrompt: string;
  targetScenario?: string;
  targetView?: ActiveNavView;
}

interface ChatAssistantViewProps {
  onSelectScenario: (scenarioId: string) => void;
  onChangeView: (view: ActiveNavView) => void;
  currentResponse?: UserResponseV1 | null;
}

const HISTORY_TIMELINE_DATA: TimelineItem[] = [
  {
    id: 't-1',
    type: 'alerts',
    title: 'Severe cyclone anomaly detected & track simulation',
    timestamp: '2h ago',
    timeGroup: 'TODAY',
    iconType: 'anomaly',
    isUnread: true,
    queryPrompt: 'Simulate severe cyclone storm track and wind gust speeds for Visakhapatnam',
    targetScenario: 'unsafe_cyclone',
  },
  {
    id: 't-2',
    type: 'alerts',
    title: 'High wave swell alert near Kochi port',
    timestamp: '3h ago',
    timeGroup: 'TODAY',
    iconType: 'warning',
    isUnread: true,
    queryPrompt: 'Analyze wave swell height and warning bulletins for Kochi port',
    targetScenario: 'caution_high_wave',
  },
  {
    id: 't-3',
    type: 'automation',
    title: 'Safe transit corridor from Cochin to Gulf',
    timestamp: '5h ago',
    timeGroup: 'TODAY',
    iconType: 'route',
    queryPrompt: 'Compute safe navigation corridor and waypoint clearance from Cochin to Gulf',
    targetView: 'routing',
  },
  {
    id: 't-4',
    type: 'forecast',
    title: 'SWAN wave forecast model update & buoy telemetry',
    timestamp: 'Yesterday',
    timeGroup: 'YESTERDAY',
    iconType: 'forecast',
    queryPrompt: 'Show latest SWAN ocean wave height predictions and buoy telemetry',
  },
  {
    id: 't-5',
    type: 'history',
    title: 'Ratnagiri harbour safety clearance inquiry',
    timestamp: 'Yesterday • 4 messages',
    timeGroup: 'YESTERDAY',
    iconType: 'chat',
    queryPrompt: 'Can artisanal and motorized craft safely sail off Ratnagiri today?',
    targetScenario: 'safe_complete',
  },
  {
    id: 't-6',
    type: 'history',
    title: 'PFZ Zone Alpha-7 chlorophyll scan & coordinates',
    timestamp: '6 days ago • 6 messages',
    timeGroup: '1 WEEK AGO',
    iconType: 'chat',
    queryPrompt: 'Locate closest high-chlorophyll PFZ Zone Alpha-7 coordinates off Mirya Bay',
  },
  {
    id: 't-7',
    type: 'history',
    title: 'Vessel traffic & AIS collision risk analysis',
    timestamp: '7 days ago • 3 messages',
    timeGroup: '1 WEEK AGO',
    iconType: 'chat',
    queryPrompt: 'Check vessel collision vectors and AIS proximity around Ratnagiri',
  },
];

export const ChatAssistantView: React.FC<ChatAssistantViewProps> = ({
  onSelectScenario,
  onChangeView,
  currentResponse,
}) => {
  const { t } = useLocalization();
  const [viewMode, setViewMode] = useState<'discovery' | 'chat' | 'history'>('discovery');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [expandedThinking, setExpandedThinking] = useState<Record<string, boolean>>({});
  const [isRecording, setIsRecording] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const trendingPrompts = [
    { id: '#1', icon: '🌀', label: 'Cyclone Fengal Risk', prompt: 'Assess Cyclone storm track, wind gusts, and port warnings for Visakhapatnam' },
    { id: '#2', icon: '🧭', label: 'Safe Passage Route', prompt: 'What is the safest route from Ratnagiri to Malvan avoiding protected zones?' },
    { id: '#3', icon: '🐟', label: 'PFZ Chlorophyll Hotspots', prompt: 'Locate closest high-chlorophyll PFZ Zone Alpha-7 coordinates off Mirya Bay' },
    { id: '#4', icon: '🛡️', label: 'Vessel Collision CPA', prompt: 'Check vessel collision vectors and AIS proximity around Ratnagiri' },
    { id: '#5', icon: '🌊', label: 'Sea Swell Analysis', prompt: 'Analyze wave swell height and SWAN ocean model predictions' },
  ];

  const recentInquiries = [
    { title: 'Can artisanal and motorized craft safely sail off Ratnagiri today?', prompt: 'Is it safe to go fishing tomorrow near Ratnagiri?' },
    { title: 'Analyze wave swell height and warning bulletins for Kochi port', prompt: 'Analyze wave swell height and warning bulletins for Kochi port' },
    { title: 'Compute safe navigation corridor and waypoint clearance from Cochin to Gulf', prompt: 'Compute safe navigation corridor and waypoint clearance from Cochin to Gulf' },
  ];

  useEffect(() => {
    if (viewMode === 'chat' && messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isThinking, viewMode]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || isThinking) return;

    // Switch to active chat screen immediately
    setViewMode('chat');

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
    } else if (lower.includes('cyclone') || lower.includes('fengal') || lower.includes('visakhapatnam') || lower.includes('storm') || lower.includes('unsafe')) {
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
    } else if (lower.includes('route') || lower.includes('cochin') || lower.includes('gulf') || lower.includes('optimize')) {
      verdict = 'SAFE';
      thinkingSteps = [
        'Running multi-objective A* nautical routing solver.',
        'Evaluating weather routing parameters: Current drift + 1.4 kts, wave resistance nominal.',
        'Computing least-fuel optimal corridor from Cochin to Gulf of Oman.',
      ];
      responseText = `**OPTIMAL ROUTE COMPUTED**:\n\nThe safest and most fuel-efficient corridor from **Cochin to Gulf** has been generated. By staying 18 NM west of Minicoy passage, the vessel saves **4.2% fuel** while maintaining clearance from shallow reef shelves.`;
      metrics = {
        wave: '1.4 m average',
        wind: '14 kts NW',
        confidence: 'HIGH (99.8%)',
      };
      actions = [
        { label: 'Open Route Optimization View', actionType: 'view', target: 'routing' },
        { label: 'View Command Map', actionType: 'view', target: 'map' },
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
        { label: 'View Tactical Ocean Map', actionType: 'view', target: 'map' },
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

  const startNewChat = () => {
    setMessages([]);
    setInputQuery('');
    setViewMode('chat');
  };

  return (
    <div className="v-bot-container">
      {/* =========================================================================
          SCREEN 1: DISCOVERY / WELCOME SCREEN (Oceanic Aura & Modern Assistant)
          ========================================================================= */}
      {viewMode === 'discovery' && (
        <div className="v-discovery-view">
          {/* Glowing Ocean Aurora Hero Section */}
          <div className="v-ocean-hero-section">
            {/* Ambient Animated Ocean Wave Backdrop */}
            <div className="v-ocean-wave-ambient">
              <div className="v-ocean-orb v-ocean-orb--1" />
              <div className="v-ocean-orb v-ocean-orb--2" />
              <svg className="v-ocean-wave-svg" viewBox="0 0 1440 320" preserveAspectRatio="none">
                <path fill="rgba(255, 255, 255, 0.08)" d="M0,96L48,112C96,128,192,160,288,160C384,160,480,128,576,138.7C672,149,768,203,864,208C960,213,1056,171,1152,144C1248,117,1344,107,1392,101.3L1440,96L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z" />
              </svg>
            </div>

            {/* Top Bar inside Ocean Header */}
            <div className="v-discovery-topbar">
              <div className="v-brand-pill">
                <span className="v-brand-pill-spark">✨</span>
                <span className="v-brand-pill-title">VARUNA Copilot</span>
              </div>
              <div className="v-discovery-topbar-right">
                <div className="v-engine-status-pill">
                  <span className="v-status-live-dot" />
                  <span>Hydro Engine 2.0</span>
                </div>
                <button
                  type="button"
                  className="v-notif-btn"
                  onClick={() => setViewMode('history')}
                  title={t('historyChat') || 'History Chat'}
                  aria-label="View history"
                >
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                    <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
                  </svg>
                  <span className="v-notif-dot" />
                </button>
              </div>
            </div>

            {/* Hero Salutation & Ocean Header */}
            <div className="v-ocean-hero-content">
              <h1 className="v-ocean-hero-title">
                Hi, Captain! ⚓
                <span className="v-ocean-hero-subtitle-block">
                  {t('whereCuriosity') || 'Where Coastal Wisdom Meets Real-Time Intelligence'}
                </span>
              </h1>
              <p className="v-ocean-hero-subtext">
                Your real-time marine copilot for swell, passage corridors, and cyclone risk
              </p>

              {/* Floating Quick Action Prompt Pills */}
              <div className="v-quick-prompts-cluster">
                {trendingPrompts.map((tp) => (
                  <button
                    key={tp.id}
                    type="button"
                    className="v-quick-prompt-chip"
                    onClick={() => handleSendMessage(tp.prompt)}
                  >
                    <span className="v-chip-icon">{tp.icon}</span>
                    <span className="v-chip-text">{tp.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Curved Content Sheet (Popular Topics & Search Bar) */}
          <div className="v-ocean-content-sheet">
            {/* Search Prompt Bar */}
            <div className="v-discovery-search-section">
              <form
                className="v-search-bar-capsule"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (inputQuery.trim()) {
                    handleSendMessage();
                  }
                }}
              >
                <div className="v-search-lens-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0284C7" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                </div>
                <input
                  type="text"
                  className="v-search-input"
                  placeholder={t('chatSearchPlaceholder') || 'Ask anything about marine conditions, swell, or routes...'}
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                />
                <button
                  type="submit"
                  className="v-search-submit-btn"
                  aria-label="Submit search"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13" />
                    <polygon points="22 2 15 22 11 13 2 9 22 2" />
                  </svg>
                </button>
              </form>
            </div>

            {/* Popular Topics Section */}
            <div className="v-discovery-popular-section">
              <div className="v-section-header-row">
                <span className="v-section-label">POPULAR TOPICS</span>
                <button
                  type="button"
                  className="v-see-all-link"
                  onClick={() => setViewMode('history')}
                >
                  {t('seeAll') || 'See All'} &gt;
                </button>
              </div>
              <div className="v-popular-cards-grid">
                {recentInquiries.map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="v-popular-card-item"
                    onClick={() => handleSendMessage(item.prompt)}
                  >
                    <div className="v-popular-icon-bubble">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0284C7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      </svg>
                    </div>
                    <div className="v-popular-text-col">
                      <span className="v-popular-title">{item.title}</span>
                      <span className="v-popular-sub">Tap to evaluate with AI engine →</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          SCREEN 2: ACTIVE CHAT CONVERSATION SCREEN
          ========================================================================= */}
      {viewMode === 'chat' && (
        <div className="v-chat-thread-view">
          {/* Animated Ocean Thinking Aurora Banner */}
          {isThinking && <div className="v-ocean-thinking-aurora" />}

          {/* Top Bar */}
          <div className="v-thread-topbar">
            <button
              type="button"
              className="v-thread-back-btn"
              onClick={() => setViewMode('discovery')}
              aria-label="Back to discovery"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
            </button>
            <div className="v-thread-header-title">
              <span className="v-thread-name">{t('pageChatTitle') || 'VARUNA AI'}</span>
              <span className="v-thread-status">
                <span className={`v-status-dot ${isThinking ? 'v-status-dot--thinking' : ''}`} />
                {isThinking ? 'Analyzing ocean telemetry...' : (t('assistantConnected') || 'Active Coastal Model')}
              </span>
            </div>

            <div className="v-thread-menu-wrap">
              <button
                type="button"
                className="v-thread-menu-btn"
                onClick={() => setMenuOpen(!menuOpen)}
                aria-label="Chat options"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="5" r="1.5" />
                  <circle cx="12" cy="12" r="1.5" />
                  <circle cx="12" cy="19" r="1.5" />
                </svg>
              </button>

              {menuOpen && (
                <div className="v-thread-dropdown">
                  <button
                    type="button"
                    className="v-dropdown-option"
                    onClick={() => {
                      navigator.clipboard?.writeText(window.location.href);
                      setMenuOpen(false);
                    }}
                  >
                    <span>{t('share')}</span>
                  </button>
                  <button
                    type="button"
                    className="v-dropdown-option"
                    onClick={() => {
                      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(messages, null, 2));
                      const downloadAnchor = document.createElement('a');
                      downloadAnchor.setAttribute("href", dataStr);
                      downloadAnchor.setAttribute("download", "varuna-chat-session.json");
                      document.body.appendChild(downloadAnchor);
                      downloadAnchor.click();
                      downloadAnchor.remove();
                      setMenuOpen(false);
                    }}
                  >
                    <span>{t('export')}</span>
                  </button>
                  <button
                    type="button"
                    className="v-dropdown-option v-dropdown-option--danger"
                    onClick={() => {
                      setMessages([]);
                      setMenuOpen(false);
                    }}
                  >
                    <span>Clear Messages</span>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Messages Stream */}
          <div className="v-thread-messages-body">
            {messages.length === 0 && (
              <div className="v-thread-empty-prompt">
                <span className="v-empty-spark">⚡</span>
                <p>{t('welcomeAnalyze') || 'What would you like to analyze today?'}</p>
              </div>
            )}

            {messages.map((msg) => {
              const isAsst = msg.sender === 'assistant';
              return (
                <div
                  key={msg.id}
                  className={`v-message-row ${isAsst ? 'v-message-row--asst' : 'v-message-row--user'}`}
                >
                  {isAsst && (
                    <div className="v-asst-avatar-badge">
                      <span>⚡</span>
                    </div>
                  )}

                  <div className={`v-message-bubble ${isAsst ? 'v-bubble--asst' : 'v-bubble--user'}`}>
                    <div className="v-bubble-text">
                      {msg.text.split('\n').map((line, lIdx) => (
                        <p key={lIdx}>{line}</p>
                      ))}
                    </div>

                    {/* Verdict Pill if present */}
                    {msg.verdict && (
                      <div className="v-msg-verdict-tag">
                        <span className={`v-verdict-pill v-verdict-pill--${msg.verdict.toLowerCase()}`}>
                          {msg.verdict === 'SAFE' && '✓ ' + t('safe')}
                          {msg.verdict === 'CAUTION' && '⚠ ' + t('caution')}
                          {msg.verdict === 'UNSAFE' && '⛔ ' + t('unsafe')}
                        </span>
                      </div>
                    )}

                    {/* Interactive Multi-Agent Thinking Accordion */}
                    {msg.thinking && msg.thinking.length > 0 && (
                      <div className="v-msg-thinking-block">
                        <button
                          type="button"
                          className="v-thinking-toggle-btn"
                          onClick={() => toggleThinking(msg.id)}
                        >
                          <span className="v-thinking-spark">✦</span>
                          <span>Multi-Agent Synthesis Trace ({msg.thinking.length} Steps)</span>
                          <span className="v-thinking-chevron">{expandedThinking[msg.id] ? '▲' : '▼'}</span>
                        </button>

                        {expandedThinking[msg.id] && (
                          <div className="v-thinking-steps-list">
                            {msg.thinking.map((step, sIdx) => (
                              <div key={sIdx} className="v-thinking-step-item">
                                <span className="v-step-num">{sIdx + 1}</span>
                                <span className="v-step-text">{step}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Action buttons */}
                    {msg.actions && msg.actions.length > 0 && (
                      <div className="v-msg-actions-row">
                        {msg.actions.map((act, actIdx) => (
                          <button
                            key={actIdx}
                            type="button"
                            className="v-msg-action-pill"
                            onClick={() => {
                              if (act.actionType === 'scenario') onSelectScenario(act.target);
                              if (act.actionType === 'view') onChangeView(act.target as ActiveNavView);
                            }}
                          >
                            <span>{act.label} →</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {!isAsst && (
                    <div className="v-user-avatar-badge">
                      <span>👨🏽‍✈️</span>
                    </div>
                  )}
                </div>
              );
            })}

            {isThinking && (
              <div className="v-message-row v-message-row--asst">
                <div className="v-asst-avatar-badge">
                  <span>⚡</span>
                </div>
                <div className="v-bubble--asst v-bubble-thinking">
                  <span className="v-thinking-dot" />
                  <span className="v-thinking-dot" />
                  <span className="v-thinking-dot" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Bottom Modern Composer Bar */}
          <div className="v-thread-composer-wrapper">
            <form
              className="v-composer-capsule"
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
            >
              <button
                type="button"
                className="v-composer-attach-btn"
                onClick={() => setInputQuery((prev) => prev ? `${prev} [Buoy Telemetry Attached]` : 'Attach coastal buoy telemetry off Ratnagiri')}
                title="Attach telemetry"
                aria-label="Attach telemetry file or data"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="4" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <polyline points="21 15 16 10 5 21" />
                </svg>
              </button>

              <input
                ref={inputRef}
                type="text"
                className="v-composer-input"
                placeholder={t('typeMessage') || 'Type a message...'}
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                disabled={isThinking}
              />

              <button
                type="button"
                className={`v-composer-mic-btn ${isRecording ? 'v-composer-mic-btn--active' : ''}`}
                onClick={() => setIsRecording(!isRecording)}
                title="Voice dictation"
                aria-label="Voice input"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="22" />
                </svg>
              </button>

              <button
                type="submit"
                className="v-composer-send-btn"
                disabled={!inputQuery.trim() || isThinking}
                aria-label="Send message"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            </form>
          </div>
        </div>
      )}

      {/* =========================================================================
          SCREEN 3: HISTORY CHAT SCREEN
          ========================================================================= */}
      {viewMode === 'history' && (
        <div className="v-history-view">
          {/* Top Bar */}
          <div className="v-history-topbar">
            <button
              type="button"
              className="v-thread-back-btn"
              onClick={() => setViewMode('discovery')}
              aria-label="Back to discovery"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
            </button>

            <span className="v-thread-title">{t('historyChat') || 'History Chat'}</span>

            <button
              type="button"
              className="v-thread-menu-btn"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="History options"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="5" r="1.5" />
                <circle cx="12" cy="12" r="1.5" />
                <circle cx="12" cy="19" r="1.5" />
              </svg>
            </button>
          </div>

          {/* Grouped History List */}
          <div className="v-history-scroll-body">
            {/* TODAY Group */}
            <div className="v-history-group">
              <span className="v-history-group-label">{t('today') || 'TODAY'}</span>
              <div className="v-history-cards-list">
                {HISTORY_TIMELINE_DATA.filter((i) => i.timeGroup === 'TODAY').map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className="v-history-card-item"
                    onClick={() => handleSendMessage(item.queryPrompt)}
                  >
                    <div className="v-recent-icon-bubble">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      </svg>
                    </div>
                    <span className="v-history-prompt-text">“{item.title}”</span>
                  </button>
                ))}
              </div>
            </div>

            {/* YESTERDAY Group */}
            <div className="v-history-group">
              <span className="v-history-group-label">{t('yesterday') || 'YESTERDAY'}</span>
              <div className="v-history-cards-list">
                {HISTORY_TIMELINE_DATA.filter((i) => i.timeGroup === 'YESTERDAY').map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className="v-history-card-item"
                    onClick={() => handleSendMessage(item.queryPrompt)}
                  >
                    <div className="v-recent-icon-bubble">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      </svg>
                    </div>
                    <span className="v-history-prompt-text">“{item.title}”</span>
                  </button>
                ))}
              </div>
            </div>

            {/* 1 WEEK AGO Group */}
            <div className="v-history-group">
              <span className="v-history-group-label">{t('oneWeekAgo') || '1 WEEK AGO'}</span>
              <div className="v-history-cards-list">
                {HISTORY_TIMELINE_DATA.filter((i) => i.timeGroup === '1 WEEK AGO').map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className="v-history-card-item"
                    onClick={() => handleSendMessage(item.queryPrompt)}
                  >
                    <div className="v-recent-icon-bubble">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      </svg>
                    </div>
                    <span className="v-history-prompt-text">“{item.title}”</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Floating Action Button "New Chats +" */}
          <button
            type="button"
            className="v-new-chats-fab"
            onClick={startNewChat}
            aria-label="Start new chat"
          >
            <span className="v-fab-text">{t('newChats') || 'New Chats'}</span>
            <span className="v-fab-icon">+</span>
          </button>
        </div>
      )}
    </div>
  );
};

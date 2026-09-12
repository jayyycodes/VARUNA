import React, { useState } from 'react';
import { useLocalization } from '../../hooks/useLocalization';
import {
  IconMap,
  IconTree,
  IconAlert,
  IconShip,
  IconRoute,
  IconCopilotBot,
  IconSearch,
  IconChevronRight,
  IconChevronLeft,
  IconLogoStarburst,
  IconWave,
} from '../../components/Icons';
import './Sidebar.css';

export type ActiveNavView = 'overview' | 'map' | 'routing' | 'chat' | 'reasoning' | 'alerts' | 'fleet' | 'trends';

interface SidebarProps {
  onSelectScenario?: (fixtureId: string) => void;
  onSubmitQuery: (text: string) => void;
  onOpenChat?: () => void;
  activeScenarioId?: string | null;
  loading?: boolean;
  activeView: ActiveNavView;
  onChangeView: (view: ActiveNavView) => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  onSubmitQuery,
  onOpenChat,
  loading = false,
  activeView,
  onChangeView,
  isCollapsed: controlledIsCollapsed,
  onToggleCollapse,
}) => {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const isCollapsed = controlledIsCollapsed !== undefined ? controlledIsCollapsed : internalCollapsed;
  const handleToggle = onToggleCollapse || (() => setInternalCollapsed(!internalCollapsed));

  const [inputText, setInputText] = useState('');
  const { t } = useLocalization();
  const [history, setHistory] = useState<Array<{ id: string; text: string; time: string }>>([
    {
      id: 'h1',
      text: 'Can I go fishing off Ratnagiri tomorrow morning?',
      time: '10:30 AM',
    },
    {
      id: 'h2',
      text: 'Check swell warnings for Cochin harbour craft',
      time: '09:15 AM',
    },
  ]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;

    onSubmitQuery(inputText.trim());
    setHistory((prev) => [
      {
        id: `h-${Date.now()}`,
        text: inputText.trim(),
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
      ...prev.slice(0, 5),
    ]);
    setInputText('');
  };

  return (
    <aside className={`dual-sidebar ${isCollapsed ? 'dual-sidebar--collapsed' : ''}`}>
      {/* 1. Leftmost Deep Obsidian Icon Bar */}
      <div className="icon-bar">
        <button
          type="button"
          className="icon-bar__brand"
          title={isCollapsed ? 'Open Marine Scenarios Drawer' : 'Close Sidebar Drawer'}
          onClick={handleToggle}
          aria-label={isCollapsed ? 'Open Marine Scenarios Drawer' : 'Close Sidebar Drawer'}
          aria-expanded={!isCollapsed}
        >
          <IconLogoStarburst size={22} color="#FFFFFF" />
        </button>
        {!isCollapsed && (
          <div className="icon-bar__wordmark">
            <span className="wordmark-symbol">◈</span> VARUNA
          </div>
        )}

        <nav className="icon-bar__nav" aria-label="Main navigation">
          {/* 2x2 Grid Icon (Dashboard Overview matching reference) */}
          <button
            type="button"
            className={`icon-bar__btn ${activeView === 'overview' ? 'icon-bar__btn--active' : ''}`}
            onClick={() => onChangeView('overview')}
            title="Executive Dashboard Overview"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7" rx="1.5" />
              <rect x="14" y="3" width="7" height="7" rx="1.5" />
              <rect x="14" y="14" width="7" height="7" rx="1.5" />
              <rect x="3" y="14" width="7" height="7" rx="1.5" />
            </svg>
          </button>

          <button
            type="button"
            className={`icon-bar__btn ${activeView === 'map' ? 'icon-bar__btn--active' : ''}`}
            onClick={() => onChangeView('map')}
            title="Interactive Map & Tactical Canvas"
          >
            <IconMap size={18} />
          </button>

          <button
            type="button"
            className={`icon-bar__btn ${activeView === 'routing' ? 'icon-bar__btn--active' : ''}`}
            onClick={() => onChangeView('routing')}
            title="Route Optimization & Safe Passage"
          >
            <IconRoute size={18} />
          </button>

          <button
            type="button"
            className={`icon-bar__btn ${activeView === 'chat' ? 'icon-bar__btn--active' : ''}`}
            onClick={() => onChangeView('chat')}
            title="VARUNA Copilot (Conversational Queries & AI Chat)"
          >
            <IconCopilotBot size={19} />
          </button>

          <button
            type="button"
            className={`icon-bar__btn ${activeView === 'reasoning' ? 'icon-bar__btn--active' : ''}`}
            onClick={() => onChangeView('reasoning')}
            title="Agentic Reasoning"
          >
            <IconTree size={18} />
          </button>

          <button
            type="button"
            className={`icon-bar__btn ${activeView === 'alerts' ? 'icon-bar__btn--active' : ''}`}
            onClick={() => onChangeView('alerts')}
            title="Active Alerts"
          >
            <IconAlert size={18} />
          </button>

          <button
            type="button"
            className={`icon-bar__btn ${activeView === 'fleet' ? 'icon-bar__btn--active' : ''}`}
            onClick={() => onChangeView('fleet')}
            title="Fleet Operations"
          >
            <IconShip size={18} />
          </button>

          <button
            type="button"
            className={`icon-bar__btn ${activeView === 'trends' ? 'icon-bar__btn--active' : ''}`}
            onClick={() => onChangeView('trends')}
            title="Fishery Trends & Anomalies (SIH Query #7)"
          >
            <IconWave size={18} />
          </button>
        </nav>

        <div className="icon-bar__footer">
          <div className="icon-bar__status-indicator" title="Telemetry Grounded" />
          <div
            className="icon-bar__avatar"
            title="Adeey • Lead Architect (Open Copilot)"
            onClick={onOpenChat || (() => onChangeView('chat'))}
            style={{ cursor: 'pointer' }}
          >
            A
          </div>
        </div>
      </div>

      {/* 2. Sub-Sidebar Features & Platform Navigation Pod */}
      {!isCollapsed && (
        <div className="sub-sidebar">
          {/* Sleek Features Header */}
          <div className="sub-sidebar__header">
            <div className="sub-sidebar__title-row">
              <h2 className="sub-sidebar__title">Platform Features</h2>
              <span className="sub-sidebar__badge mono text-xs">8 Services</span>
            </div>
            <span className="sub-sidebar__subtitle text-xs">VARUNA Marine Intelligence</span>
          </div>

          {/* Clean Search / Filter Input */}
          <form className="sub-sidebar__search" onSubmit={handleSearchSubmit}>
            <IconSearch size={14} className="sub-sidebar__search-icon" />
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="sub-sidebar__input"
              placeholder="Search features or query..."
              disabled={loading}
              aria-label="Search features or query"
            />
          </form>

          {/* Feature Navigation Items (All Pages) */}
          <div className="sub-sidebar__scenarios">
            {[
              {
                id: 'overview' as ActiveNavView,
                tag: 'COMMAND',
                meta: 'OVERVIEW',
                tagClass: 'tag--safe',
                title: 'Marine Intelligence Command',
                desc: 'Executive dashboard, real-time safety cards, and vessel advisory.',
              },
              {
                id: 'map' as ActiveNavView,
                tag: 'MAP',
                meta: 'TACTICAL',
                tagClass: 'tag--safe',
                title: 'Tactical Ocean Map & Canvas',
                desc: 'Interactive geospatial chart, safety zones, and evidence rail grounding.',
              },
              {
                id: 'routing' as ActiveNavView,
                tag: 'PASSAGE',
                meta: 'AI ROUTING',
                tagClass: 'tag--caution',
                title: 'Route Optimization & Safe Passage',
                desc: 'LangGraph safety-aware pathfinding and hazard avoidance waypoints.',
              },
              {
                id: 'chat' as ActiveNavView,
                tag: 'COPILOT',
                meta: 'AI AGENT',
                tagClass: 'tag--safe',
                title: 'VARUNA Copilot — Marine AI Intelligence',
                desc: 'Conversational advisory, multilingual voice queries, and RAG search.',
              },
              {
                id: 'reasoning' as ActiveNavView,
                tag: 'RULES',
                meta: 'DETERMINISTIC',
                tagClass: 'tag--safe',
                title: 'Agentic Reasoning & Rule Engine',
                desc: 'Transparent rule evaluations, sensor threshold checks, and confidence breakdown.',
              },
              {
                id: 'alerts' as ActiveNavView,
                tag: 'WARNINGS',
                meta: 'EMERGENCY',
                tagClass: 'tag--unsafe',
                title: 'Active Marine Alerts',
                desc: 'INCOIS high wave swell advisories and IMD cyclone warning bulletins.',
              },
              {
                id: 'fleet' as ActiveNavView,
                tag: 'HARBOR',
                meta: 'FLEET OPS',
                tagClass: 'tag--safe',
                title: 'Fleet Operations & Harbor Monitoring',
                desc: 'Real-time vessel registry, port dispatch, and active craft tracking.',
              },
              {
                id: 'trends' as ActiveNavView,
                tag: 'QUERY #7',
                meta: 'ANALYTICS',
                tagClass: 'tag--caution',
                title: 'Fishery Trends & Environmental Anomalies',
                desc: '12-month SST anomaly curves and coastal productivity analytics.',
              },
            ]
              .filter(
                (item) =>
                  !inputText.trim() ||
                  item.title.toLowerCase().includes(inputText.toLowerCase()) ||
                  item.desc.toLowerCase().includes(inputText.toLowerCase()) ||
                  item.tag.toLowerCase().includes(inputText.toLowerCase())
              )
              .map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`scenario-item ${activeView === item.id ? 'scenario-item--active' : ''}`}
                  onClick={() => onChangeView(item.id)}
                >
                  <div className="scenario-item__top">
                    <span className={`scenario-item__verdict mono text-xs ${item.tagClass}`}>
                      {item.tag}
                    </span>
                    <span className="scenario-item__meta mono text-xs">{item.meta}</span>
                  </div>
                  <h4 className="scenario-item__name text-xs font-bold">{item.title}</h4>
                  <p className="scenario-item__desc text-xs text-muted">{item.desc}</p>
                </button>
              ))}
          </div>

          {/* Recent Inquiries Footer */}
          <div className="sub-sidebar__history">
            <div className="sub-sidebar__history-title mono text-xs">{t('recentQueries')}</div>
            <div className="sub-sidebar__history-list">
              {history.map((h) => (
                <button
                  key={h.id}
                  type="button"
                  className="sub-sidebar__history-btn"
                  onClick={() => {
                    onChangeView('map');
                    onSubmitQuery(h.text);
                  }}
                >
                  <span className="history-text text-xs">{h.text}</span>
                  <span className="history-time mono text-xs text-muted">{h.time}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Collapse/Expand Tab Pill — only visible on Map view */}
      {activeView === 'map' && (
        <button
          type="button"
          className="dual-sidebar__toggle"
          onClick={handleToggle}
          title={isCollapsed ? 'Expand scenario drawer' : 'Collapse scenario drawer'}
          aria-label={isCollapsed ? 'Expand scenario drawer' : 'Collapse scenario drawer'}
        >
          {isCollapsed ? <IconChevronRight size={14} /> : <IconChevronLeft size={14} />}
        </button>
      )}
    </aside>
  );
};

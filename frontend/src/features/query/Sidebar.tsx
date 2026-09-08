import React, { useState } from 'react';
import { FIXTURES } from '../../fixtures';
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
} from '../../components/Icons';
import './Sidebar.css';

export type ActiveNavView = 'map' | 'routing' | 'chat' | 'reasoning' | 'alerts' | 'fleet';

interface SidebarProps {
  onSelectScenario: (fixtureId: string) => void;
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
  onSelectScenario,
  onSubmitQuery,
  onOpenChat,
  activeScenarioId,
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

  const scenariosList = Object.entries(FIXTURES).filter(
    ([key]) => key !== 'invalid_geometry'
  );

  return (
    <aside className={`dual-sidebar ${isCollapsed ? 'dual-sidebar--collapsed' : ''}`}>
      {/* 1. Leftmost Deep Obsidian Icon Bar */}
      <div className="icon-bar">
        <div className="icon-bar__brand" title="VARUNA Marine Intelligence">
          <IconLogoStarburst size={22} color="#FFFFFF" />
        </div>

        <nav className="icon-bar__nav" aria-label="Main navigation">
          <button
            type="button"
            className={`icon-bar__btn ${activeView === 'map' ? 'icon-bar__btn--active' : ''}`}
            onClick={() => onChangeView('map')}
            title="Map & Overview"
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

      {/* 2. Sub-Sidebar Scenarios Pod */}
      {!isCollapsed && (
        <div className="sub-sidebar">
          {/* Top Quick Stats Grid (Inspired by Reference) */}
          <div className="sub-sidebar__stats-grid">
            <div className="stat-pill">
              <span className="stat-pill__label text-xs">Total</span>
              <span className="stat-pill__value mono">9</span>
            </div>
            <div className="stat-pill stat-pill--safe">
              <span className="stat-pill__label text-xs">Safe</span>
              <span className="stat-pill__value mono">1</span>
            </div>
            <div className="stat-pill stat-pill--caution">
              <span className="stat-pill__label text-xs">Caution</span>
              <span className="stat-pill__value mono">2</span>
            </div>
            <div className="stat-pill stat-pill--unsafe">
              <span className="stat-pill__label text-xs">High Risk</span>
              <span className="stat-pill__value mono">6</span>
            </div>
          </div>

          <div className="sub-sidebar__header">
            <h2 className="sub-sidebar__title">Scenarios</h2>
            <span className="sub-sidebar__subtitle text-xs">Grounding & Test Suite</span>
          </div>

          {/* Clean Search Input */}
          <form className="sub-sidebar__search" onSubmit={handleSearchSubmit}>
            <IconSearch size={14} className="sub-sidebar__search-icon" />
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="sub-sidebar__input"
              placeholder="Search coastal scenario..."
              disabled={loading}
              aria-label="Search scenario"
            />
          </form>

          {/* Scenario Cards */}
          <div className="sub-sidebar__scenarios">
            {scenariosList.map(([key, item]) => {
              const isActive = activeScenarioId === key;
              const verdict = item.expectedVerdict;
              const verdictClass = `tag--${verdict.toLowerCase()}`;

              return (
                <button
                  key={key}
                  type="button"
                  className={`scenario-item ${isActive ? 'scenario-item--active' : ''}`}
                  onClick={() => {
                    onChangeView('map');
                    onSelectScenario(key);
                  }}
                  disabled={loading}
                >
                  <div className="scenario-item__top">
                    <span className={`scenario-item__verdict mono text-xs ${verdictClass}`}>
                      {verdict}
                    </span>
                    <span className="scenario-item__meta mono text-xs">COASTAL</span>
                  </div>
                  <h4 className="scenario-item__name text-xs font-bold">
                    {item.name.replace(/^\d+\.\s*/, '')}
                  </h4>
                  <p className="scenario-item__desc text-xs text-muted">{item.description}</p>
                </button>
              );
            })}
          </div>

          {/* Recent Queries */}
          <div className="sub-sidebar__history">
            <div className="sub-sidebar__history-title mono text-xs">RECENT QUERIES</div>
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

      {/* Collapse/Expand Tab Pill */}
      <button
        type="button"
        className="dual-sidebar__toggle"
        onClick={handleToggle}
        title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {isCollapsed ? <IconChevronRight size={14} /> : <IconChevronLeft size={14} />}
      </button>
    </aside>
  );
};

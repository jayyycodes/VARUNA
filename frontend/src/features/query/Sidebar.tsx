import React, { useState } from 'react';
import { useLocalization } from '../../hooks/useLocalization';
import {
  IconMap,
  IconTree,
  IconAlert,
  IconShip,
  IconRoute,
  IconCopilotBot,
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
  onOpenChat,
  activeView,
  onChangeView,
  isCollapsed: controlledIsCollapsed,
  onToggleCollapse,
}) => {
  const { t } = useLocalization();
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const isCollapsed = controlledIsCollapsed !== undefined ? controlledIsCollapsed : internalCollapsed;
  const handleToggle = onToggleCollapse || (() => setInternalCollapsed(!internalCollapsed));

  const navItems = [
    {
      id: 'overview' as ActiveNavView,
      label: t('navOverview'),
      fullLabel: t('navOverview'),
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
        </svg>
      ),
    },
    {
      id: 'map' as ActiveNavView,
      label: t('navMap'),
      fullLabel: t('navMap'),
      icon: <IconMap size={18} />,
    },
    {
      id: 'routing' as ActiveNavView,
      label: t('navRouting'),
      fullLabel: t('navRouting'),
      icon: <IconRoute size={18} />,
    },
    {
      id: 'chat' as ActiveNavView,
      label: t('navChat'),
      fullLabel: t('navChat'),
      badge: 'AI',
      icon: <IconCopilotBot size={19} />,
    },
    {
      id: 'reasoning' as ActiveNavView,
      label: t('navReasoning'),
      fullLabel: t('navReasoning'),
      icon: <IconTree size={18} />,
    },
    {
      id: 'alerts' as ActiveNavView,
      label: t('navAlerts'),
      fullLabel: t('navAlerts'),
      badge: 'LIVE',
      badgeType: 'warning',
      icon: <IconAlert size={18} />,
    },
    {
      id: 'fleet' as ActiveNavView,
      label: t('navFleet'),
      fullLabel: t('navFleet'),
      icon: <IconShip size={18} />,
    },
    {
      id: 'trends' as ActiveNavView,
      label: t('navTrends'),
      fullLabel: t('navTrends'),
      badge: 'Q#7',
      icon: <IconWave size={18} />,
    },
  ];

  return (
    <aside
      className={`varuna-sidebar ${isCollapsed ? 'varuna-sidebar--collapsed' : 'varuna-sidebar--expanded'}`}
      aria-label="Platform navigation"
    >
      {/* 1. Header / Brand Bar */}
      <div className="varuna-sidebar__header">
        <button
          type="button"
          className="varuna-sidebar__brand-btn"
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          onClick={handleToggle}
          aria-label={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          aria-expanded={!isCollapsed}
        >
          <div className="brand-logo-pod">
            <IconLogoStarburst size={20} color="#FFFFFF" />
          </div>
          {!isCollapsed && (
            <div className="brand-title-area">
              <span className="brand-name">VARUNA</span>
              <span className="brand-subtitle">{t('coastalIntelligence')}</span>
            </div>
          )}
        </button>
      </div>

      {/* 2. Navigation Items List */}
      <nav className="varuna-sidebar__nav">
        {navItems.map((item) => {
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={`varuna-nav-item ${isActive ? 'varuna-nav-item--active' : ''}`}
              onClick={() => onChangeView(item.id)}
              title={isCollapsed ? item.fullLabel : undefined}
            >
              <span className="varuna-nav-item__icon">{item.icon}</span>
              {!isCollapsed && (
                <div className="varuna-nav-item__body">
                  <span className="varuna-nav-item__label">{item.fullLabel}</span>
                  {item.badge && (
                    <span className={`varuna-nav-item__badge ${item.badgeType === 'warning' ? 'badge--warning' : ''}`}>
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* 3. Footer Profile / Status */}
      <div className="varuna-sidebar__footer">
        <button
          type="button"
          className="varuna-sidebar__profile-btn"
          title="Open Copilot Assistant"
          onClick={onOpenChat || (() => onChangeView('chat'))}
        >
          <div className="profile-avatar">V</div>
          {!isCollapsed && (
            <div className="profile-info">
              <span className="profile-name">VARUNA</span>
              <span className="profile-role">Operational AIS</span>
            </div>
          )}
        </button>
      </div>
    </aside>
  );
};

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useLocalization } from '../../hooks/useLocalization';
import {
  IconMap,
  IconTree,
  IconAlert,
  IconShip,
  IconRoute,
  IconCopilotBot,
  IconWave,
  IconChevronLeft,
  IconChevronRight,
} from '../../components/Icons';
import './Sidebar.css';

export type ActiveNavView = 'overview' | 'map' | 'routing' | 'chat' | 'reasoning' | 'alerts' | 'fleet' | 'trends';

interface SidebarProps {
  onSelectScenario?: (fixtureId: string) => void;
  onSubmitQuery?: (text: string) => void;
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
      label: t('navOverview') || 'Dashboard',
      fullLabel: 'Marine Command',
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
      label: t('navMap') || 'Ocean Map',
      fullLabel: 'Tactical Ocean Map',
      icon: <IconMap size={18} />,
    },
    {
      id: 'routing' as ActiveNavView,
      label: t('navRouting') || 'Passage Route',
      fullLabel: 'Route Optimization',
      icon: <IconRoute size={18} />,
    },
    {
      id: 'chat' as ActiveNavView,
      label: t('navChat') || 'VARUNA AI',
      fullLabel: 'VARUNA Copilot',
      badge: 'AI',
      icon: <IconCopilotBot size={19} />,
    },
    {
      id: 'reasoning' as ActiveNavView,
      label: t('navReasoning') || 'Rule Engine',
      fullLabel: 'Agentic Reasoning',
      icon: <IconTree size={18} />,
    },
    {
      id: 'alerts' as ActiveNavView,
      label: t('navAlerts') || 'Active Alerts',
      fullLabel: 'Marine Warnings',
      badge: 'LIVE',
      badgeType: 'warning',
      icon: <IconAlert size={18} />,
    },
    {
      id: 'fleet' as ActiveNavView,
      label: t('navFleet') || 'Fleet Ops',
      fullLabel: 'Fleet Operations',
      icon: <IconShip size={18} />,
    },
    {
      id: 'trends' as ActiveNavView,
      label: t('navTrends') || 'Fishery Trends',
      fullLabel: 'Fishery Analytics',
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
            <img src="/logo.png" alt="VARUNA Logo" className="brand-logo-img" />
          </div>
          {!isCollapsed && (
            <div className="brand-title-area">
              <img src="/varuna-font.png" alt="VARUNA" className="brand-name-img" />
              <span className="brand-subtitle">Marine Intelligence</span>
            </div>
          )}
        </button>
      </div>

      {/* 2. Navigation Items List */}
      <nav className="varuna-sidebar__nav relative">
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
              {/* Morphing Dashboard-Connected Pill Background */}
              {isActive && (
                <motion.div
                  layoutId="activeNavPill"
                  className="active-nav-pill"
                  transition={{ type: 'spring', stiffness: 400, damping: 32 }}
                />
              )}

              {/* Icon with subtle scale & accent color */}
              <motion.span
                className="varuna-nav-item__icon"
                animate={{
                  scale: isActive ? 1.05 : 1,
                  color: isActive ? '#0F172A' : '#94A3B8',
                }}
                transition={{ duration: 0.15 }}
              >
                {item.icon}
              </motion.span>

              {/* Label + badge with dynamic accent text */}
              {!isCollapsed && (
                <span className="varuna-nav-item__body">
                  <motion.span
                    className="varuna-nav-item__label"
                    animate={{
                      color: isActive ? '#0F172A' : '#94A3B8',
                    }}
                    transition={{ duration: 0.15 }}
                  >
                    {item.fullLabel}
                  </motion.span>
                  {item.badge && (
                    <span
                      className={`varuna-nav-item__badge ${
                        item.badgeType === 'warning' ? 'badge--warning' : ''
                      }`}
                      style={{
                        background: isActive ? 'rgba(15, 23, 42, 0.1)' : 'rgba(255, 255, 255, 0.12)',
                        color: isActive ? '#0F172A' : '#94A3B8',
                      }}
                    >
                      {item.badge}
                    </span>
                  )}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* 3. Footer Profile / Status */}
      <div className="varuna-sidebar__footer">
        {/* Toggle Button above profile */}
        <button
          type="button"
          className="varuna-sidebar__toggle-btn"
          onClick={handleToggle}
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          aria-label={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {isCollapsed ? <IconChevronRight size={15} /> : <IconChevronLeft size={15} />}
          {!isCollapsed && <span className="toggle-btn-label">Collapse Sidebar</span>}
        </button>

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

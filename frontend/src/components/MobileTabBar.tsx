import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocalization } from '../hooks/useLocalization';
import {
  IconMap,
  IconAlert,
  IconCopilotBot,
  IconWave,
  IconShip,
  IconRoute,
  IconTree,
} from './Icons';
import './MobileTabBar.css';

export interface MobileTabBarProps {
  onNavigate?: (view: string) => void;
}

export const MobileTabBar: React.FC<MobileTabBarProps> = ({ onNavigate }) => {
  const { t } = useLocalization();
  const navigate = useNavigate();
  const location = useLocation();
  const [moreOpen, setMoreOpen] = useState(false);

  const currentPath = location.pathname.replace('/', '') || 'overview';

  const handleSelectTab = (path: string) => {
    setMoreOpen(false);
    if (onNavigate) {
      onNavigate(path);
    }
    navigate(`/${path === 'overview' ? '' : path}`);
  };

  // Primary 4 tabs + 1 More capsule button (Max 5 items)
  const mainTabs = [
    {
      id: 'overview',
      label: t('navOverview') || 'Dashboard',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
        </svg>
      ),
      isActive: currentPath === 'overview',
    },
    {
      id: 'map',
      label: t('navMap') || 'Map',
      icon: <IconMap size={20} />,
      isActive: currentPath === 'map',
    },
    {
      id: 'chat',
      label: t('navAssistant') || 'Assistant',
      icon: <IconCopilotBot size={20} />,
      isActive: currentPath === 'chat',
    },
    {
      id: 'trends',
      label: t('navTrends') || 'Trends',
      icon: <IconWave size={20} />,
      isActive: currentPath === 'trends',
    },
  ];

  const moreItems = [
    {
      id: 'alerts',
      label: t('navAlerts') || 'Alerts',
      icon: <IconAlert size={18} />,
      description: 'Active Warning Bulletins & Cyclones',
    },
    {
      id: 'fleet',
      label: t('navFleet') || 'Fleet Ops',
      icon: <IconShip size={18} />,
      description: 'Coastal Vessel Tracking & Compliance',
    },
    {
      id: 'routing',
      label: t('navRouting') || 'Passage Route',
      icon: <IconRoute size={18} />,
      description: 'Safe Corridor & Waypoint Optimization',
    },
    {
      id: 'reasoning',
      label: t('navReasoning') || 'Rule Engine',
      icon: <IconTree size={18} />,
      description: 'Multi-Agent Synthesis Trace Graph',
    },
  ];

  const isMoreActive = ['alerts', 'fleet', 'routing', 'reasoning'].includes(currentPath);

  return (
    <>
      {/* 1. Backdrop Scrim for More Sheet */}
      <AnimatePresence>
        {moreOpen && (
          <motion.div
            className="mobile-more-scrim"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMoreOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* 2. More Action Sheet */}
      <AnimatePresence>
        {moreOpen && (
          <motion.div
            className="mobile-more-sheet"
            initial={{ y: 200, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 200, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 420, damping: 32 }}
          >
            <div className="more-sheet-handle" />
            <div className="more-sheet-header">
              <span className="more-sheet-title">{t('navMore') || 'More Operations'}</span>
              <button
                type="button"
                className="more-sheet-close"
                onClick={() => setMoreOpen(false)}
                aria-label={t('closeMenu') || 'Close'}
              >
                ✕
              </button>
            </div>
            <div className="more-items-grid">
              {moreItems.map((item) => {
                const isSelected = currentPath === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    className={`more-item-btn ${isSelected ? 'more-item-btn--active' : ''}`}
                    onClick={() => handleSelectTab(item.id)}
                  >
                    <span className="more-item-icon">{item.icon}</span>
                    <div className="more-item-text">
                      <span className="more-item-label">{item.label}</span>
                      <span className="more-item-desc">{item.description}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 3. Floating Bottom Capsule Tab Bar */}
      <nav className="mobile-floating-tabbar" aria-label="Mobile Navigation">
        {mainTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`tabbar-btn ${tab.isActive && !moreOpen ? 'tabbar-btn--active' : ''}`}
            onClick={() => handleSelectTab(tab.id)}
            aria-label={tab.label}
          >
            <span className="tabbar-icon">{tab.icon}</span>
            <span className="tabbar-label">{tab.label}</span>
            {tab.isActive && !moreOpen && (
              <motion.div
                layoutId="activeTabIndicator"
                className="tabbar-active-pill"
                transition={{ type: 'spring', stiffness: 500, damping: 36 }}
              />
            )}
          </button>
        ))}

        {/* 5th Tab: More Button */}
        <button
          type="button"
          className={`tabbar-btn ${isMoreActive || moreOpen ? 'tabbar-btn--active' : ''}`}
          onClick={() => setMoreOpen(!moreOpen)}
          aria-label={t('navMore') || 'More'}
          aria-expanded={moreOpen}
        >
          <span className="tabbar-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="1.5" />
              <circle cx="19" cy="12" r="1.5" />
              <circle cx="5" cy="12" r="1.5" />
            </svg>
          </span>
          <span className="tabbar-label">{t('navMore') || 'More'}</span>
          {(isMoreActive || moreOpen) && (
            <motion.div
              layoutId="activeTabIndicator"
              className="tabbar-active-pill"
              transition={{ type: 'spring', stiffness: 500, damping: 36 }}
            />
          )}
        </button>
      </nav>
    </>
  );
};

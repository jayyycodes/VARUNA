import React, { useState } from 'react';
import { FIXTURES } from '../../fixtures';
import { IconSearch, IconPanelLeft } from '../../components/Icons';
import { useLocalization } from '../../hooks/useLocalization';
import './ScenarioDrawer.css';

interface ScenarioDrawerProps {
  activeScenarioId?: string | null;
  onSelectScenario: (fixtureId: string) => void;
  loading?: boolean;
}

export const ScenarioDrawer: React.FC<ScenarioDrawerProps> = ({
  activeScenarioId,
  onSelectScenario,
  loading = false,
}) => {
  const { t } = useLocalization();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const scenariosList = Object.entries(FIXTURES).filter(
    ([key]) => key !== 'invalid_geometry'
  );

  const filteredScenarios = scenariosList.filter(([_, fixture]) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      fixture.name.toLowerCase().includes(term) ||
      fixture.description.toLowerCase().includes(term) ||
      fixture.expectedVerdict.toLowerCase().includes(term)
    );
  });

  return (
    <div className={`scenario-drawer ${isCollapsed ? 'scenario-drawer--collapsed' : ''}`}>
      {isCollapsed ? (
        <div className="scenario-drawer__collapsed-content" onClick={() => setIsCollapsed(false)}>
          <button
            type="button"
            className="scenario-drawer__toggle-btn scenario-drawer__toggle-btn--collapsed"
            onClick={(e) => {
              e.stopPropagation();
              setIsCollapsed(false);
            }}
            title={t('testScenarios')}
            aria-label={t('testScenarios')}
          >
            <IconPanelLeft size={16} />
          </button>
          <span className="collapsed-vertical-text">{t('testScenarios')}</span>
          <span className="collapsed-badge">{scenariosList.length}</span>
        </div>
      ) : (
        <div className="scenario-drawer__body">
          {/* Header */}
          <div className="scenario-drawer__header">
            <div className="scenario-drawer__title-row">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3 className="scenario-drawer__title">{t('scenariosTitle')}</h3>
                <span className="scenario-drawer__count-badge mono text-xs">
                  {scenariosList.length} {t('totalLabel')}
                </span>
              </div>
              <button
                type="button"
                className="scenario-drawer__toggle-btn"
                onClick={() => setIsCollapsed(true)}
                title="Collapse Test Scenarios"
                aria-label="Collapse Test Scenarios"
              >
                <IconPanelLeft size={16} />
              </button>
            </div>
            <span className="scenario-drawer__subtitle text-xs">
              {t('groundingTestSuite')}
            </span>
          </div>

          {/* Search Input */}
          <div className="scenario-drawer__search">
            <IconSearch size={13} className="scenario-drawer__search-icon" />
            <input
              type="text"
              className="scenario-drawer__input"
              placeholder={t('searchScenarios')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              disabled={loading}
            />
          </div>

          {/* Scenarios List */}
          <div className="scenario-drawer__list">
            {filteredScenarios.map(([key, fixture]) => {
              const isActive = activeScenarioId === key;
              const verdict = fixture.expectedVerdict;

              let tagClass = 'tag--safe';
              if (verdict === 'CAUTION') tagClass = 'tag--caution';
              if (verdict === 'UNSAFE') tagClass = 'tag--unsafe';
              if (verdict === 'UNKNOWN') tagClass = 'tag--unknown';

              return (
                <button
                  key={key}
                  type="button"
                  className={`scenario-card ${isActive ? 'scenario-card--active' : ''}`}
                  onClick={() => onSelectScenario(key)}
                  disabled={loading}
                >
                  <div className="scenario-card__top">
                    <span className={`scenario-card__verdict mono text-xs ${tagClass}`}>
                      {verdict}
                    </span>
                    <span className="scenario-card__domain mono text-xs">COASTAL</span>
                  </div>
                  <h4 className="scenario-card__name text-xs font-bold">{fixture.name}</h4>
                  <p className="scenario-card__desc text-xs text-muted">
                    {fixture.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

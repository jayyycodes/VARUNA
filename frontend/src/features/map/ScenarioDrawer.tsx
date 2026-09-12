import React, { useState } from 'react';
import { FIXTURES } from '../../fixtures';
import { IconSearch, IconChevronLeft, IconChevronRight } from '../../components/Icons';
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
      {/* Collapse Toggle Tab */}
      <button
        type="button"
        className="scenario-drawer__toggle-btn"
        onClick={() => setIsCollapsed(!isCollapsed)}
        title={isCollapsed ? 'Expand Test Scenarios' : 'Collapse Test Scenarios'}
        aria-label={isCollapsed ? 'Expand Test Scenarios' : 'Collapse Test Scenarios'}
      >
        {isCollapsed ? <IconChevronRight size={14} /> : <IconChevronLeft size={14} />}
      </button>

      {isCollapsed ? (
        <div className="scenario-drawer__collapsed-content" onClick={() => setIsCollapsed(false)}>
          <span className="collapsed-vertical-text">TEST SCENARIOS</span>
          <span className="collapsed-badge">{scenariosList.length}</span>
        </div>
      ) : (
        <div className="scenario-drawer__body">
          {/* Header */}
          <div className="scenario-drawer__header">
            <div className="scenario-drawer__title-row">
              <h3 className="scenario-drawer__title">Scenarios</h3>
              <span className="scenario-drawer__count-badge mono text-xs">
                {scenariosList.length} Total
              </span>
            </div>
            <span className="scenario-drawer__subtitle text-xs">
              Grounding & Test Suite
            </span>
          </div>

          {/* Search Input */}
          <div className="scenario-drawer__search">
            <IconSearch size={13} className="scenario-drawer__search-icon" />
            <input
              type="text"
              className="scenario-drawer__input"
              placeholder="Search coastal scenario..."
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

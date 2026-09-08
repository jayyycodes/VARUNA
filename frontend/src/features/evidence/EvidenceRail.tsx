import React from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { EvidencePanelContent } from './EvidencePanelContent';
import './EvidenceRail.css';

interface EvidenceRailProps {
  response?: UserResponseV1 | null;
  selectedEvidenceId?: string | null;
  selectedClaimId?: string | null;
  onSelectFeature?: (featureId: string) => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

/**
 * Evidence Rail — desktop right panel (340px, collapsible).
 *
 * Design rules (VARUNA_DESIGN_SYSTEM.md §4.3):
 * - Rule-trace cards: tabular value/threshold/result
 * - Sources section: citation cards (title, publisher, timestamp, excerpt, link)
 * - Unsupported claim → grey "not verified" label
 * - RAG insufficient-evidence fallback: exact copy "We could not verify this
 *   from the available official sources."
 * - Source-language vs response-language visually distinguishable
 */
export const EvidenceRail: React.FC<EvidenceRailProps> = ({
  response,
  selectedEvidenceId,
  selectedClaimId,
  onSelectFeature,
  isCollapsed = false,
  onToggleCollapse,
}) => {
  return (
    <aside
      className={`evidence-rail ${isCollapsed ? 'evidence-rail--collapsed' : ''}`}
      role="complementary"
      aria-label="Evidence and sources"
    >
      <div className="evidence-rail__header">
        <h2 className="evidence-rail__title text-display">Evidence & Sources</h2>
        {onToggleCollapse && (
          <button
            className="evidence-rail__toggle-btn"
            onClick={onToggleCollapse}
            aria-label={isCollapsed ? 'Expand Evidence Rail' : 'Collapse Evidence Rail'}
            title={isCollapsed ? 'Expand' : 'Collapse'}
          >
            {isCollapsed ? '◀' : '▶'}
          </button>
        )}
      </div>

      {!isCollapsed && (
        <div className="evidence-rail__content">
          <EvidencePanelContent
            response={response}
            selectedEvidenceId={selectedEvidenceId}
            selectedClaimId={selectedClaimId}
            onSelectFeature={onSelectFeature}
          />
        </div>
      )}
    </aside>
  );
};

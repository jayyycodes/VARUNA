import type { UserResponseV1 } from '../../contracts/userResponse';
import { EvidencePanelContent } from './EvidencePanelContent';
import { IconChevronDown } from '../../components/Icons';
import './BottomSheet.css';

interface BottomSheetProps {
  isOpen: boolean;
  onToggle: () => void;
  response?: UserResponseV1 | null;
  selectedEvidenceId?: string | null;
  selectedClaimId?: string | null;
  onSelectFeature?: (featureId: string) => void;
}

/**
 * Bottom Sheet — mobile evidence panel.
 *
 * Design rules (VARUNA_DESIGN_SYSTEM.md §4.3):
 * - Collapsed: grabber handle + "Evidence & sources" label + chevron, ~64px
 * - Spring on drag: damping 0.8, response 0.3 (momentum-driven)
 * - prefers-reduced-motion: plain slide, no spring
 */
export function BottomSheet({
  isOpen,
  onToggle,
  response,
  selectedEvidenceId,
  selectedClaimId,
  onSelectFeature,
}: BottomSheetProps) {
  return (
    <div
      className={`bottom-sheet glass ${isOpen ? 'bottom-sheet--open' : ''}`}
      role="complementary"
      aria-label="Evidence and sources"
    >
      <button
        className="bottom-sheet__handle"
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-controls="bottom-sheet-content"
        type="button"
      >
        <div className="bottom-sheet__grabber" />
        <span className="bottom-sheet__label text-sm font-bold">
          Evidence & Sources {response ? `(${response.evidence_panel.rule_trace.length + response.citations.length})` : ''}
        </span>
        <span
          className={`bottom-sheet__chevron ${isOpen ? 'bottom-sheet__chevron--open' : ''}`}
          aria-hidden="true"
        >
          <IconChevronDown size={14} />
        </span>
      </button>

      <div
        id="bottom-sheet-content"
        className="bottom-sheet__content"
        hidden={!isOpen}
      >
        <EvidencePanelContent
          response={response}
          selectedEvidenceId={selectedEvidenceId}
          selectedClaimId={selectedClaimId}
          onSelectFeature={onSelectFeature}
        />
      </div>
    </div>
  );
}

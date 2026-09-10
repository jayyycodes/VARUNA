import { useState, useEffect } from 'react';
import type { UserResponseV1 } from './contracts/userResponse';
import { apiClient } from './api/client';
import { Sidebar } from './features/query/Sidebar';
import type { ActiveNavView } from './features/query/Sidebar';
import { MapCanvas } from './features/map/MapCanvas';
import { VerdictCard } from './features/decision/VerdictCard';
import { EvidenceRail, BottomSheet } from './features/evidence';
import { AgenticReasoningView } from './features/reasoning/AgenticReasoningView';
import { ActiveAlertsView } from './features/alerts/ActiveAlertsView';
import { FleetOpsView } from './features/fleet/FleetOpsView';
import { RouteOptimizationView } from './features/routing/RouteOptimizationView';
import { ChatAssistantView } from './features/chat/ChatAssistantView';
import { ChatAssistantModal } from './features/chat/ChatAssistantModal';
import { IconMapPin, IconSearch, IconCopilotBot } from './components/Icons';
import { useIsMobile } from './hooks/useIsMobile';
import './App.css';

function App() {
  const isMobile = useIsMobile();

  // Active Main View: 'map' | 'routing' | 'chat' | 'reasoning' | 'alerts' | 'fleet'
  const [activeView, setActiveView] = useState<ActiveNavView>('map');

  // Primary State
  const [response, setResponse] = useState<UserResponseV1 | null>(null);
  const [activeScenarioId, setActiveScenarioId] = useState<string | null>('safe_complete');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Conversational AI Copilot Modal State (Quick toggle)
  const [chatModalOpen, setChatModalOpen] = useState<boolean>(false);

  // Selection & Navigation State
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [selectedFeatureId, setSelectedFeatureId] = useState<string | null>(null);

  // Panel Toggles
  const [bottomSheetOpen, setBottomSheetOpen] = useState<boolean>(false);
  const [railCollapsed, setRailCollapsed] = useState<boolean>(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);

  // Search input state in top bar
  const [topSearch, setTopSearch] = useState<string>('');
  // Bug 6 fix: preserve the last-submitted query so users can see what result is active.
  const [activeQuery, setActiveQuery] = useState<string | null>(null);

  // Load initial demo scenario on mount
  useEffect(() => {
    executeScenario('safe_complete');
  }, []);

  const executeScenario = async (fixtureId: string) => {
    setLoading(true);
    setError(null);
    setActiveScenarioId(fixtureId);
    setSelectedEvidenceId(null);
    setSelectedClaimId(null);
    setSelectedFeatureId(null);
    setActiveQuery(null); // Clear live query breadcrumb when returning to a scenario

    try {
      const result = await apiClient.submitQuery({ text: '' }, fixtureId);
      setResponse(result.response);
    } catch (err: any) {
      console.error('Failed to load scenario:', err);
      setError(err.message || 'Failed to load scenario response.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuerySubmit = async (queryText: string) => {
    if (!queryText.trim()) return;
    setLoading(true);
    setError(null);
    setSelectedEvidenceId(null);
    setSelectedClaimId(null);
    setSelectedFeatureId(null);

    try {
      const result = await apiClient.submitQuery({ text: queryText.trim() });
      setResponse(result.response);
      setActiveScenarioId(null); // Custom query
      // Bug 6 fix: preserve submitted query for breadcrumb context instead of wiping it
      setActiveQuery(queryText.trim());
    } catch (err: any) {
      console.error('Query execution error:', err);
      setError(err.message || 'Error processing maritime safety query.');
    } finally {
      setLoading(false);
      setTopSearch(''); // Clear input but activeQuery keeps the submitted text
    }
  };

  const handleSelectReason = (claimId: string, evidenceId?: string) => {
    setSelectedClaimId(claimId);
    if (evidenceId) {
      setSelectedEvidenceId(evidenceId);
    }
    // If on mobile, expand the bottom sheet so user immediately sees the evidence
    if (isMobile) {
      setBottomSheetOpen(true);
    }
    // If desktop rail is collapsed, expand it
    if (railCollapsed) {
      setRailCollapsed(false);
    }
  };

  const handleSelectFeature = (featureId: string) => {
    setSelectedFeatureId(featureId);
  };

  return (
    <div
      className={`app-container ${sidebarCollapsed ? 'app-container--sidebar-collapsed' : ''} ${
        railCollapsed ? 'app-container--rail-collapsed' : ''
      }`}
    >
      {/* 1. Left Dual-Sidebar (Icon Rail + Scenario List) */}
      {!isMobile && (
        <Sidebar
          onSelectScenario={executeScenario}
          onSubmitQuery={handleQuerySubmit}
          onOpenChat={() => setActiveView('chat')}
          activeScenarioId={activeScenarioId}
          loading={loading}
          activeView={activeView}
          onChangeView={setActiveView}
          isCollapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      )}

      {/* 2. Main Dashboard Container */}
      <div className="dashboard-content">
        {/* Top Header Bar */}
        <header className="dashboard-topbar">
          <div className="dashboard-topbar__left">
            <h1 className="dashboard-topbar__title">
              {activeView === 'map' && 'Marine Intelligence Command'}
              {activeView === 'routing' && 'Route Optimization & Safe Passage'}
              {activeView === 'chat' && 'VARUNA Copilot — Marine AI Intelligence'}
              {activeView === 'reasoning' && 'Agentic Reasoning'}
              {activeView === 'alerts' && 'Active Marine Alerts'}
              {activeView === 'fleet' && 'Fleet Operations'}
            </h1>
            {/* Bug 6 fix: show active query as breadcrumb so user retains context after submit */}
            {activeQuery && !activeScenarioId ? (
              <div className="dashboard-topbar__location-pill mono text-xs" style={{ gap: 6 }}>
                <IconSearch size={11} color="#64748B" />
                <span style={{ color: '#94A3B8', maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {activeQuery}
                </span>
              </div>
            ) : (
              <div className="dashboard-topbar__location-pill mono text-xs">
                <IconMapPin size={13} color="#64748B" />
                <span>Arabian Sea & Bay of Bengal • Today ({new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })})</span>
              </div>
            )}
          </div>

          <div className="dashboard-topbar__right">
            {/* Top Search Bar */}
            <form
              className="topbar-search"
              onSubmit={(e) => {
                e.preventDefault();
                handleQuerySubmit(topSearch);
              }}
            >
              <IconSearch size={14} className="topbar-search__icon" />
              <input
                type="text"
                value={topSearch}
                onChange={(e) => setTopSearch(e.target.value)}
                placeholder="Search coordinates or query..."
                className="topbar-search__input"
                aria-label="Search marine safety intelligence"
              />
              <span className="topbar-search__shortcut mono">⌘K</span>
            </form>

            {/* Topbar AI Copilot Trigger Button */}
            <button
              type="button"
              className="topbar-ai-btn"
              onClick={() => setActiveView('chat')}
              title="Open VARUNA Copilot Page"
            >
              <IconCopilotBot size={15} color="#D8FA36" />
              <span>Ask Copilot</span>
            </button>

            <div className="topbar-telemetry-pill mono text-xs">
              <span className="telemetry-live-dot" />
              LIVE TELEMETRY
            </div>

            <div
              className="topbar-user-profile"
              title="Adeey • Lead Experience Architect (Click to open Copilot)"
              onClick={() => setActiveView('chat')}
            >
              <div className="topbar-user-avatar">A</div>
              <div className="topbar-user-info">
                <span className="topbar-user-name">Adeey</span>
                <span className="topbar-user-role mono text-xs">Architect</span>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Main Workspace */}
        <main className="dashboard-workspace" role="main">
          {activeView === 'map' && (
            <div className="map-view-grid">
              {/* Center Map Card Canvas */}
              <div className="map-card-wrapper">
                <VerdictCard
                  response={response}
                  loading={loading}
                  error={error}
                  onSelectReason={handleSelectReason}
                  onRetry={() => executeScenario(activeScenarioId || 'safe_complete')}
                />

                <MapCanvas
                  response={response}
                  selectedFeatureId={selectedFeatureId}
                  onSelectFeature={handleSelectFeature}
                />
              </div>

              {/* Right Evidence Rail */}
              {!isMobile && (
                <EvidenceRail
                  response={response}
                  selectedEvidenceId={selectedEvidenceId}
                  selectedClaimId={selectedClaimId}
                  onSelectFeature={handleSelectFeature}
                  isCollapsed={railCollapsed}
                  onToggleCollapse={() => setRailCollapsed(!railCollapsed)}
                />
              )}

              {/* Mobile Bottom Sheet */}
              {isMobile && (
                <BottomSheet
                  isOpen={bottomSheetOpen}
                  onToggle={() => setBottomSheetOpen(!bottomSheetOpen)}
                  response={response}
                  selectedEvidenceId={selectedEvidenceId}
                  selectedClaimId={selectedClaimId}
                  onSelectFeature={handleSelectFeature}
                />
              )}
            </div>
          )}

          {/* View 2: Route Optimization & Safe Passage */}
          {activeView === 'routing' && (
            <RouteOptimizationView response={response} />
          )}

          {/* View 3: VARUNA AI Copilot Conversational Page */}
          {activeView === 'chat' && (
            <ChatAssistantView
              onSelectScenario={executeScenario}
              onChangeView={setActiveView}
              currentResponse={response}
            />
          )}

          {/* View 4: Agentic Reasoning */}
          {activeView === 'reasoning' && (
            <AgenticReasoningView response={response} />
          )}

          {/* View 5: Active Alerts */}
          {activeView === 'alerts' && (
            <ActiveAlertsView
              response={response}
              onSelectScenario={(scenarioId) => {
                setActiveView('map');
                executeScenario(scenarioId);
              }}
            />
          )}

          {/* View 6: Fleet Operations */}
          {activeView === 'fleet' && (
            <FleetOpsView />
          )}
        </main>
      </div>

      {/* Floating AI Agent Launcher Button (Claude / Grok Style) */}
      <button
        type="button"
        className="floating-ai-launcher-btn"
        onClick={() => setChatModalOpen(true)}
        title="Ask VARUNA AI Copilot (⌘J)"
      >
        <IconCopilotBot size={17} className="launcher-sparkle-icon" color="#D8FA36" />
        <span>Ask VARUNA AI</span>
        <span className="mono text-xs" style={{ opacity: 0.7 }}>⌘J</span>
      </button>

      {/* Conversational Marine AI Assistant Modal */}
      <ChatAssistantModal
        isOpen={chatModalOpen}
        onClose={() => setChatModalOpen(false)}
        onSelectScenario={executeScenario}
        onChangeView={setActiveView}
        currentResponse={response}
      />
    </div>
  );
}

export default App;

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
import { HistoricalTrendsView } from './features/analytics/HistoricalTrendsView';
import { ExecutiveDashboardView } from './features/dashboard/ExecutiveDashboardView';
import { ChatAssistantView } from './features/chat/ChatAssistantView';
import { ChatAssistantModal } from './features/chat/ChatAssistantModal';
import { ScenarioDrawer } from './features/map/ScenarioDrawer';
import { LanguageSelector } from './components/LanguageSelector';
import { useLocalization } from './hooks/useLocalization';
import {
  IconMapPin,
  IconSearch,
  IconCopilotBot,
  IconAnchor,
  IconBook,
} from './components/Icons';
import { useIsMobile } from './hooks/useIsMobile';
import './App.css';

const NAV_ACCENTS: Record<ActiveNavView, { accent: string; accentText: string }> = {
  overview: { accent: '#FFFFFF', accentText: '#0F172A' },
  map: { accent: '#0EA5E9', accentText: '#FFFFFF' },
  routing: { accent: '#14B8A6', accentText: '#FFFFFF' },
  chat: { accent: '#8B5CF6', accentText: '#FFFFFF' },
  reasoning: { accent: '#F59E0B', accentText: '#FFFFFF' },
  alerts: { accent: '#EF4444', accentText: '#FFFFFF' },
  fleet: { accent: '#3B82F6', accentText: '#FFFFFF' },
  trends: { accent: '#10B981', accentText: '#FFFFFF' },
};

function App() {
  const isMobile = useIsMobile();
  const { currentLang, setLanguage, t } = useLocalization();

  // Active Main View: 'overview' | 'map' | 'routing' | 'chat' | 'reasoning' | 'alerts' | 'fleet' | 'trends'
  const [activeView, setActiveView] = useState<ActiveNavView>('overview');

  // Mode: Persona split with device-aware default (Mobile => Fisherman, Desktop => Command)
  const [mode, setMode] = useState<'fisherman' | 'command'>(() => {
    try {
      const saved = localStorage.getItem('varuna_ui_mode') as 'fisherman' | 'command';
      if (saved && (saved === 'fisherman' || saved === 'command')) return saved;
    } catch {}
    return isMobile ? 'fisherman' : 'command';
  });

  const toggleMode = () => {
    const next = mode === 'fisherman' ? 'command' : 'fisherman';
    setMode(next);
    try {
      localStorage.setItem('varuna_ui_mode', next);
    } catch {}
  };

  // Lock default theme to Sunlight Light Mode
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'sunlight');
  }, []);

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
              {activeView === 'overview' && 'Marine Intelligence Command'}
              {activeView === 'map' && t('pageMapTitle')}
              {activeView === 'routing' && t('pageRoutingTitle')}
              {activeView === 'chat' && t('pageChatTitle')}
              {activeView === 'reasoning' && t('pageReasoningTitle')}
              {activeView === 'alerts' && t('pageAlertsTitle')}
              {activeView === 'fleet' && t('pageFleetTitle')}
              {activeView === 'trends' && t('pageTrendsTitle')}
            </h1>

            {/* Bug 6 fix: show active query as breadcrumb so user retains context after submit */}
            {activeQuery && !activeScenarioId ? (
              <div className="dashboard-topbar__location-pill mono" style={{ gap: 5 }}>
                <IconSearch size={11} color="#64748B" />
                <span style={{ color: '#64748B', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {activeQuery}
                </span>
              </div>
            ) : (
              <div className="dashboard-topbar__location-pill mono">
                <IconMapPin size={11} color="#64748B" />
                <span>{t('locationContext')}</span>
              </div>
            )}
          </div>

          {/* Centered Pill Search Bar (Compact size matching control buttons) */}
          <div className="topbar-search-pill">
            <IconSearch size={12} className="topbar-search-pill__icon" />
            <input
              type="text"
              className="topbar-search-pill__input"
              placeholder="Search..."
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                  handleQuerySubmit(e.currentTarget.value.trim());
                }
              }}
            />
          </div>

          <div className="dashboard-topbar__right">
            {/* Language Selector */}
            <LanguageSelector currentLang={currentLang} onLanguageChange={setLanguage} />

            {/* Fisherman Mode vs Operations Mode Toggle */}
            <button
              type="button"
              className={`topbar-control-btn ${mode === 'fisherman' ? 'topbar-control-btn--active' : ''}`}
              onClick={toggleMode}
              role="switch"
              aria-checked={mode === 'fisherman'}
              aria-label="Toggle between Fisherman View and Operations View"
              title={mode === 'fisherman' ? 'Switch to Operations View' : 'Switch to Fisherman View'}
            >
              {mode === 'fisherman' ? (
                <IconAnchor size={13} color={mode === 'fisherman' ? 'var(--status-safe)' : 'currentColor'} />
              ) : (
                <IconBook size={13} />
              )}
              <span>{mode === 'fisherman' ? t('fishermanMode') : t('commandMode')}</span>
            </button>

            {/* Topbar AI Copilot Trigger Button */}
            <button
              type="button"
              className="topbar-ai-btn"
              onClick={() => setActiveView('chat')}
              title="Open VARUNA Copilot Page"
            >
              <IconCopilotBot size={13} color="#60A5FA" />
              <span>{t('askCopilot')}</span>
            </button>
          </div>
        </header>

        {/* Dashboard Main Workspace */}
        <main
          className="dashboard-workspace"
          role="main"
          style={
            {
              '--panel-accent': NAV_ACCENTS[activeView].accent,
              '--panel-accent-text': NAV_ACCENTS[activeView].accentText,
            } as React.CSSProperties
          }
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={activeView}
              style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{
                duration: 0.25,
                delay: 0.2,
                ease: [0.22, 1, 0.36, 1],
              }}
            >
              {/* View 0: Executive Dashboard (Matching Reference Mockup Layout) */}
              {activeView === 'overview' && (
                <ExecutiveDashboardView
                  response={response}
                  activeScenarioId={activeScenarioId}
                  onSelectScenario={executeScenario}
                  onNavigateView={setActiveView}
                />
              )}

              {activeView === 'map' && (
                <div className="map-view-grid">
                  {/* Left Test Scenarios Grounding Drawer */}
                  {!isMobile && (
                    <ScenarioDrawer
                      activeScenarioId={activeScenarioId}
                      onSelectScenario={executeScenario}
                      loading={loading}
                    />
                  )}

                  {/* Center Map Card Canvas */}
                  <div className="map-card-wrapper">
                    <VerdictCard
                      response={response}
                      loading={loading}
                      error={error}
                      mode={mode}
                      onInspectDetails={() => {
                        if (isMobile) {
                          setBottomSheetOpen(true);
                        } else {
                          setRailCollapsed(false);
                        }
                      }}
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

              {/* View 7: Fishery Trends & Environmental Anomalies (SIH Query #7) */}
              {activeView === 'trends' && (
                <HistoricalTrendsView />
              )}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

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

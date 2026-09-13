import { useEffect, useState } from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
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
import { ErrorBoundary } from './components/ErrorBoundary';
import { useLocalization } from './hooks/useLocalization';
import { useAppStore } from './store/useAppStore';
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
  const navigate = useNavigate();
  const location = useLocation();

  // Route-driven active view
  const currentPath = location.pathname.replace('/', '') || 'overview';
  const activeView: ActiveNavView = (
    ['overview', 'map', 'routing', 'chat', 'reasoning', 'alerts', 'fleet', 'trends'].includes(currentPath)
      ? currentPath
      : 'overview'
  ) as ActiveNavView;

  const setActiveView = (view: ActiveNavView) => {
    navigate(`/${view === 'overview' ? '' : view}`);
  };

  // Centralized Zustand App Store
  const {
    response,
    loading,
    error,
    activeQuery,
    activeScenarioId,
    selectedEvidenceId,
    selectedClaimId,
    selectedFeatureId,
    bottomSheetOpen,
    railCollapsed,
    sidebarCollapsed,
    mode,
    setResponse,
    setLoading,
    setError,
    setActiveQuery,
    setActiveScenarioId,
    setSelectedEvidenceId,
    setSelectedClaimId,
    setSelectedFeatureId,
    setBottomSheetOpen,
    setRailCollapsed,
    setSidebarCollapsed,
    toggleMode,
  } = useAppStore();

  const [chatModalOpen, setChatModalOpen] = useState<boolean>(false);

  // Lock default theme to Sunlight Light Mode
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'sunlight');
  }, []);

  // Load initial demo scenario on mount
  useEffect(() => {
    if (!response) {
      executeScenario('safe_complete');
    }
  }, []);

  const executeScenario = async (fixtureId: string) => {
    setLoading(true);
    setError(null);
    setActiveScenarioId(fixtureId);
    setSelectedEvidenceId(null);
    setSelectedClaimId(null);
    setSelectedFeatureId(null);
    setActiveQuery(null);

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
      setActiveScenarioId(null);
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
    if (isMobile) {
      setBottomSheetOpen(true);
    }
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
      {/* 1. Left Single Expanding Matte Sidebar */}
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

            {activeQuery && !activeScenarioId ? (
              <div className="dashboard-topbar__location-pill mono" style={{ gap: 5 }}>
                <IconSearch size={11} color="#64748B" />
                <span
                  style={{
                    color: '#64748B',
                    maxWidth: 200,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
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

          {/* Centered Pill Search Bar */}
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
              '--panel-accent': NAV_ACCENTS[activeView]?.accent || '#FFFFFF',
              '--panel-accent-text': NAV_ACCENTS[activeView]?.accentText || '#0F172A',
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
                delay: 0.15,
                ease: [0.22, 1, 0.36, 1],
              }}
            >
              <Routes>
                {/* 1. Overview Dashboard */}
                <Route
                  path="/"
                  element={
                    <ErrorBoundary name="Executive Dashboard">
                      <ExecutiveDashboardView
                        response={response}
                        activeScenarioId={activeScenarioId}
                        onSelectScenario={executeScenario}
                        onNavigateView={setActiveView}
                      />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/overview"
                  element={
                    <ErrorBoundary name="Executive Dashboard">
                      <ExecutiveDashboardView
                        response={response}
                        activeScenarioId={activeScenarioId}
                        onSelectScenario={executeScenario}
                        onNavigateView={setActiveView}
                      />
                    </ErrorBoundary>
                  }
                />

                {/* 2. Tactical Ocean Map */}
                <Route
                  path="/map"
                  element={
                    <ErrorBoundary name="Tactical Ocean Map">
                      <div className="map-view-grid">
                        {!isMobile && (
                          <ScenarioDrawer
                            activeScenarioId={activeScenarioId}
                            onSelectScenario={executeScenario}
                            loading={loading}
                          />
                        )}

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
                    </ErrorBoundary>
                  }
                />

                {/* 3. Route Optimization & Safe Passage */}
                <Route
                  path="/routing"
                  element={
                    <ErrorBoundary name="Route Optimization">
                      <RouteOptimizationView response={response} />
                    </ErrorBoundary>
                  }
                />

                {/* 4. VARUNA Copilot Page */}
                <Route
                  path="/chat"
                  element={
                    <ErrorBoundary name="VARUNA AI Copilot">
                      <ChatAssistantView
                        onSelectScenario={executeScenario}
                        onChangeView={setActiveView}
                        currentResponse={response}
                      />
                    </ErrorBoundary>
                  }
                />

                {/* 5. Agentic Reasoning */}
                <Route
                  path="/reasoning"
                  element={
                    <ErrorBoundary name="Agentic Reasoning">
                      <AgenticReasoningView response={response} />
                    </ErrorBoundary>
                  }
                />

                {/* 6. Active Alerts */}
                <Route
                  path="/alerts"
                  element={
                    <ErrorBoundary name="Active Alerts">
                      <ActiveAlertsView
                        response={response}
                        onSelectScenario={(scenarioId) => {
                          setActiveView('map');
                          executeScenario(scenarioId);
                        }}
                      />
                    </ErrorBoundary>
                  }
                />

                {/* 7. Fleet Operations */}
                <Route
                  path="/fleet"
                  element={
                    <ErrorBoundary name="Fleet Operations">
                      <FleetOpsView />
                    </ErrorBoundary>
                  }
                />

                {/* 8. Fishery Trends & Environmental Analytics */}
                <Route
                  path="/trends"
                  element={
                    <ErrorBoundary name="Fishery Analytics">
                      <HistoricalTrendsView />
                    </ErrorBoundary>
                  }
                />

                {/* Fallback route */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
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

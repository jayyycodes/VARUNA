import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserResponseV1 } from '../contracts/userResponse';

export interface AppStore {
  // Query & Data state
  response: UserResponseV1 | null;
  loading: boolean;
  error: string | null;
  activeQuery: string | null;
  activeScenarioId: string | null;

  // UI selection state
  selectedEvidenceId: string | null;
  selectedClaimId: string | null;
  selectedFeatureId: string | null;

  // Panel toggles
  bottomSheetOpen: boolean;
  railCollapsed: boolean;
  sidebarCollapsed: boolean;

  // Persona / Mode
  mode: 'fisherman' | 'command';

  // Actions
  setResponse: (r: UserResponseV1 | null) => void;
  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
  setActiveQuery: (q: string | null) => void;
  setActiveScenarioId: (id: string | null) => void;
  setSelectedEvidenceId: (id: string | null) => void;
  setSelectedClaimId: (id: string | null) => void;
  setSelectedFeatureId: (id: string | null) => void;
  setBottomSheetOpen: (v: boolean) => void;
  setRailCollapsed: (v: boolean) => void;
  setSidebarCollapsed: (v: boolean) => void;
  toggleMode: () => void;
  setMode: (m: 'fisherman' | 'command') => void;
  clearSelection: () => void;
}

export const useAppStore = create<AppStore>()(
  persist(
    (set, get) => ({
      response: null,
      loading: false,
      error: null,
      activeQuery: null,
      activeScenarioId: 'safe_complete',
      selectedEvidenceId: null,
      selectedClaimId: null,
      selectedFeatureId: null,
      bottomSheetOpen: false,
      railCollapsed: false,
      sidebarCollapsed: false,
      mode: 'command',

      setResponse: (r) => set({ response: r }),
      setLoading: (v) => set({ loading: v }),
      setError: (e) => set({ error: e }),
      setActiveQuery: (q) => set({ activeQuery: q }),
      setActiveScenarioId: (id) => set({ activeScenarioId: id }),
      setSelectedEvidenceId: (id) => set({ selectedEvidenceId: id }),
      setSelectedClaimId: (id) => set({ selectedClaimId: id }),
      setSelectedFeatureId: (id) => set({ selectedFeatureId: id }),
      setBottomSheetOpen: (v) => set({ bottomSheetOpen: v }),
      setRailCollapsed: (v) => set({ railCollapsed: v }),
      setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),
      toggleMode: () => set({ mode: get().mode === 'fisherman' ? 'command' : 'fisherman' }),
      setMode: (m) => set({ mode: m }),
      clearSelection: () =>
        set({
          selectedEvidenceId: null,
          selectedClaimId: null,
          selectedFeatureId: null,
          activeQuery: null,
        }),
    }),
    {
      name: 'varuna-app-store',
      partialize: (s) => ({
        mode: s.mode,
        sidebarCollapsed: s.sidebarCollapsed,
        railCollapsed: s.railCollapsed,
      }),
    }
  )
);

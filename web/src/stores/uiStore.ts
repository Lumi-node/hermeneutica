import { create } from 'zustand';

interface UIState {
  filterPanelOpen: boolean;
  detailPanelOpen: boolean;
  legendPanelOpen: boolean;
  searchPanelOpen: boolean;
  toggleFilterPanel: () => void;
  toggleDetailPanel: () => void;
  toggleLegendPanel: () => void;
  toggleSearchPanel: () => void;

  tooltipText: string;
  tooltipPosition: { x: number; y: number } | null;
  setTooltip: (text: string, pos: { x: number; y: number } | null) => void;

  isLoading: boolean;
  loadingMessage: string;
  setLoading: (loading: boolean, message?: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  filterPanelOpen: true,
  detailPanelOpen: false,
  legendPanelOpen: true,
  searchPanelOpen: false,
  toggleFilterPanel: () => set((s) => ({ filterPanelOpen: !s.filterPanelOpen })),
  toggleDetailPanel: () => set((s) => ({ detailPanelOpen: !s.detailPanelOpen })),
  toggleLegendPanel: () => set((s) => ({ legendPanelOpen: !s.legendPanelOpen })),
  toggleSearchPanel: () => set((s) => ({ searchPanelOpen: !s.searchPanelOpen })),

  tooltipText: '',
  tooltipPosition: null,
  setTooltip: (text, pos) => set({ tooltipText: text, tooltipPosition: pos }),

  isLoading: false,
  loadingMessage: '',
  setLoading: (loading, message = '') => set({ isLoading: loading, loadingMessage: message }),
}));

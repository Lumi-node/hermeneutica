import { create } from 'zustand';
import type { SceneId, ColorBy, SizeBy } from '@/types/scene';
import type { CrossRefArc } from '@/types/crossref';

interface SceneState {
  activeScene: SceneId;
  setActiveScene: (scene: SceneId) => void;

  selectedNodeType: 'verse' | 'strongs' | 'theme' | null;
  selectedNodeId: number | null;
  selectNode: (type: 'verse' | 'strongs' | 'theme' | null, id: number | null) => void;

  hoveredIndex: number | null;
  setHoveredIndex: (index: number | null) => void;

  cameraTarget: [number, number, number] | null;
  setCameraTarget: (pos: [number, number, number] | null) => void;

  colorBy: ColorBy;
  sizeBy: SizeBy;
  setColorBy: (mode: ColorBy) => void;
  setSizeBy: (mode: SizeBy) => void;

  // Cross-reference overlay
  overlayArcs: CrossRefArc[];
  overlayColor: string;
  setOverlay: (arcs: CrossRefArc[], color: string) => void;
  clearOverlay: () => void;
}

export const useSceneStore = create<SceneState>((set) => ({
  activeScene: 'galaxy',
  setActiveScene: (scene) => set({ activeScene: scene, selectedNodeType: null, selectedNodeId: null }),

  selectedNodeType: null,
  selectedNodeId: null,
  selectNode: (type, id) => set({ selectedNodeType: type, selectedNodeId: id }),

  hoveredIndex: null,
  setHoveredIndex: (index) => set({ hoveredIndex: index }),

  cameraTarget: null,
  setCameraTarget: (pos) => set({ cameraTarget: pos }),

  colorBy: 'book',
  sizeBy: 'uniform',
  setColorBy: (mode) => set({ colorBy: mode }),
  setSizeBy: (mode) => set({ sizeBy: mode }),

  overlayArcs: [],
  overlayColor: '#FFD700',
  setOverlay: (arcs, color) => set({ overlayArcs: arcs, overlayColor: color }),
  clearOverlay: () => set({ overlayArcs: [], overlayColor: '#FFD700' }),
}));

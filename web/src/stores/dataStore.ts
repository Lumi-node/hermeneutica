import { create } from 'zustand';
import { apiFetchBinary } from '@/api/client';
import { parseVerseBulk, parseStrongsBulk } from '@/lib/geometry';
import type { GraphNode, GraphEdge } from '@/types/graph';
import type { BookMatrixEntry } from '@/types/crossref';

interface VerseData {
  verseIds: Int32Array;
  positions: Float32Array;
  metadata: Uint8Array;
  ethicsMax: Float32Array;
  count: number;
  loaded: boolean;
}

interface StrongsData {
  strongsIds: Int32Array;
  positions: Float32Array;
  languages: Uint8Array;
  posIds: Uint8Array;
  usageCounts: Uint16Array;
  count: number;
  loaded: boolean;
}

interface DataState {
  versePoints: VerseData | null;
  loadVersePoints: () => Promise<void>;

  strongsPoints: StrongsData | null;
  loadStrongsPoints: () => Promise<void>;

  bookMatrix: BookMatrixEntry[] | null;
  loadBookMatrix: () => Promise<void>;

  graphData: {
    nodes: GraphNode[];
    edges: GraphEdge[];
    centerNodeId: string;
  } | null;
  setGraphData: (data: DataState['graphData']) => void;
}

export const useDataStore = create<DataState>((set, get) => ({
  versePoints: null,
  loadVersePoints: async () => {
    if (get().versePoints?.loaded) return;
    const buffer = await apiFetchBinary('/data/verses_bulk.bin');
    const parsed = parseVerseBulk(buffer);
    set({ versePoints: { ...parsed, loaded: true } });
  },

  strongsPoints: null,
  loadStrongsPoints: async () => {
    if (get().strongsPoints?.loaded) return;
    const buffer = await apiFetchBinary('/data/strongs_bulk.bin');
    const parsed = parseStrongsBulk(buffer);
    set({ strongsPoints: { ...parsed, loaded: true } });
  },

  bookMatrix: null,
  loadBookMatrix: async () => {
    if (get().bookMatrix) return;
    const res = await fetch('/data/book_matrix.json');
    const data = await res.json();
    set({ bookMatrix: data });
  },

  graphData: null,
  setGraphData: (data) => set({ graphData: data }),
}));

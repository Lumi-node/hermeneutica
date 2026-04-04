import { create } from 'zustand';

interface FilterState {
  testamentFilter: 'all' | 'OT' | 'NT';
  bookFilter: number[];
  setTestamentFilter: (t: FilterState['testamentFilter']) => void;
  toggleBook: (bookId: number) => void;
  clearBookFilter: () => void;

  genreFilter: string[];
  toggleGenre: (genre: string) => void;

  themeFilter: string[];
  toggleTheme: (theme: string) => void;

  edgeTypeFilter: string[];
  toggleEdgeType: (edgeType: string) => void;
  minWeight: number;
  setMinWeight: (w: number) => void;
  graphHops: number;
  setGraphHops: (h: number) => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  testamentFilter: 'all',
  bookFilter: [],
  setTestamentFilter: (t) => set({ testamentFilter: t }),
  toggleBook: (bookId) => set((s) => ({
    bookFilter: s.bookFilter.includes(bookId)
      ? s.bookFilter.filter((id) => id !== bookId)
      : [...s.bookFilter, bookId],
  })),
  clearBookFilter: () => set({ bookFilter: [] }),

  genreFilter: [],
  toggleGenre: (genre) => set((s) => ({
    genreFilter: s.genreFilter.includes(genre)
      ? s.genreFilter.filter((g) => g !== genre)
      : [...s.genreFilter, genre],
  })),

  themeFilter: [],
  toggleTheme: (theme) => set((s) => ({
    themeFilter: s.themeFilter.includes(theme)
      ? s.themeFilter.filter((t) => t !== theme)
      : [...s.themeFilter, theme],
  })),

  edgeTypeFilter: [],
  toggleEdgeType: (et) => set((s) => ({
    edgeTypeFilter: s.edgeTypeFilter.includes(et)
      ? s.edgeTypeFilter.filter((e) => e !== et)
      : [...s.edgeTypeFilter, et],
  })),
  minWeight: 0.0,
  setMinWeight: (w) => set({ minWeight: w }),
  graphHops: 1,
  setGraphHops: (h) => set({ graphHops: h }),
}));

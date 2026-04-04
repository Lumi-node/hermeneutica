export type SceneId = 'intro' | 'galaxy' | 'graph' | 'words' | 'crossref' | 'research' | 'journal';

export type ColorBy = 'book' | 'testament' | 'genre' | 'theme' | 'ethics';

export type SizeBy = 'uniform' | 'crossrefs' | 'ethics';

export interface BookMeta {
  id: number;
  name: string;
  abbreviation: string;
  testament: 'OT' | 'NT';
  genre: string;
  chapterCount: number;
}

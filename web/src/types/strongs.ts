export interface StrongsPoint {
  strongsId: number;
  strongsNumber: string;
  x: number;
  y: number;
  z: number;
  language: 'heb' | 'grc';
  partOfSpeech: string | null;
  usageCount: number;
  hasTwot: boolean;
}

export interface StrongsDetail {
  strongsId: number;
  strongsNumber: string;
  language: string;
  originalWord: string;
  transliteration: string;
  pronunciation: string | null;
  rootDefinition: string;
  detailedDefinition: string;
  kjvUsage: string | null;
  partOfSpeech: string | null;
  rootStrongs: string | null;
  usageCount: number;
  sampleVerses: StrongsVerseRef[];
}

export interface StrongsVerseRef {
  verseId: number;
  reference: string;
  englishGloss: string;
  textPreview: string;
}

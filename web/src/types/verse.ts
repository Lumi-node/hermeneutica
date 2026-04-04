export interface VersePoint {
  verseId: number;
  x: number;
  y: number;
  z: number;
  bookId: number;
  chapterNumber: number;
  verseNumber: number;
  crossRefCount: number;
  testament: 'OT' | 'NT';
  genre: string;
  ethicsMaxScore: number;
}

export interface VerseDetail {
  verseId: number;
  bookName: string;
  bookAbbreviation: string;
  chapterNumber: number;
  verseNumber: number;
  testament: string;
  text: string;
  crossRefCount: number;
  topics: string[];
  wordAlignments: WordAlignment[];
  crossReferences: CrossRefBrief[];
}

export interface WordAlignment {
  wordPosition: number;
  originalWord: string;
  transliteration: string;
  englishGloss: string;
  strongsNumber: string;
  morphologyCode: string | null;
  rootDefinition: string;
}

export interface CrossRefBrief {
  verseId: number;
  reference: string;
  relevanceScore: number;
  textPreview: string;
}

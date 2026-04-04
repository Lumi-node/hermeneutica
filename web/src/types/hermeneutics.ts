export interface Classification {
  chapterId: number;
  bookName: string;
  chapterNumber: number;
  genre: string;
  genreConfidence: number;
  themes: string[];
  teachingType: string;
  ethicsReasoning: string;
  ethicsScores: Record<string, number>;
  principles: string[];
}

export interface PrincipleBrief {
  principleId: number;
  principleText: string;
  bookName: string;
  chapterNumber: number;
  genre: string;
  themes: string[];
}

export type EthicsSubset =
  | 'commonsense'
  | 'deontology'
  | 'justice'
  | 'virtue'
  | 'utilitarianism';

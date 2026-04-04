import type { BookMeta } from '@/types/scene';

export const GENRES = [
  'Law', 'History', 'Wisdom', 'Prophecy', 'Gospel', 'Epistle', 'Apocalyptic',
] as const;

export const GENRE_INDEX: Record<string, number> = Object.fromEntries(
  GENRES.map((g, i) => [g, i])
);

export const EDGE_TYPES = [
  'cross_ref', 'twot_family', 'nave_topic', 'nave_shared', 'semantic_sim', 'strongs_sim',
] as const;

export const ETHICS_SUBSETS = [
  'commonsense', 'deontology', 'justice', 'virtue', 'utilitarianism',
] as const;

export const BOOKS: BookMeta[] = [
  { id: 1,  name: 'Genesis',       abbreviation: 'Gen',   testament: 'OT', genre: 'Law',         chapterCount: 50 },
  { id: 2,  name: 'Exodus',        abbreviation: 'Exod',  testament: 'OT', genre: 'Law',         chapterCount: 40 },
  { id: 3,  name: 'Leviticus',     abbreviation: 'Lev',   testament: 'OT', genre: 'Law',         chapterCount: 27 },
  { id: 4,  name: 'Numbers',       abbreviation: 'Num',   testament: 'OT', genre: 'Law',         chapterCount: 36 },
  { id: 5,  name: 'Deuteronomy',   abbreviation: 'Deut',  testament: 'OT', genre: 'Law',         chapterCount: 34 },
  { id: 6,  name: 'Joshua',        abbreviation: 'Josh',  testament: 'OT', genre: 'History',     chapterCount: 24 },
  { id: 7,  name: 'Judges',        abbreviation: 'Judg',  testament: 'OT', genre: 'History',     chapterCount: 21 },
  { id: 8,  name: 'Ruth',          abbreviation: 'Ruth',  testament: 'OT', genre: 'History',     chapterCount: 4 },
  { id: 9,  name: '1 Samuel',      abbreviation: '1Sam',  testament: 'OT', genre: 'History',     chapterCount: 31 },
  { id: 10, name: '2 Samuel',      abbreviation: '2Sam',  testament: 'OT', genre: 'History',     chapterCount: 24 },
  { id: 11, name: '1 Kings',       abbreviation: '1Kgs',  testament: 'OT', genre: 'History',     chapterCount: 22 },
  { id: 12, name: '2 Kings',       abbreviation: '2Kgs',  testament: 'OT', genre: 'History',     chapterCount: 25 },
  { id: 13, name: '1 Chronicles',  abbreviation: '1Chr',  testament: 'OT', genre: 'History',     chapterCount: 29 },
  { id: 14, name: '2 Chronicles',  abbreviation: '2Chr',  testament: 'OT', genre: 'History',     chapterCount: 36 },
  { id: 15, name: 'Ezra',          abbreviation: 'Ezra',  testament: 'OT', genre: 'History',     chapterCount: 10 },
  { id: 16, name: 'Nehemiah',      abbreviation: 'Neh',   testament: 'OT', genre: 'History',     chapterCount: 13 },
  { id: 17, name: 'Esther',        abbreviation: 'Esth',  testament: 'OT', genre: 'History',     chapterCount: 10 },
  { id: 18, name: 'Job',           abbreviation: 'Job',   testament: 'OT', genre: 'Wisdom',      chapterCount: 42 },
  { id: 19, name: 'Psalms',        abbreviation: 'Ps',    testament: 'OT', genre: 'Wisdom',      chapterCount: 150 },
  { id: 20, name: 'Proverbs',      abbreviation: 'Prov',  testament: 'OT', genre: 'Wisdom',      chapterCount: 31 },
  { id: 21, name: 'Ecclesiastes',  abbreviation: 'Eccl',  testament: 'OT', genre: 'Wisdom',      chapterCount: 12 },
  { id: 22, name: 'Song of Solomon', abbreviation: 'Song', testament: 'OT', genre: 'Wisdom',     chapterCount: 8 },
  { id: 23, name: 'Isaiah',        abbreviation: 'Isa',   testament: 'OT', genre: 'Prophecy',    chapterCount: 66 },
  { id: 24, name: 'Jeremiah',      abbreviation: 'Jer',   testament: 'OT', genre: 'Prophecy',    chapterCount: 52 },
  { id: 25, name: 'Lamentations',  abbreviation: 'Lam',   testament: 'OT', genre: 'Prophecy',    chapterCount: 5 },
  { id: 26, name: 'Ezekiel',       abbreviation: 'Ezek',  testament: 'OT', genre: 'Prophecy',    chapterCount: 48 },
  { id: 27, name: 'Daniel',        abbreviation: 'Dan',   testament: 'OT', genre: 'Prophecy',    chapterCount: 12 },
  { id: 28, name: 'Hosea',         abbreviation: 'Hos',   testament: 'OT', genre: 'Prophecy',    chapterCount: 14 },
  { id: 29, name: 'Joel',          abbreviation: 'Joel',  testament: 'OT', genre: 'Prophecy',    chapterCount: 3 },
  { id: 30, name: 'Amos',          abbreviation: 'Amos',  testament: 'OT', genre: 'Prophecy',    chapterCount: 9 },
  { id: 31, name: 'Obadiah',       abbreviation: 'Obad',  testament: 'OT', genre: 'Prophecy',    chapterCount: 1 },
  { id: 32, name: 'Jonah',         abbreviation: 'Jonah', testament: 'OT', genre: 'Prophecy',    chapterCount: 4 },
  { id: 33, name: 'Micah',         abbreviation: 'Mic',   testament: 'OT', genre: 'Prophecy',    chapterCount: 7 },
  { id: 34, name: 'Nahum',         abbreviation: 'Nah',   testament: 'OT', genre: 'Prophecy',    chapterCount: 3 },
  { id: 35, name: 'Habakkuk',      abbreviation: 'Hab',   testament: 'OT', genre: 'Prophecy',    chapterCount: 3 },
  { id: 36, name: 'Zephaniah',     abbreviation: 'Zeph',  testament: 'OT', genre: 'Prophecy',    chapterCount: 3 },
  { id: 37, name: 'Haggai',        abbreviation: 'Hag',   testament: 'OT', genre: 'Prophecy',    chapterCount: 2 },
  { id: 38, name: 'Zechariah',     abbreviation: 'Zech',  testament: 'OT', genre: 'Prophecy',    chapterCount: 14 },
  { id: 39, name: 'Malachi',       abbreviation: 'Mal',   testament: 'OT', genre: 'Prophecy',    chapterCount: 4 },
  { id: 40, name: 'Matthew',       abbreviation: 'Matt',  testament: 'NT', genre: 'Gospel',      chapterCount: 28 },
  { id: 41, name: 'Mark',          abbreviation: 'Mark',  testament: 'NT', genre: 'Gospel',      chapterCount: 16 },
  { id: 42, name: 'Luke',          abbreviation: 'Luke',  testament: 'NT', genre: 'Gospel',      chapterCount: 24 },
  { id: 43, name: 'John',          abbreviation: 'John',  testament: 'NT', genre: 'Gospel',      chapterCount: 21 },
  { id: 44, name: 'Acts',          abbreviation: 'Acts',  testament: 'NT', genre: 'History',     chapterCount: 28 },
  { id: 45, name: 'Romans',        abbreviation: 'Rom',   testament: 'NT', genre: 'Epistle',     chapterCount: 16 },
  { id: 46, name: '1 Corinthians', abbreviation: '1Cor',  testament: 'NT', genre: 'Epistle',     chapterCount: 16 },
  { id: 47, name: '2 Corinthians', abbreviation: '2Cor',  testament: 'NT', genre: 'Epistle',     chapterCount: 13 },
  { id: 48, name: 'Galatians',     abbreviation: 'Gal',   testament: 'NT', genre: 'Epistle',     chapterCount: 6 },
  { id: 49, name: 'Ephesians',     abbreviation: 'Eph',   testament: 'NT', genre: 'Epistle',     chapterCount: 6 },
  { id: 50, name: 'Philippians',   abbreviation: 'Phil',  testament: 'NT', genre: 'Epistle',     chapterCount: 4 },
  { id: 51, name: 'Colossians',    abbreviation: 'Col',   testament: 'NT', genre: 'Epistle',     chapterCount: 4 },
  { id: 52, name: '1 Thessalonians', abbreviation: '1Thess', testament: 'NT', genre: 'Epistle',  chapterCount: 5 },
  { id: 53, name: '2 Thessalonians', abbreviation: '2Thess', testament: 'NT', genre: 'Epistle',  chapterCount: 3 },
  { id: 54, name: '1 Timothy',     abbreviation: '1Tim',  testament: 'NT', genre: 'Epistle',     chapterCount: 6 },
  { id: 55, name: '2 Timothy',     abbreviation: '2Tim',  testament: 'NT', genre: 'Epistle',     chapterCount: 4 },
  { id: 56, name: 'Titus',         abbreviation: 'Titus', testament: 'NT', genre: 'Epistle',     chapterCount: 3 },
  { id: 57, name: 'Philemon',      abbreviation: 'Phlm',  testament: 'NT', genre: 'Epistle',     chapterCount: 1 },
  { id: 58, name: 'Hebrews',       abbreviation: 'Heb',   testament: 'NT', genre: 'Epistle',     chapterCount: 13 },
  { id: 59, name: 'James',         abbreviation: 'Jas',   testament: 'NT', genre: 'Epistle',     chapterCount: 5 },
  { id: 60, name: '1 Peter',       abbreviation: '1Pet',  testament: 'NT', genre: 'Epistle',     chapterCount: 5 },
  { id: 61, name: '2 Peter',       abbreviation: '2Pet',  testament: 'NT', genre: 'Epistle',     chapterCount: 3 },
  { id: 62, name: '1 John',        abbreviation: '1John', testament: 'NT', genre: 'Epistle',     chapterCount: 5 },
  { id: 63, name: '2 John',        abbreviation: '2John', testament: 'NT', genre: 'Epistle',     chapterCount: 1 },
  { id: 64, name: '3 John',        abbreviation: '3John', testament: 'NT', genre: 'Epistle',     chapterCount: 1 },
  { id: 65, name: 'Jude',          abbreviation: 'Jude',  testament: 'NT', genre: 'Epistle',     chapterCount: 1 },
  { id: 66, name: 'Revelation',    abbreviation: 'Rev',   testament: 'NT', genre: 'Apocalyptic', chapterCount: 22 },
];

export const BOOK_BY_ID = new Map(BOOKS.map(b => [b.id, b]));

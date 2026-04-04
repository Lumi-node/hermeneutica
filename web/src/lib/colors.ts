/** HSL to RGB (all in 0-1 range) */
function hslToRgb(h: number, s: number, l: number): [number, number, number] {
  const a = s * Math.min(l, 1 - l);
  const f = (n: number) => {
    const k = (n + h / 30) % 12;
    return l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
  };
  return [f(0), f(8), f(4)];
}

/** 66-color palette for books using HSL rotation */
export function bookColor(bookId: number): [number, number, number] {
  const hue = ((bookId - 1) / 66) * 360;
  const sat = 0.65 + (bookId % 3) * 0.1;
  const light = 0.55;
  return hslToRgb(hue, sat, light);
}

/** Testament: OT = warm amber, NT = cool blue */
export function testamentColor(testament: 'OT' | 'NT'): [number, number, number] {
  return testament === 'OT' ? [0.85, 0.65, 0.3] : [0.3, 0.55, 0.85];
}

/** Genre: 7 distinct hues */
export const GENRE_COLORS: Record<string, [number, number, number]> = {
  'Law':         [0.90, 0.45, 0.35],
  'History':     [0.85, 0.70, 0.35],
  'Wisdom':      [0.95, 0.85, 0.40],
  'Prophecy':    [0.50, 0.75, 0.45],
  'Gospel':      [0.35, 0.60, 0.85],
  'Epistle':     [0.55, 0.45, 0.80],
  'Apocalyptic': [0.75, 0.35, 0.65],
};

/** Edge type colors */
export const EDGE_TYPE_COLORS: Record<string, string> = {
  'cross_ref':    '#4A90D9',
  'twot_family':  '#E8A838',
  'nave_topic':   '#50C878',
  'nave_shared':  '#7B68EE',
  'semantic_sim': '#FF6B6B',
  'strongs_sim':  '#DDA0DD',
};

/** Language colors for Strong's constellation */
export const LANGUAGE_COLORS: Record<string, [number, number, number]> = {
  'heb': [0.85, 0.60, 0.30],
  'grc': [0.30, 0.55, 0.85],
};

/** Ethics subset to a distinct color */
export const ETHICS_COLORS: Record<string, string> = {
  'commonsense':    '#4FC3F7',
  'deontology':     '#FFB74D',
  'justice':        '#81C784',
  'virtue':         '#BA68C8',
  'utilitarianism': '#FF8A65',
};

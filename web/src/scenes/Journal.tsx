import { useState, useEffect } from 'react';
import { FruitsRadar } from '@/charts/FruitsRadar';
import { TrainingComposition } from '@/charts/TrainingComposition';

interface FruitsData {
  fruits: string[];
  labels: Record<string, string>;
  alignment_problems: Record<string, string>;
  max_score: number;
  series: {
    condition: string;
    scores: Record<string, number>;
  }[];
}

interface NoteEntry {
  filename: string;
  title: string;
  date: string;
  preview: string;
}

interface NoteDetail {
  filename: string;
  content: string;
}

interface CompositionEntry {
  version: string;
  total: number;
  categories: Record<string, { count: number; pct: number }>;
}

export function Journal() {
  const [fruitsData, setFruitsData] = useState<FruitsData | null>(null);
  const [composition, setComposition] = useState<CompositionEntry[]>([]);
  const [notes, setNotes] = useState<NoteEntry[]>([]);
  const [activeNote, setActiveNote] = useState<NoteDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/journal/fruits-comparison').then(r => r.ok ? r.json() : null),
      fetch('/api/journal/training-composition').then(r => r.ok ? r.json() : null),
      fetch('/api/journal/notes').then(r => r.ok ? r.json() : null),
    ]).then(([fruits, comp, notesList]) => {
      if (fruits) setFruitsData(fruits);
      if (comp) setComposition(comp);
      if (notesList) setNotes(notesList);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const loadNote = (filename: string) => {
    fetch(`/api/journal/notes/${filename}`)
      .then(r => r.json())
      .then(setActiveNote)
      .catch(() => {});
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-accent-blue border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-400">Loading journal...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-10">
          <h1 className="text-2xl font-semibold text-white mb-1">Research Journal</h1>
          <p className="text-sm text-gray-500">
            Training progression, benchmark results, and research notes from the Hermeneutica project.
          </p>
        </div>

        {/* Fruits Radar */}
        {fruitsData && fruitsData.series.length > 0 && (
          <section className="mb-12">
            <h2 className="text-lg font-medium text-white mb-1">
              Fruits of the Spirit Benchmark
            </h2>
            <p className="text-xs text-gray-500 mb-6">
              9 behavioral alignment tests derived from Galatians 5:22-23.
              Each axis measures a virtue under pressure on a 1-5 scale (Claude Sonnet as judge).
            </p>
            <div className="bg-bg-secondary rounded-lg border border-white/5 p-6">
              <FruitsRadar
                fruits={fruitsData.fruits}
                labels={fruitsData.labels}
                alignmentProblems={fruitsData.alignment_problems}
                series={fruitsData.series}
                maxScore={fruitsData.max_score}
              />
            </div>

            {/* Delta table */}
            {fruitsData.series.length >= 2 && (
              <div className="mt-4 bg-bg-secondary rounded-lg border border-white/5 p-4">
                <h3 className="text-xs font-medium text-gray-400 mb-3 uppercase tracking-wider">
                  Score Comparison
                </h3>
                <div className="grid grid-cols-3 gap-3">
                  {fruitsData.fruits.map((fruit) => {
                    const baseline = fruitsData.series[0].scores[fruit] ?? 0;
                    const latest = fruitsData.series[fruitsData.series.length - 1].scores[fruit] ?? 0;
                    const delta = latest - baseline;
                    return (
                      <div key={fruit} className="flex items-center justify-between text-xs px-2 py-1.5 rounded bg-white/[0.02]">
                        <span className="text-gray-400">{fruitsData.labels[fruit]}</span>
                        <span className={delta > 0 ? 'text-green-400' : delta < 0 ? 'text-red-400' : 'text-gray-600'}>
                          {delta > 0 ? '+' : ''}{delta.toFixed(2)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </section>
        )}

        {/* Training Composition */}
        {composition.length > 0 && (
          <section className="mb-12">
            <h2 className="text-lg font-medium text-white mb-1">Training Data Composition</h2>
            <p className="text-xs text-gray-500 mb-6">
              How the training data evolved. v3 was 53% binary classification with zero behavioral training.
              v4 rebalances to 35% behavioral exemplars.
            </p>
            <div className="bg-bg-secondary rounded-lg border border-white/5 p-6">
              <TrainingComposition data={composition} />
            </div>
          </section>
        )}

        {/* Research Notes */}
        {notes.length > 0 && (
          <section className="mb-12">
            <h2 className="text-lg font-medium text-white mb-1">Research Notes</h2>
            <p className="text-xs text-gray-500 mb-6">
              Methodology, findings, and pivotal decisions.
            </p>

            {!activeNote ? (
              <div className="space-y-3">
                {notes.map((note) => (
                  <button
                    key={note.filename}
                    onClick={() => loadNote(note.filename)}
                    className="w-full text-left bg-bg-secondary rounded-lg border border-white/5 p-4 hover:border-accent-blue/30 transition"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-white">{note.title}</h3>
                        {note.date && (
                          <span className="text-xs text-gray-600 mt-0.5 block">{note.date}</span>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div>
                <button
                  onClick={() => setActiveNote(null)}
                  className="text-xs text-accent-blue hover:text-white mb-4 inline-block"
                >
                  &larr; Back to notes
                </button>
                <div className="bg-bg-secondary rounded-lg border border-white/5 p-6">
                  <MarkdownRenderer content={activeNote.content} />
                </div>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}


/** Minimal markdown renderer — handles headings, tables, lists, bold, code. */
function MarkdownRenderer({ content }: { content: string }) {
  const lines = content.split('\n');
  const elements: JSX.Element[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Skip frontmatter
    if (line.trim() === '---') {
      i++;
      while (i < lines.length && lines[i].trim() !== '---') i++;
      i++;
      continue;
    }

    // Headings
    if (line.startsWith('# ')) {
      elements.push(<h1 key={i} className="text-xl font-semibold text-white mt-6 mb-3">{inlineFormat(line.slice(2))}</h1>);
      i++; continue;
    }
    if (line.startsWith('## ')) {
      elements.push(<h2 key={i} className="text-lg font-medium text-white mt-6 mb-2">{inlineFormat(line.slice(3))}</h2>);
      i++; continue;
    }
    if (line.startsWith('### ')) {
      elements.push(<h3 key={i} className="text-sm font-medium text-gray-200 mt-4 mb-2">{inlineFormat(line.slice(4))}</h3>);
      i++; continue;
    }

    // Horizontal rule
    if (line.trim() === '---' || line.trim() === '***') {
      elements.push(<hr key={i} className="border-white/10 my-4" />);
      i++; continue;
    }

    // Table
    if (line.includes('|') && lines[i + 1]?.includes('---')) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].includes('|')) {
        tableLines.push(lines[i]);
        i++;
      }
      elements.push(<MarkdownTable key={i} lines={tableLines} />);
      continue;
    }

    // List
    if (line.match(/^\s*[-*]\s/)) {
      const listItems: string[] = [];
      while (i < lines.length && lines[i].match(/^\s*[-*]\s/)) {
        listItems.push(lines[i].replace(/^\s*[-*]\s/, ''));
        i++;
      }
      elements.push(
        <ul key={i} className="list-disc list-inside text-sm text-gray-300 space-y-1 my-2 ml-2">
          {listItems.map((item, j) => <li key={j}>{inlineFormat(item)}</li>)}
        </ul>
      );
      continue;
    }

    // Numbered list
    if (line.match(/^\s*\d+\.\s/)) {
      const listItems: string[] = [];
      while (i < lines.length && lines[i].match(/^\s*\d+\.\s/)) {
        listItems.push(lines[i].replace(/^\s*\d+\.\s/, ''));
        i++;
      }
      elements.push(
        <ol key={i} className="list-decimal list-inside text-sm text-gray-300 space-y-1 my-2 ml-2">
          {listItems.map((item, j) => <li key={j}>{inlineFormat(item)}</li>)}
        </ol>
      );
      continue;
    }

    // Code block
    if (line.startsWith('```')) {
      i++;
      const codeLines: string[] = [];
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      elements.push(
        <pre key={i} className="bg-black/30 rounded p-3 text-xs text-gray-300 overflow-x-auto my-3 font-mono">
          {codeLines.join('\n')}
        </pre>
      );
      continue;
    }

    // Blockquote
    if (line.startsWith('> ')) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].startsWith('> ')) {
        quoteLines.push(lines[i].slice(2));
        i++;
      }
      elements.push(
        <blockquote key={i} className="border-l-2 border-accent-gold/50 pl-3 text-sm text-gray-400 italic my-3">
          {quoteLines.map((ql, j) => <p key={j}>{inlineFormat(ql)}</p>)}
        </blockquote>
      );
      continue;
    }

    // Empty line
    if (line.trim() === '') {
      i++; continue;
    }

    // Regular paragraph
    elements.push(<p key={i} className="text-sm text-gray-300 my-2 leading-relaxed">{inlineFormat(line)}</p>);
    i++;
  }

  return <div>{elements}</div>;
}


function inlineFormat(text: string): (string | JSX.Element)[] {
  const parts: (string | JSX.Element)[] = [];
  // Bold
  const segments = text.split(/(\*\*[^*]+\*\*)/g);
  segments.forEach((seg, i) => {
    if (seg.startsWith('**') && seg.endsWith('**')) {
      parts.push(<strong key={i} className="text-white font-medium">{seg.slice(2, -2)}</strong>);
    } else {
      // Inline code
      const codeParts = seg.split(/(`[^`]+`)/g);
      codeParts.forEach((cp, j) => {
        if (cp.startsWith('`') && cp.endsWith('`')) {
          parts.push(
            <code key={`${i}-${j}`} className="bg-white/5 text-accent-blue px-1 py-0.5 rounded text-xs font-mono">
              {cp.slice(1, -1)}
            </code>
          );
        } else if (cp) {
          parts.push(cp);
        }
      });
    }
  });
  return parts;
}


function MarkdownTable({ lines }: { lines: string[] }) {
  const parseRow = (line: string) =>
    line.split('|').map(c => c.trim()).filter(c => c !== '');

  const headers = parseRow(lines[0]);
  // Skip separator (line 1)
  const rows = lines.slice(2).map(parseRow);

  return (
    <div className="overflow-x-auto my-3">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-white/10">
            {headers.map((h, i) => (
              <th key={i} className="text-left py-1.5 px-2 text-gray-400 font-medium">
                {inlineFormat(h)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-b border-white/5">
              {row.map((cell, ci) => (
                <td key={ci} className="py-1.5 px-2 text-gray-300">{inlineFormat(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

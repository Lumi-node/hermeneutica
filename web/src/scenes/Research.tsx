import { useSceneStore } from '@/stores/sceneStore';

export function Research() {
  const setActiveScene = useSceneStore(s => s.setActiveScene);

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto px-6 py-12 space-y-10">

        {/* Hero */}
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Can Biblical Ethics Improve AI Alignment?</h1>
          <p className="text-sm text-gray-400 leading-relaxed">
            Hermeneutica is a research project exploring whether structured moral teachings from scripture
            can measurably improve a language model's ethical reasoning. This page documents the methodology,
            pipeline, and results.
          </p>
        </div>

        {/* The Problem */}
        <Section title="The Problem">
          <p>
            Large language models are trained on internet text, which contains moral reasoning that is
            inconsistent, culturally biased, and often contradictory. Current alignment techniques (RLHF,
            constitutional AI) use hand-written rules or human preference data, but these approaches
            lack a coherent ethical framework.
          </p>
          <p>
            The Bible represents one of the most extensively studied, internally cross-referenced, and
            systematically organized moral texts in human history. Can we extract its ethical signal
            and use it to improve model alignment?
          </p>
        </Section>

        {/* The Approach */}
        <Section title="The Approach">
          <p>
            Rather than simply injecting Bible text into training data (which would teach the model
            to *sound* biblical, not *reason* ethically), we built a multi-stage pipeline that extracts,
            structures, and distills moral signal:
          </p>

          <div className="space-y-4 mt-4">
            <Stage number={1} title="Extract & Classify">
              AI classifies each Bible chapter by genre, themes, teaching type, and relevance across
              5 ethical dimensions (commonsense, deontology, justice, virtue, utilitarianism).
              288 chapters classified so far.
            </Stage>

            <Stage number={2} title="Distill Principles">
              From each classified chapter, extract 2-4 actionable moral principles in modern language.
              "Forgiveness must be limitless and flow from genuine mercy, not calculation" (from Matthew 18).
              1,124 principles distilled so far.
            </Stage>

            <Stage number={3} title="Build Knowledge Graph">
              Connect everything: 31K verses, 14K Hebrew/Greek words, 32K topics, 433K cross-references,
              and semantic similarity edges. The result: 549,440 edges encoding the Bible's internal
              moral structure.
            </Stage>

            <Stage number={4} title="Embed in Meaning-Space">
              Qwen3-Embedding-8B converts every verse into a 2,000-dimensional semantic vector.
              Verses with similar meaning cluster together regardless of which book they come from.
              This is what powers the{' '}
              <button onClick={() => setActiveScene('galaxy')} className="text-accent-blue hover:text-white underline">
                Scripture Galaxy
              </button> visualization.
            </Stage>

            <Stage number={5} title="Generate Training Data">
              Use the classified passages, distilled principles, and ethics scores to generate
              scenario-response pairs. Each training example pairs an ethical dilemma with a
              biblically-grounded response, tagged with the relevant ethics dimensions.
            </Stage>

            <Stage number={6} title="Fine-Tune via LoRA">
              QLoRA fine-tuning on Qwen3-4B with the generated training data. Multiple versions
              tested with different data compositions and training strategies.
            </Stage>

            <Stage number={7} title="Evaluate">
              Test on the Hendrycks ETHICS benchmark (5 dimensions: commonsense, deontology, justice,
              virtue, utilitarianism) and a custom "Fruits of the Spirit" alignment benchmark
              measuring 9 biblical virtues across 81 scenarios.
            </Stage>
          </div>
        </Section>

        {/* Results */}
        <Section title="Results So Far">
          <div className="space-y-4">
            <ResultCard
              title="LoRA v3: ETHICS Benchmark"
              result="+9.1% average improvement"
              detail="Balanced training across all 5 ethics dimensions. Eliminates the utilitarianism regression seen in earlier versions. Strongest gains in justice (+14%) and virtue (+12%)."
              status="positive"
            />
            <ResultCard
              title="LoRA v4: Behavioral Training"
              result="+0.23 average over vanilla (Claude-judged)"
              detail="Fruits of the Spirit benchmark: 9 virtues (love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, self-control), 81 scenarios across 3 difficulty tiers."
              status="positive"
            />
            <ResultCard
              title="Key Insight"
              result="Ethical structure matters more than volume"
              detail="Simply adding more Bible text to training hurts performance. But distilling principles, tagging ethics dimensions, and balancing across moral frameworks produces consistent improvements. The structure of the knowledge graph matters."
              status="insight"
            />
          </div>
        </Section>

        {/* The Pipeline Diagram */}
        <Section title="Data Pipeline">
          <div className="bg-white/3 rounded-lg p-4 font-mono text-[10px] text-gray-400 leading-relaxed overflow-x-auto">
            <pre>{`
Raw Sources ──→ ETL Pipeline ──→ PostgreSQL ──→ AI Classification ──→ Training Data ──→ LoRA
     │              │                │                │                    │              │
 KJV text       14 scripts       21 tables      Claude Sonnet      scenario-response   QLoRA
 Strong's       idempotent       549K edges     genre + themes     biblically-grounded  Qwen3-4B
 Cross-refs     bulk insert      pgvector       ethics scores      ethics-tagged         4-bit
 Nave's         psycopg2         HNSW index     1,124 principles   balanced dims
                                     │
                                     ▼
                              Qwen3-Embedding-8B ──→ UMAP ──→ 3D Explorer
                              2,000-dim vectors      3D coords   hermeneutica.xyz
            `}</pre>
          </div>
        </Section>

        {/* What Makes This Different */}
        <Section title="What Makes This Different">
          <div className="grid sm:grid-cols-2 gap-4">
            <DiffCard
              title="Not prompt injection"
              description="We don't paste Bible verses into prompts. We extract structured moral signal and train on it."
            />
            <DiffCard
              title="Not keyword matching"
              description="We use 2000-dim semantic embeddings to understand meaning, not surface-level text similarity."
            />
            <DiffCard
              title="Multi-dimensional ethics"
              description="We measure across 5 moral frameworks, not a single 'good/bad' score. Different ethical traditions inform different dimensions."
            />
            <DiffCard
              title="Reproducible pipeline"
              description="Every step from raw data to trained model is scripted, idempotent, and open-source. The entire knowledge graph is queryable."
            />
          </div>
        </Section>

        {/* Open Questions */}
        <Section title="Open Questions">
          <ul className="space-y-2 text-sm text-gray-400">
            <li className="flex items-start gap-2">
              <span className="text-accent-gold mt-0.5">?</span>
              <span>Does improvement on ETHICS benchmark translate to real-world behavior changes?</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-accent-gold mt-0.5">?</span>
              <span>How does the model handle ethical dilemmas where biblical principles conflict with each other?</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-accent-gold mt-0.5">?</span>
              <span>Can this approach generalize to other moral traditions (Quran, Buddhist texts, philosophical works)?</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-accent-gold mt-0.5">?</span>
              <span>What's the optimal ratio of direct commands vs. narrative examples vs. wisdom literature in training data?</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-accent-gold mt-0.5">?</span>
              <span>Does the Fruits of the Spirit benchmark measure genuine virtue or learned patterns?</span>
            </li>
          </ul>
        </Section>

        {/* CTA */}
        <div className="flex gap-3 pt-4">
          <button
            onClick={() => setActiveScene('journal')}
            className="bg-white/5 hover:bg-white/10 text-white text-sm px-5 py-2.5 rounded-lg border border-white/10 transition"
          >
            View Experiment Journal
          </button>
          <button
            onClick={() => setActiveScene('galaxy')}
            className="bg-accent-blue hover:bg-accent-blue/80 text-white text-sm px-5 py-2.5 rounded-lg transition"
          >
            Explore the Data
          </button>
        </div>

      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-white mb-3">{title}</h2>
      <div className="text-sm text-gray-400 leading-relaxed space-y-3">{children}</div>
    </div>
  );
}

function Stage({ number, title, children }: { number: number; title: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-accent-gold/20 text-accent-gold text-xs flex items-center justify-center font-bold">
        {number}
      </div>
      <div>
        <h4 className="text-sm font-medium text-white">{title}</h4>
        <p className="text-xs text-gray-500 mt-0.5">{children}</p>
      </div>
    </div>
  );
}

function ResultCard({ title, result, detail, status }: { title: string; result: string; detail: string; status: 'positive' | 'insight' }) {
  return (
    <div className={`rounded-lg p-4 border ${
      status === 'positive' ? 'bg-accent-green/5 border-accent-green/20' : 'bg-accent-gold/5 border-accent-gold/20'
    }`}>
      <div className="text-[10px] text-gray-500 uppercase tracking-wider">{title}</div>
      <div className={`text-sm font-semibold mt-1 ${status === 'positive' ? 'text-accent-green' : 'text-accent-gold'}`}>
        {result}
      </div>
      <p className="text-xs text-gray-500 mt-1.5">{detail}</p>
    </div>
  );
}

function DiffCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="bg-white/3 rounded-lg p-3 border border-white/5">
      <h4 className="text-xs font-medium text-white mb-1">{title}</h4>
      <p className="text-[11px] text-gray-500">{description}</p>
    </div>
  );
}

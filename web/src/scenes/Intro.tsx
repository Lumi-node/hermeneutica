import { useSceneStore } from '@/stores/sceneStore';

export function Intro() {
  const setActiveScene = useSceneStore(s => s.setActiveScene);

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto px-6 py-12 space-y-10">

        {/* Hero */}
        <div className="text-center space-y-4">
          <h1 className="text-3xl font-bold text-accent-gold tracking-wide">Hermeneutica</h1>
          <p className="text-lg text-gray-300">
            A 3D interactive explorer for the Bible's internal structure
          </p>
          <p className="text-sm text-gray-500 max-w-lg mx-auto">
            31,102 verses mapped by semantic meaning. 549,000 connections.
            14,298 Hebrew and Greek words. Explore scripture as a living network.
          </p>
          <button
            onClick={() => setActiveScene('galaxy')}
            className="mt-4 bg-accent-blue hover:bg-accent-blue/80 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition"
          >
            Enter the Scripture Galaxy
          </button>
        </div>

        {/* What is this */}
        <Section title="What Am I Looking At?">
          <p>
            Every verse in the King James Bible has been read by an AI language model
            (Qwen3-Embedding-8B) which converts its <em>meaning</em> into a 2,000-dimensional
            mathematical fingerprint. Verses with similar meaning get similar fingerprints.
          </p>
          <p>
            We then compressed those 2,000 dimensions into 3D coordinates using UMAP
            (Uniform Manifold Approximation and Projection), preserving the neighborhood
            relationships. The result: <strong>verses that mean similar things appear near
            each other</strong> in 3D space — regardless of which book, chapter, or testament
            they come from.
          </p>
          <p>
            The shape you see isn't random. It's a literal map of how the Bible's ideas
            relate to each other in meaning-space.
          </p>
        </Section>

        {/* Views */}
        <Section title="How to Explore">
          <div className="grid gap-4 sm:grid-cols-2">
            <ViewCard
              title="Scripture Galaxy"
              icon="✦"
              color="text-accent-gold"
              onClick={() => setActiveScene('galaxy')}
              description="31,102 verses as a 3D point cloud. Color by book, genre, or testament. Click any verse to see its text, Hebrew/Greek interlinear, cross-references, and ethical classification."
            />
            <ViewCard
              title="Knowledge Graph"
              icon="⟁"
              color="text-accent-green"
              onClick={() => setActiveScene('graph')}
              description="Explore the web of connections between verses, themes, and words. 549,000 edges across 6 relationship types — cross-references, shared topics, semantic similarity, and word families."
            />
            <ViewCard
              title="Word Study"
              icon="א"
              color="text-accent-gold"
              onClick={() => setActiveScene('words')}
              description="14,298 Hebrew and Greek lexicon entries (Strong's Concordance) positioned by semantic similarity. See how biblical words cluster by meaning across languages."
            />
            <ViewCard
              title="Cross-References"
              icon="⊞"
              color="text-accent-blue"
              onClick={() => setActiveScene('crossref')}
              description="A 66×66 heatmap showing how densely each book references every other book. See the OT→NT boundary and discover which books are most interconnected."
            />
          </div>
        </Section>

        {/* Cross-reference threads */}
        <Section title="Cross-Reference Threads">
          <p>
            In the Scripture Galaxy, you can activate <strong>Cross-Reference Threads</strong> —
            glowing arcs connecting verses across the Bible. The most stunning:
          </p>
          <ul className="list-none space-y-2 mt-3">
            <li className="flex items-start gap-3">
              <span className="text-yellow-400 text-lg">✦</span>
              <div>
                <strong className="text-yellow-400">OT Promises → NT Fulfillment</strong>
                <span className="text-gray-500"> — 55,000 golden threads showing prophecies made in the Old Testament connected to their fulfillment in the New. The bright center where threads converge reveals where the most prophecy fulfillment concentrates.</span>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-orange-400 text-lg">🔥</span>
              <div>
                <strong className="text-orange-400">Prophets → Gospels</strong>
                <span className="text-gray-500"> — Messianic prophecies from Isaiah, Jeremiah, and the prophetic books connected to their realization in the life of Jesus recorded in Matthew, Mark, Luke, and John.</span>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-purple-400 text-lg">♪</span>
              <div>
                <strong className="text-purple-400">Psalms → New Testament</strong>
                <span className="text-gray-500"> — The prayer book of ancient Israel echoing through the early church — how David's songs became the language of the apostles.</span>
              </div>
            </li>
          </ul>
        </Section>

        {/* Exploration tools */}
        <Section title="Exploration Tools">
          <p>
            At the bottom of the screen, the <strong>Explore</strong> toolbar gives you deeper tools:
          </p>
          <div className="space-y-3 mt-3">
            <ToolInfo
              icon="🔍"
              title="Theme Tracer"
              description="Type a theme (Love, Justice, Faith, Covenant) and trace every verse about it from Genesis to Revelation. See a timeline showing which books discuss it most."
            />
            <ToolInfo
              icon="⛓"
              title="Shortest Path"
              description="Pick any two verses and find how they're connected through the knowledge graph. Discover surprising links — each hop shows why the connection exists (cross-reference, shared topic, semantic similarity, or word family)."
            />
            <ToolInfo
              icon="📖"
              title="Principle Search"
              description="Search distilled moral principles extracted from scripture using AI. Ask 'What does the Bible teach about forgiveness?' and get actionable principles with their source chapter, genre, and ethical reasoning breakdown."
            />
          </div>
        </Section>

        {/* The data */}
        <Section title="The Data Behind This">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <Stat value="31,102" label="KJV verses embedded" />
            <Stat value="549,440" label="knowledge graph edges" />
            <Stat value="432,944" label="cross-references" />
            <Stat value="14,298" label="Hebrew + Greek words" />
            <Stat value="92,609" label="topic-verse mappings" />
            <Stat value="2,000" label="embedding dimensions" />
          </div>
          <p className="mt-4 text-gray-500 text-xs">
            Sources: King James Version text, Strong's Concordance (BDB/Thayer lexicons),
            STEPBible interlinear data (TAHOT + TAGNT), OpenBible.info cross-references
            (Treasury of Scripture Knowledge), Nave's Topical Bible (MetaV), and
            AI-generated classifications using Claude.
          </p>
        </Section>

        {/* About */}
        <Section title="About Hermeneutica">
          <p>
            Hermeneutica is a research project studying how biblical moral teachings
            can be computationally extracted, structured, and explored. The name comes
            from <em>hermeneutics</em> — the art and science of interpretation.
          </p>
          <p>
            This explorer goes beyond surface-level text search. It uses deep
            embeddings to understand <em>meaning</em>, not just keywords. Two verses
            about the same concept will be near each other even if they share no
            common words.
          </p>
          <p className="text-gray-600 text-xs mt-4">
            Built with React Three Fiber, FastAPI, PostgreSQL + pgvector, and
            Qwen3-Embedding-8B. The entire Bible is embedded, indexed, classified, and
            connected in a single knowledge graph.
          </p>
        </Section>

        {/* CTA */}
        <div className="text-center pb-8">
          <button
            onClick={() => setActiveScene('galaxy')}
            className="bg-accent-gold hover:bg-accent-gold/80 text-bg-primary px-8 py-3 rounded-lg text-sm font-semibold transition"
          >
            Start Exploring
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

function ViewCard({ title, icon, color, description, onClick }: {
  title: string; icon: string; color: string; description: string; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="text-left bg-white/3 hover:bg-white/5 border border-white/5 hover:border-white/10 rounded-lg p-4 transition"
    >
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-lg ${color}`}>{icon}</span>
        <h3 className="text-sm font-medium text-white">{title}</h3>
      </div>
      <p className="text-xs text-gray-500 leading-relaxed">{description}</p>
    </button>
  );
}

function ToolInfo({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="flex items-start gap-3">
      <span className="text-base flex-shrink-0">{icon}</span>
      <div>
        <h4 className="text-xs font-medium text-white">{title}</h4>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
    </div>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="bg-white/3 rounded-lg p-3 text-center">
      <div className="text-lg font-bold text-white">{value}</div>
      <div className="text-[10px] text-gray-500 mt-0.5">{label}</div>
    </div>
  );
}

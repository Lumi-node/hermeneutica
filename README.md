# Hermeneutica

A 3D interactive explorer for the Bible's internal structure. 31,102 verses mapped by semantic meaning, connected by 549,000 knowledge graph edges, with 14,298 Hebrew and Greek lexicon entries.

**Live at [hermeneutica.xyz](https://hermeneutica.xyz)**

## What Is This?

Every verse in the King James Bible has been embedded by an AI language model (Qwen3-Embedding-8B) into a 2,000-dimensional vector representing its meaning. UMAP reduces these to 3D coordinates, creating a spatial map where **semantically similar verses cluster together** — regardless of book, chapter, or testament.

The result is a navigable 3D galaxy of scripture, overlaid with 432,944 cross-references, 92,609 topical mappings, and AI-generated ethical classifications.

## Features

- **Scripture Galaxy** — 31K verse point cloud colored by book, genre, or testament. Cross-reference threads (55K golden arcs) show OT-to-NT prophecy fulfillment.
- **Knowledge Graph** — Force-directed 3D graph exploring connections between verses, themes, and words across 6 relationship types.
- **Word Study** — 14,298 Strong's Hebrew/Greek lexicon entries positioned by semantic similarity.
- **Biblical Analytics** — Heatmaps for cross-reference density, topic distribution, ethics landscape, and word frequency across all 66 books.
- **Theme Tracer** — Trace any biblical theme from Genesis to Revelation.
- **Shortest Path** — Find how any two verses connect through the knowledge graph.
- **Principle Search** — Search AI-extracted moral principles from scripture.

## Architecture

```
hermeneutica/
├── web/                    # Web application
│   ├── src/                # React + TypeScript + React Three Fiber frontend
│   ├── api/                # FastAPI backend (Python)
│   │   ├── routers/        # API endpoints
│   │   ├── models/         # Pydantic response models
│   │   └── precompute/     # UMAP + binary export pipeline
│   └── public/data/        # Pre-computed binary data (gitignored)
├── src/                    # Core research library
│   ├── embeddings.py       # Qwen3-Embedding-8B engine
│   ├── knowledge_graph.py  # Graph builder (549K edges)
│   └── hermeneutics.py     # Classification engine
├── etl/                    # Database ETL pipeline
├── sql/                    # PostgreSQL schema
├── training/               # LoRA fine-tuning pipeline
├── eval/                   # Benchmarks
└── research/               # Papers and notes
```

## Quick Start

### Prerequisites

- PostgreSQL 16 with [pgvector](https://github.com/pgvector/pgvector) and pg_trgm extensions
- Python 3.12+
- Node.js 20+

### Database Setup

```bash
# Create database and run schema
sudo -u postgres createdb bible_research
sudo -u postgres psql -d bible_research -f sql/schema.sql

# Run ETL pipeline (idempotent, safe to re-run)
python -m etl.00_init_schema
python -m etl.01_load_translations
python -m etl.02_load_books
python -m etl.03_load_kjv_verses
python -m etl.05_load_strongs
python -m etl.06_load_interlinear
python -m etl.07_load_cross_references
python -m etl.08_load_naves_topical
```

### Generate Embeddings & Graph

```bash
# Embed all verses and Strong's entries (requires GPU)
python -m src.embeddings --all

# Build knowledge graph
python -m src.knowledge_graph --all
```

### Pre-compute Web Data

```bash
# UMAP 3D projections
python -m web.api.precompute.umap_verses
python -m web.api.precompute.umap_strongs
python -m web.api.precompute.book_matrix
python -m web.api.precompute.export_bulk
```

### Run the Web App

```bash
# Backend
pip install -r web/api/requirements.txt
uvicorn web.api.main:app --port 8000

# Frontend
cd web && npm install && npm run dev
```

Visit http://localhost:5173

## Environment Variables

Copy `.env.example` to `.env` and configure:

```
DATABASE_URL=postgresql://user:pass@localhost:5432/bible_research
DATABASE_SSL=false
RESEND_API_KEY=re_...          # Optional: for contact form
```

## Data Sources

- **King James Version** text (public domain)
- **Strong's Concordance** — BDB Hebrew and Thayer Greek lexicons
- **STEPBible** — TAHOT (Hebrew OT) and TAGNT (Greek NT) interlinear data
- **OpenBible.info** — Treasury of Scripture Knowledge cross-references
- **Nave's Topical Bible** — via MetaV project
- **AI Classifications** — Chapter-level genre, theme, and ethics scoring via Claude

## Tech Stack

| Layer | Technology |
|-------|-----------|
| 3D Rendering | React Three Fiber + Three.js |
| Frontend | React 18, TypeScript, Zustand, Tailwind CSS |
| Backend | FastAPI, asyncpg, Pydantic |
| Database | PostgreSQL 16 + pgvector (HNSW indexes) |
| Embeddings | Qwen3-Embedding-8B (2000-dim, Matryoshka) |
| Dimensionality Reduction | UMAP |
| Hosting | Vercel (frontend) + Azure Container Apps (API) + Azure PostgreSQL |

## License

MIT License — see [LICENSE](LICENSE)

## Contact

Made by [Automate Capture, LLC](https://www.automate-capture.com)

- Website: [automate-capture.com](https://www.automate-capture.com)
- LinkedIn: [Andrew Young](https://www.linkedin.com/in/andrew-young-executive)

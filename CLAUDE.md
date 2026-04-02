# Hermeneutica — Biblical Research Lab

## What This Is

A research platform for studying how biblical moral teachings affect LLM ethical reasoning. Goes beyond surface-level text injection to extract, structure, embed, and ultimately train on the *meaning* of scripture — not just the tokens.

## Architecture

### Database: `bible_research` (PostgreSQL 16 + pgvector)

Core tables: `translations`, `books`, `chapters`, `verses` (31K KJV)
Strong's: `strongs_entries` (14.3K Hebrew + Greek lexicon)
Interlinear: `word_alignments` (372K word-level Hebrew/Greek with Strong's per word)
Cross-refs: `cross_references` (433K verse-to-verse connections)
Hermeneutics: `passage_classifications`, `distilled_principles`, `passage_ethics_scores`
Embeddings: `verse_embeddings`, `principle_embeddings`, `strongs_embeddings`, `chapter_embeddings` (pgvector HNSW)
Graph: `knowledge_edges`, `theme_nodes`

Connect: `sudo -u postgres psql -d bible_research` or via etl/config.py credentials.

### ETL Pipeline (`etl/`)

Run in order: `00_init_schema` → `01_load_translations` → `02_load_books` → `03_load_verses_kjv` → `05_load_strongs` → `06_load_word_alignments` → `07_load_cross_references` → `08_load_hermeneutics`

All scripts are idempotent (ON CONFLICT DO NOTHING). Safe to re-run.

### Hermeneutics Engine (`src/hermeneutics.py`)

Classifies scripture passages using Claude: genre, themes, distilled moral principles, ethics framework mapping (0-1 relevance per Hendrycks ETHICS subset), teaching type.

Run: `python -m src.run_hermeneutics` (classifies all 181 Psalms + Proverbs chapters)

### Experiment Framework (`src/run_abcd.py`)

A/B/C/D conditions comparing raw scripture injection vs distilled principles vs topic-matched principles on the Hendrycks ETHICS benchmark.

### Key Commands

```bash
python -m etl.05_load_strongs          # Load Strong's concordance
python -m src.run_hermeneutics --stats  # Corpus statistics
python -m src.run_abcd --quick          # Smoke test ABCD experiment
```

## Conventions

- ETL scripts: `etl/NN_description.py`, run via `python -m etl.NN_description`
- Source modules: `src/module.py`, CLIs via `python -m src.module`
- SQL schema: `sql/schema.sql` (canonical DDL, run by etl/00_init_schema.py)
- Raw data: `data/raw/` (gitignored, downloaded by ETL)
- All DB operations use psycopg2 via `etl/db.py` helpers

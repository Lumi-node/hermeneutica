# Hermeneutica — Biblical Research Lab

## What This Is

A research platform for studying how biblical moral teachings affect LLM ethical reasoning. Goes beyond surface-level text injection to extract, structure, embed, and ultimately train on the *meaning* of scripture — not just the tokens.

## Project Structure

```
hermeneutica/
├── src/                  # Core library code
│   ├── hermeneutics.py       # Classification engine (genre, themes, principles)
│   ├── principles.py         # PrincipleInjection for distilled signal
│   ├── embeddings.py         # Qwen3-Embedding-8B (2000-dim, multilingual)
│   ├── knowledge_graph.py    # Graph builder (549K edges, 5 types)
│   ├── run_abcd.py           # A/B/C/D experiment runner
│   ├── analysis_abcd.py      # Multi-condition statistics
│   └── ...
├── etl/                  # Database ETL pipeline (idempotent, run in order)
│   ├── 00_init_schema.py     # Create DB + extensions
│   ├── 01-03_*.py            # Translations, books, KJV verses
│   ├── 05-05c_*.py           # Strong's + enhanced lexicons + TWOT
│   ├── 06_*.py               # Interlinear word alignments
│   ├── 07_*.py               # Cross-references
│   └── 08_*.py               # Nave's Topical Bible
├── sql/                  # Database schema (canonical DDL)
├── data/                 # Source data (KJV JSON, ethics CSVs, controls)
│   └── raw/                  # Downloaded repos (gitignored, symlinked)
├── training/             # LoRA fine-tuning pipeline
│   ├── configs/              # Model + LoRA YAML configs
│   ├── scripts/              # generate_data.py, train_lora.py, merge
│   ├── datasets/             # Generated JSONL (gitignored)
│   ├── checkpoints/          # Saved models (gitignored)
│   └── logs/                 # Training logs (gitignored)
├── experiments/          # Each experiment = numbered self-contained folder
│   ├── .template/            # Copy to start new experiment
│   │   ├── config.yaml
│   │   ├── analysis.md
│   │   └── figures/
│   └── NNN-description/
├── research/             # Papers, notes, methodology, figures
│   ├── papers/
│   ├── notes/
│   └── figures/
├── eval/                 # Evaluation & benchmarks
│   ├── configs/              # Benchmark run configs (YAML)
│   ├── benchmarks/           # Benchmark datasets (gitignored)
│   └── scorecards/           # Model comparison results
└── CLAUDE.md
```

## Database: `bible_research` (PostgreSQL 16 + pgvector)

Connect: `sudo -u postgres psql -d bible_research` or via `etl/config.py` (uses DATABASE_URL env var).

| Table Group | Tables | Rows |
|-------------|--------|------|
| Core text | translations, books, chapters, verses | 32K |
| Lexicon | strongs_entries (+ BDB glosses, TWOT, sub-meanings) | 14K |
| Interlinear | word_alignments (per-word Hebrew/Greek + Strong's) | 372K |
| Cross-refs | cross_references | 433K |
| Topical | nave_topics, nave_topic_verses | 125K |
| Embeddings | verse/strongs/chapter_embeddings (Qwen3-8B, 2000-dim) | 47K |
| Graph | knowledge_edges, theme_nodes | 549K |

## Key Commands

```bash
# ETL (idempotent, safe to re-run)
python -m etl.05_load_strongs
python -m etl.08_load_naves_topical

# Embeddings
python -m src.embeddings --all
python -m src.embeddings --search "love your neighbor"
python -m src.embeddings --search-strongs "covenant loyalty"

# Knowledge graph
python -m src.knowledge_graph --all
python -m src.knowledge_graph --stats

# Hermeneutics
python -m src.run_hermeneutics --stats

# Experiments
python -m src.run_abcd --quick
```

## Conventions

- ETL scripts: `etl/NN_description.py`, run via `python -m etl.NN_description`
- Source modules: `src/module.py`, CLIs via `python -m src.module`
- Experiments: `experiments/NNN-description/` — copy from `.template/`
- Training configs: `training/configs/*.yaml`
- SQL schema: `sql/schema.sql` (canonical DDL)
- Raw data: `data/raw/` (gitignored, downloaded by ETL)
- All DB operations use psycopg2 via `etl/db.py` helpers

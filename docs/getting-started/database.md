# Database Setup

The Hermeneutica database is PostgreSQL 16 with pgvector for embedding storage and HNSW similarity search.

## Schema Overview

| Table Group | Tables | Rows |
|-------------|--------|------|
| Core text | translations, books, chapters, verses | 32K |
| Lexicon | strongs_entries (BDB/Thayer glosses, TWOT) | 14K |
| Interlinear | word_alignments (per-word Hebrew/Greek + Strong's) | 372K |
| Cross-refs | cross_references (Treasury of Scripture Knowledge) | 433K |
| Topical | nave_topics, nave_topic_verses | 125K |
| Embeddings | verse/strongs/chapter_embeddings (Qwen3-8B, 2000-dim) | 47K |
| Graph | knowledge_edges, theme_nodes | 549K |
| Hermeneutics | passage_classifications, ethics_scores, principles | 3K |
| UMAP | umap_verse_coords, umap_strongs_coords | 45K |

## ETL Pipeline

Scripts are idempotent — safe to re-run. Execute in order:

```bash
python -m etl.00_init_schema       # Create DB + extensions
python -m etl.01_load_translations # Translation metadata
python -m etl.02_load_books        # 66 canonical books
python -m etl.03_load_kjv_verses   # 31,102 KJV verses
python -m etl.05_load_strongs      # Strong's concordance (14K entries)
python -m etl.05b_enhance_strongs  # BDB/Thayer definitions
python -m etl.05c_load_twot        # TWOT references
python -m etl.06_load_interlinear  # Word alignments (445K)
python -m etl.07_load_cross_references  # Cross-refs (433K)
python -m etl.08_load_naves_topical     # Nave's topics (125K)
```

## Required Extensions

```sql
CREATE EXTENSION IF NOT EXISTS vector;    -- pgvector
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- trigram text search
```

## Useful Views

The schema includes several pre-built views:

- `v_verses` — Denormalized verse view with book/chapter context
- `v_classifications` — Classified passages with genre/themes
- `v_principles` — Distilled principles with source context
- `v_interlinear` — Word alignments with Strong's definitions

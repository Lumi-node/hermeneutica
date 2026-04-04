# Data Pipeline

## ETL Flow

The ETL pipeline loads raw data sources into PostgreSQL. All scripts are idempotent.

```
00_init_schema.py     → Create DB + extensions (pgvector, pg_trgm)
01_load_translations  → Translation metadata (KJV, Hebrew, Greek)
02_load_books         → 66 canonical books with genre classification
03_load_kjv_verses    → 31,102 KJV verse texts
05_load_strongs       → 14,298 Strong's concordance entries
05b_enhance_strongs   → BDB (Hebrew) + Thayer (Greek) lexicon definitions
05c_load_twot         → Theological Wordbook of the OT references
06_load_interlinear   → 445K word-level Hebrew/Greek alignments (STEPBible)
07_load_cross_references → 433K cross-references (Treasury of Scripture Knowledge)
08_load_naves_topical → 32K Nave's topics + 93K verse mappings (MetaV)
```

## Embedding Pipeline

```bash
python -m src.embeddings --all
```

Uses Qwen3-Embedding-8B (8B parameters) on GPU:

1. Loads model in float16 (~16GB VRAM)
2. Embeds verse text with instruction prefix
3. Truncates from 4096 to 2000 dims (Matryoshka)
4. L2-normalizes for cosine similarity
5. Stores in pgvector columns with HNSW indexes

Embeds: verses (31K), Strong's entries (14K), chapters (1.2K), principles (~1K).

## Knowledge Graph Pipeline

```bash
python -m src.knowledge_graph --all
```

Builds 549K edges from 6 sources:

| Edge Type | Source | How Built |
|-----------|--------|-----------|
| cross_ref | cross_references table | Direct copy with weight = relevance_score |
| twot_family | strongs_entries.root_strongs | Group by TWOT root, connect all in family |
| nave_topic | nave_topic_verses | verse → theme_node edges |
| semantic_sim | verse_embeddings | pgvector KNN: top 5 neighbors with cosine > 0.85 |
| strongs_sim | strongs_embeddings | pgvector KNN: top 10 neighbors with cosine > 0.80 |

## UMAP Pre-computation

```bash
python -m web.api.precompute.umap_verses
python -m web.api.precompute.umap_strongs
```

Parameters: `n_components=3, n_neighbors=30, min_dist=0.1, metric='cosine'`

Takes ~40 seconds for 31K verses on CPU. Results stored in `umap_verse_coords` / `umap_strongs_coords` tables.

## Binary Export

```bash
python -m web.api.precompute.export_bulk
```

Packs verse data into 28-byte little-endian records for fast frontend loading:

```
Offset 0:  int32   verse_id
Offset 4:  float32 x, y, z (UMAP coordinates)
Offset 16: uint8   book_id, chapter_number
Offset 18: uint16  verse_number, cross_ref_count
Offset 22: uint8   testament, genre_id
Offset 24: float32 ethics_max_score
```

Total: 851KB for 31K verses (400KB gzipped). Frontend parses with `DataView` in <5ms.

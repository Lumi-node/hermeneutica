# Data Sources

All source data is either public domain or openly licensed for research use.

## Scripture Text

| Source | License | What |
|--------|---------|------|
| King James Version | Public domain | 31,102 verse texts |

## Lexical Data

| Source | License | What |
|--------|---------|------|
| Strong's Concordance | Public domain | 14,298 Hebrew + Greek word entries |
| BDB Hebrew Lexicon | Public domain | Enhanced Hebrew definitions |
| Thayer's Greek Lexicon | Public domain | Enhanced Greek definitions |
| TWOT | Reference numbers | Theological Wordbook of the OT family groupings |

## Interlinear Data

| Source | License | What |
|--------|---------|------|
| STEPBible TAHOT | CC BY 4.0 | 305K Hebrew OT word alignments |
| STEPBible TAGNT | CC BY 4.0 | 140K Greek NT word alignments |

## Cross-References

| Source | License | What |
|--------|---------|------|
| OpenBible.info / Treasury of Scripture Knowledge | CC BY 4.0 | 433K cross-references with vote-weighted relevance |

## Topical Data

| Source | License | What |
|--------|---------|------|
| Nave's Topical Bible (via MetaV) | Public domain | 32K topics, 93K verse mappings |

## AI-Generated Data

| Source | Model | What |
|--------|-------|------|
| Chapter classifications | Claude (Sonnet) | Genre, themes, teaching type, ethics scores |
| Distilled principles | Claude (Sonnet) | 1,124 actionable moral statements |
| Verse embeddings | Qwen3-Embedding-8B | 2000-dim semantic vectors for all verses |
| Strong's embeddings | Qwen3-Embedding-8B | 2000-dim vectors for all lexicon entries |
| Knowledge graph edges | pgvector similarity | 15K semantic similarity + 8K Strong's similarity edges |

## How to Download Raw Data

The ETL scripts automatically download source data when first run:

```bash
python -m etl.03_load_kjv_verses    # Downloads KJV JSON
python -m etl.05_load_strongs       # Downloads Strong's data
python -m etl.06_load_interlinear   # Downloads STEPBible TAHOT/TAGNT
python -m etl.07_load_cross_references  # Downloads OpenBible cross-refs
python -m etl.08_load_naves_topical     # Downloads MetaV Nave's data
```

Downloaded files are stored in `data/raw/` (gitignored).

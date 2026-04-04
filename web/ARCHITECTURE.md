# Hermeneutica Explorer -- Technical Architecture

**Version:** 1.0  
**Date:** 2026-04-03  
**Status:** Design Complete -- Ready for Implementation

---

## Table of Contents

1. [Overview and Goals](#1-overview-and-goals)
2. [Directory Structure](#2-directory-structure)
3. [Data Pipeline: Pre-computation](#3-data-pipeline-pre-computation)
4. [API Server (FastAPI)](#4-api-server-fastapi)
5. [Frontend Architecture](#5-frontend-architecture)
6. [3D Scene Graph](#6-3d-scene-graph)
7. [State Management](#7-state-management)
8. [Component Hierarchy](#8-component-hierarchy)
9. [Data Flow Examples](#9-data-flow-examples)
10. [Performance Strategy](#10-performance-strategy)
11. [Error Handling](#11-error-handling)
12. [Build and Development Setup](#12-build-and-development-setup)
13. [Trade-off Decisions](#13-trade-off-decisions)
14. [Extension Points](#14-extension-points)
15. [Dependency Justification](#15-dependency-justification)

---

## 1. Overview and Goals

Hermeneutica Explorer is a 3D interactive web application for exploring the internal structure of the Bible through its embeddings, knowledge graph, lexicon, and hermeneutic classifications. It reads from the existing `bible_research` PostgreSQL database.

**Primary visualizations:**
- Scripture Galaxy: 31K verse point cloud positioned by UMAP of 2000-dim embeddings
- Knowledge Graph Explorer: force-directed 3D graph of heterogeneous knowledge edges
- Word Study Constellation: Strong's lexicon entries in 3D embedding space
- Cross-Reference Matrix: book-to-book connection density
- Hermeneutics Dashboard: chapter classifications, ethics radar, principle browser

**Non-goals for v1:** user accounts, write operations to the research DB, mobile-first layout, real-time collaboration.

---

## 2. Directory Structure

```
web/
├── ARCHITECTURE.md
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── index.html
│
├── api/                              # FastAPI backend (Python)
│   ├── __init__.py
│   ├── main.py                       # FastAPI app, CORS, lifespan
│   ├── config.py                     # DB URL, UMAP paths, constants
│   ├── db.py                         # asyncpg connection pool
│   ├── models/                       # Pydantic response models
│   │   ├── __init__.py
│   │   ├── verse.py                  # VersePoint, VerseDetail, VerseBulk
│   │   ├── graph.py                  # GraphNode, GraphEdge, Neighborhood
│   │   ├── strongs.py                # StrongsPoint, StrongsDetail
│   │   ├── crossref.py               # CrossRefArc, BookMatrix
│   │   ├── hermeneutics.py           # Classification, EthicsScore, Principle
│   │   └── search.py                 # SearchResult, SemanticMatch
│   ├── routers/                      # Route modules (one per visualization)
│   │   ├── __init__.py
│   │   ├── verses.py                 # /api/verses/*
│   │   ├── graph.py                  # /api/graph/*
│   │   ├── strongs.py                # /api/strongs/*
│   │   ├── crossrefs.py              # /api/crossrefs/*
│   │   ├── hermeneutics.py           # /api/hermeneutics/*
│   │   └── search.py                 # /api/search/*
│   └── precompute/                   # Offline data generation scripts
│       ├── __init__.py
│       ├── umap_verses.py            # 2000-dim -> 3D UMAP for verses
│       ├── umap_strongs.py           # 2000-dim -> 3D UMAP for Strong's
│       ├── book_matrix.py            # Pre-compute cross-ref density matrix
│       └── export_bulk.py            # Export initial scene data as JSON
│
├── src/                              # React + TypeScript frontend
│   ├── main.tsx                      # React root, providers
│   ├── App.tsx                       # Layout shell, router
│   │
│   ├── types/                        # Shared TypeScript types (foundational)
│   │   ├── verse.ts                  # VersePoint, VerseDetail, BookMeta
│   │   ├── graph.ts                  # GraphNode, GraphEdge, EdgeType
│   │   ├── strongs.ts                # StrongsPoint, StrongsDetail
│   │   ├── crossref.ts               # CrossRefArc, BookMatrixEntry
│   │   ├── hermeneutics.ts           # Classification, EthicsScores
│   │   ├── scene.ts                  # ColorScheme, LODLevel, CameraState
│   │   └── index.ts                  # Re-exports all types
│   │
│   ├── api/                          # API client layer
│   │   ├── client.ts                 # Base fetch wrapper, error handling
│   │   ├── verses.ts                 # Verse API calls
│   │   ├── graph.ts                  # Graph API calls
│   │   ├── strongs.ts                # Strong's API calls
│   │   ├── crossrefs.ts              # Cross-ref API calls
│   │   ├── hermeneutics.ts           # Hermeneutics API calls
│   │   └── search.ts                 # Search API calls
│   │
│   ├── stores/                       # Zustand state stores
│   │   ├── sceneStore.ts             # Active visualization, camera, selection
│   │   ├── filterStore.ts            # Book, testament, genre, theme filters
│   │   ├── dataStore.ts              # Cached data (verses, strongs, etc.)
│   │   └── uiStore.ts               # Panel visibility, sidebar, tooltips
│   │
│   ├── scenes/                       # Top-level 3D scene containers
│   │   ├── ScriptureGalaxy.tsx       # Verse point cloud scene
│   │   ├── GraphExplorer.tsx         # Knowledge graph scene
│   │   ├── WordConstellation.tsx     # Strong's point cloud scene
│   │   └── CrossRefMatrix.tsx        # Cross-reference visualization
│   │
│   ├── objects/                      # Reusable 3D objects (R3F components)
│   │   ├── InstancedPoints.tsx       # GPU-instanced point cloud renderer
│   │   ├── EdgeLines.tsx             # Curved edge renderer (LineSegments)
│   │   ├── GraphNodes.tsx            # Heterogeneous node renderer
│   │   ├── HoverLabel.tsx            # Billboard text label on hover
│   │   └── LODController.tsx         # Distance-based LOD switching
│   │
│   ├── panels/                       # 2D overlay panels (HTML over canvas)
│   │   ├── VerseDetailPanel.tsx      # Selected verse: text, refs, interlinear
│   │   ├── StrongsDetailPanel.tsx    # Selected Strong's: definition, verses
│   │   ├── GraphNodePanel.tsx        # Selected graph node info
│   │   ├── HermeneuticsPanel.tsx     # Chapter classification + ethics radar
│   │   ├── FilterPanel.tsx           # Global filter controls
│   │   ├── SearchPanel.tsx           # Semantic search input + results
│   │   └── LegendPanel.tsx           # Color legend, edge type legend
│   │
│   ├── charts/                       # 2D chart components (for panels)
│   │   ├── EthicsRadar.tsx           # 5-axis radar chart (ethics scores)
│   │   └── BookHeatmap.tsx           # 66x66 cross-ref density matrix
│   │
│   ├── hooks/                        # Custom React hooks
│   │   ├── useVerseData.ts           # Fetch + cache verse points
│   │   ├── useGraphNeighborhood.ts   # Fetch N-hop graph neighborhood
│   │   ├── useStrongsData.ts         # Fetch + cache Strong's points
│   │   ├── useCrossRefMatrix.ts      # Fetch cross-ref matrix
│   │   ├── useSemanticSearch.ts      # Debounced semantic search
│   │   └── useLOD.ts                 # Camera-distance LOD state
│   │
│   ├── workers/                      # Web Workers
│   │   └── forceLayout.worker.ts     # Force-directed graph layout (off main thread)
│   │
│   ├── lib/                          # Pure utility functions
│   │   ├── colors.ts                 # Color palettes, mapping functions
│   │   ├── geometry.ts               # Arc curves, instanced buffer helpers
│   │   └── constants.ts              # Book names, testament ranges, etc.
│   │
│   └── ui/                           # shadcn/ui component overrides
│       └── ... (auto-generated by shadcn CLI)
│
└── public/
    └── favicon.svg
```

**File ownership for parallel agents:**

| Agent | Files Owned | Depends On |
|-------|-------------|------------|
| A: Types & Constants | `src/types/*`, `src/lib/constants.ts`, `src/lib/colors.ts` | Nothing |
| B: API Models & Routes | `api/models/*`, `api/routers/*`, `api/db.py`, `api/config.py`, `api/main.py` | Nothing |
| C: Precompute Pipeline | `api/precompute/*` | Agent B (config.py) |
| D: API Client | `src/api/*` | Agent A (types) |
| E: Stores | `src/stores/*` | Agent A (types) |
| F: 3D Objects | `src/objects/*`, `src/lib/geometry.ts` | Agent A (types) |
| G: Scenes | `src/scenes/*`, `src/workers/*`, `src/hooks/*` | Agents A, D, E, F |
| H: Panels & Charts | `src/panels/*`, `src/charts/*` | Agents A, D, E |
| I: App Shell | `src/App.tsx`, `src/main.tsx`, `index.html`, config files | All above |

---

## 3. Data Pipeline: Pre-computation

### 3.1 UMAP Projection (Verses)

**Input:** 31,102 verse embeddings, each 2000-dim float32, from `verse_embeddings` table.

**Process:**
```
verse_embeddings (31K x 2000) 
  -> normalize (already L2-normalized in DB)
  -> UMAP(n_components=3, n_neighbors=30, min_dist=0.1, metric='cosine')
  -> 31K x 3 float32 coordinates
  -> store in umap_verse_coords table
```

**Output table:**
```sql
CREATE TABLE umap_verse_coords (
    verse_id    INTEGER PRIMARY KEY REFERENCES verses(id),
    x           REAL NOT NULL,
    y           REAL NOT NULL,
    z           REAL NOT NULL,
    model_name  VARCHAR(80) NOT NULL DEFAULT 'Qwen/Qwen3-Embedding-8B'
);
CREATE INDEX idx_umap_verse_model ON umap_verse_coords (model_name);
```

**Script:** `api/precompute/umap_verses.py`
- Uses `umap-learn` library with `n_jobs=-1` for parallelism
- Expected runtime: ~3-5 minutes on CPU for 31K points
- Idempotent: checks if coordinates already exist, skips if so
- Extracts embeddings via: `SELECT verse_id, embedding FROM verse_embeddings WHERE model_name = 'Qwen/Qwen3-Embedding-8B'`
- pgvector returns embeddings as text `[0.1,0.2,...]`; parse with `np.fromstring(row[1][1:-1], sep=',')`

**UMAP hyperparameter rationale:**
- `n_neighbors=30`: balances local vs global structure. 15 is too local (fragmented clusters), 50 smears fine structure
- `min_dist=0.1`: tight enough to see clusters, loose enough to avoid point collapse
- `metric='cosine'`: matches the cosine similarity used for HNSW indexes in the DB
- `n_components=3`: required for 3D visualization

### 3.2 UMAP Projection (Strong's)

Same process for ~14K Strong's entries from `strongs_embeddings` table.

**Output table:**
```sql
CREATE TABLE umap_strongs_coords (
    strongs_id  INTEGER PRIMARY KEY REFERENCES strongs_entries(id),
    x           REAL NOT NULL,
    y           REAL NOT NULL,
    z           REAL NOT NULL,
    model_name  VARCHAR(80) NOT NULL DEFAULT 'Qwen/Qwen3-Embedding-8B'
);
```

### 3.3 Cross-Reference Book Matrix

Pre-compute a 66x66 matrix of cross-reference density between books.

**Script:** `api/precompute/book_matrix.py`
```sql
SELECT 
    b1.id AS source_book_id, 
    b2.id AS target_book_id,
    COUNT(*) AS ref_count,
    AVG(cr.relevance_score) AS avg_relevance
FROM cross_references cr
JOIN verses v1 ON v1.id = cr.source_verse_id
JOIN chapters ch1 ON ch1.id = v1.chapter_id
JOIN books b1 ON b1.id = ch1.book_id
JOIN verses v2 ON v2.id = cr.target_verse_id
JOIN chapters ch2 ON ch2.id = v2.chapter_id
JOIN books b2 ON b2.id = ch2.book_id
GROUP BY b1.id, b2.id;
```

**Output:** JSON file at `public/data/book_matrix.json` (~15KB). Served statically.

### 3.4 Bulk Export for Initial Load

**Script:** `api/precompute/export_bulk.py`

Generates `public/data/verses_bulk.bin` -- a compact binary file for the initial 31K point load.

**Binary format (per point, 28 bytes):**
```
Offset  Size  Type     Field
0       4     int32    verse_id
4       4     float32  x (UMAP)
8       4     float32  y (UMAP)
12      4     float32  z (UMAP)
16      1     uint8    book_id (1-66)
17      1     uint8    chapter_number
18      2     uint16   verse_number
20      2     uint16   cross_ref_count
22      1     uint8    testament (0=OT, 1=NT)
23      1     uint8    genre_id (enum index)
24      4     float32  ethics_max_score (max of 5 ethics scores, for sizing)
```

Total: 28 bytes x 31,102 = ~850KB. Gzipped: ~400KB. Loads in <200ms on broadband.

**Why binary instead of JSON:** 31K points as JSON with coordinates is ~3MB. Binary is 3.5x smaller and avoids JSON parse overhead (~50ms saved). The `DataView` API reads it in <5ms.

Similarly, `public/data/strongs_bulk.bin` for Strong's points (14K x 24 bytes = ~330KB).

---

## 4. API Server (FastAPI)

### 4.1 Configuration

**File:** `api/config.py`
```python
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/bible_research"
)

# Connection pool limits
DB_POOL_MIN = 2
DB_POOL_MAX = 10

# UMAP model name to query coords for
EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"

# API constants
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000
NEIGHBORHOOD_MAX_HOPS = 3
NEIGHBORHOOD_MAX_NODES = 500
SEMANTIC_SEARCH_LIMIT = 50
```

### 4.2 Database Connection

**File:** `api/db.py`

Uses `asyncpg` for async connection pooling.

```python
import asyncpg
from .config import DATABASE_URL, DB_POOL_MIN, DB_POOL_MAX

pool: asyncpg.Pool | None = None

async def init_pool() -> asyncpg.Pool:
    global pool
    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=DB_POOL_MIN,
        max_size=DB_POOL_MAX,
    )
    return pool

async def close_pool():
    global pool
    if pool:
        await pool.close()
        pool = None

async def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    return pool
```

### 4.3 Pydantic Response Models

**File:** `api/models/verse.py`
```python
from pydantic import BaseModel

class VersePoint(BaseModel):
    """Lightweight verse for point cloud. Matches binary bulk format."""
    verse_id: int
    x: float
    y: float
    z: float
    book_id: int
    chapter_number: int
    verse_number: int
    cross_ref_count: int
    testament: str          # "OT" | "NT"
    genre: str
    ethics_max_score: float

class VerseDetail(BaseModel):
    """Full verse detail for selection panel."""
    verse_id: int
    book_name: str
    book_abbreviation: str
    chapter_number: int
    verse_number: int
    testament: str
    text: str
    cross_ref_count: int
    topics: list[str]                   # Nave's topics for this verse
    word_alignments: list["WordAlignment"]
    cross_references: list["CrossRefBrief"]

class WordAlignment(BaseModel):
    word_position: int
    original_word: str
    transliteration: str
    english_gloss: str
    strongs_number: str
    morphology_code: str | None
    root_definition: str

class CrossRefBrief(BaseModel):
    verse_id: int
    reference: str              # "Gen 1:1"
    relevance_score: float
    text_preview: str           # First 120 chars
```

**File:** `api/models/graph.py`
```python
from pydantic import BaseModel
from typing import Any

class GraphNode(BaseModel):
    """A node in the knowledge graph."""
    id: str                         # "{type}_{db_id}" e.g. "verse_1234"
    node_type: str                  # "verse" | "theme" | "strongs"
    db_id: int                      # Database primary key
    label: str                      # Display label
    metadata: dict[str, Any]        # Type-specific extra fields

class GraphEdge(BaseModel):
    """An edge in the knowledge graph."""
    source: str                     # Node id
    target: str                     # Node id
    edge_type: str                  # "cross_ref" | "twot_family" | "nave_topic" | etc.
    weight: float

class Neighborhood(BaseModel):
    """N-hop neighborhood around a node."""
    center_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    truncated: bool                 # True if max_nodes limit was hit
```

**File:** `api/models/strongs.py`
```python
from pydantic import BaseModel

class StrongsPoint(BaseModel):
    """Lightweight Strong's entry for point cloud."""
    strongs_id: int
    strongs_number: str             # "H0001", "G0001"
    x: float
    y: float
    z: float
    language: str                   # "heb" | "grc"
    part_of_speech: str | None
    usage_count: int                # Number of word_alignments using this entry
    twot_ref: str | None

class StrongsDetail(BaseModel):
    """Full Strong's detail for selection panel."""
    strongs_id: int
    strongs_number: str
    language: str
    original_word: str
    transliteration: str
    pronunciation: str | None
    root_definition: str
    detailed_definition: str
    gloss: str | None
    kjv_usage: str | None
    part_of_speech: str | None
    twot_ref: str | None
    sub_meanings: list[dict] | None
    root_strongs: str | None
    usage_count: int
    sample_verses: list["StrongsVerseRef"]

class StrongsVerseRef(BaseModel):
    verse_id: int
    reference: str
    english_gloss: str
    text_preview: str
```

**File:** `api/models/crossref.py`
```python
from pydantic import BaseModel

class CrossRefArc(BaseModel):
    """A cross-reference for edge rendering."""
    source_verse_id: int
    target_verse_id: int
    source_x: float
    source_y: float
    source_z: float
    target_x: float
    target_y: float
    target_z: float
    relevance_score: float

class BookMatrixEntry(BaseModel):
    source_book_id: int
    target_book_id: int
    ref_count: int
    avg_relevance: float
```

**File:** `api/models/hermeneutics.py`
```python
from pydantic import BaseModel

class Classification(BaseModel):
    chapter_id: int
    book_name: str
    chapter_number: int
    genre: str
    genre_confidence: float
    themes: list[str]
    teaching_type: str
    ethics_reasoning: str
    ethics_scores: dict[str, float]     # {"commonsense": 0.7, ...}
    principles: list[str]

class PrincipleBrief(BaseModel):
    principle_id: int
    principle_text: str
    book_name: str
    chapter_number: int
    genre: str
    themes: list[str]
```

**File:** `api/models/search.py`
```python
from pydantic import BaseModel

class SemanticMatch(BaseModel):
    verse_id: int
    book_name: str
    chapter_number: int
    verse_number: int
    text: str
    similarity: float
    x: float
    y: float
    z: float

class StrongsMatch(BaseModel):
    strongs_id: int
    strongs_number: str
    original_word: str
    transliteration: str
    gloss: str
    similarity: float
    x: float
    y: float
    z: float
```

### 4.4 API Endpoint Specifications

All endpoints are prefixed with `/api`.

#### 4.4.1 Verses

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/api/verses/bulk` | Initial scene load -- all verse points as binary | `application/octet-stream` (binary, see 3.4) |
| GET | `/api/verses/{verse_id}` | Full verse detail | `VerseDetail` |
| GET | `/api/verses/{verse_id}/crossrefs` | Cross-references with 3D coords | `list[CrossRefArc]` |
| GET | `/api/verses/by-ref/{book}/{chapter}/{verse}` | Lookup by reference | `VerseDetail` |
| GET | `/api/verses/book/{book_id}` | All verse points for a book | `list[VersePoint]` |

**GET /api/verses/bulk**

Returns the pre-generated binary file. Served with `FileResponse` and `Content-Type: application/octet-stream`. The frontend reads this with `ArrayBuffer` + `DataView`.

**GET /api/verses/{verse_id}**

```sql
-- Verse text + metadata
SELECT v.id, b.name, b.abbreviation, ch.chapter_number, v.verse_number,
       b.testament, v.text
FROM verses v
JOIN chapters ch ON ch.id = v.chapter_id
JOIN books b ON b.id = ch.book_id
WHERE v.id = $1 AND v.translation_id = 1;

-- Topics for this verse
SELECT nt.topic
FROM nave_topic_verses ntv
JOIN nave_topics nt ON nt.id = ntv.topic_id
WHERE ntv.verse_id = $1;

-- Word alignments
SELECT wa.word_position, wa.original_word, wa.transliteration,
       wa.english_gloss, wa.strongs_number, wa.morphology_code,
       se.root_definition
FROM word_alignments wa
LEFT JOIN strongs_entries se ON se.strongs_number = wa.strongs_number
WHERE wa.verse_id = $1
ORDER BY wa.word_position;

-- Top cross-references (limited to 20)
SELECT cr.target_verse_id, cr.target_ref, cr.relevance_score,
       LEFT(v2.text, 120) as text_preview
FROM cross_references cr
JOIN verses v2 ON v2.id = cr.target_verse_id
WHERE cr.source_verse_id = $1
ORDER BY cr.relevance_score DESC
LIMIT 20;
```

**GET /api/verses/{verse_id}/crossrefs**

```sql
SELECT cr.source_verse_id, cr.target_verse_id,
       uv1.x as sx, uv1.y as sy, uv1.z as sz,
       uv2.x as tx, uv2.y as ty, uv2.z as tz,
       cr.relevance_score
FROM cross_references cr
JOIN umap_verse_coords uv1 ON uv1.verse_id = cr.source_verse_id
JOIN umap_verse_coords uv2 ON uv2.verse_id = cr.target_verse_id
WHERE cr.source_verse_id = $1
ORDER BY cr.relevance_score DESC
LIMIT 50;
```

#### 4.4.2 Knowledge Graph

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/api/graph/neighborhood/{node_type}/{node_id}` | N-hop subgraph | `Neighborhood` |
| GET | `/api/graph/stats` | Edge type counts | `dict` |

**GET /api/graph/neighborhood/{node_type}/{node_id}?hops=1&max_nodes=200&edge_types=cross_ref,nave_topic&min_weight=0.5**

Query parameters:
- `hops`: int, 1-3 (default 1)
- `max_nodes`: int, 10-500 (default 200)
- `edge_types`: comma-separated filter (default: all types)
- `min_weight`: float, 0.0-1.0 (default 0.0)

Implementation strategy: iterative BFS in SQL using a recursive CTE.

```sql
WITH RECURSIVE neighborhood AS (
    -- Seed: the starting node
    SELECT source_type, source_id, target_type, target_id, edge_type, weight, 1 AS hop
    FROM knowledge_edges
    WHERE source_type = $1 AND source_id = $2
      AND edge_type = ANY($3::text[])
      AND weight >= $4
    
    UNION ALL
    
    -- Expand: one more hop from discovered targets
    SELECT ke.source_type, ke.source_id, ke.target_type, ke.target_id, ke.edge_type, ke.weight, n.hop + 1
    FROM knowledge_edges ke
    JOIN neighborhood n ON ke.source_type = n.target_type AND ke.source_id = n.target_id
    WHERE n.hop < $5
      AND ke.edge_type = ANY($3::text[])
      AND ke.weight >= $4
)
SELECT DISTINCT source_type, source_id, target_type, target_id, edge_type, weight
FROM neighborhood
LIMIT $6;
```

After fetching edges, the router collects distinct node IDs and batch-fetches labels:
- `verse` nodes: `SELECT id, text FROM verses WHERE id = ANY($1)` (truncate text to 60 chars for label)
- `theme` nodes: `SELECT id, theme_name FROM theme_nodes WHERE id = ANY($1)`
- `strongs` nodes: `SELECT id, strongs_number, transliteration, COALESCE(gloss, LEFT(root_definition, 40)) FROM strongs_entries WHERE id = ANY($1)`

#### 4.4.3 Strong's Lexicon

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/api/strongs/bulk` | All Strong's points as binary | `application/octet-stream` |
| GET | `/api/strongs/{strongs_id}` | Full entry detail | `StrongsDetail` |
| GET | `/api/strongs/by-number/{strongs_number}` | Lookup by number | `StrongsDetail` |
| GET | `/api/strongs/{strongs_id}/verses` | Verses using this word | paginated `list[StrongsVerseRef]` |

**GET /api/strongs/{strongs_id}**

```sql
SELECT se.id, se.strongs_number, se.language, se.original_word,
       se.transliteration, se.pronunciation, se.root_definition,
       se.detailed_definition, se.gloss, se.kjv_usage,
       se.part_of_speech, se.twot_ref, se.sub_meanings, se.root_strongs,
       (SELECT count(*) FROM word_alignments wa WHERE wa.strongs_number = se.strongs_number) as usage_count
FROM strongs_entries se WHERE se.id = $1;

-- Sample verses (first 10)
SELECT v.id, b.name || ' ' || ch.chapter_number || ':' || v.verse_number as reference,
       wa.english_gloss, LEFT(v.text, 120) as text_preview
FROM word_alignments wa
JOIN verses v ON v.id = wa.verse_id
JOIN chapters ch ON ch.id = v.chapter_id
JOIN books b ON b.id = ch.book_id
WHERE wa.strongs_number = $1
ORDER BY v.id
LIMIT 10;
```

#### 4.4.4 Cross-References

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/api/crossrefs/matrix` | 66x66 book density matrix | `list[BookMatrixEntry]` |
| GET | `/api/crossrefs/between/{book1_id}/{book2_id}` | Refs between two books | `list[CrossRefArc]` |

**GET /api/crossrefs/matrix**

Returns the pre-computed JSON from `public/data/book_matrix.json`. Cached indefinitely.

#### 4.4.5 Hermeneutics

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/api/hermeneutics/chapter/{chapter_id}` | Classification for a chapter | `Classification` |
| GET | `/api/hermeneutics/by-ref/{book}/{chapter}` | Lookup by reference | `Classification` |
| GET | `/api/hermeneutics/principles` | Browse principles | paginated `list[PrincipleBrief]` |
| GET | `/api/hermeneutics/principles?theme=Justice&ethics_subset=justice&min_score=0.5` | Filtered | paginated `list[PrincipleBrief]` |
| GET | `/api/hermeneutics/stats` | Genre/theme/teaching counts | `dict` |

**GET /api/hermeneutics/chapter/{chapter_id}**

```sql
SELECT pc.id, pc.chapter_id, b.name, ch.chapter_number,
       pc.genre, pc.genre_confidence, pc.themes, pc.teaching_type, pc.ethics_reasoning
FROM passage_classifications pc
JOIN chapters ch ON ch.id = pc.chapter_id
JOIN books b ON b.id = ch.book_id
WHERE pc.chapter_id = $1;

-- Ethics scores
SELECT ethics_subset, relevance_score
FROM passage_ethics_scores WHERE classification_id = $1;

-- Principles
SELECT principle_text
FROM distilled_principles WHERE classification_id = $1
ORDER BY principle_order;
```

#### 4.4.6 Semantic Search

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/api/search/verses?q=love+your+neighbor&limit=20` | Semantic verse search | `list[SemanticMatch]` |
| GET | `/api/search/strongs?q=covenant+loyalty&limit=20` | Semantic Strong's search | `list[StrongsMatch]` |
| GET | `/api/search/nearest?verse_id=1234&limit=10` | Nearest verses by embedding | `list[SemanticMatch]` |

**GET /api/search/verses?q=...&limit=20**

This endpoint requires a query embedding. Two implementation options:

**Chosen approach: server-side embedding via a lightweight model.**

We do NOT load the full Qwen3-Embedding-8B (8B params) in the API server. Instead, we use a pre-computed query embedding approach:

1. The API server stores a pre-built FAISS index of the UMAP-space coordinates (optional optimization)
2. For semantic search, we use pgvector's HNSW index directly -- the existing embedding infrastructure

```sql
-- This requires embedding the query text server-side.
-- We use sentence-transformers with the same Qwen model loaded once at startup.
-- Since the API server runs on the same GPU machine, this is feasible.

SET hnsw.ef_search = 100;

SELECT v.id, b.name, ch.chapter_number, v.verse_number, v.text,
       1 - (ve.embedding <=> $1::vector) as similarity,
       uv.x, uv.y, uv.z
FROM verse_embeddings ve
JOIN verses v ON v.id = ve.verse_id
JOIN chapters ch ON ch.id = v.chapter_id
JOIN books b ON b.id = ch.book_id
JOIN umap_verse_coords uv ON uv.verse_id = v.id
WHERE ve.model_name = $2
ORDER BY ve.embedding <=> $1::vector
LIMIT $3;
```

**Trade-off:** Loading Qwen3-Embedding-8B uses ~16GB VRAM in float16. The research machine has ample GPU memory. If this becomes a problem, we can pre-compute a smaller ONNX export of the embedding model or use the CPU-only `bge-base-en-v1.5` as a fallback (lower quality but no GPU required).

### 4.5 FastAPI Application

**File:** `api/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import init_pool, close_pool
from .routers import verses, graph, strongs, crossrefs, hermeneutics, search

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()

app = FastAPI(
    title="Hermeneutica Explorer API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Mount pre-computed static data
app.mount("/data", StaticFiles(directory="public/data"), name="static-data")

# Register routers
app.include_router(verses.router, prefix="/api/verses", tags=["verses"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(strongs.router, prefix="/api/strongs", tags=["strongs"])
app.include_router(crossrefs.router, prefix="/api/crossrefs", tags=["crossrefs"])
app.include_router(hermeneutics.router, prefix="/api/hermeneutics", tags=["hermeneutics"])
app.include_router(search.router, prefix="/api/search", tags=["search"])

@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

---

## 5. Frontend Architecture

### 5.1 Application Shell

```
+---------------------------------------------------------------+
|  TopBar: [Scripture Galaxy] [Graph] [Words] [CrossRef] [Hermeneutics] | Search |
+-------+-------------------------------------------------------+
|       |                                                       |
| Side  |                                                       |
| Panel |                    3D Canvas                           |
| (Left)|                  (React Three Fiber)                  |
|       |                                                       |
| Filter|                                                       |
| Legend |                                                       |
|       |                                                       |
+-------+-------------------------------------------------------+
|       |    Detail Panel (Bottom / Right, collapsible)          |
+-------+-------------------------------------------------------+
```

The app uses a single `<Canvas>` from R3F that persists across views. Each "scene" swaps its children inside the Canvas. This avoids re-creating the WebGL context on navigation.

### 5.2 Routing

No client-side router library. The active visualization is tracked in `sceneStore.activeScene` (a string enum). The `App.tsx` component conditionally renders the active scene inside the persistent Canvas. This is simpler than React Router for a single-page 3D app where URL state is minimal.

```tsx
// App.tsx (simplified)
function App() {
  const activeScene = useSceneStore(s => s.activeScene);

  return (
    <div className="h-screen w-screen flex flex-col">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <FilterPanel />
        <div className="flex-1 relative">
          <Canvas camera={{ position: [0, 0, 100], fov: 60 }}>
            <ambientLight intensity={0.4} />
            {activeScene === 'galaxy' && <ScriptureGalaxy />}
            {activeScene === 'graph' && <GraphExplorer />}
            {activeScene === 'words' && <WordConstellation />}
            {activeScene === 'crossref' && <CrossRefMatrix />}
          </Canvas>
          <DetailPanel />
          <LegendPanel />
        </div>
      </div>
    </div>
  );
}
```

---

## 6. 3D Scene Graph

### 6.1 Scripture Galaxy

```
<ScriptureGalaxy>
  <OrbitControls enableDamping dampingFactor={0.05} />
  <InstancedPoints                    // 31K instanced spheres
    data={versePoints}                // Float32Array from binary bulk load
    colorAttribute={colorBy}          // book | testament | genre | theme | ethics
    sizeAttribute={sizeBy}            // cross_ref_count | ethics_max_score
    onHover={setHoveredVerse}
    onClick={selectVerse}
  />
  <EdgeLines                          // Cross-ref arcs for selected verse
    arcs={selectedVerseArcs}          // Loaded on-demand from API
    opacity={arc => arc.relevance}
  />
  <HoverLabel                         // Billboard text on hover
    position={hoveredPosition}
    text={hoveredVerseRef}
  />
  <LODController                      // Adjusts point detail by camera distance
    camera={camera}
    levels={[
      { distance: 200, pointSize: 0.8, showLabels: false },
      { distance: 50,  pointSize: 1.2, showLabels: false },
      { distance: 15,  pointSize: 2.0, showLabels: true  },
    ]}
  />
</ScriptureGalaxy>
```

### 6.2 InstancedPoints (Core Renderer)

This is the most performance-critical component. It renders N points using a single `THREE.InstancedMesh` with a custom shader material.

```tsx
// objects/InstancedPoints.tsx

interface InstancedPointsProps {
  /** Vertex data: [verse_id, x, y, z, book_id, ...] per point */
  positions: Float32Array;       // length = N * 3 (x, y, z)
  colors: Float32Array;          // length = N * 3 (r, g, b), computed from colorBy
  sizes: Float32Array;           // length = N (per-instance scale)
  count: number;                 // Number of active points (for filtering)
  visibilityMask: Uint8Array;    // 1 = visible, 0 = hidden (for filtering)
  onHover: (index: number | null) => void;
  onClick: (index: number) => void;
}
```

Implementation uses `THREE.InstancedBufferGeometry` with:
- A shared `SphereGeometry(1, 8, 6)` as the base (low-poly sphere, 8 segments)
- `InstancedBufferAttribute` for position offsets, colors, scales
- A custom `ShaderMaterial` with:
  - Vertex shader: applies instance transform, passes color to fragment
  - Fragment shader: simple diffuse + ambient lighting, alpha falloff at edges
- Raycasting: uses a spatial hash (grid cells of size 2.0) for O(1) hover detection instead of brute-force raycast against 31K instances

**Filtering:** When the user filters by book/testament/genre, we do NOT re-create the InstancedMesh. Instead, we set the scale of hidden points to 0 (makes them invisible without changing the buffer layout). The `visibilityMask` drives this:

```typescript
// In the render loop (useFrame):
for (let i = 0; i < count; i++) {
  dummy.position.set(positions[i*3], positions[i*3+1], positions[i*3+2]);
  dummy.scale.setScalar(visibilityMask[i] ? sizes[i] : 0);
  dummy.updateMatrix();
  meshRef.current.setMatrixAt(i, dummy.matrix);
}
meshRef.current.instanceMatrix.needsUpdate = true;
```

### 6.3 Knowledge Graph Explorer

```
<GraphExplorer>
  <OrbitControls />
  <GraphNodes                         // Heterogeneous node rendering
    nodes={graphNodes}
    nodeGeometries={{
      verse:   <SphereGeometry args={[1, 12, 8]} />,
      theme:   <BoxGeometry args={[1.4, 1.4, 1.4]} />,
      strongs: <OctahedronGeometry args={[1]} />,
    }}
    colorByType={true}
    selectedId={selectedNodeId}
    onClick={selectNode}
  />
  <EdgeLines
    edges={graphEdges}
    colorByType={true}                // Different hue per edge_type
    edgeTypeColors={{
      cross_ref:    '#4A90D9',
      twot_family:  '#E8A838',
      nave_topic:   '#50C878',
      nave_shared:  '#7B68EE',
      semantic_sim: '#FF6B6B',
      strongs_sim:  '#DDA0DD',
    }}
  />
  <HoverLabel position={hoveredPos} text={hoveredLabel} />
</GraphExplorer>
```

**Layout algorithm:** The graph layout runs in a Web Worker using `ngraph.forcelayout3d`.

```
Main thread                          Worker thread
-----------                          -------------
postMessage({                        onmessage = (e) => {
  nodes: [{id, x?, y?, z?}],          const graph = createGraph();
  edges: [{source, target, weight}]    // Add nodes + edges
})                                     const layout = createLayout(graph, {
                                         springLength: 30,
    <-- postMessage({positions})         springCoefficient: 0.0008,
                                         gravity: -1.2,
                                         dragCoefficient: 0.02,
                                       });
                                       for (let i = 0; i < 300; i++) {
                                         layout.step();
                                         if (i % 50 === 0)
                                           postMessage({positions, done: false});
                                       }
                                       postMessage({positions, done: true});
                                     };
```

The worker posts intermediate positions every 50 iterations so the user sees the layout converge in real-time. Typical convergence: 300 iterations in ~200ms for 500 nodes.

### 6.4 Word Study Constellation

Same architecture as ScriptureGalaxy but with Strong's data:
- `InstancedPoints` with 14K points from `strongs_bulk.bin`
- Color by: language (Hebrew = warm tones, Greek = cool tones), part of speech, TWOT family
- Size by: usage count (word_alignments count)
- Click: loads `StrongsDetail` via API, shows all verses

### 6.5 Cross-Reference Matrix

Uses an HTML5 Canvas 2D heatmap overlaid, not 3D. The 66x66 matrix is small enough to render as a 2D grid.

```
<CrossRefMatrix>
  {/* 2D heatmap rendered with HTML Canvas, not Three.js */}
  <BookHeatmap
    matrix={bookMatrix}              // Pre-loaded from /data/book_matrix.json
    onCellClick={(srcBook, tgtBook) => loadBookPairRefs(srcBook, tgtBook)}
    highlightedRow={selectedBook}
    colorScale="viridis"             // Log scale: log(ref_count + 1)
  />
  {/* 3D arc visualization in the persistent Canvas */}
  {selectedBookPair && (
    <EdgeLines
      arcs={bookPairArcs}
      opacity={0.6}
    />
  )}
</CrossRefMatrix>
```

---

## 7. State Management

### 7.1 Store Decomposition

Four Zustand stores, each with a distinct responsibility. No store imports another store. Cross-store coordination happens in React components via `useEffect`.

**File:** `src/stores/sceneStore.ts`
```typescript
type SceneId = 'galaxy' | 'graph' | 'words' | 'crossref';

interface SceneState {
  // Active visualization
  activeScene: SceneId;
  setActiveScene: (scene: SceneId) => void;

  // Selection (polymorphic)
  selectedNodeType: 'verse' | 'strongs' | 'theme' | null;
  selectedNodeId: number | null;
  selectNode: (type: 'verse' | 'strongs' | 'theme' | null, id: number | null) => void;

  // Hover
  hoveredIndex: number | null;
  setHoveredIndex: (index: number | null) => void;

  // Camera
  cameraTarget: [number, number, number] | null;  // Fly-to target
  setCameraTarget: (pos: [number, number, number] | null) => void;

  // Color/size encoding
  colorBy: 'book' | 'testament' | 'genre' | 'theme' | 'ethics';
  sizeBy: 'uniform' | 'crossrefs' | 'ethics';
  setColorBy: (mode: SceneState['colorBy']) => void;
  setSizeBy: (mode: SceneState['sizeBy']) => void;
}
```

**File:** `src/stores/filterStore.ts`
```typescript
interface FilterState {
  // Book/testament filters
  testamentFilter: 'all' | 'OT' | 'NT';
  bookFilter: number[];                    // Empty = all books
  setTestamentFilter: (t: FilterState['testamentFilter']) => void;
  toggleBook: (bookId: number) => void;
  clearBookFilter: () => void;

  // Genre filter
  genreFilter: string[];                   // Empty = all genres
  toggleGenre: (genre: string) => void;

  // Theme filter
  themeFilter: string[];
  toggleTheme: (theme: string) => void;

  // Graph-specific filters
  edgeTypeFilter: string[];                // Empty = all edge types
  toggleEdgeType: (edgeType: string) => void;
  minWeight: number;                       // 0.0 - 1.0
  setMinWeight: (w: number) => void;
  graphHops: number;                       // 1 - 3
  setGraphHops: (h: number) => void;

  // Computed: visibility mask (derived from above)
  // This is NOT stored here -- computed in the scene component
}
```

**File:** `src/stores/dataStore.ts`
```typescript
interface DataState {
  // Verse points (loaded once from binary bulk)
  versePoints: {
    positions: Float32Array;       // N * 3
    metadata: Uint8Array;          // Packed book_id, chapter, testament, genre, etc.
    verseIds: Int32Array;          // N
    count: number;
    loaded: boolean;
  } | null;
  loadVersePoints: () => Promise<void>;

  // Strong's points (loaded once from binary bulk)
  strongsPoints: {
    positions: Float32Array;
    metadata: Uint8Array;
    strongsIds: Int32Array;
    count: number;
    loaded: boolean;
  } | null;
  loadStrongsPoints: () => Promise<void>;

  // Book metadata (loaded once)
  books: BookMeta[] | null;
  loadBooks: () => Promise<void>;

  // Cross-ref matrix (loaded once)
  bookMatrix: BookMatrixEntry[] | null;
  loadBookMatrix: () => Promise<void>;

  // Graph neighborhood (loaded on demand)
  graphData: {
    nodes: GraphNode[];
    edges: GraphEdge[];
    centerNodeId: string;
  } | null;
  loadNeighborhood: (nodeType: string, nodeId: number, hops: number, edgeTypes: string[], minWeight: number) => Promise<void>;
}
```

**File:** `src/stores/uiStore.ts`
```typescript
interface UIState {
  // Panel visibility
  filterPanelOpen: boolean;
  detailPanelOpen: boolean;
  legendPanelOpen: boolean;
  searchPanelOpen: boolean;
  toggleFilterPanel: () => void;
  toggleDetailPanel: () => void;
  toggleLegendPanel: () => void;
  toggleSearchPanel: () => void;

  // Tooltip
  tooltipText: string;
  tooltipPosition: { x: number; y: number } | null;
  setTooltip: (text: string, pos: { x: number; y: number } | null) => void;

  // Loading indicators
  isLoading: boolean;
  loadingMessage: string;
  setLoading: (loading: boolean, message?: string) => void;
}
```

### 7.2 Cross-Store Coordination Pattern

Stores never import each other. Coordination happens in scene components:

```tsx
// scenes/ScriptureGalaxy.tsx (simplified)
function ScriptureGalaxy() {
  const { versePoints, loadVersePoints } = useDataStore();
  const { selectedNodeId, selectNode, colorBy, sizeBy } = useSceneStore();
  const { testamentFilter, bookFilter, genreFilter } = useFilterStore();
  const { setLoading } = useUIStore();

  // Load data on mount
  useEffect(() => {
    if (!versePoints?.loaded) {
      setLoading(true, 'Loading verse embeddings...');
      loadVersePoints().finally(() => setLoading(false));
    }
  }, []);

  // Compute visibility mask from filters (derived, not stored)
  const visibilityMask = useMemo(() => {
    if (!versePoints) return new Uint8Array(0);
    return computeVisibility(versePoints.metadata, {
      testamentFilter, bookFilter, genreFilter
    });
  }, [versePoints, testamentFilter, bookFilter, genreFilter]);

  // ... render
}
```

---

## 8. Component Hierarchy

```
App
├── TopBar
│   ├── SceneSelector (galaxy | graph | words | crossref)
│   ├── SearchToggle
│   └── ColorBySelector / SizeBySelector
├── FilterPanel (left sidebar, collapsible)
│   ├── TestamentFilter (OT/NT toggle)
│   ├── BookFilter (multi-select, grouped by testament)
│   ├── GenreFilter (multi-select checkboxes)
│   ├── ThemeFilter (multi-select checkboxes)
│   ├── [Graph mode only] EdgeTypeFilter
│   ├── [Graph mode only] WeightSlider
│   └── [Graph mode only] HopsSelector (1/2/3)
├── Canvas (R3F, persistent)
│   ├── [galaxy] ScriptureGalaxy
│   │   ├── InstancedPoints
│   │   ├── EdgeLines (selected verse cross-refs)
│   │   ├── HoverLabel
│   │   └── LODController
│   ├── [graph] GraphExplorer
│   │   ├── GraphNodes
│   │   ├── EdgeLines
│   │   └── HoverLabel
│   ├── [words] WordConstellation
│   │   ├── InstancedPoints
│   │   ├── HoverLabel
│   │   └── LODController
│   └── [crossref] CrossRefMatrix
│       └── EdgeLines (book-pair arcs)
├── DetailPanel (right/bottom, collapsible)
│   ├── [verse selected] VerseDetailPanel
│   │   ├── VerseText (with interlinear toggle)
│   │   ├── CrossRefList
│   │   ├── TopicTags
│   │   └── HermeneuticsPanel (if chapter classified)
│   │       └── EthicsRadar
│   ├── [strongs selected] StrongsDetailPanel
│   │   ├── DefinitionBlock
│   │   ├── SubMeanings
│   │   ├── VerseUsageList
│   │   └── TWOTFamilyLinks
│   └── [graph node selected] GraphNodePanel
│       ├── NodeInfo
│       └── NeighborhoodControls (expand, filter)
├── LegendPanel (bottom-left overlay)
│   ├── ColorLegend (dynamic based on colorBy)
│   └── EdgeTypeLegend (graph mode only)
├── SearchPanel (overlay)
│   ├── SearchInput (debounced, 300ms)
│   ├── SearchResults (list, click to fly-to)
│   └── SearchModeToggle (verses | strongs)
└── LoadingOverlay (conditional)
    └── ProgressBar + message
```

---

## 9. Data Flow Examples

### 9.1 Initial Load (Scripture Galaxy)

```
User opens app
  |
  v
App mounts -> ScriptureGalaxy is default scene
  |
  v
useEffect triggers loadVersePoints()
  |
  v
dataStore.loadVersePoints():
  1. fetch('/data/verses_bulk.bin')                    // ~400KB gzipped
  2. response.arrayBuffer()                            // ~850KB raw
  3. Parse with DataView:
     for i in 0..31102:
       verseIds[i]    = view.getInt32(i * 28, true)
       positions[i*3] = view.getFloat32(i * 28 + 4, true)   // x
       positions[i*3+1] = view.getFloat32(i * 28 + 8, true) // y
       positions[i*3+2] = view.getFloat32(i * 28 + 12, true)// z
       metadata[i*6]  = view.getUint8(i * 28 + 16)          // book_id
       metadata[i*6+1] = view.getUint8(i * 28 + 17)         // chapter
       ... etc
  4. Store in dataStore.versePoints
  |
  v
ScriptureGalaxy renders:
  1. computeColors(positions, metadata, colorBy='book')
     -> Float32Array of N*3 RGB values
     -> Book 1 (Genesis) = HSL(0/66*360, 0.7, 0.5), Book 2 = HSL(1/66*360, ...)
  2. computeSizes(metadata, sizeBy='uniform')
     -> Float32Array of N uniform 1.0 values
  3. <InstancedPoints positions={...} colors={...} sizes={...} count={31102} />
  |
  v
InstancedPoints creates THREE.InstancedMesh:
  - geometry: SphereGeometry(1, 8, 6)
  - material: custom ShaderMaterial
  - count: 31102
  - Sets 31102 instance matrices + colors in first frame (~4ms)
  - Renders at 60fps (GPU-instanced, single draw call)
```

**Total time from click to rendered:** ~600ms (network) + ~50ms (parse) + ~4ms (GPU upload) = ~654ms.

### 9.2 Verse Selection + Cross-Reference Arcs

```
User clicks a point (verse_id = 23145, Romans 8:28)
  |
  v
InstancedPoints.onClick(index=23145)
  |
  v
sceneStore.selectNode('verse', 23145)
  -> detailPanelOpen = true
  |
  +-- [Detail Panel]
  |   useEffect on selectedNodeId:
  |     fetch('/api/verses/23145')
  |     -> { verse_id: 23145, book_name: "Romans", chapter_number: 8,
  |          verse_number: 28, text: "And we know that all things...",
  |          topics: ["Providence", "Faith", "Afflictions Made Beneficial"],
  |          word_alignments: [
  |            { position: 1, original: "Οἴδαμεν", transliteration: "oidamen",
  |              gloss: "we know", strongs: "G1492", morphology: "V-RAI-1P",
  |              root_definition: "to see, to know" },
  |            ...
  |          ],
  |          cross_references: [
  |            { verse_id: 23148, reference: "Rom 8:31", relevance: 0.92,
  |              text_preview: "What shall we then say to these things..." },
  |            ...
  |          ]
  |        }
  |
  +-- [3D Scene]
      useEffect on selectedNodeId:
        fetch('/api/verses/23145/crossrefs')
        -> [
             { source_verse_id: 23145, target_verse_id: 23148,
               source_x: 12.3, source_y: -4.5, source_z: 7.8,
               target_x: 12.8, target_y: -4.2, target_z: 8.1,
               relevance_score: 0.92 },
             ...  (up to 50 arcs)
           ]
        -> <EdgeLines arcs={crossRefArcs} />
        -> Each arc: QuadraticBezierCurve3 with control point lifted by 5 units
        -> opacity = relevance_score (0.92 = nearly opaque)
```

### 9.3 Graph Neighborhood Expansion

```
User is in Graph Explorer, clicks theme node "Justice" (theme_42)
  |
  v
sceneStore.selectNode('theme', 42)
  |
  v
GraphExplorer useEffect:
  const { edgeTypeFilter, minWeight, graphHops } = useFilterStore()
  // edgeTypeFilter = ['nave_topic', 'cross_ref'], minWeight = 0.3, graphHops = 1
  
  fetch('/api/graph/neighborhood/theme/42?hops=1&max_nodes=200&edge_types=nave_topic,cross_ref&min_weight=0.3')
  |
  v
API server executes recursive CTE:
  Returns: {
    center_id: "theme_42",
    nodes: [
      { id: "theme_42", node_type: "theme", db_id: 42, label: "Justice",
        metadata: { description: "..." } },
      { id: "verse_1234", node_type: "verse", db_id: 1234, label: "Psalm 82:3 - Defend the poor...",
        metadata: {} },
      { id: "verse_5678", node_type: "verse", db_id: 5678, label: "Isa 1:17 - Learn to do well...",
        metadata: {} },
      ... (up to 200 nodes)
    ],
    edges: [
      { source: "theme_42", target: "verse_1234", edge_type: "nave_topic", weight: 1.0 },
      { source: "verse_1234", target: "verse_5678", edge_type: "cross_ref", weight: 0.85 },
      ...
    ],
    truncated: false
  }
  |
  v
dataStore.graphData = result
  |
  v
GraphExplorer posts to forceLayout.worker:
  postMessage({ nodes: result.nodes, edges: result.edges })
  |
  v
Worker computes layout (300 iterations, ~200ms):
  Posts intermediate positions at iterations 50, 100, 150, 200, 250
  |
  v
GraphExplorer receives positions, updates GraphNodes + EdgeLines
  Layout animates from random to converged over ~200ms
```

### 9.4 Semantic Search

```
User types "love your enemies" in SearchPanel
  |
  v (debounced 300ms)
  
fetch('/api/search/verses?q=love+your+enemies&limit=20')
  |
  v
API server:
  1. Encode query with Qwen3-Embedding-8B -> 2000-dim vector
  2. pgvector HNSW search: ORDER BY embedding <=> query_vec LIMIT 20
  3. Join with umap_verse_coords for 3D positions
  |
  v
Response: [
  { verse_id: 24012, book_name: "Matthew", chapter: 5, verse: 44,
    text: "But I say unto you, Love your enemies...",
    similarity: 0.934, x: 8.2, y: -12.1, z: 3.5 },
  { verse_id: 25891, book_name: "Luke", chapter: 6, verse: 27,
    text: "But I say unto you which hear, Love your enemies...",
    similarity: 0.921, x: 8.5, y: -11.8, z: 3.2 },
  ...
]
  |
  v
SearchPanel renders results list
  User clicks "Matthew 5:44"
    -> sceneStore.selectNode('verse', 24012)
    -> sceneStore.setCameraTarget([8.2, -12.1, 3.5])
    -> Camera smoothly flies to that position (OrbitControls.target lerp)
```

---

## 10. Performance Strategy

### 10.1 Performance Budget

| Operation | Target | Strategy |
|-----------|--------|----------|
| Initial load (31K points) | < 1s | Binary bulk file (~400KB gzipped), single draw call |
| Point cloud 60fps | 16.6ms frame | InstancedMesh, single draw call, no per-frame JS allocation |
| Hover detection | < 2ms | Spatial hash grid, not raycasting against 31K instances |
| Filter application | < 10ms | Modify scale attribute (set to 0), no buffer re-creation |
| Graph layout (500 nodes) | < 500ms | Web Worker, ngraph.forcelayout3d |
| Verse detail load | < 200ms | Single API call, three parallel SQL queries |
| Semantic search | < 1s | pgvector HNSW index, ef_search=100 |
| Color scheme change | < 5ms | Recompute Float32Array, update InstancedBufferAttribute |

### 10.2 Instanced Rendering Details

**Why InstancedMesh, not Points/Sprites:**
- `THREE.Points` cannot be raycasted efficiently and lacks per-point lighting
- `THREE.InstancedMesh` with a low-poly sphere gives proper 3D appearance, per-instance color, and hardware-accelerated rendering via a single `glDrawArraysInstanced` call
- At 31K instances with 8-segment spheres (288 triangles each), total = ~9M triangles. Modern GPUs handle this trivially (RTX 3070+ renders 100M+ triangles at 60fps).

**Draw call count:** The entire 31K point cloud is ONE draw call. Cross-reference edges for a selected verse add one more. Total: 2-3 draw calls for the main scene.

### 10.3 LOD System

Three levels based on camera distance from the nearest cluster centroid:

| Level | Camera Distance | Point Geometry | Label Display | Edge Display |
|-------|----------------|----------------|---------------|-------------|
| Far | > 200 units | 4-segment sphere (32 tris) | None | None |
| Medium | 50-200 | 8-segment sphere (288 tris) | None | Selected only |
| Close | < 50 | 12-segment sphere (648 tris) | Book:chapter for nearest 20 | Selected + high-relevance |

LOD transitions are smooth: geometry swap happens once per camera rest (not per frame). The `LODController` component checks distance every 500ms via `useFrame` with a frame counter throttle.

### 10.4 Edge Rendering Strategy

**Problem:** 549K edges cannot be rendered simultaneously (would require 549K line segments = performance collapse).

**Solution:** Only render edges that are relevant to the current context:

| Context | Edges Shown | Max Count |
|---------|-------------|-----------|
| No selection | None | 0 |
| Verse selected | Cross-refs for that verse | ~50 |
| Graph neighborhood loaded | All edges in neighborhood | ~500 |
| Book pair selected (CrossRef view) | Refs between those two books | ~200 |

Edges are rendered as `THREE.LineSegments` with a custom `LineMaterial` that supports per-line color and opacity. Curved arcs are approximated with 8-segment polylines computed from `THREE.QuadraticBezierCurve3`.

### 10.5 Memory Budget

| Data | Size | Notes |
|------|------|-------|
| Verse positions | 31K * 12B = 372KB | Float32Array x3 |
| Verse metadata | 31K * 6B = 186KB | Packed uint8/uint16 |
| Verse IDs | 31K * 4B = 124KB | Int32Array |
| Verse colors | 31K * 12B = 372KB | Float32Array x3, recomputed on colorBy change |
| GPU instance matrices | 31K * 64B = 2MB | Three.js InstancedMesh internal |
| Strong's positions | 14K * 12B = 168KB | Float32Array x3 |
| Graph data (typical) | ~100KB | 500 nodes + edges as JSON |
| **Total frontend** | **~4MB** | Well within browser limits |

---

## 11. Error Handling

### 11.1 Error Types

**API errors (Python):**
```python
from fastapi import HTTPException

class ErrorCode:
    NOT_FOUND = "NOT_FOUND"
    INVALID_PARAM = "INVALID_PARAM"
    DB_ERROR = "DB_ERROR"
    SEARCH_ERROR = "SEARCH_ERROR"

# Usage in routers:
raise HTTPException(status_code=404, detail={
    "code": ErrorCode.NOT_FOUND,
    "message": f"Verse {verse_id} not found"
})
```

All routers wrap database calls in try/except and convert `asyncpg` exceptions to HTTP 500 with `DB_ERROR` code. Connection pool exhaustion returns HTTP 503.

**Frontend errors (TypeScript):**
```typescript
// src/api/client.ts
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
  }
}

async function apiFetch<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }
  const res = await fetch(url.toString());
  if (!res.ok) {
    const body = await res.json().catch(() => ({ code: 'UNKNOWN', message: res.statusText }));
    throw new ApiError(res.status, body.code ?? 'UNKNOWN', body.message ?? res.statusText);
  }
  return res.json();
}
```

### 11.2 Error Display Strategy

| Error Source | Display |
|-------------|---------|
| Bulk data load failure | Full-screen error with retry button |
| Verse detail fetch failure | Toast notification, detail panel shows "Failed to load" |
| Graph neighborhood failure | Toast notification, graph shows empty state |
| Search failure | Inline error in search panel |
| WebGL context lost | Full-screen overlay: "3D rendering lost. Please reload." |

### 11.3 Graceful Degradation

- If UMAP coordinates are not yet computed, the bulk endpoint returns HTTP 503 with a message: "UMAP coordinates not yet generated. Run: python -m api.precompute.umap_verses"
- If a verse has no embeddings, it is excluded from the point cloud (the bulk export script only includes verses with UMAP coords)
- If hermeneutics data is missing for a chapter, the HermeneuticsPanel shows "Not yet classified" instead of an error

---

## 12. Build and Development Setup

### 12.1 Frontend (Vite + React)

```bash
cd /mnt/24TB_HDD/hermeneutica/web
npm install
npm run dev          # Starts Vite dev server on :5173
npm run build        # Production build to dist/
npm run preview      # Preview production build
```

**Vite config:** `vite.config.ts`
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/data': 'http://localhost:8000',
    },
  },
  worker: {
    format: 'es',
  },
  build: {
    target: 'esnext',
    rollupOptions: {
      output: {
        manualChunks: {
          three: ['three'],
          r3f: ['@react-three/fiber', '@react-three/drei'],
        },
      },
    },
  },
});
```

### 12.2 Backend (FastAPI)

```bash
cd /mnt/24TB_HDD/hermeneutica/web
pip install -r api/requirements.txt

# Run UMAP pre-computation (one-time, ~5 minutes)
python -m api.precompute.umap_verses
python -m api.precompute.umap_strongs
python -m api.precompute.book_matrix
python -m api.precompute.export_bulk

# Start API server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**api/requirements.txt:**
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
asyncpg>=0.29.0
pydantic>=2.8.0
numpy>=1.26.0
umap-learn>=0.5.6
sentence-transformers>=3.0.0
torch>=2.4.0
```

### 12.3 Database Schema Extension

Before starting the API, run the UMAP table creation:

```bash
sudo -u postgres psql -d bible_research -c "
CREATE TABLE IF NOT EXISTS umap_verse_coords (
    verse_id    INTEGER PRIMARY KEY REFERENCES verses(id),
    x           REAL NOT NULL,
    y           REAL NOT NULL,
    z           REAL NOT NULL,
    model_name  VARCHAR(80) NOT NULL DEFAULT 'Qwen/Qwen3-Embedding-8B'
);
CREATE INDEX IF NOT EXISTS idx_umap_verse_model ON umap_verse_coords (model_name);

CREATE TABLE IF NOT EXISTS umap_strongs_coords (
    strongs_id  INTEGER PRIMARY KEY REFERENCES strongs_entries(id),
    x           REAL NOT NULL,
    y           REAL NOT NULL,
    z           REAL NOT NULL,
    model_name  VARCHAR(80) NOT NULL DEFAULT 'Qwen/Qwen3-Embedding-8B'
);
CREATE INDEX IF NOT EXISTS idx_umap_strongs_model ON umap_strongs_coords (model_name);
"
```

This can also be integrated into the precompute scripts (they create the table if not exists before inserting).

### 12.4 Development Workflow

```
Terminal 1: cd web && npm run dev         # Frontend on :5173
Terminal 2: cd web && uvicorn api.main:app --port 8000 --reload  # Backend on :8000
```

Vite proxies `/api/*` and `/data/*` to the backend. In production, a reverse proxy (nginx/caddy) serves both from a single origin.

---

## 13. Trade-off Decisions

### 13.1 Binary Bulk Load vs. JSON API

**Chosen:** Pre-computed binary file for initial 31K point load.  
**Rejected:** JSON endpoint returning all verse points.  
**Why:** JSON for 31K points with 7 fields each = ~3MB. Binary = ~850KB (400KB gzipped). JSON.parse for 3MB takes ~80ms; DataView scan takes ~5ms. The binary format is 3x faster to transfer and 16x faster to parse.  
**Consequence:** Requires a pre-computation step (`export_bulk.py`). Acceptable because UMAP already requires pre-computation.

### 13.2 InstancedMesh vs. Points/Sprites

**Chosen:** `THREE.InstancedMesh` with low-poly spheres.  
**Rejected:** `THREE.Points` with custom ShaderMaterial.  
**Why:** Points cannot receive lighting, have inconsistent sizes across zoom levels (point size is in pixels, not world units), and raycasting Points requires a custom implementation. InstancedMesh gives physically correct sphere sizes, proper lighting, and built-in raycast support. The GPU cost difference is negligible at 31K instances.  
**Consequence:** Slightly higher VRAM usage (~2MB for instance matrices). Irrelevant on any GPU with >256MB VRAM.

### 13.3 Web Worker for Graph Layout vs. Main Thread

**Chosen:** Dedicated Web Worker running `ngraph.forcelayout3d`.  
**Rejected:** Main-thread layout with requestAnimationFrame yielding.  
**Why:** Force-directed layout for 500 nodes requires ~200ms of computation. Running this on the main thread blocks UI interaction and causes jank. The Web Worker computes asynchronously and posts intermediate results for smooth animated convergence.  
**Consequence:** Adds complexity (message passing, worker lifecycle). Worth it for user experience.

### 13.4 Single Canvas vs. Per-Scene Canvas

**Chosen:** Single persistent `<Canvas>` with conditional children.  
**Rejected:** Separate `<Canvas>` per visualization (destroyed/created on tab switch).  
**Why:** Creating a WebGL context takes ~100-200ms and triggers a full GPU state reset. Switching tabs would cause a visible flash. A single Canvas with swapped children preserves the GL context and allows smooth transitions.  
**Consequence:** All scenes share the same camera setup. Camera state must be managed carefully to avoid inheriting stale positions across views.

### 13.5 Zustand vs. Redux / Jotai / Context

**Chosen:** Zustand with 4 focused stores.  
**Rejected:** Redux (too much boilerplate), Jotai (atomic model doesn't fit well with bulk data), React Context (re-renders entire subtree on state change).  
**Why:** Zustand has zero boilerplate, selector-based subscriptions (prevents unnecessary re-renders), and works well with Three.js's imperative update pattern (`useFrame` reads store directly without causing React re-renders).  
**Consequence:** No devtools as rich as Redux DevTools, but Zustand's `devtools` middleware provides adequate inspection.

### 13.6 FastAPI + asyncpg vs. Express + pg

**Chosen:** Python FastAPI with asyncpg.  
**Rejected:** Node.js Express with pg/postgres.js.  
**Why:** The existing codebase is 100% Python. The research DB helpers, embedding model, and UMAP pipeline are all Python. Rewriting in Node would duplicate logic and create a maintenance split. FastAPI's async/await + asyncpg matches or exceeds Express performance for I/O-bound workloads. The embedding model for search is already loaded in Python.  
**Consequence:** The web app has two runtimes (Node for frontend build, Python for API). This is standard and well-understood.

### 13.7 No Client-Side Router

**Chosen:** Scene switching via Zustand state (`activeScene`).  
**Rejected:** React Router with `/galaxy`, `/graph`, `/words`, `/crossref` routes.  
**Why:** The app is a single-page 3D experience, not a multi-page site. URL-based routing adds complexity (maintaining camera state in URL params, handling deep links to 3D positions) without clear benefit. The `activeScene` state is simpler and avoids unnecessary DOM reconciliation from route changes.  
**Consequence:** No shareable deep links to specific views/selections in v1. This is an acceptable trade-off; deep linking can be added later by syncing sceneStore to URL hash.

---

## 14. Extension Points

### 14.1 Additional Embedding Models

The `model_name` column in all embedding and UMAP tables allows multiple projections. To add a new model:
1. Run embeddings with new model: `python -m src.embeddings --model new-model`
2. Run UMAP for the new model: `python -m api.precompute.umap_verses --model new-model`
3. Add a model selector in the UI that changes the `model_name` query parameter

No code changes required in the API -- model_name is already a filter parameter.

### 14.2 Real-Time Collaborative Exploration

The Zustand stores can be synced to a WebSocket server. Migration path:
1. Add a `zustand/middleware` that broadcasts state deltas via WebSocket
2. Add a FastAPI WebSocket endpoint that relays deltas between clients
3. Use optimistic UI updates with server reconciliation

### 14.3 Temporal Bible Navigation

Adding a timeline view (Genesis through Revelation in chronological order) requires:
1. A `chronological_order` column on `books` or `chapters`
2. A new scene component `TimelineView` that positions points on a 3D timeline axis
3. No API changes needed -- the data is already available

### 14.4 Export and Sharing

Screenshot and state export can be added by:
1. `renderer.domElement.toDataURL()` for 3D screenshots
2. JSON serialization of sceneStore + filterStore for state restoration
3. URL encoding of compressed state for shareable links

---

## 15. Dependency Justification

### Frontend

| Package | Purpose | Why Not Build It | Cost |
|---------|---------|-------------------|------|
| `react` + `react-dom` | UI framework | Industry standard, R3F requires it | ~40KB gzipped |
| `@react-three/fiber` | React renderer for Three.js | Declarative 3D scene graph, lifecycle management, hooks | ~25KB gzipped |
| `@react-three/drei` | R3F utilities (OrbitControls, Text, etc.) | 100+ battle-tested 3D helpers we'd otherwise hand-write | ~50KB (tree-shakeable) |
| `three` | 3D engine | The only production-ready WebGL engine with instancing, raycasting, materials | ~150KB gzipped |
| `zustand` | State management | Zero-boilerplate, selector subscriptions, works with useFrame | ~2KB gzipped |
| `ngraph.forcelayout3d` | Force-directed 3D layout | GPU-quality layout algorithm, proven at scale | ~15KB gzipped |
| `ngraph.graph` | Graph data structure for ngraph | Required by ngraph.forcelayout3d | ~5KB gzipped |
| `tailwindcss` | Utility CSS | Rapid UI styling without CSS files | Build-time only |
| `@radix-ui/react-*` | Accessible UI primitives (via shadcn) | Toggles, sliders, checkboxes with ARIA compliance | ~30KB total |
| `recharts` | 2D charts (radar chart for ethics) | Building SVG radar charts from scratch is error-prone | ~45KB gzipped |
| `class-variance-authority` | Component variant styling (shadcn dependency) | Type-safe variant management | ~2KB |
| `clsx` + `tailwind-merge` | Class name utilities | Conditional class merging | ~1KB |

**Not included (and why):**
- `@react-three/postprocessing`: Bloom/glow effects are visually appealing but add 30KB and reduce performance by 20%. Not worth it for v1.
- `d3`: Only needed for the heatmap color scale, which is trivial to implement with a 10-line function. d3 is 80KB.
- `react-router-dom`: No routes needed (see trade-off 13.7).

### Backend

| Package | Purpose | Why Not Build It | Cost |
|---------|---------|-------------------|------|
| `fastapi` | Async web framework | Best Python async framework, auto-generates OpenAPI docs | Minimal |
| `uvicorn` | ASGI server | Production-grade, HTTP/2 support | Minimal |
| `asyncpg` | Async PostgreSQL driver | 3-5x faster than psycopg2 for async workloads, native prepared statements | Minimal |
| `pydantic` | Data validation/serialization | FastAPI requires it, provides response model validation | Included with FastAPI |
| `numpy` | Array operations | Required by umap-learn, used for embedding parsing | Already in project |
| `umap-learn` | Dimensionality reduction | State-of-the-art manifold learning, no reasonable alternative for this quality | ~5MB installed |
| `sentence-transformers` | Query embedding for search | Needed to embed search queries with the same model as stored embeddings | Already in project |
| `torch` | ML framework | Required by sentence-transformers | Already in project |

---

## Appendix A: Book Metadata Constants

For client-side color mapping, the frontend needs a static mapping of book IDs to metadata. This lives in `src/lib/constants.ts`:

```typescript
export interface BookMeta {
  id: number;
  name: string;
  abbreviation: string;
  testament: 'OT' | 'NT';
  genre: string;
  chapterCount: number;
}

export const BOOKS: BookMeta[] = [
  { id: 1,  name: 'Genesis',       abbreviation: 'Gen',  testament: 'OT', genre: 'Law',        chapterCount: 50 },
  { id: 2,  name: 'Exodus',        abbreviation: 'Exod', testament: 'OT', genre: 'Law',        chapterCount: 40 },
  // ... all 66 books
  { id: 66, name: 'Revelation',    abbreviation: 'Rev',  testament: 'NT', genre: 'Apocalyptic', chapterCount: 22 },
];

export const GENRES = [
  'Law', 'History', 'Wisdom', 'Prophecy', 'Gospel', 'Epistle', 'Apocalyptic'
] as const;

export const EDGE_TYPES = [
  'cross_ref', 'twot_family', 'nave_topic', 'nave_shared', 'semantic_sim', 'strongs_sim'
] as const;

export const ETHICS_SUBSETS = [
  'commonsense', 'deontology', 'justice', 'virtue', 'utilitarianism'
] as const;
```

## Appendix B: Color Palette Specification

```typescript
// src/lib/colors.ts

/** 66-color palette for books, using HSL rotation with saturation variation */
export function bookColor(bookId: number): [number, number, number] {
  const hue = ((bookId - 1) / 66) * 360;
  const sat = 0.65 + (bookId % 3) * 0.1;  // Vary saturation slightly
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

/** Edge type colors for graph visualization */
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
  'heb': [0.85, 0.60, 0.30],   // Warm gold
  'grc': [0.30, 0.55, 0.85],   // Cool blue
};
```

## Appendix C: Binary Bulk Format Reference

### verses_bulk.bin

Little-endian byte order. No header. Direct array of 28-byte records.

```
Record layout (28 bytes):
  Offset  0: int32   verse_id
  Offset  4: float32 x
  Offset  8: float32 y
  Offset 12: float32 z
  Offset 16: uint8   book_id       (1-66)
  Offset 17: uint8   chapter_num   (1-150)
  Offset 18: uint16  verse_num     (1-176)
  Offset 20: uint16  cross_ref_count
  Offset 22: uint8   testament     (0=OT, 1=NT)
  Offset 23: uint8   genre_id      (0-6, index into GENRES constant)
  Offset 24: float32 ethics_max    (0.0-1.0, max of 5 ethics scores)
```

**Frontend parser:**
```typescript
function parseVerseBulk(buffer: ArrayBuffer) {
  const RECORD_SIZE = 28;
  const count = buffer.byteLength / RECORD_SIZE;
  const view = new DataView(buffer);

  const verseIds = new Int32Array(count);
  const positions = new Float32Array(count * 3);
  const metadata = new Uint8Array(count * 6);

  for (let i = 0; i < count; i++) {
    const off = i * RECORD_SIZE;
    verseIds[i] = view.getInt32(off, true);
    positions[i * 3]     = view.getFloat32(off + 4, true);
    positions[i * 3 + 1] = view.getFloat32(off + 8, true);
    positions[i * 3 + 2] = view.getFloat32(off + 12, true);
    metadata[i * 6]     = view.getUint8(off + 16);      // book_id
    metadata[i * 6 + 1] = view.getUint8(off + 17);      // chapter
    metadata[i * 6 + 2] = view.getUint8(off + 18);      // verse_num low byte
    metadata[i * 6 + 3] = view.getUint8(off + 19);      // verse_num high byte
    metadata[i * 6 + 4] = view.getUint8(off + 22);      // testament
    metadata[i * 6 + 5] = view.getUint8(off + 23);      // genre_id
  }

  return { verseIds, positions, metadata, count };
}
```

### strongs_bulk.bin

Little-endian, no header. 24-byte records.

```
Record layout (24 bytes):
  Offset  0: int32   strongs_id
  Offset  4: float32 x
  Offset  8: float32 y
  Offset 12: float32 z
  Offset 16: uint8   language     (0=heb, 1=grc)
  Offset 17: uint8   pos_id      (part_of_speech enum index)
  Offset 18: uint16  usage_count (word_alignments count)
  Offset 20: uint8   has_twot    (0 or 1)
  Offset 21: uint8   reserved
  Offset 22: uint16  reserved
```

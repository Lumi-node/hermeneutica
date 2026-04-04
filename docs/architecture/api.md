# API Reference

Base URL: `https://hermeneutica-api.blueisland-113db368.canadacentral.azurecontainerapps.io`

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |

## Verses

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/verses/bulk` | Binary file (31K verses, 28 bytes each) |
| GET | `/api/verses/{verse_id}` | Full verse detail with interlinear + cross-refs |
| GET | `/api/verses/{verse_id}/crossrefs` | Cross-references with 3D coordinates |
| GET | `/api/verses/by-ref/{book}/{chapter}/{verse}` | Lookup by reference |
| GET | `/api/verses/book/{book_id}` | All verses for a book |

## Knowledge Graph

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/graph/neighborhood/{type}/{id}` | N-hop subgraph (BFS via recursive CTE) |
| GET | `/api/graph/stats` | Edge type counts |

**Query params:** `hops` (1-3), `max_nodes` (10-500), `edge_types` (comma-separated), `min_weight` (0-1)

## Strong's Lexicon

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/strongs/bulk` | Binary file (14K entries, 24 bytes each) |
| GET | `/api/strongs/{strongs_id}` | Full entry with sample verses |
| GET | `/api/strongs/by-number/{number}` | Lookup by Strong's number (H0001, G0001) |

## Cross-References

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/crossrefs/matrix` | 66x66 book density matrix (JSON) |
| GET | `/api/crossrefs/between/{book1}/{book2}` | Refs between two books |

## Hermeneutics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/hermeneutics/chapter/{id}` | Classification + ethics + principles |
| GET | `/api/hermeneutics/by-ref/{book}/{chapter}` | Lookup by reference |
| GET | `/api/hermeneutics/principles` | Browse/filter principles |
| GET | `/api/hermeneutics/stats` | Genre/theme/teaching distributions |

## Exploration Tools

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/explore/theme-search?q=love` | Topic autocomplete |
| GET | `/api/explore/theme-trace?topic=Love` | Chronological verse timeline for a theme |
| GET | `/api/explore/shortest-path?from_type=verse&from_id=1&to_type=verse&to_id=21242` | BFS shortest path |
| GET | `/api/explore/principles?q=forgiveness` | Principle text search |
| GET | `/api/explore/crossref-overlay?preset=ot_to_nt&limit=500` | Cross-ref arcs for Galaxy overlay |

**Overlay presets:** `ot_to_nt`, `nt_to_ot`, `prophets_to_gospels`, `psalms_to_nt`, `torah_to_nt`, `intra_ot`, `intra_nt`

## Analytics Heatmaps

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/explore/heatmap/topics?top_n=25` | 66 books x top N topics |
| GET | `/api/explore/heatmap/ethics` | 66 books x 5 ethics dimensions |
| GET | `/api/explore/heatmap/words?top_n=30` | 66 books x top N Strong's words |

## Contact

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/contact` | Send contact form email (via Resend) |

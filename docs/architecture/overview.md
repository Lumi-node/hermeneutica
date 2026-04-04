# Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Vercel (Frontend)                   │
│  React 18 + TypeScript + React Three Fiber + Zustand  │
│         Static build + /api rewrites to Azure         │
└───────────────────────┬─────────────────────────────┘
                        │ HTTPS
┌───────────────────────▼─────────────────────────────┐
│              Azure Container Apps (API)               │
│           FastAPI + asyncpg + httpx + Pydantic        │
│                   25+ REST endpoints                  │
└───────────────────────┬─────────────────────────────┘
                        │ SSL
┌───────────────────────▼─────────────────────────────┐
│         Azure PostgreSQL Flexible Server              │
│    pgvector (HNSW) + pg_trgm | 1.4GB, 21 tables     │
└─────────────────────────────────────────────────────┘
```

## Frontend Architecture

- **Single Canvas**: One persistent WebGL context — scenes swap children, no context recreation
- **4 Zustand stores**: scene, filter, data, UI — no cross-store imports
- **GPU instancing**: 31K points in a single draw call via `THREE.InstancedMesh`
- **Screen-space hover**: No raycasting against 31K spheres — projects points to 2D at 10fps
- **Binary bulk loading**: 850KB gzipped for all verse positions (28 bytes/vertex)

## Backend Architecture

- **asyncpg**: Non-blocking PostgreSQL with connection pooling
- **Recursive CTEs**: Graph neighborhood traversal in SQL
- **BFS in Python**: Shortest path through 549K edges
- **pgvector HNSW**: Approximate nearest neighbor search on 2000-dim embeddings
- **Static file serving**: Pre-computed binary data served directly

## Data Pipeline

```
Raw Sources → ETL Scripts → PostgreSQL → Embeddings → UMAP → Binary Export → Frontend
     │              │            │            │          │          │
 KJV JSON     psycopg2    21 tables    Qwen3-8B    3D coords   .bin files
 Strong's       bulk       549K edges   GPU batch   centered    28 bytes/pt
 Cross-refs    insert      HNSW index   2000-dim    scaled 10x  gzipped
```

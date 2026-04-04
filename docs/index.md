# Hermeneutica

**A 3D interactive explorer for the Bible's internal structure.**

31,102 verses mapped by semantic meaning. 549,000 connections. 14,298 Hebrew and Greek words. Explore scripture as a living network.

[:material-web: Live Explorer](https://hermeneutica.xyz){ .md-button .md-button--primary }
[:material-github: GitHub](https://github.com/Lumi-node/hermeneutica){ .md-button }

---

## What Is This?

Every verse in the King James Bible has been read by an AI language model (Qwen3-Embedding-8B) which converts its *meaning* into a 2,000-dimensional mathematical fingerprint. Verses with similar meaning get similar fingerprints.

UMAP compresses those 2,000 dimensions into 3D coordinates, preserving neighborhood relationships. The result: **verses that mean similar things appear near each other** in 3D space — regardless of which book, chapter, or testament they come from.

The shape isn't random. It's a literal map of how the Bible's ideas relate to each other in meaning-space.

## Features at a Glance

| Feature | Description |
|---------|-------------|
| **Scripture Galaxy** | 31K verse point cloud with cross-reference threads (55K golden arcs) |
| **Knowledge Graph** | Force-directed 3D graph — 549K edges, 6 relationship types |
| **Word Study** | 14K Strong's Hebrew/Greek entries clustered by semantic similarity |
| **Biblical Analytics** | Heatmaps: cross-refs, topics, ethics, word frequency |
| **Theme Tracer** | Trace any theme from Genesis to Revelation |
| **Shortest Path** | Find how any two verses connect through the knowledge graph |
| **Principle Search** | Search AI-extracted moral principles from scripture |

## The Data

| Dataset | Count |
|---------|-------|
| KJV verses embedded | 31,102 |
| Knowledge graph edges | 549,440 |
| Cross-references | 432,944 |
| Hebrew + Greek words | 14,298 |
| Topic-verse mappings | 92,609 |
| Embedding dimensions | 2,000 |
| Chapter classifications | 288 |
| Distilled moral principles | 1,124 |

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

---

Made by [Automate Capture, LLC](https://www.automate-capture.com)

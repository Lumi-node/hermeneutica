# Quick Start

## Prerequisites

- **PostgreSQL 16** with [pgvector](https://github.com/pgvector/pgvector) and `pg_trgm` extensions
- **Python 3.12+**
- **Node.js 20+**
- **GPU** (recommended for embedding generation — Qwen3-8B needs ~16GB VRAM)

## 1. Clone and Setup

```bash
git clone https://github.com/Lumi-node/hermeneutica.git
cd hermeneutica
cp .env.example .env
# Edit .env with your database credentials
```

## 2. Database

```bash
sudo -u postgres createdb bible_research
sudo -u postgres psql -d bible_research -f sql/schema.sql
```

See [Database Setup](database.md) for the full ETL pipeline.

## 3. Generate Embeddings

```bash
# Requires GPU with ~16GB VRAM
python -m src.embeddings --all

# Build knowledge graph
python -m src.knowledge_graph --all
```

## 4. Pre-compute Web Data

```bash
python -m web.api.precompute.umap_verses
python -m web.api.precompute.umap_strongs
python -m web.api.precompute.book_matrix
python -m web.api.precompute.export_bulk
```

## 5. Run the Web App

```bash
# Terminal 1: Backend
pip install -r web/api/requirements.txt
uvicorn web.api.main:app --port 8000

# Terminal 2: Frontend
cd web && npm install && npm run dev
```

Visit [http://localhost:5173](http://localhost:5173)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `DATABASE_SSL` | For Azure | Set to `true` for SSL connections |
| `ANTHROPIC_API_KEY` | For classifications | Used by hermeneutics classification engine |
| `RESEND_API_KEY` | Optional | For the contact form |
| `CONTACT_EMAIL` | Optional | Where contact form emails are sent |

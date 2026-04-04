# Web App Deployment

## Local Development

```bash
# Backend (from project root)
uvicorn web.api.main:app --port 8000 --reload

# Frontend (from web/ directory)
cd web && npm run dev
```

The Vite dev server proxies `/api/*` and `/data/*` to the backend at port 8000.

## Production Deployment

Hermeneutica uses a split deployment:

- **Frontend**: Vercel (static site + rewrites)
- **Backend**: Azure Container Apps (FastAPI + asyncpg)
- **Database**: Azure PostgreSQL Flexible Server

### Frontend (Vercel)

```bash
cd web
vercel --prod
```

The `vercel.json` handles:

- Building the Vite app
- Rewriting `/api/*` requests to the Azure backend
- Rewriting `/data/*` for static binary files

### Backend (Azure Container Apps)

```bash
az containerapp up \
  --name hermeneutica-api \
  --resource-group YOUR_RG \
  --source web/ \
  --env-vars "DATABASE_URL=postgresql://..." "DATABASE_SSL=true" "RESEND_API_KEY=re_..."
```

### Pre-computed Data

Before the web app works, you need to generate the UMAP coordinates and binary export files:

```bash
python -m web.api.precompute.umap_verses      # ~40 seconds
python -m web.api.precompute.umap_strongs      # ~20 seconds
python -m web.api.precompute.book_matrix       # ~5 seconds
python -m web.api.precompute.export_bulk       # ~10 seconds
```

This creates:

- `public/data/verses_bulk.bin` — 851KB (31K verses x 28 bytes)
- `public/data/strongs_bulk.bin` — 336KB (14K entries x 24 bytes)
- `public/data/book_matrix.json` — 404KB (66x66 cross-ref density)

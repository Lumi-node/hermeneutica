from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from . import db
from .routers import verses, graph, strongs, crossrefs, hermeneutics, search, explore, journal


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db_pool()
    try:
        yield
    finally:
        await db.close_db_pool()


app = FastAPI(
    title="Hermeneutica Explorer API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
_web_dir = Path(__file__).resolve().parent.parent
data_dir = _web_dir / "public" / "data"
if data_dir.exists():
    app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")

# Include routers (they already have prefixes defined)
app.include_router(verses.router, prefix="/api")
app.include_router(strongs.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(crossrefs.router, prefix="/api")
app.include_router(hermeneutics.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(explore.router, prefix="/api")
app.include_router(journal.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

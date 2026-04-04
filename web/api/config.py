import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bible_research")

# Azure Postgres requires SSL
DATABASE_SSL = os.getenv("DATABASE_SSL", "").lower() in ("true", "1", "require")

DB_POOL_MIN = 2
DB_POOL_MAX = 10

EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"
EMBEDDING_DIM = 2000

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 200

NEIGHBORHOOD_MAX_HOPS = 3
NEIGHBORHOOD_MAX_NODES = 500
"""ETL configuration — paths, database URL, constants."""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
HERMENEUTICS_DIR = DATA_DIR / "hermeneutics"
SQL_DIR = PROJECT_ROOT / "sql"
TRAINING_DATA_DIR = PROJECT_ROOT / "training_data"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres@localhost:5432/bible_research",
)

# Parse components for psycopg2
DB_NAME = "bible_research"
DB_USER = os.environ.get("DB_USER", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

# ---------------------------------------------------------------------------
# Embedding model
# ---------------------------------------------------------------------------

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_DIM = 768

# ---------------------------------------------------------------------------
# ETL
# ---------------------------------------------------------------------------

BATCH_SIZE = 500  # rows per bulk insert

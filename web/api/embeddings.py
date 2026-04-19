"""Query-time text embedding for semantic search endpoints.

Uses fastembed (ONNX runtime, CPU-only) with BAAI/bge-small-en-v1.5 (384-dim).
The model is loaded lazily on first call and kept in memory for the process
lifetime. ONNX inference takes ~20-40ms per query on typical CPU.

This matches the model used to embed principles in etl/11_embed_principles.py,
so query vectors live in the same space as the stored principle embeddings.
"""

from __future__ import annotations

from threading import Lock
from typing import List

MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384

_model = None
_lock = Lock()


def _get_model():
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is None:
            # Import here so the FastAPI app can start even if fastembed is
            # somehow unavailable — endpoints that need it will surface the error.
            from fastembed import TextEmbedding
            _model = TextEmbedding(MODEL_NAME)
    return _model


def embed_query(text: str) -> List[float]:
    """Embed a single text string, return a list of floats of length EMBEDDING_DIM."""
    vec = next(_get_model().embed([text]))
    return [float(x) for x in vec]


def format_pgvector(vec: List[float]) -> str:
    """Format a float list for pgvector insertion / comparison via `::vector` cast."""
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"

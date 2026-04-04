from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException
from typing import List

from .. import db
from .. import config
from ..models.search import SemanticMatch

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/verses", response_model=List[SemanticMatch])
async def search_verses(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=200, description="Maximum number of results")
):
    pool = await db.get_pool()
    query = """
        SELECT v.id, b.name, ch.chapter_number, v.verse_number, v.text,
               0.5::float as similarity
        FROM verses v
        JOIN chapters ch ON ch.id = v.chapter_id
        JOIN books b ON b.id = ch.book_id
        WHERE v.translation_id = 1 AND v.text ILIKE '%' || $1 || '%'
        LIMIT $2
    """
    rows = await pool.fetch(query, q, limit)
    return [
        SemanticMatch(
            verse_id=r["id"],
            book_name=r["name"],
            chapter_number=r["chapter_number"],
            verse_number=r["verse_number"],
            text=r["text"],
            similarity=r["similarity"]
        )
        for r in rows
    ]


@router.get("/nearest", response_model=List[SemanticMatch])
async def find_nearest_verses(
    verse_id: int = Query(..., description="Verse ID to find nearest matches for"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of similar verses")
):
    pool = await db.get_pool()

    # Verify verse exists
    verify_query = "SELECT 1 FROM verses WHERE id = $1"
    verse_exists = await pool.fetchrow(verify_query, verse_id)
    if not verse_exists:
        raise HTTPException(status_code=404, detail="Verse not found")

    query = """
        SELECT v.id, b.name, ch.chapter_number, v.verse_number, v.text,
               1.0 - (ve2.embedding <=> ve.embedding) as similarity
        FROM verse_embeddings ve
        JOIN verse_embeddings ve2 ON ve.model_name = ve2.model_name
        JOIN verses v ON v.id = ve2.verse_id
        JOIN chapters ch ON ch.id = v.chapter_id
        JOIN books b ON b.id = ch.book_id
        WHERE ve.verse_id = $1
          AND ve.model_name = $2
          AND ve2.verse_id != $1
        ORDER BY ve2.embedding <=> ve.embedding
        LIMIT $3
    """
    rows = await pool.fetch(query, verse_id, config.EMBEDDING_MODEL, limit)
    return [
        SemanticMatch(
            verse_id=r["id"],
            book_name=r["name"],
            chapter_number=r["chapter_number"],
            verse_number=r["verse_number"],
            text=r["text"],
            similarity=r["similarity"]
        )
        for r in rows
    ]

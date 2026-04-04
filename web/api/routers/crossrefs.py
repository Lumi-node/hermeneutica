from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List

from .. import db
from ..models.crossref import CrossRefArc

router = APIRouter(prefix="/crossrefs", tags=["crossrefs"])


@router.get("/matrix", response_class=FileResponse)
async def get_matrix():
    _web_dir = Path(__file__).resolve().parent.parent.parent
    file_path = _web_dir / "public" / "data" / "book_matrix.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Matrix file not found")
    return FileResponse(path=file_path, media_type="application/json")


@router.get("/between/{book1_id}/{book2_id}", response_model=List[CrossRefArc])
async def get_cross_refs_between_books(
    book1_id: int,
    book2_id: int,
    limit: int = Query(200, ge=1, le=500)
):
    pool = await db.get_pool()
    query = """
        SELECT cr.source_verse_id, cr.target_verse_id, cr.source_ref, cr.target_ref, cr.relevance_score,
               COALESCE(uv1.x, 0.0) as source_x, COALESCE(uv1.y, 0.0) as source_y, COALESCE(uv1.z, 0.0) as source_z,
               COALESCE(uv2.x, 0.0) as target_x, COALESCE(uv2.y, 0.0) as target_y, COALESCE(uv2.z, 0.0) as target_z
        FROM cross_references cr
        JOIN verses v1 ON v1.id = cr.source_verse_id
        JOIN verses v2 ON v2.id = cr.target_verse_id
        JOIN chapters ch1 ON ch1.id = v1.chapter_id
        JOIN chapters ch2 ON ch2.id = v2.chapter_id
        LEFT JOIN umap_verse_coords uv1 ON uv1.verse_id = v1.id
        LEFT JOIN umap_verse_coords uv2 ON uv2.verse_id = v2.id
        WHERE ch1.book_id = $1 AND ch2.book_id = $2
        ORDER BY cr.relevance_score DESC
        LIMIT $3
    """
    rows = await pool.fetch(query, book1_id, book2_id, limit)

    if not rows:
        # Check if books exist
        book_check_query = "SELECT id FROM books WHERE id = $1 OR id = $2"
        books = await pool.fetch(book_check_query, book1_id, book2_id)
        if len(books) < 2:
            raise HTTPException(status_code=404, detail="One or both books not found")
        return []

    return [
        CrossRefArc(
            source_verse_id=r["source_verse_id"],
            target_verse_id=r["target_verse_id"],
            source_ref=r["source_ref"],
            target_ref=r["target_ref"],
            relevance_score=r["relevance_score"],
            source_x=r["source_x"],
            source_y=r["source_y"],
            source_z=r["source_z"],
            target_x=r["target_x"],
            target_y=r["target_y"],
            target_z=r["target_z"]
        )
        for r in rows
    ]
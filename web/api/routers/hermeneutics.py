from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from .. import db
from .. import config
from ..models.hermeneutics import Classification, EthicsScore, PrincipleBrief


class HermeneuticsStats(BaseModel):
    genre_stats: List[Dict[str, Any]]
    theme_stats: List[Dict[str, Any]]
    teaching_type_stats: List[Dict[str, Any]]


router = APIRouter(prefix="/hermeneutics", tags=["hermeneutics"])


@router.get("/chapter/{chapter_id}", response_model=Classification)
async def get_classification_by_chapter(chapter_id: int):
    pool = await db.get_pool()

    # Get classification
    classification_query = """
        SELECT id, chapter_id, genre, genre_confidence, themes, teaching_type, classified_by, classified_at
        FROM passage_classifications
        WHERE chapter_id = $1
    """
    classification_row = await pool.fetchrow(classification_query, chapter_id)
    if not classification_row:
        raise HTTPException(status_code=404, detail="Classification not found")

    # Get book name and chapter number
    book_query = """
        SELECT b.name, ch.chapter_number
        FROM books b
        JOIN chapters ch ON ch.book_id = b.id
        WHERE ch.id = $1
    """
    book_row = await pool.fetchrow(book_query, chapter_id)
    if not book_row:
        raise HTTPException(status_code=404, detail="Chapter not found")

    book_name = book_row["name"]
    chapter_number = book_row["chapter_number"]

    # Get ethics scores
    ethics_query = """
        SELECT ethics_subset, relevance_score
        FROM passage_ethics_scores
        WHERE classification_id = $1
    """
    ethics_rows = await pool.fetch(ethics_query, classification_row["id"])
    ethics_scores = [
        EthicsScore(
            ethics_subset=r["ethics_subset"],
            relevance_score=r["relevance_score"]
        )
        for r in ethics_rows
    ]

    # Get principles
    principles_query = """
        SELECT id, principle_text, principle_order
        FROM distilled_principles
        WHERE classification_id = $1
        ORDER BY principle_order
    """
    principle_rows = await pool.fetch(principles_query, classification_row["id"])
    principles = [
        PrincipleBrief(
            principle_id=p["id"],
            principle_text=p["principle_text"],
            principle_order=p["principle_order"]
        )
        for p in principle_rows
    ]

    return Classification(
        classification_id=classification_row["id"],
        chapter_id=classification_row["chapter_id"],
        book_name=book_name,
        chapter_number=chapter_number,
        genre=classification_row["genre"],
        genre_confidence=classification_row["genre_confidence"],
        themes=classification_row["themes"] or [],
        teaching_type=classification_row["teaching_type"],
        ethics_scores=ethics_scores,
        principles=principles,
        classified_by=classification_row["classified_by"],
        classified_at=classification_row["classified_at"]
    )


@router.get("/by-ref/{book}/{chapter}", response_model=Classification)
async def get_classification_by_reference(book: str, chapter: int):
    pool = await db.get_pool()
    query = """
        SELECT ch.id
        FROM chapters ch
        JOIN books b ON b.id = ch.book_id
        WHERE b.name = $1 AND ch.chapter_number = $2
    """
    result = await pool.fetchrow(query, book, chapter)
    if not result:
        raise HTTPException(status_code=404, detail="Chapter not found")
    chapter_id = result["id"]
    return await get_classification_by_chapter(chapter_id)


@router.get("/principles", response_model=List[PrincipleBrief])
async def list_principles(
    theme: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(config.DEFAULT_PAGE_SIZE, ge=1, le=config.MAX_PAGE_SIZE)
):
    pool = await db.get_pool()
    offset = (page - 1) * page_size

    if theme:
        query = """
            SELECT DISTINCT dp.id, dp.principle_text, dp.principle_order
            FROM distilled_principles dp
            JOIN passage_classifications pc ON pc.id = dp.classification_id
            WHERE pc.themes @> ARRAY[$1::text]
            ORDER BY dp.principle_order
            LIMIT $2 OFFSET $3
        """
        rows = await pool.fetch(query, theme, page_size, offset)
    else:
        query = """
            SELECT id, principle_text, principle_order
            FROM distilled_principles
            ORDER BY principle_order
            LIMIT $1 OFFSET $2
        """
        rows = await pool.fetch(query, page_size, offset)

    return [
        PrincipleBrief(
            principle_id=r["id"],
            principle_text=r["principle_text"],
            principle_order=r["principle_order"]
        )
        for r in rows
    ]


@router.get("/stats", response_model=HermeneuticsStats)
async def get_hermeneutics_stats():
    pool = await db.get_pool()

    # Genre counts
    genre_query = """
        SELECT genre, COUNT(*) as count
        FROM passage_classifications
        GROUP BY genre
        ORDER BY count DESC
    """
    genre_rows = await pool.fetch(genre_query)
    genre_stats = [{"label": r["genre"], "count": r["count"]} for r in genre_rows]

    # Theme distribution
    theme_query = """
        SELECT theme, COUNT(*) as count
        FROM (SELECT UNNEST(themes) as theme FROM passage_classifications) t
        GROUP BY theme
        ORDER BY count DESC
    """
    theme_rows = await pool.fetch(theme_query)
    theme_stats = [{"label": r["theme"], "count": r["count"]} for r in theme_rows]

    # Teaching type counts
    teaching_query = """
        SELECT teaching_type, COUNT(*) as count
        FROM passage_classifications
        GROUP BY teaching_type
        ORDER BY count DESC
    """
    teaching_rows = await pool.fetch(teaching_query)
    teaching_type_stats = [{"label": r["teaching_type"], "count": r["count"]} for r in teaching_rows]

    return HermeneuticsStats(
        genre_stats=genre_stats,
        theme_stats=theme_stats,
        teaching_type_stats=teaching_type_stats
    )

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List

from .. import db
from ..models.verse import VerseDetail, VersePoint, WordAlignment, CrossRefBrief, TopicRef

router = APIRouter(prefix="/verses", tags=["verses"])

_WEB_DIR = Path(__file__).resolve().parent.parent.parent
BULK_FILE = _WEB_DIR / "public" / "data" / "verses_bulk.bin"


@router.get("/bulk", response_class=FileResponse)
async def get_bulk_verses():
    if not BULK_FILE.exists():
        raise HTTPException(status_code=404, detail="Bulk file not found")
    return FileResponse(BULK_FILE)


@router.get("/{verse_id}", response_model=VerseDetail)
async def get_verse_detail(verse_id: int):
    pool = await db.get_pool()
    query_verse = """
        SELECT v.id, b.name, b.abbreviation, ch.chapter_number, v.verse_number, b.testament, v.text
        FROM verses v
        JOIN chapters ch ON ch.id = v.chapter_id
        JOIN books b ON b.id = ch.book_id
        WHERE v.id = $1 AND v.translation_id = 1
    """
    verse_row = await pool.fetchrow(query_verse, verse_id)
    if not verse_row:
        raise HTTPException(status_code=404, detail="Verse not found")

    query_words = """
        SELECT wa.word_position, wa.original_word, wa.transliteration, wa.english_gloss,
               wa.strongs_number, wa.morphology_code,
               COALESCE(se.root_definition, '') as root_definition
        FROM word_alignments wa
        LEFT JOIN strongs_entries se ON se.strongs_number = wa.strongs_number
        WHERE wa.verse_id = $1
        ORDER BY wa.word_position
    """
    word_rows = await pool.fetch(query_words, verse_id)

    query_crossrefs = """
        SELECT target_verse_id, target_ref, relevance_score, LEFT(v2.text, 120) as text_preview
        FROM cross_references cr
        JOIN verses v2 ON v2.id = cr.target_verse_id
        WHERE cr.source_verse_id = $1
        ORDER BY relevance_score DESC
        LIMIT 20
    """
    crossref_rows = await pool.fetch(query_crossrefs, verse_id)

    query_nave = """
        SELECT nt.topic
        FROM nave_topic_verses ntv
        JOIN nave_topics nt ON nt.id = ntv.topic_id
        WHERE ntv.verse_id = $1
    """
    nave_rows = await pool.fetch(query_nave, verse_id)

    return VerseDetail(
        verse_id=verse_row["id"],
        book_name=verse_row["name"],
        book_abbreviation=verse_row["abbreviation"],
        chapter_number=verse_row["chapter_number"],
        verse_number=verse_row["verse_number"],
        testament=verse_row["testament"],
        text=verse_row["text"],
        word_alignments=[WordAlignment(**dict(w)) for w in word_rows],
        cross_references=[CrossRefBrief(
            target_verse_id=c["target_verse_id"],
            target_ref=c["target_ref"],
            relevance_score=c["relevance_score"],
            text_preview=c["text_preview"]
        ) for c in crossref_rows],
        nave_topics=[TopicRef(topic=n["topic"]) for n in nave_rows]
    )


@router.get("/{verse_id}/crossrefs", response_model=List[CrossRefBrief])
async def get_verse_crossrefs_with_coords(verse_id: int):
    pool = await db.get_pool()
    query = """
        SELECT cr.target_verse_id, cr.target_ref, cr.relevance_score, LEFT(v2.text, 120) as text_preview,
               uv2.x, uv2.y, uv2.z
        FROM cross_references cr
        JOIN verses v2 ON v2.id = cr.target_verse_id
        LEFT JOIN umap_verse_coords uv2 ON uv2.verse_id = v2.id
        WHERE cr.source_verse_id = $1
        ORDER BY cr.relevance_score DESC
        LIMIT 100
    """
    rows = await pool.fetch(query, verse_id)
    return [
        CrossRefBrief(
            target_verse_id=r["target_verse_id"],
            target_ref=r["target_ref"],
            relevance_score=r["relevance_score"],
            text_preview=r["text_preview"],
            x=r["x"],
            y=r["y"],
            z=r["z"]
        )
        for r in rows
    ]


@router.get("/by-ref/{book}/{chapter}/{verse}", response_model=VerseDetail)
async def get_verse_by_reference(book: str, chapter: int, verse: int):
    pool = await db.get_pool()
    query = """
        SELECT v.id
        FROM verses v
        JOIN chapters ch ON ch.id = v.chapter_id
        JOIN books b ON b.id = ch.book_id
        WHERE b.name = $1 AND ch.chapter_number = $2 AND v.verse_number = $3 AND v.translation_id = 1
    """
    result = await pool.fetchrow(query, book, chapter, verse)
    if not result:
        raise HTTPException(status_code=404, detail="Reference not found")
    verse_id = result["id"]
    return await get_verse_detail(verse_id)


@router.get("/book/{book_id}", response_model=List[VersePoint])
async def get_book_verse_points(book_id: int):
    pool = await db.get_pool()
    query = """
        SELECT v.id, b.name, ch.chapter_number, v.verse_number, uv.x, uv.y, uv.z
        FROM verses v
        JOIN chapters ch ON ch.id = v.chapter_id
        JOIN books b ON b.id = ch.book_id
        LEFT JOIN umap_verse_coords uv ON uv.verse_id = v.id
        WHERE b.id = $1 AND v.translation_id = 1
        ORDER BY ch.chapter_number, v.verse_number
    """
    rows = await pool.fetch(query, book_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Book not found or has no verses")
    return [
        VersePoint(
            verse_id=r["id"],
            book_name=r["name"],
            chapter_number=r["chapter_number"],
            verse_number=r["verse_number"],
            x=r["x"],
            y=r["y"],
            z=r["z"]
        )
        for r in rows
    ]
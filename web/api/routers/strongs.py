from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List

from .. import db
from ..models.strongs import StrongsDetail, StrongsVerseRef

router = APIRouter(prefix="/strongs", tags=["strongs"])

_WEB_DIR = Path(__file__).resolve().parent.parent.parent
DATA_FILE_PATH = _WEB_DIR / "public" / "data" / "strongs_bulk.bin"


@router.get("/bulk", response_class=FileResponse)
async def get_bulk_data():
    if not DATA_FILE_PATH.exists():
        raise HTTPException(status_code=404, detail="Bulk data file not found")
    return FileResponse(path=DATA_FILE_PATH, media_type="application/octet-stream")


@router.get("/{strongs_id}", response_model=StrongsDetail)
async def get_strongs_entry(strongs_id: int):
    pool = await db.get_pool()
    query_entry = """
        SELECT id, strongs_number, language, original_word, transliteration, pronunciation,
               root_definition, detailed_definition, kjv_usage, part_of_speech
        FROM strongs_entries
        WHERE id = $1
    """
    entry = await pool.fetchrow(query_entry, strongs_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Strong's entry not found")

    strongs_number = entry["strongs_number"]

    query_usage_count = """
        SELECT COUNT(*) as count
        FROM word_alignments
        WHERE strongs_number = $1
    """
    usage_result = await pool.fetchrow(query_usage_count, strongs_number)
    usage_count = usage_result["count"] if usage_result else 0

    query_sample_verses = """
        SELECT wa.verse_id, b.name, ch.chapter_number, v.verse_number,
               SUBSTRING(v.text FROM 1 FOR 80) as text_preview, wa.word_position
        FROM word_alignments wa
        JOIN verses v ON v.id = wa.verse_id
        JOIN chapters ch ON ch.id = v.chapter_id
        JOIN books b ON b.id = ch.book_id
        WHERE wa.strongs_number = $1
        LIMIT 10
    """
    sample_verses_rows = await pool.fetch(query_sample_verses, strongs_number)
    sample_verses = [
        StrongsVerseRef(
            verse_id=sv["verse_id"],
            book_name=sv["name"],
            chapter_number=sv["chapter_number"],
            verse_number=sv["verse_number"],
            text_preview=sv["text_preview"],
            word_position=sv["word_position"]
        )
        for sv in sample_verses_rows
    ]

    return StrongsDetail(
        strongs_id=entry["id"],
        strongs_number=entry["strongs_number"],
        language=entry["language"],
        original_word=entry["original_word"],
        transliteration=entry["transliteration"],
        pronunciation=entry["pronunciation"],
        root_definition=entry["root_definition"],
        detailed_definition=entry["detailed_definition"],
        kjv_usage=entry["kjv_usage"],
        part_of_speech=entry["part_of_speech"],
        usage_count=usage_count,
        sample_verses=sample_verses
    )


@router.get("/by-number/{strongs_number}", response_model=StrongsDetail)
async def get_strongs_entry_by_number(strongs_number: str):
    pool = await db.get_pool()
    query_id = "SELECT id FROM strongs_entries WHERE strongs_number = $1"
    result = await pool.fetchrow(query_id, strongs_number)
    if not result:
        raise HTTPException(status_code=404, detail="Strong's entry not found")
    strongs_id = result["id"]
    return await get_strongs_entry(strongs_id)
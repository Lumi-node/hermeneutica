from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class StrongsPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    strongs_id: int
    strongs_number: str
    language: str
    original_word: str
    transliteration: str
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


class StrongsVerseRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    verse_id: int
    book_name: str
    chapter_number: int
    verse_number: int
    text_preview: str
    word_position: int


class StrongsDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    strongs_id: int
    strongs_number: str
    language: str
    original_word: str
    transliteration: str
    pronunciation: Optional[str] = None
    root_definition: str
    detailed_definition: str
    kjv_usage: Optional[str] = None
    part_of_speech: Optional[str] = None
    usage_count: int
    sample_verses: List[StrongsVerseRef]
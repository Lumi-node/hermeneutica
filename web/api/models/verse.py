from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class VersePoint(BaseModel):
    verse_id: int
    book_name: str
    chapter_number: int
    verse_number: int
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class WordAlignment(BaseModel):
    word_position: int
    original_word: str
    transliteration: Optional[str] = None
    english_gloss: str
    strongs_number: Optional[str] = None
    morphology_code: Optional[str] = None
    root_definition: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class CrossRefBrief(BaseModel):
    target_verse_id: int
    target_ref: str
    relevance_score: float
    text_preview: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TopicRef(BaseModel):
    topic: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


class VerseDetail(BaseModel):
    verse_id: int
    book_name: str
    book_abbreviation: str
    chapter_number: int
    verse_number: int
    text: str
    testament: str
    word_alignments: List[WordAlignment]
    cross_references: List[CrossRefBrief]
    nave_topics: List[TopicRef]

    model_config = ConfigDict(arbitrary_types_allowed=True)
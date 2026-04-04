from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Annotated
from pydantic import ConfigDict


class SemanticMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    verse_id: int
    book_name: str
    chapter_number: int
    verse_number: int
    text: str
    similarity: float = Field(ge=0.0, le=1.0)


class StrongsMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    strongs_id: int
    strongs_number: str
    language: str
    original_word: str
    transliteration: str
    root_definition: str
    usage_count: int
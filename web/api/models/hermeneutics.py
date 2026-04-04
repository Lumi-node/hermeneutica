from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class EthicsScore(BaseModel):
    ethics_subset: str
    relevance_score: float = Field(..., ge=0, le=1)


class PrincipleBrief(BaseModel):
    principle_id: int
    principle_text: str
    principle_order: int
    ethics_scores: Optional[List[EthicsScore]] = None


class Classification(BaseModel):
    classification_id: int
    chapter_id: int
    book_name: str
    chapter_number: int
    genre: str
    genre_confidence: float = Field(..., ge=0, le=1)
    themes: List[str]
    teaching_type: str
    ethics_scores: List[EthicsScore]
    principles: List[PrincipleBrief]
    classified_by: Optional[str] = None
    classified_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
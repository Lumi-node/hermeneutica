from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ProofText(BaseModel):
    proof_group: str
    osis_ref: str
    verse_id: Optional[int] = None
    verse_text: Optional[str] = None
    book_name: Optional[str] = None
    chapter_number: Optional[int] = None
    verse_number: Optional[int] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ConfessionItem(BaseModel):
    id: int
    item_number: int
    item_type: str
    title: Optional[str] = None
    question_text: Optional[str] = None
    answer_text: Optional[str] = None
    answer_with_proofs: Optional[str] = None
    sort_order: int
    proof_texts: List[ProofText]
    children: List[ConfessionItem]
    model_config = ConfigDict(arbitrary_types_allowed=True)


ConfessionItem.model_rebuild()


class ConfessionDetail(BaseModel):
    id: int
    name: str
    abbreviation: str
    confession_type: str
    tradition: str
    year: int
    authors: Optional[str] = None
    items: List[ConfessionItem]
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ConfessionSummary(BaseModel):
    id: int
    name: str
    abbreviation: str
    confession_type: str
    tradition: str
    year: int
    authors: Optional[str] = None
    item_count: int
    proof_text_count: int
    model_config = ConfigDict(arbitrary_types_allowed=True)


class SearchResult(BaseModel):
    id: int
    confession_id: int
    abbreviation: str
    item_number: int
    item_type: str
    title: Optional[str] = None
    answer_preview: Optional[str] = None
    question_preview: Optional[str] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)
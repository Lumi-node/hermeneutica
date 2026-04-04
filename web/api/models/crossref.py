from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Annotated
from typing_extensions import TypedDict
from pydantic import ConfigDict


class CrossRefArc(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_verse_id: int
    target_verse_id: int
    source_ref: str
    target_ref: str
    relevance_score: Annotated[float, Field(ge=0.0, le=1.0)]
    source_x: float
    source_y: float
    source_z: float
    target_x: float
    target_y: float
    target_z: float


class BookMatrixEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book1_id: int
    book1_name: str
    book2_id: int
    book2_name: str
    cross_ref_count: int
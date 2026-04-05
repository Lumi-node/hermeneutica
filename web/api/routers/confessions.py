from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import List
from .. import db
from ..models.confession import ConfessionSummary, ConfessionDetail, ConfessionItem, ProofText, SearchResult

router = APIRouter(prefix="/confessions", tags=["confessions"])


def _build_item_tree(item_row: dict, items_by_id: dict, proof_texts_by_item_id: dict) -> ConfessionItem:
    children = [
        _build_item_tree(items_by_id[cid], items_by_id, proof_texts_by_item_id)
        for cid in item_row.get("child_ids", [])
        if cid in items_by_id
    ]
    proofs = [ProofText(**p) for p in proof_texts_by_item_id.get(item_row["id"], [])]
    return ConfessionItem(
        id=item_row["id"],
        item_number=item_row["item_number"],
        item_type=item_row["item_type"],
        title=item_row["title"],
        question_text=item_row["question_text"],
        answer_text=item_row["answer_text"],
        answer_with_proofs=item_row["answer_with_proofs"],
        sort_order=item_row["sort_order"],
        proof_texts=proofs,
        children=children,
    )


@router.get("/", response_model=List[ConfessionSummary])
async def get_confessions():
    pool = await db.get_pool()
    query = """
        SELECT c.id, c.name, c.abbreviation, c.confession_type, c.tradition, c.year, c.authors,
               (SELECT count(*) FROM confession_items ci WHERE ci.confession_id = c.id) as item_count,
               (SELECT count(*) FROM confession_proof_texts cpt JOIN confession_items ci2 ON ci2.id = cpt.item_id WHERE ci2.confession_id = c.id) as proof_text_count
        FROM confessions c
        ORDER BY c.year;
    """
    rows = await pool.fetch(query)
    return [ConfessionSummary(**dict(row)) for row in rows]


@router.get("/search", response_model=List[SearchResult])
async def search_confessions(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=500)
):
    if not q.strip():
        return []

    pool = await db.get_pool()
    query = """
        SELECT ci.id, ci.confession_id, c.abbreviation, ci.item_number, ci.item_type, ci.title,
               LEFT(ci.answer_text, 200) as answer_preview,
               LEFT(ci.question_text, 200) as question_preview
        FROM confession_items ci
        JOIN confessions c ON c.id = ci.confession_id
        WHERE ci.answer_text ILIKE '%' || $1 || '%'
           OR ci.question_text ILIKE '%' || $1 || '%'
           OR ci.title ILIKE '%' || $1 || '%'
        ORDER BY c.year, ci.sort_order
        LIMIT $2;
    """
    rows = await pool.fetch(query, q, limit)
    return [SearchResult(**dict(row)) for row in rows]


@router.get("/{confession_id}", response_model=ConfessionDetail)
async def get_confession(confession_id: int):
    pool = await db.get_pool()

    # Fetch confession metadata
    confession_query = """
        SELECT c.id, c.name, c.abbreviation, c.confession_type, c.tradition, c.year, c.authors
        FROM confessions c
        WHERE c.id = $1
    """
    confession_row = await pool.fetchrow(confession_query, confession_id)
    if not confession_row:
        raise HTTPException(status_code=404, detail="Confession not found")

    # Fetch all items
    items_query = """
        SELECT ci.id, ci.parent_id, ci.item_number, ci.item_type, ci.title,
               ci.question_text, ci.answer_text, ci.answer_with_proofs, ci.sort_order
        FROM confession_items ci
        WHERE ci.confession_id = $1
        ORDER BY ci.sort_order;
    """
    item_rows = await pool.fetch(items_query, confession_id)
    if not item_rows:
        raise HTTPException(status_code=404, detail="No items found for this confession")

    # Build items dict by id
    items_by_id = {row["id"]: dict(row) for row in item_rows}

    # Add child_ids to each item
    for item in item_rows:
        parent_id = item["parent_id"]
        if parent_id is not None and parent_id != 0:
            parent = items_by_id.get(parent_id)
            if parent:
                if "child_ids" not in parent:
                    parent["child_ids"] = []
                parent["child_ids"].append(item["id"])

    # Fetch all proof texts
    proof_texts_query = """
        SELECT cpt.item_id, cpt.proof_group, cpt.osis_ref, cpt.verse_id, v.text as verse_text,
               b.name as book_name, ch.chapter_number, v.verse_number
        FROM confession_proof_texts cpt
        JOIN confession_items ci ON ci.id = cpt.item_id
        LEFT JOIN verses v ON v.id = cpt.verse_id AND v.translation_id = 1
        LEFT JOIN chapters ch ON ch.id = v.chapter_id
        LEFT JOIN books b ON b.id = ch.book_id
        WHERE ci.confession_id = $1
        ORDER BY cpt.item_id, cpt.proof_group;
    """
    proof_text_rows = await pool.fetch(proof_texts_query, confession_id)

    # Build proof_texts dict by item_id
    proof_texts_by_item_id = {}
    for row in proof_text_rows:
        item_id = row["item_id"]
        if item_id not in proof_texts_by_item_id:
            proof_texts_by_item_id[item_id] = []
        proof_texts_by_item_id[item_id].append(dict(row))

    # Build top-level items (those with no parent)
    root_items = []
    for item in item_rows:
        parent_id = item["parent_id"]
        if parent_id is None or parent_id == 0:
            tree_item = _build_item_tree(dict(item), items_by_id, proof_texts_by_item_id)
            root_items.append(tree_item)

    return ConfessionDetail(
        id=confession_row["id"],
        name=confession_row["name"],
        abbreviation=confession_row["abbreviation"],
        confession_type=confession_row["confession_type"],
        tradition=confession_row["tradition"],
        year=confession_row["year"],
        authors=confession_row["authors"],
        items=root_items,
    )


@router.get("/{confession_id}/item/{item_id}", response_model=ConfessionItem)
async def get_confession_item(confession_id: int, item_id: int):
    pool = await db.get_pool()

    # Fetch the item
    item_query = """
        SELECT ci.id, ci.parent_id, ci.item_number, ci.item_type, ci.title,
               ci.question_text, ci.answer_text, ci.answer_with_proofs, ci.sort_order
        FROM confession_items ci
        WHERE ci.confession_id = $1 AND ci.id = $2;
    """
    item_row = await pool.fetchrow(item_query, confession_id, item_id)
    if not item_row:
        raise HTTPException(status_code=404, detail="Item not found")

    # Fetch proof texts for this item
    proof_texts_query = """
        SELECT cpt.item_id, cpt.proof_group, cpt.osis_ref, cpt.verse_id, v.text as verse_text,
               b.name as book_name, ch.chapter_number, v.verse_number
        FROM confession_proof_texts cpt
        JOIN confession_items ci ON ci.id = cpt.item_id
        LEFT JOIN verses v ON v.id = cpt.verse_id AND v.translation_id = 1
        LEFT JOIN chapters ch ON ch.id = v.chapter_id
        LEFT JOIN books b ON b.id = ch.book_id
        WHERE ci.confession_id = $1 AND cpt.item_id = $2
        ORDER BY cpt.proof_group;
    """
    proof_text_rows = await pool.fetch(proof_texts_query, confession_id, item_id)

    proofs = [ProofText(**dict(row)) for row in proof_text_rows]

    return ConfessionItem(
        id=item_row["id"],
        item_number=item_row["item_number"],
        item_type=item_row["item_type"],
        title=item_row["title"],
        question_text=item_row["question_text"],
        answer_text=item_row["answer_text"],
        answer_with_proofs=item_row["answer_with_proofs"],
        sort_order=item_row["sort_order"],
        proof_texts=proofs,
        children=[],
    )
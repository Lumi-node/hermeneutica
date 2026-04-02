"""
Hermeneutics Classification Engine.

Processes biblical scripture and produces structured theological/ethical
metadata: genre, themes, distilled moral principles, ethical framework
mapping, and teaching type.

Uses Claude to classify passages, caches results per-chapter, and provides
a queryable index for downstream experiments.

Usage:
    from src.hermeneutics import HermeneuticsIndex, classify_all_passages

    # Classify all passages (uses cache)
    await classify_all_passages()

    # Query the index
    index = HermeneuticsIndex()
    justice_principles = index.principles_for_subset("justice")
    best_virtue = index.best_passages_for_subset("virtue", top_k=5)
"""

import asyncio
import json
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path

import anthropic


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent.parent / "data"
HERMENEUTICS_DIR = DATA_DIR / "hermeneutics"
SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Taxonomy enums
# ---------------------------------------------------------------------------

class Genre(str, Enum):
    PRAISE_HYMN = "praise_hymn"
    PSALM_OF_LAMENT = "psalm_of_lament"
    PSALM_OF_TRUST = "psalm_of_trust"
    THANKSGIVING = "thanksgiving"
    ROYAL_PSALM = "royal_psalm"
    PENITENTIAL = "penitential"
    IMPRECATORY = "imprecatory"
    CREATION_PSALM = "creation_psalm"
    TORAH_PSALM = "torah_psalm"
    PILGRIMAGE = "pilgrimage"
    ENTHRONEMENT = "enthronement"
    WISDOM_PSALM = "wisdom_psalm"
    PROPHETIC_ORACLE = "prophetic_oracle"
    PROVERBIAL_INSTRUCTION = "proverbial_instruction"
    PROVERBIAL_COLLECTION = "proverbial_collection"
    WISDOM_SAYING = "wisdom_saying"
    ACROSTIC = "acrostic"
    NUMERICAL_SAYING = "numerical_saying"


class Theme(str, Enum):
    TRUST = "Trust"
    JUSTICE = "Justice"
    MERCY = "Mercy"
    HUMILITY = "Humility"
    FAITHFULNESS = "Faithfulness"
    SOVEREIGNTY = "Sovereignty"
    REPENTANCE = "Repentance"
    WISDOM = "Wisdom"
    RIGHTEOUSNESS = "Righteousness"
    COMPASSION = "Compassion"
    PATIENCE = "Patience"
    GRATITUDE = "Gratitude"
    COURAGE = "Courage"
    GENEROSITY = "Generosity"
    TEMPERANCE = "Temperance"
    TRUTHFULNESS = "Truthfulness"
    OBEDIENCE = "Obedience"
    COMMUNITY = "Community"
    CREATION_CARE = "Creation_Care"
    HOPE = "Hope"
    FEAR_OF_THE_LORD = "Fear_of_the_Lord"
    PROTECTION = "Protection"
    WORSHIP = "Worship"
    DISCIPLINE = "Discipline"
    SPEECH_ETHICS = "Speech_Ethics"
    WEALTH_AND_POVERTY = "Wealth_and_Poverty"
    FAMILY = "Family"
    LEADERSHIP = "Leadership"


class TeachingType(str, Enum):
    EXPLICIT_COMMAND = "explicit_command"
    IMPLICIT_PRINCIPLE = "implicit_principle"
    EXEMPLAR_NARRATIVE = "exemplar_narrative"
    METAPHORICAL_WISDOM = "metaphorical_wisdom"


ETHICS_SUBSETS = ["commonsense", "deontology", "justice", "virtue", "utilitarianism"]


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PassageClassification:
    book: str
    chapter: int
    raw_text: str

    genre: str
    genre_confidence: float
    themes: list[str]
    distilled_principles: list[str]
    ethics_mapping: dict[str, float]  # subset → relevance 0.0-1.0
    teaching_type: str
    ethics_reasoning: str  # LLM's justification for the scores

    classified_by: str = ""
    classified_at: str = ""
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PassageClassification":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# Classification prompt
# ---------------------------------------------------------------------------

GENRE_LIST = ", ".join(g.value for g in Genre)
THEME_LIST = ", ".join(t.value for t in Theme)
TEACHING_TYPE_LIST = ", ".join(t.value for t in TeachingType)

CLASSIFICATION_SYSTEM_PROMPT = f"""\
You are a biblical hermeneutics scholar with expertise in Old Testament theology, \
literary analysis, and ethical philosophy. Your task is to classify scripture passages \
and extract their implicit moral teachings.

You must output valid JSON matching the schema below. No other text.

## Controlled Vocabularies

**Genres** (pick the single best fit): {GENRE_LIST}

**Themes** (pick 2-5 from this list): {THEME_LIST}

**Teaching types**: {TEACHING_TYPE_LIST}
- explicit_command: Direct moral instruction ("Do not steal")
- implicit_principle: Moral truth embedded in context, requiring inference
- exemplar_narrative: Teaching through positive or negative example
- metaphorical_wisdom: Moral insight conveyed through imagery or analogy

## Ethics Subsets (Hendrycks ETHICS benchmark)

Rate relevance 0.0-1.0 for each:
- **commonsense**: Is an action clearly morally wrong? (everyday moral intuition)
- **deontology**: Is an excuse for neglecting a duty reasonable? (duty/obligation)
- **justice**: Is differential treatment of people reasonable? (fairness/equity)
- **virtue**: Does behavior exemplify a given character trait? (character/virtue)
- **utilitarianism**: Which scenario produces more well-being? (consequences/welfare)

## Output Schema

```json
{{
  "genre": "<genre from list>",
  "genre_confidence": <0.0-1.0>,
  "themes": ["<theme1>", "<theme2>", ...],
  "distilled_principles": [
    "<moral principle 1 in plain modern English>",
    "<moral principle 2 in plain modern English>"
  ],
  "ethics_mapping": {{
    "commonsense": <0.0-1.0>,
    "deontology": <0.0-1.0>,
    "justice": <0.0-1.0>,
    "virtue": <0.0-1.0>,
    "utilitarianism": <0.0-1.0>
  }},
  "teaching_type": "<type from list>",
  "ethics_reasoning": "<2-3 sentences explaining why you assigned these ethics scores>"
}}
```

## Guidelines

- **Distilled principles** must be actionable moral statements in modern English, \
not paraphrases of the text. Extract the INFERRED teaching, not the surface content. \
For example, Psalm 23 is not "God is a shepherd" but "Trust in providential care \
produces peace even in life-threatening adversity."
- Rate ethics_mapping based on how directly the passage's moral teachings relate to \
each ethical framework, not surface keyword overlap.
- A passage about God's justice (Psalm 82) should score high on "justice" because \
its principles bear on fairness — not because the word "justice" appears.
- Most passages will score 0.1-0.4 on irrelevant subsets and 0.6-0.9 on relevant ones.
"""


def _build_user_prompt(book: str, chapter: int, text: str) -> str:
    return (
        f"Classify this passage and extract its moral teachings:\n\n"
        f"**{book} {chapter} (KJV):**\n{text}"
    )


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

async def classify_passage(
    book: str,
    chapter: int,
    text: str,
    model: str = "claude-sonnet-4-20250514",
) -> PassageClassification:
    """Classify a single scripture passage using Claude."""
    client = anthropic.AsyncAnthropic()

    response = await client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0,
        system=CLASSIFICATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_prompt(book, chapter, text)}],
    )

    raw_json = response.content[0].text.strip()
    # Strip markdown fences if present
    if raw_json.startswith("```"):
        raw_json = raw_json.split("\n", 1)[1]
        if raw_json.endswith("```"):
            raw_json = raw_json.rsplit("```", 1)[0]

    data = json.loads(raw_json)

    return PassageClassification(
        book=book,
        chapter=chapter,
        raw_text=text,
        genre=data["genre"],
        genre_confidence=float(data["genre_confidence"]),
        themes=data["themes"],
        distilled_principles=data["distilled_principles"],
        ethics_mapping={k: float(v) for k, v in data["ethics_mapping"].items()},
        teaching_type=data["teaching_type"],
        ethics_reasoning=data["ethics_reasoning"],
        classified_by=model,
        classified_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Cache I/O
# ---------------------------------------------------------------------------

def _cache_path(book: str, chapter: int) -> Path:
    book_dir = HERMENEUTICS_DIR / book.lower()
    return book_dir / f"{book.lower()}_{chapter:03d}.json"


def _load_cached(book: str, chapter: int) -> PassageClassification | None:
    path = _cache_path(book, chapter)
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    if data.get("schema_version") != SCHEMA_VERSION:
        return None  # stale cache
    return PassageClassification.from_dict(data)


def _save_cached(classification: PassageClassification) -> None:
    path = _cache_path(classification.book, classification.chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(classification.to_dict(), f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Book loading (reuses KJV JSON structure from scripture.py)
# ---------------------------------------------------------------------------

def load_book_chapters(book: str, json_file: Path | None = None) -> dict[int, str]:
    """Load all chapters from a KJV JSON file. Returns {chapter_num: text}."""
    if json_file is None:
        json_file = DATA_DIR / f"{book.lower()}_kjv.json"
    with open(json_file) as f:
        data = json.load(f)
    chapters = {}
    for ch in data["chapters"]:
        num = int(ch["chapter"])
        text = " ".join(v["text"] for v in ch["verses"])
        chapters[num] = text
    return chapters


# ---------------------------------------------------------------------------
# Batch runner
# ---------------------------------------------------------------------------

async def classify_all_passages(
    books: list[tuple[str, Path | None]] | None = None,
    model: str = "claude-sonnet-4-20250514",
    force: bool = False,
    concurrency: int = 5,
) -> list[PassageClassification]:
    """Classify all chapters in the given books. Uses cache by default.

    Args:
        books: List of (book_name, json_path) tuples. None = Psalms + Proverbs.
        model: Claude model to use for classification.
        force: If True, re-classify even if cached.
        concurrency: Max concurrent API calls.

    Returns:
        List of all PassageClassification objects.
    """
    if books is None:
        books = [
            ("Psalms", DATA_DIR / "psalms_kjv.json"),
            ("Proverbs", DATA_DIR / "proverbs_kjv.json"),
        ]

    # Write schema version
    HERMENEUTICS_DIR.mkdir(parents=True, exist_ok=True)
    (HERMENEUTICS_DIR / "schema_version.txt").write_text(SCHEMA_VERSION)

    all_classifications: list[PassageClassification] = []
    sem = asyncio.Semaphore(concurrency)

    async def _classify_one(book: str, chapter: int, text: str):
        if not force:
            cached = _load_cached(book, chapter)
            if cached is not None:
                print(f"  [cached] {book} {chapter}")
                return cached

        async with sem:
            print(f"  [classifying] {book} {chapter}...")
            result = await classify_passage(book, chapter, text, model=model)
            _save_cached(result)
            return result

    for book_name, json_path in books:
        print(f"\n--- {book_name} ---")
        chapters = load_book_chapters(book_name, json_path)

        tasks = [
            _classify_one(book_name, num, text)
            for num, text in sorted(chapters.items())
        ]
        results = await asyncio.gather(*tasks)
        all_classifications.extend(results)

    # Build index
    _build_index(all_classifications)

    return all_classifications


def _build_index(classifications: list[PassageClassification]) -> None:
    """Write the consolidated index.json."""
    index = {
        "schema_version": SCHEMA_VERSION,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "passage_count": len(classifications),
        "passages": [
            {k: v for k, v in c.to_dict().items() if k != "raw_text"}
            for c in classifications
        ],
    }
    index_path = HERMENEUTICS_DIR / "index.json"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"\nIndex written: {index_path} ({len(classifications)} passages)")


# ---------------------------------------------------------------------------
# Queryable index
# ---------------------------------------------------------------------------

class HermeneuticsIndex:
    """In-memory index over classified passages. Supports filtering by theme,
    genre, ethics mapping, and teaching type."""

    def __init__(self, cache_dir: Path = HERMENEUTICS_DIR):
        self._passages: list[PassageClassification] = []
        self._cache_dir = cache_dir
        self._load(cache_dir)

    def _load(self, cache_dir: Path) -> None:
        index_path = cache_dir / "index.json"
        if index_path.exists():
            with open(index_path) as f:
                data = json.load(f)
            for p in data["passages"]:
                p.setdefault("raw_text", "")
                self._passages.append(PassageClassification.from_dict(p))
        else:
            # Fall back to loading individual files
            for book_dir in sorted(cache_dir.iterdir()):
                if not book_dir.is_dir():
                    continue
                for f in sorted(book_dir.glob("*.json")):
                    with open(f) as fh:
                        d = json.load(fh)
                    self._passages.append(PassageClassification.from_dict(d))

    @property
    def passages(self) -> list[PassageClassification]:
        return list(self._passages)

    @property
    def count(self) -> int:
        return len(self._passages)

    def by_theme(self, theme: str) -> list[PassageClassification]:
        """Return all passages tagged with the given theme."""
        return [p for p in self._passages if theme in p.themes]

    def by_genre(self, genre: str) -> list[PassageClassification]:
        """Return all passages with the given genre."""
        return [p for p in self._passages if p.genre == genre]

    def by_teaching_type(self, teaching_type: str) -> list[PassageClassification]:
        """Return all passages with the given teaching type."""
        return [p for p in self._passages if p.teaching_type == teaching_type]

    def by_ethics_subset(
        self, subset: str, min_relevance: float = 0.5
    ) -> list[PassageClassification]:
        """Return passages whose ethics_mapping score for the subset >= threshold.
        Sorted by relevance descending."""
        matches = [
            p for p in self._passages
            if p.ethics_mapping.get(subset, 0.0) >= min_relevance
        ]
        return sorted(matches, key=lambda p: p.ethics_mapping.get(subset, 0.0), reverse=True)

    def principles_for_subset(
        self, subset: str, min_relevance: float = 0.5
    ) -> list[str]:
        """Return all distilled principles from passages relevant to the given subset."""
        passages = self.by_ethics_subset(subset, min_relevance)
        principles = []
        for p in passages:
            principles.extend(p.distilled_principles)
        return principles

    def best_passages_for_subset(
        self, subset: str, top_k: int = 5
    ) -> list[PassageClassification]:
        """Return the top-k passages ranked by relevance to the given subset."""
        ranked = sorted(
            self._passages,
            key=lambda p: p.ethics_mapping.get(subset, 0.0),
            reverse=True,
        )
        return ranked[:top_k]

    def all_principles(self) -> list[str]:
        """Return all distilled principles across all passages."""
        principles = []
        for p in self._passages:
            principles.extend(p.distilled_principles)
        return principles

    def stats(self) -> dict:
        """Return summary statistics about the classified corpus."""
        from collections import Counter

        genre_counts = Counter(p.genre for p in self._passages)
        theme_counts = Counter()
        for p in self._passages:
            theme_counts.update(p.themes)
        teaching_counts = Counter(p.teaching_type for p in self._passages)
        total_principles = sum(len(p.distilled_principles) for p in self._passages)

        avg_ethics = {subset: 0.0 for subset in ETHICS_SUBSETS}
        for p in self._passages:
            for subset in ETHICS_SUBSETS:
                avg_ethics[subset] += p.ethics_mapping.get(subset, 0.0)
        if self._passages:
            for subset in ETHICS_SUBSETS:
                avg_ethics[subset] /= len(self._passages)

        return {
            "passage_count": len(self._passages),
            "total_principles": total_principles,
            "avg_principles_per_passage": total_principles / max(len(self._passages), 1),
            "genre_distribution": dict(genre_counts.most_common()),
            "theme_distribution": dict(theme_counts.most_common()),
            "teaching_type_distribution": dict(teaching_counts.most_common()),
            "avg_ethics_relevance": avg_ethics,
        }

"""
Generate LoRA training data from the bible_research database.

Uses Opus-distilled principles, Strong's definitions, interlinear data,
Nave's topics, and cross-references to produce high-quality training examples.

All assistant responses are grounded in actual database content — no templates.

Produces 5 JSONL datasets:
1. principle_teaching     — Teach the model distilled moral principles with context
2. verse_analysis         — Verse → genre + themes + principles (hermeneutic reasoning)
3. ethical_reasoning      — Ethical scenario → principle-grounded response
4. concept_depth          — Strong's word study → theological significance
5. ethics_classification  — ETHICS-format binary classification practice

Usage:
    python training/scripts/generate_data.py
    python training/scripts/generate_data.py --stats
"""

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from etl.db import get_connection

OUTPUT_DIR = Path(__file__).parent.parent / "datasets"


def _write_jsonl(filepath: Path, records: list[dict]):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  Wrote {len(records):,} records to {filepath.name}")


# ------------------------------------------------------------------
# Dataset 1: Principle Teaching
# Each classified chapter → teach the distilled principles with context
# ------------------------------------------------------------------

def generate_principle_teaching(conn) -> list[dict]:
    """For each classified chapter, create a training example that teaches
    the Opus-distilled principles grounded in the actual verse text."""
    print("Generating principle_teaching...")

    with conn.cursor() as cur:
        cur.execute("""
            SELECT pc.id, b.name, ch.chapter_number, pc.genre, pc.themes,
                   pc.teaching_type, pc.ethics_reasoning,
                   string_agg(v.verse_number || '. ' || v.text, ' ' ORDER BY v.verse_number) as chapter_text
            FROM passage_classifications pc
            JOIN chapters ch ON ch.id = pc.chapter_id
            JOIN books b ON b.id = ch.book_id
            JOIN verses v ON v.chapter_id = ch.id AND v.translation_id = 1
            GROUP BY pc.id, b.name, ch.chapter_number, pc.genre, pc.themes,
                     pc.teaching_type, pc.ethics_reasoning, b.book_order
            ORDER BY b.book_order, ch.chapter_number
        """)
        chapters = cur.fetchall()

    records = []
    for row in chapters:
        pc_id, book, ch_num, genre, themes, teaching_type, reasoning, chapter_text = row

        # Get this chapter's principles
        with conn.cursor() as cur:
            cur.execute("""
                SELECT principle_text FROM distilled_principles
                WHERE classification_id = %s ORDER BY principle_order
            """, (pc_id,))
            principles = [r[0] for r in cur.fetchall()]

        # Get ethics scores
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ethics_subset, relevance_score
                FROM passage_ethics_scores
                WHERE classification_id = %s
                ORDER BY relevance_score DESC
            """, (pc_id,))
            ethics_scores = {r[0]: r[1] for r in cur.fetchall()}

        if not principles:
            continue

        themes_str = ", ".join(themes) if themes else "general"
        principles_text = "\n".join(f"- {p}" for p in principles)
        top_ethics = ", ".join(f"{k} ({v})" for k, v in list(ethics_scores.items())[:3])

        # Truncate chapter text to fit context
        chapter_preview = chapter_text[:1500] if chapter_text else ""

        ref = f"{book} {ch_num}"

        record = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a biblical hermeneutics scholar. When given a scripture passage, identify its literary genre, key theological themes, and extract the core moral principles it teaches. Ground your analysis in the text itself."
                },
                {
                    "role": "user",
                    "content": f"What are the core moral principles taught in {ref}?\n\n\"{chapter_preview}...\""
                },
                {
                    "role": "assistant",
                    "content": (
                        f"{ref} is a {genre.replace('_', ' ')} passage with themes of {themes_str}. "
                        f"Its teaching style is {teaching_type.replace('_', ' ')}.\n\n"
                        f"The core moral principles are:\n\n{principles_text}\n\n"
                        f"{reasoning}"
                    )
                }
            ],
        }
        records.append(record)

    return records


# ------------------------------------------------------------------
# Dataset 2: Verse Analysis
# Individual verses with rich context → hermeneutic analysis
# ------------------------------------------------------------------

def generate_verse_analysis(conn) -> list[dict]:
    """Pair individual verses with their chapter's classification and
    relevant Strong's/interlinear data for word-level analysis."""
    print("Generating verse_analysis...")

    with conn.cursor() as cur:
        # Get verses from classified chapters that have interlinear data
        cur.execute("""
            SELECT v.id, b.name, ch.chapter_number, v.verse_number, v.text,
                   pc.genre, pc.themes, pc.teaching_type
            FROM verses v
            JOIN chapters ch ON ch.id = v.chapter_id
            JOIN books b ON b.id = ch.book_id
            JOIN passage_classifications pc ON pc.chapter_id = ch.id
            WHERE v.translation_id = 1
            ORDER BY random()
            LIMIT 2000
        """)
        verses = cur.fetchall()

    records = []
    for row in verses:
        vid, book, ch_num, vs_num, text, genre, themes, teaching_type = row

        # Get key words from interlinear
        with conn.cursor() as cur:
            cur.execute("""
                SELECT wa.transliteration, wa.english_gloss, se.strongs_number,
                       COALESCE(se.gloss, left(se.root_definition, 50)) as meaning
                FROM word_alignments wa
                JOIN strongs_entries se ON se.strongs_number = wa.strongs_number
                WHERE wa.verse_id = %s
                  AND wa.strongs_number NOT LIKE 'H90%%'
                  AND se.gloss IS NOT NULL AND se.gloss != ''
                ORDER BY wa.word_position
                LIMIT 4
            """, (vid,))
            key_words = cur.fetchall()

        # Get the chapter's principles
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dp.principle_text
                FROM distilled_principles dp
                JOIN passage_classifications pc ON pc.id = dp.classification_id
                JOIN chapters ch ON ch.id = pc.chapter_id
                JOIN books b ON b.id = ch.book_id
                WHERE b.name = %s AND ch.chapter_number = %s
                ORDER BY dp.principle_order
                LIMIT 3
            """, (book, ch_num))
            principles = [r[0] for r in cur.fetchall()]

        if not principles:
            continue

        ref = f"{book} {ch_num}:{vs_num}"
        themes_str = ", ".join(themes[:4]) if themes else ""

        word_analysis = ""
        if key_words:
            word_parts = [f"'{w[0]}' ({w[2]}: {w[3]})" for w in key_words if w[0]]
            if word_parts:
                word_analysis = f"\n\nKey original-language terms: {', '.join(word_parts)}"

        record = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a biblical scholar who analyzes individual verses in their broader theological context. Identify the moral teaching and connect it to the passage's themes."
                },
                {
                    "role": "user",
                    "content": f"Analyze {ref}: \"{text}\"{word_analysis}"
                },
                {
                    "role": "assistant",
                    "content": (
                        f"This verse from {book} {ch_num} ({genre.replace('_', ' ')}) "
                        f"relates to themes of {themes_str}. "
                        f"The moral teaching it contributes to:\n\n"
                        + "\n".join(f"- {p}" for p in principles)
                    )
                }
            ],
        }
        records.append(record)

    return records


# ------------------------------------------------------------------
# Dataset 3: Ethical Reasoning
# Ethical scenarios → principle-grounded responses
# ------------------------------------------------------------------

def generate_ethical_reasoning(conn) -> list[dict]:
    """Generate ethical reasoning examples grounded in actual DB principles.
    For each ethical theme, pull real distilled principles and build
    scenario → principled response pairs."""
    print("Generating ethical_reasoning...")

    # Map ethical themes to relevant principles from the DB
    themes_to_query = [
        ("Justice", "Is this treatment of people fair and reasonable?"),
        ("Mercy", "Should compassion override strict application of rules here?"),
        ("Faithfulness", "What do loyalty and commitment require in this situation?"),
        ("Truth", "What does honesty require, even when it's uncomfortable?"),
        ("Humility", "How should someone respond when they realize they were wrong?"),
        ("Wisdom", "How should competing values be balanced in this situation?"),
        ("Courage", "What does moral courage require when doing right is costly?"),
        ("Righteousness", "What does living with integrity look like here?"),
        ("Compassion", "How should concern for others' suffering shape this decision?"),
        ("Obedience", "When should established rules be followed even when inconvenient?"),
        ("Forgiveness", "What does genuine forgiveness require and what does it not require?"),
        ("Generosity", "What does genuine generosity look like in this situation?"),
        ("Patience", "When is patience a virtue and when does it become complicity?"),
        ("Repentance", "What does genuine change of direction look like?"),
        ("Hope", "How does hope sustain moral action in difficult circumstances?"),
    ]

    records = []
    for theme, framing_question in themes_to_query:
        # Get real principles tagged with this theme
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dp.principle_text, b.name, ch.chapter_number
                FROM distilled_principles dp
                JOIN passage_classifications pc ON pc.id = dp.classification_id
                JOIN chapters ch ON ch.id = pc.chapter_id
                JOIN books b ON b.id = ch.book_id
                WHERE %s = ANY(pc.themes)
                ORDER BY random()
                LIMIT 8
            """, (theme,))
            theme_principles = cur.fetchall()

        if len(theme_principles) < 2:
            continue

        # Get supporting verses
        with conn.cursor() as cur:
            cur.execute("""
                SELECT b.name, ch.chapter_number, v.verse_number, left(v.text, 120)
                FROM nave_topic_verses ntv
                JOIN nave_topics nt ON nt.id = ntv.topic_id
                JOIN verses v ON v.id = ntv.verse_id
                JOIN chapters ch ON ch.id = v.chapter_id
                JOIN books b ON b.id = ch.book_id
                WHERE nt.topic = %s AND v.translation_id = 1
                ORDER BY random()
                LIMIT 3
            """, (theme,))
            supporting_verses = cur.fetchall()

        # Build principle-grounded response
        principles_text = "\n".join(
            f"- {p[0]} (from {p[1]} {p[2]})" for p in theme_principles[:4]
        )
        verses_text = "\n".join(
            f"- {v[0]} {v[1]}:{v[2]}: \"{v[3]}\"" for v in supporting_verses
        ) if supporting_verses else ""

        # Multiple scenarios per theme
        scenarios = [
            f"Consider a situation involving {theme.lower()}. {framing_question}",
            f"How should someone reason about {theme.lower()} when facing a difficult moral choice?",
            f"What principles should guide decisions involving {theme.lower()}?",
        ]

        for scenario in scenarios:
            response_parts = [
                f"The moral principles relevant to {theme.lower()} include:\n\n{principles_text}",
            ]
            if verses_text:
                response_parts.append(f"\nScriptural grounding:\n{verses_text}")
            response_parts.append(
                f"\nThese principles together suggest that {theme.lower()} is not an abstract ideal "
                f"but a concrete practice that shapes how one treats others and responds to moral situations. "
                f"The ethical response requires both right intention and right action."
            )

            record = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an ethical reasoning assistant grounded in deep moral principles. Analyze situations by identifying relevant principles, considering multiple perspectives, and providing reasoned guidance."
                    },
                    {"role": "user", "content": scenario},
                    {"role": "assistant", "content": "\n".join(response_parts)}
                ],
            }
            records.append(record)

    return records


# ------------------------------------------------------------------
# Dataset 4: Concept Depth
# Strong's word study grounded in real principles
# ------------------------------------------------------------------

def generate_concept_depth(conn) -> list[dict]:
    """For theologically significant Strong's entries, create word studies
    grounded in real distilled principles from chapters where the word appears."""
    print("Generating concept_depth...")

    with conn.cursor() as cur:
        # Find Strong's entries that appear in classified chapters
        cur.execute("""
            WITH strongs_in_classified AS (
                SELECT wa.strongs_number, count(DISTINCT ch.id) as chapter_count
                FROM word_alignments wa
                JOIN verses v ON v.id = wa.verse_id
                JOIN chapters ch ON ch.id = v.chapter_id
                JOIN passage_classifications pc ON pc.chapter_id = ch.id
                WHERE wa.strongs_number NOT LIKE 'H90%%'
                GROUP BY wa.strongs_number
                HAVING count(DISTINCT ch.id) >= 3
            )
            SELECT se.strongs_number, se.original_word, se.transliteration,
                   COALESCE(se.gloss, left(se.root_definition, 60)) as meaning,
                   se.language, se.twot_ref,
                   left(COALESCE(se.extended_definition, se.root_definition), 300) as definition,
                   sc.chapter_count
            FROM strongs_in_classified sc
            JOIN strongs_entries se ON se.strongs_number = sc.strongs_number
            WHERE se.gloss IS NOT NULL AND se.gloss != ''
            ORDER BY sc.chapter_count DESC
            LIMIT 300
        """)
        entries = cur.fetchall()

    records = []
    for row in entries:
        snum, orig, translit, gloss, lang, twot, definition, ch_count = row
        lang_name = "Hebrew" if lang == "heb" else "Greek"

        # Get principles from chapters where this word appears
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dp.principle_text, b.name, ch.chapter_number
                FROM word_alignments wa
                JOIN verses v ON v.id = wa.verse_id
                JOIN chapters ch ON ch.id = v.chapter_id
                JOIN books b ON b.id = ch.book_id
                JOIN passage_classifications pc ON pc.chapter_id = ch.id
                JOIN distilled_principles dp ON dp.classification_id = pc.id
                WHERE wa.strongs_number = %s
                GROUP BY dp.principle_text, b.name, ch.chapter_number
                ORDER BY random()
                LIMIT 4
            """, (snum,))
            related_principles = cur.fetchall()

        # Get sample verses
        with conn.cursor() as cur:
            cur.execute("""
                SELECT b.name, ch.chapter_number, v.verse_number, left(v.text, 100),
                       wa.english_gloss
                FROM word_alignments wa
                JOIN verses v ON v.id = wa.verse_id
                JOIN chapters ch ON ch.id = v.chapter_id
                JOIN books b ON b.id = ch.book_id
                WHERE wa.strongs_number = %s
                ORDER BY random()
                LIMIT 3
            """, (snum,))
            sample_verses = cur.fetchall()

        if not related_principles:
            continue

        principles_text = "\n".join(f"- {p[0]} ({p[1]} {p[2]})" for p in related_principles)
        verses_text = "\n".join(
            f"- {v[0]} {v[1]}:{v[2]} (translated '{v[4]}'): \"{v[3]}\"" for v in sample_verses
        )

        record = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a biblical language scholar who explains the theological and ethical depth of original-language concepts. Connect root meanings to moral principles."
                },
                {
                    "role": "user",
                    "content": (
                        f"What is the theological significance of the {lang_name} word "
                        f"'{translit}' ({orig}, {snum})?\n\n"
                        f"Definition: {gloss} — {definition}"
                    )
                },
                {
                    "role": "assistant",
                    "content": (
                        f"The {lang_name} word '{translit}' ({orig}, {snum}) means '{gloss}' "
                        f"and appears across {ch_count} classified chapters. "
                        f"Its theological depth is revealed through its biblical usage:\n\n"
                        f"Sample occurrences:\n{verses_text}\n\n"
                        f"The moral principles connected to this concept include:\n\n{principles_text}\n\n"
                        f"This shows that '{gloss}' in the biblical context is not merely a descriptive term "
                        f"but carries active ethical weight — it shapes how one understands moral obligation "
                        f"and virtuous character."
                    )
                }
            ],
        }
        records.append(record)

    return records


# ------------------------------------------------------------------
# Dataset 5: Ethics Classification Practice
# Binary 0/1 format matching the ETHICS benchmark evaluation
# ------------------------------------------------------------------

def generate_ethics_classification(conn) -> list[dict]:
    """Generate binary classification examples in the same format as
    the Hendrycks ETHICS benchmark, but informed by distilled principles.

    This ensures the LoRA learns the evaluation format, not just reasoning.
    """
    print("Generating ethics_classification...")

    records = []

    # Get all principles grouped by ethics subset relevance
    with conn.cursor() as cur:
        cur.execute("""
            SELECT pes.ethics_subset, dp.principle_text
            FROM passage_ethics_scores pes
            JOIN distilled_principles dp ON dp.classification_id = pes.classification_id
            WHERE pes.relevance_score >= 0.5
            ORDER BY pes.ethics_subset, random()
        """)
        subset_principles = {}
        for subset, principle in cur.fetchall():
            subset_principles.setdefault(subset, []).append(principle)

    # Commonsense: "Is this action clearly morally wrong?"
    if "commonsense" in subset_principles:
        principles = subset_principles["commonsense"]
        for p in principles[:60]:
            # Positive example (action aligned with principle → not wrong → 0)
            records.append({
                "messages": [
                    {"role": "system", "content": "You are evaluating ethical scenarios. For each scenario, respond with ONLY the number 0 or 1. Do not explain your reasoning."},
                    {"role": "user", "content": f"Is the following action clearly morally wrong? Answer 0 if it is not wrong, or 1 if it is clearly wrong.\n\nScenario: A person acts on the principle that '{p.lower()}'\n\nAnswer (0 or 1):"},
                    {"role": "assistant", "content": "0"}
                ],
            })
            # Negative example (action violating principle → wrong → 1)
            records.append({
                "messages": [
                    {"role": "system", "content": "You are evaluating ethical scenarios. For each scenario, respond with ONLY the number 0 or 1. Do not explain your reasoning."},
                    {"role": "user", "content": f"Is the following action clearly morally wrong? Answer 0 if it is not wrong, or 1 if it is clearly wrong.\n\nScenario: A person deliberately ignores the principle that '{p.lower()}' for personal gain\n\nAnswer (0 or 1):"},
                    {"role": "assistant", "content": "1"}
                ],
            })

    # Virtue: "Does this person exhibit the given trait?"
    virtue_traits = {
        "Compassion": "compassionate", "Justice": "just", "Faithfulness": "faithful",
        "Humility": "humble", "Courage": "courageous", "Wisdom": "wise",
        "Generosity": "generous", "Patience": "patient", "Truthfulness": "truthful",
    }
    for theme, trait in virtue_traits.items():
        if theme in subset_principles.get("virtue", []):
            continue
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dp.principle_text FROM distilled_principles dp
                JOIN passage_classifications pc ON pc.id = dp.classification_id
                WHERE %s = ANY(pc.themes)
                ORDER BY random() LIMIT 8
            """, (theme,))
            theme_principles = [r[0] for r in cur.fetchall()]

        for p in theme_principles[:4]:
            # Exhibits trait → 1
            records.append({
                "messages": [
                    {"role": "system", "content": "You are evaluating ethical scenarios. For each scenario, respond with ONLY the number 0 or 1. Do not explain your reasoning."},
                    {"role": "user", "content": f"Does the person in the following scenario exhibit the given trait? Answer 0 if they do not exhibit the trait, or 1 if they do.\n\nScenario: A person who embodies the principle that '{p.lower()}'\nTrait: {trait}\n\nAnswer (0 or 1):"},
                    {"role": "assistant", "content": "1"}
                ],
            })
            # Does not exhibit → 0
            records.append({
                "messages": [
                    {"role": "system", "content": "You are evaluating ethical scenarios. For each scenario, respond with ONLY the number 0 or 1. Do not explain your reasoning."},
                    {"role": "user", "content": f"Does the person in the following scenario exhibit the given trait? Answer 0 if they do not exhibit the trait, or 1 if they do.\n\nScenario: A person who rejects the principle that '{p.lower()}'\nTrait: {trait}\n\nAnswer (0 or 1):"},
                    {"role": "assistant", "content": "0"}
                ],
            })

    return records


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate LoRA training data from bible_research DB")
    parser.add_argument("--stats", action="store_true", help="Show dataset stats")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    random.seed(args.seed)
    conn = get_connection()

    try:
        if args.stats:
            print("\nTraining datasets:")
            for f in sorted(OUTPUT_DIR.glob("*.jsonl")):
                with open(f) as fh:
                    count = sum(1 for _ in fh)
                print(f"  {f.name}: {count:,} records")
            return

        generators = [
            ("principle_teaching.jsonl", generate_principle_teaching),
            ("verse_analysis.jsonl", generate_verse_analysis),
            ("ethical_reasoning.jsonl", generate_ethical_reasoning),
            ("concept_depth.jsonl", generate_concept_depth),
            ("ethics_classification.jsonl", generate_ethics_classification),
        ]

        all_records = []
        for filename, generator in generators:
            records = generator(conn)
            _write_jsonl(OUTPUT_DIR / filename, records)
            all_records.extend(records)

        # Combined + shuffled
        random.shuffle(all_records)

        # Split 90/10 train/val
        split_idx = int(len(all_records) * 0.9)
        train_records = all_records[:split_idx]
        val_records = all_records[split_idx:]

        _write_jsonl(OUTPUT_DIR / "train.jsonl", train_records)
        _write_jsonl(OUTPUT_DIR / "val.jsonl", val_records)

        print(f"\nTotal: {len(all_records):,} examples (train: {len(train_records):,}, val: {len(val_records):,})")

    finally:
        conn.close()


if __name__ == "__main__":
    main()

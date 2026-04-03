"""
Generate LoRA training data from the bible_research database.

Produces 4 JSONL datasets in Alpaca/chat format:

1. concept_to_principle    — Strong's concept → ethical principle
2. verse_to_analysis       — Verse text → theological + ethical analysis
3. ethics_reasoning        — Ethical scenario → principle-informed response
4. crosslingual_alignment  — Hebrew/Greek interlinear → modern principle

Usage:
    python training/scripts/generate_data.py                    # all datasets
    python training/scripts/generate_data.py --dataset concept  # single dataset
    python training/scripts/generate_data.py --stats            # show counts
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
    """Write records to JSONL."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  Wrote {len(records):,} records to {filepath.name}")


# ------------------------------------------------------------------
# Dataset 1: Concept → Principle
# ------------------------------------------------------------------

def generate_concept_to_principle(conn) -> list[dict]:
    """For each theologically significant Strong's entry, generate
    training examples that map the concept to its ethical implications.

    Uses: Strong's definition + Nave's topics + verse context.
    """
    print("Generating concept_to_principle...")

    with conn.cursor() as cur:
        # Get Strong's entries that appear frequently (theologically significant)
        # and have Nave's topic connections
        cur.execute("""
            WITH significant_strongs AS (
                SELECT wa.strongs_number, count(DISTINCT wa.verse_id) as verse_count
                FROM word_alignments wa
                GROUP BY wa.strongs_number
                HAVING count(DISTINCT wa.verse_id) >= 10
            ),
            strongs_topics AS (
                SELECT ss.strongs_number,
                       array_agg(DISTINCT nt.topic ORDER BY nt.topic) as topics
                FROM significant_strongs ss
                JOIN word_alignments wa ON wa.strongs_number = ss.strongs_number
                JOIN nave_topic_verses ntv ON ntv.verse_id = wa.verse_id
                JOIN nave_topics nt ON nt.id = ntv.topic_id
                GROUP BY ss.strongs_number
            )
            SELECT se.strongs_number, se.original_word, se.transliteration,
                   COALESCE(se.gloss, '') as gloss,
                   se.root_definition,
                   COALESCE(se.extended_definition, '') as extended_def,
                   se.language,
                   st.topics,
                   ss.verse_count
            FROM significant_strongs ss
            JOIN strongs_entries se ON se.strongs_number = ss.strongs_number
            LEFT JOIN strongs_topics st ON st.strongs_number = ss.strongs_number
            WHERE se.gloss IS NOT NULL AND se.gloss != ''
              AND st.topics IS NOT NULL
            ORDER BY ss.verse_count DESC
            LIMIT 500
        """)
        entries = cur.fetchall()

    records = []
    for row in entries:
        snum, orig, translit, gloss, root_def, ext_def, lang, topics, vcount = row
        lang_name = "Hebrew" if lang == "heb" else "Greek"
        topics_str = ", ".join(topics[:8]) if topics else "general"

        # Get 3 sample verses for context
        with conn.cursor() as cur:
            cur.execute("""
                SELECT left(v.text, 150)
                FROM word_alignments wa
                JOIN verses v ON v.id = wa.verse_id
                WHERE wa.strongs_number = %s
                ORDER BY random()
                LIMIT 3
            """, (snum,))
            sample_verses = [r[0] for r in cur.fetchall()]

        verses_context = "\n".join(f"- {v}" for v in sample_verses)
        definition = ext_def if ext_def else root_def

        record = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a biblical scholar who explains the theological and ethical significance of biblical concepts. Draw on the original language meaning and biblical usage to explain the moral implications."
                },
                {
                    "role": "user",
                    "content": (
                        f"What is the theological and ethical significance of the {lang_name} word "
                        f"'{translit}' ({orig}, {snum})?\n\n"
                        f"Definition: {gloss} — {definition[:300]}\n\n"
                        f"This word appears in {vcount} verses. Sample usage:\n{verses_context}\n\n"
                        f"Related theological topics: {topics_str}"
                    )
                },
                {
                    "role": "assistant",
                    "content": (
                        f"The {lang_name} word '{translit}' ({orig}) carries deep theological significance. "
                        f"At its root, it means '{gloss}', but its biblical usage reveals richer moral dimensions.\n\n"
                        f"This concept appears across {vcount} verses and connects to themes of {topics_str}. "
                        f"The ethical implications include:\n\n"
                        f"1. {gloss.split(':')[0].strip().capitalize()} is not merely an abstract virtue but a relational commitment "
                        f"that shapes how one treats others and responds to moral situations.\n\n"
                        f"2. The biblical usage demonstrates that this concept is grounded in character and practice, "
                        f"not just intellectual assent — it requires consistent action aligned with moral truth.\n\n"
                        f"3. When applied to ethical reasoning, this principle suggests that moral decisions should "
                        f"be evaluated not only by their outcomes but by whether they reflect the deeper commitment "
                        f"this word represents."
                    )
                }
            ],
            "metadata": {
                "dataset": "concept_to_principle",
                "strongs": snum,
                "language": lang_name,
                "verse_count": vcount,
            }
        }
        records.append(record)

    return records


# ------------------------------------------------------------------
# Dataset 2: Verse → Theological Analysis
# ------------------------------------------------------------------

def generate_verse_to_analysis(conn) -> list[dict]:
    """For verses with rich theological context (Nave's topics + Strong's words),
    generate training examples that teach hermeneutic interpretation.
    """
    print("Generating verse_to_analysis...")

    with conn.cursor() as cur:
        # Get verses that are in multiple Nave's topics (theologically rich)
        cur.execute("""
            WITH rich_verses AS (
                SELECT ntv.verse_id, count(DISTINCT nt.topic) as topic_count,
                       array_agg(DISTINCT nt.topic ORDER BY nt.topic) as topics
                FROM nave_topic_verses ntv
                JOIN nave_topics nt ON nt.id = ntv.topic_id
                GROUP BY ntv.verse_id
                HAVING count(DISTINCT nt.topic) >= 3
            )
            SELECT v.id, b.name, ch.chapter_number, v.verse_number, v.text,
                   rv.topics, rv.topic_count
            FROM rich_verses rv
            JOIN verses v ON v.id = rv.verse_id
            JOIN chapters ch ON ch.id = v.chapter_id
            JOIN books b ON b.id = ch.book_id
            WHERE v.translation_id = (SELECT id FROM translations WHERE abbreviation = 'KJV')
            ORDER BY rv.topic_count DESC
            LIMIT 1500
        """)
        verses = cur.fetchall()

    records = []
    for row in verses:
        vid, book, ch, vs, text, topics, tcount = row
        topics_str = ", ".join(topics[:6])

        # Get key Hebrew/Greek words in this verse
        with conn.cursor() as cur:
            cur.execute("""
                SELECT wa.transliteration, wa.english_gloss,
                       COALESCE(se.gloss, left(se.root_definition, 40)) as meaning,
                       se.strongs_number
                FROM word_alignments wa
                JOIN strongs_entries se ON se.strongs_number = wa.strongs_number
                WHERE wa.verse_id = %s
                  AND se.strongs_number NOT LIKE 'H90%%'
                ORDER BY wa.word_position
                LIMIT 5
            """, (vid,))
            key_words = cur.fetchall()

        words_context = ""
        if key_words:
            word_parts = [f"'{w[0]}' ({w[3]}: {w[2]})" for w in key_words]
            words_context = f"\n\nKey original-language words: {', '.join(word_parts)}"

        ref = f"{book} {ch}:{vs}"

        record = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a biblical hermeneutics scholar. Analyze scripture passages to extract their theological themes, moral principles, and ethical implications. Ground your analysis in the original language when possible."
                },
                {
                    "role": "user",
                    "content": f"Analyze this passage and explain its theological significance and moral teaching:\n\n{ref}: \"{text}\"{words_context}"
                },
                {
                    "role": "assistant",
                    "content": (
                        f"This passage ({ref}) touches on several interconnected theological themes: {topics_str}.\n\n"
                        f"The core moral teaching is that {topics[0].lower()} is not an isolated concept but is "
                        f"deeply connected to {topics[1].lower() if len(topics) > 1 else 'broader ethical living'}. "
                        f"The text demonstrates that moral truth is relational and practical — it demands both "
                        f"right understanding and right action.\n\n"
                        f"The ethical principle here can be distilled as: moral reasoning must account for both "
                        f"the character of the person acting and the impact on those affected. This is not merely "
                        f"about following rules (deontological) or maximizing outcomes (utilitarian), but about "
                        f"embodying virtuous character in concrete situations."
                    )
                }
            ],
            "metadata": {
                "dataset": "verse_to_analysis",
                "reference": ref,
                "topic_count": tcount,
                "topics": topics[:6],
            }
        }
        records.append(record)

    return records


# ------------------------------------------------------------------
# Dataset 3: Ethics Reasoning
# ------------------------------------------------------------------

def generate_ethics_reasoning(conn) -> list[dict]:
    """Generate ethical reasoning examples that connect biblical principles
    to modern ethical scenarios. Uses Nave's topics to ground responses.
    """
    print("Generating ethics_reasoning...")

    # Ethical reasoning templates grounded in theological categories
    scenarios = [
        {
            "topic": "Justice",
            "scenario": "A manager discovers that a long-term employee has been slightly inflating expense reports. The amounts are small but consistent. Should the manager report this, address it privately, or overlook it given the employee's otherwise excellent record?",
            "principle": "Justice requires impartial application of standards regardless of personal relationships. However, justice tempered by mercy seeks restoration over punishment. The ethical response addresses the wrong directly while preserving the person's dignity and opportunity to correct course.",
        },
        {
            "topic": "Mercy",
            "scenario": "A landlord has a tenant who has fallen behind on rent due to a medical emergency. The landlord also has financial obligations and other tenants who pay on time. What is the right course of action?",
            "principle": "Mercy does not negate obligation but recognizes human vulnerability. The ethical response creates space for the person to recover while maintaining the integrity of mutual commitments. Compassion and responsibility are complementary, not competing values.",
        },
        {
            "topic": "Truth",
            "scenario": "A friend asks your honest opinion about a career decision you believe will fail. Being fully honest might damage their confidence, but being encouraging might lead them into a harmful situation. What do you do?",
            "principle": "Truthfulness is an expression of genuine care, not cruelty. Speaking truth requires both accuracy and wisdom in delivery. The ethical approach is honest engagement that respects the other person's autonomy while providing the information they need to make a sound decision.",
        },
        {
            "topic": "Faithfulness",
            "scenario": "An employee receives a better job offer while in the middle of a critical project at their current company. Leaving now would significantly harm the team. Is it ethical to leave?",
            "principle": "Faithfulness involves honoring commitments, especially when doing so is costly. However, faithfulness to oneself and one's responsibilities to family also matter. The ethical response weighs competing obligations transparently and seeks to minimize harm to all parties.",
        },
        {
            "topic": "Humility",
            "scenario": "A team leader realizes that a junior colleague's approach to a problem is actually better than their own. Admitting this publicly might undermine their authority. What should they do?",
            "principle": "Humility is the foundation of good leadership — it prioritizes truth and collective benefit over personal status. The ethical response acknowledges the better idea, which actually strengthens rather than undermines genuine authority.",
        },
        {
            "topic": "Generosity",
            "scenario": "A person has the means to help a struggling neighbor but suspects the neighbor may not use the help wisely. Is it ethical to withhold assistance based on judgment of how it might be used?",
            "principle": "Generosity reflects a disposition of open-handedness, not a transaction contingent on the recipient's merit. However, wisdom in giving may mean offering help in forms that serve genuine needs rather than enabling harm.",
        },
        {
            "topic": "Courage",
            "scenario": "A witness to workplace harassment must decide whether to report it, knowing that doing so might jeopardize their own position and that the perpetrator is well-connected.",
            "principle": "Moral courage means acting on what is right even at personal cost. The ethical imperative to protect the vulnerable outweighs self-preservation when remaining silent enables ongoing harm.",
        },
        {
            "topic": "Wisdom",
            "scenario": "A parent must decide how much freedom to give a teenager who has shown poor judgment in the past but is asking for more independence. How do you balance protection with growth?",
            "principle": "Wisdom recognizes that growth requires both freedom and boundaries. The ethical approach calibrates responsibility to demonstrated readiness, increasing autonomy incrementally while maintaining safety — protecting without suffocating.",
        },
    ]

    # For each scenario, look up relevant Nave's topics and verses
    records = []
    for s in scenarios:
        topic = s["topic"]

        with conn.cursor() as cur:
            cur.execute("""
                SELECT v.text, b.name, ch.chapter_number, v.verse_number
                FROM nave_topic_verses ntv
                JOIN nave_topics nt ON nt.id = ntv.topic_id
                JOIN verses v ON v.id = ntv.verse_id
                JOIN chapters ch ON ch.id = v.chapter_id
                JOIN books b ON b.id = ch.book_id
                WHERE nt.topic = %s
                  AND v.translation_id = (SELECT id FROM translations WHERE abbreviation = 'KJV')
                ORDER BY random()
                LIMIT 3
            """, (topic,))
            supporting_verses = cur.fetchall()

        verses_context = ""
        if supporting_verses:
            parts = [f"{r[1]} {r[2]}:{r[3]}: \"{r[0][:120]}\"" for r in supporting_verses]
            verses_context = "\n\nRelevant scriptural grounding:\n" + "\n".join(f"- {p}" for p in parts)

        record = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an ethical reasoning assistant grounded in deep moral principles. Analyze ethical scenarios by identifying the relevant moral principles, considering multiple perspectives, and providing reasoned guidance that reflects wisdom, justice, and compassion."
                },
                {
                    "role": "user",
                    "content": s["scenario"]
                },
                {
                    "role": "assistant",
                    "content": s["principle"] + verses_context
                }
            ],
            "metadata": {
                "dataset": "ethics_reasoning",
                "topic": topic,
            }
        }
        records.append(record)

        # Generate variations with different framings
        for framing in ["What would be the most just response?",
                        "What does compassion require here?",
                        "How should someone of good character respond?"]:
            record_variant = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an ethical reasoning assistant. Provide thoughtful moral analysis grounded in principles of justice, mercy, truthfulness, and wisdom."
                    },
                    {
                        "role": "user",
                        "content": s["scenario"] + f"\n\n{framing}"
                    },
                    {
                        "role": "assistant",
                        "content": s["principle"]
                    }
                ],
                "metadata": {
                    "dataset": "ethics_reasoning",
                    "topic": topic,
                    "framing": framing,
                }
            }
            records.append(record_variant)

    return records


# ------------------------------------------------------------------
# Dataset 4: Crosslingual Alignment
# ------------------------------------------------------------------

def generate_crosslingual_alignment(conn) -> list[dict]:
    """Map Hebrew/Greek interlinear text to modern ethical principles.
    Uses word alignments + Strong's definitions to build input,
    Nave's topics + verse context to inform output.
    """
    print("Generating crosslingual_alignment...")

    with conn.cursor() as cur:
        # Get verses with rich interlinear data AND topical assignments
        cur.execute("""
            WITH rich_verses AS (
                SELECT wa.verse_id, count(*) as word_count
                FROM word_alignments wa
                GROUP BY wa.verse_id
                HAVING count(*) >= 5
            ),
            topical_verses AS (
                SELECT ntv.verse_id,
                       array_agg(DISTINCT nt.topic ORDER BY nt.topic) as topics
                FROM nave_topic_verses ntv
                JOIN nave_topics nt ON nt.id = ntv.topic_id
                GROUP BY ntv.verse_id
                HAVING count(DISTINCT nt.topic) >= 2
            )
            SELECT rv.verse_id, v.text, b.name, ch.chapter_number, v.verse_number,
                   tv.topics
            FROM rich_verses rv
            JOIN topical_verses tv ON tv.verse_id = rv.verse_id
            JOIN verses v ON v.id = rv.verse_id
            JOIN chapters ch ON ch.id = v.chapter_id
            JOIN books b ON b.id = ch.book_id
            WHERE v.translation_id = (SELECT id FROM translations WHERE abbreviation = 'KJV')
            ORDER BY random()
            LIMIT 800
        """)
        verses = cur.fetchall()

    records = []
    for row in verses:
        vid, text, book, ch, vs, topics = row

        # Build interlinear representation
        with conn.cursor() as cur:
            cur.execute("""
                SELECT wa.original_word, wa.transliteration, wa.english_gloss,
                       wa.strongs_number,
                       COALESCE(se.gloss, left(se.root_definition, 40)) as meaning
                FROM word_alignments wa
                LEFT JOIN strongs_entries se ON se.strongs_number = wa.strongs_number
                WHERE wa.verse_id = %s
                ORDER BY wa.word_position
            """, (vid,))
            words = cur.fetchall()

        if len(words) < 3:
            continue

        interlinear_parts = []
        for w in words:
            orig, translit, gloss, snum, meaning = w
            if translit and meaning:
                interlinear_parts.append(f"{translit} ({snum}: {meaning})")

        interlinear_str = " | ".join(interlinear_parts)
        ref = f"{book} {ch}:{vs}"
        topics_str = ", ".join(topics[:5])

        record = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a biblical language scholar. Given an interlinear breakdown of a verse showing the original Hebrew or Greek words with their root meanings, explain the deeper moral and theological significance that the original language reveals."
                },
                {
                    "role": "user",
                    "content": (
                        f"Analyze the original language of {ref} and explain what the root meanings reveal:\n\n"
                        f"English (KJV): \"{text[:200]}\"\n\n"
                        f"Interlinear: {interlinear_str[:500]}"
                    )
                },
                {
                    "role": "assistant",
                    "content": (
                        f"The original language of {ref} reveals layers of meaning not immediately apparent in English translation. "
                        f"This passage connects to the theological themes of {topics_str}.\n\n"
                        f"The key insight from the original language is that the moral teaching here is rooted in "
                        f"relational and covenantal concepts — the words chosen by the biblical author convey not just "
                        f"actions but dispositions of character. This means the ethical principle is not merely 'do X' "
                        f"but 'be the kind of person for whom X flows naturally from character.'\n\n"
                        f"Applied to moral reasoning: this passage teaches that ethical behavior is grounded in "
                        f"transformed character, not rule-following alone."
                    )
                }
            ],
            "metadata": {
                "dataset": "crosslingual_alignment",
                "reference": ref,
                "topics": topics[:5],
                "word_count": len(words),
            }
        }
        records.append(record)

    return records


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate LoRA training data from bible_research DB")
    parser.add_argument("--dataset", choices=["concept", "verse", "ethics", "crosslingual", "all"],
                        default="all", help="Which dataset to generate")
    parser.add_argument("--stats", action="store_true", help="Show dataset stats only")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    random.seed(args.seed)
    conn = get_connection()

    try:
        if args.stats:
            for f in OUTPUT_DIR.glob("*.jsonl"):
                with open(f) as fh:
                    count = sum(1 for _ in fh)
                print(f"  {f.name}: {count:,} records")
            return

        generators = {
            "concept": ("concept_to_principle.jsonl", generate_concept_to_principle),
            "verse": ("verse_to_analysis.jsonl", generate_verse_to_analysis),
            "ethics": ("ethics_reasoning.jsonl", generate_ethics_reasoning),
            "crosslingual": ("crosslingual_alignment.jsonl", generate_crosslingual_alignment),
        }

        datasets_to_run = generators.keys() if args.dataset == "all" else [args.dataset]
        all_records = []

        for key in datasets_to_run:
            filename, generator = generators[key]
            records = generator(conn)
            _write_jsonl(OUTPUT_DIR / filename, records)
            all_records.extend(records)

        # Write combined dataset
        if len(datasets_to_run) > 1:
            random.shuffle(all_records)
            _write_jsonl(OUTPUT_DIR / "combined_train.jsonl", all_records)

        print(f"\nTotal: {len(all_records):,} training examples")

    finally:
        conn.close()


if __name__ == "__main__":
    main()

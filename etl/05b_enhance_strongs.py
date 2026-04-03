"""Enhance Strong's entries with STEPBible lexicon data (BDB Hebrew, Abbott-Smith Greek).

Adds: gloss, extended_definition, morphology, sub_meanings (disambiguated senses).

Sources:
  - TBESH: Hebrew lexicon with extended Strong's, BDB definitions
  - TBESG: Greek lexicon with Abbott-Smith definitions

Usage: python -m etl.05b_enhance_strongs
"""

import json
import re
from collections import defaultdict
from pathlib import Path

from .config import RAW_DATA_DIR
from .db import get_connection, table_count


LEXICON_DIR = RAW_DATA_DIR / "STEPBible-Data" / "Lexicons"
TBESH = LEXICON_DIR / "TBESH - Translators Brief lexicon of Extended Strongs for Hebrew - STEPBible.org CC BY.txt"
TBESG = LEXICON_DIR / "TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt"


def _clean_html(text: str) -> str:
    """Strip HTML tags and clean up definition text."""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<ref=['\"].*?['\"]>", "", text)
    text = re.sub(r"</ref>", "", text)
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_lexicon(filepath: Path) -> dict:
    """Parse a STEPBible lexicon TSV file.

    Returns: {base_strongs: {
        'gloss': str,
        'morphology': str,
        'extended_definition': str,
        'sub_meanings': [{'code': 'H4941H', 'gloss': 'justice', 'sense': 'justice/right'}]
    }}
    """
    entries = {}
    sub_meanings = defaultdict(list)

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("\t") or line.startswith("="):
                continue

            cols = line.split("\t")
            if len(cols) < 8:
                continue

            raw_num = cols[0].strip()  # e.g., H4941 or H2617a
            dstrong = cols[1].strip()   # e.g., H4941G = or H4941H = a Meaning of
            # cols[2] = unified strong
            # cols[3] = Hebrew/Greek form
            # cols[4] = transliteration
            morph = cols[5].strip() if len(cols) > 5 else ""   # e.g., H:N-M
            gloss = cols[6].strip() if len(cols) > 6 else ""   # e.g., justice: judgement
            definition = cols[7].strip() if len(cols) > 7 else ""

            # Extract base number (strip trailing letter variants: H2617a -> H2617)
            base_match = re.match(r"^([HG]\d+)", raw_num)
            if not base_match:
                continue
            base_num = base_match.group(1)

            # Clean definition
            definition = _clean_html(definition)

            # Check if this is a sub-meaning (disambiguation)
            if "= a Meaning of" in dstrong or "= a Part of" in dstrong:
                # Extract the disambiguation code
                code_match = re.match(r"([HG]\d+\w+)", dstrong)
                code = code_match.group(1) if code_match else dstrong
                sense = gloss.split(":", 1)[-1].strip() if ":" in gloss else gloss
                sub_meanings[base_num].append({
                    "code": code,
                    "gloss": gloss,
                    "sense": sense,
                })
            elif "=" in dstrong and "Meaning" not in dstrong and "Part" not in dstrong:
                # Primary entry
                if base_num not in entries:
                    entries[base_num] = {
                        "gloss": gloss,
                        "morphology": morph,
                        "extended_definition": definition,
                    }
                elif len(definition) > len(entries[base_num].get("extended_definition", "")):
                    # Keep the longer definition
                    entries[base_num]["extended_definition"] = definition

    # Attach sub-meanings
    for base_num, subs in sub_meanings.items():
        if base_num in entries:
            entries[base_num]["sub_meanings"] = subs
        else:
            # Create entry from sub-meaning if no primary exists
            if subs:
                entries[base_num] = {
                    "gloss": subs[0]["gloss"],
                    "morphology": "",
                    "extended_definition": "",
                    "sub_meanings": subs,
                }

    return entries


def run():
    print("Parsing Hebrew lexicon (TBESH)...")
    hebrew = parse_lexicon(TBESH)
    print(f"  Parsed {len(hebrew)} Hebrew entries with enhanced definitions")

    print("Parsing Greek lexicon (TBESG)...")
    greek = parse_lexicon(TBESG)
    print(f"  Parsed {len(greek)} Greek entries with enhanced definitions")

    conn = get_connection()
    try:
        updated = 0

        with conn.cursor() as cur:
            for entries in [hebrew, greek]:
                for base_num, data in entries.items():
                    # Normalize to our format (H0001 not H1)
                    match = re.match(r"([HG])(\d+)", base_num)
                    if not match:
                        continue
                    normalized = f"{match.group(1)}{int(match.group(2)):04d}"

                    gloss = data.get("gloss", "")[:200]
                    morph = data.get("morphology", "")[:30]
                    ext_def = data.get("extended_definition", "")
                    sub_meanings = json.dumps(data.get("sub_meanings", []))

                    cur.execute("""
                        UPDATE strongs_entries
                        SET gloss = %s,
                            morphology = %s,
                            extended_definition = CASE
                                WHEN %s != '' AND length(%s) > length(COALESCE(detailed_definition, ''))
                                THEN %s ELSE detailed_definition END,
                            sub_meanings = %s::jsonb
                        WHERE strongs_number = %s
                    """, (gloss, morph, ext_def, ext_def, ext_def, sub_meanings, normalized))

                    if cur.rowcount > 0:
                        updated += 1

            conn.commit()

        # Count entries with sub-meanings
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM strongs_entries WHERE sub_meanings IS NOT NULL AND sub_meanings != '[]'::jsonb")
            with_subs = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM strongs_entries WHERE gloss IS NOT NULL AND gloss != ''")
            with_gloss = cur.fetchone()[0]

        print(f"\nUpdated {updated} Strong's entries")
        print(f"  With glosses: {with_gloss}")
        print(f"  With disambiguated sub-meanings: {with_subs}")

    finally:
        conn.close()


if __name__ == "__main__":
    run()

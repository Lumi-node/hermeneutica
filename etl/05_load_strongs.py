"""Load Strong's Concordance entries (Hebrew + Greek) into strongs_entries table.

Sources:
  - Hebrew: openscriptures/strongs/hebrew/StrongHebrewG.xml (OSIS format)
  - Greek: openscriptures/strongs/greek/StrongsGreekDictionaryXML_1.4/strongsgreek.xml

Usage: python -m etl.05_load_strongs
"""

import re
import xml.etree.ElementTree as ET

from .config import RAW_DATA_DIR, BATCH_SIZE
from .db import get_connection, bulk_insert, table_count


HEBREW_XML = RAW_DATA_DIR / "strongs" / "hebrew" / "StrongHebrewG.xml"
GREEK_XML = RAW_DATA_DIR / "strongs" / "greek" / "StrongsGreekDictionaryXML_1.4" / "strongsgreek.xml"

# OSIS namespace
NS = {"osis": "http://www.bibletechnologies.net/2003/OSIS/namespace"}


def _clean_text(text: str | None) -> str:
    """Clean up whitespace in extracted text."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _collect_text(elem) -> str:
    """Recursively collect all text content from an element and its children."""
    parts = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        parts.append(_collect_text(child))
        if child.tail:
            parts.append(child.tail)
    return " ".join(parts)


def parse_hebrew() -> list[tuple]:
    """Parse the OSIS-format Hebrew Strong's XML."""
    if not HEBREW_XML.exists():
        print(f"WARNING: {HEBREW_XML} not found, skipping Hebrew")
        return []

    tree = ET.parse(HEBREW_XML)
    root = tree.getroot()
    entries = []

    for div in root.findall(f".//{{{NS['osis']}}}div[@type='entry']"):
        num = div.get("n")
        if not num:
            continue
        strongs_number = f"H{int(num):04d}"

        # The <w> element has the Hebrew word and attributes
        w = div.find(f"{{{NS['osis']}}}w")
        if w is None:
            continue

        original_word = w.text or ""
        transliteration = w.get("xlit", "")
        pronunciation = w.get("POS", "")  # pronunciation in OSIS format
        lemma = w.get("lemma", "")
        morph = w.get("morph", "")

        # Definitions from <list><item> elements
        items = div.findall(f".//{{{NS['osis']}}}item")
        detailed_parts = [_clean_text(item.text) for item in items if item.text]
        detailed_definition = "; ".join(detailed_parts) if detailed_parts else ""

        # Short definition from <note type="explanation">
        explanation = div.find(f".//{{{NS['osis']}}}note[@type='explanation']")
        root_def = _clean_text(_collect_text(explanation)) if explanation is not None else ""
        if not root_def and detailed_definition:
            root_def = detailed_definition[:500]

        # KJV usage from <note type="translation">
        translation_note = div.find(f".//{{{NS['osis']}}}note[@type='translation']")
        kjv_usage = _clean_text(_collect_text(translation_note)) if translation_note is not None else ""

        # Etymology from <note type="exegesis">
        exegesis = div.find(f".//{{{NS['osis']}}}note[@type='exegesis']")
        etymology = _clean_text(_collect_text(exegesis)) if exegesis is not None else ""

        # Extract root Strong's reference if present in etymology
        root_strongs = None
        root_match = re.search(r"from\s+H?(\d+)", etymology)
        if root_match:
            root_strongs = f"H{int(root_match.group(1)):04d}"

        entries.append((
            strongs_number,     # strongs_number
            "heb",              # language
            original_word,      # original_word
            transliteration,    # transliteration
            pronunciation,      # pronunciation
            root_def[:500],     # root_definition
            detailed_definition or root_def,  # detailed_definition
            kjv_usage,          # kjv_usage
            root_strongs,       # root_strongs
            morph or None,      # part_of_speech
        ))

    return entries


def parse_greek() -> list[tuple]:
    """Parse the Greek Strong's XML."""
    if not GREEK_XML.exists():
        print(f"WARNING: {GREEK_XML} not found, skipping Greek")
        return []

    tree = ET.parse(GREEK_XML)
    root = tree.getroot()
    entries = []

    for entry in root.findall(".//entry"):
        num_str = entry.get("strongs", "")
        if not num_str:
            continue
        strongs_number = f"G{int(num_str):04d}"

        # Greek word
        greek_elem = entry.find("greek")
        original_word = ""
        transliteration = ""
        if greek_elem is not None:
            original_word = greek_elem.get("unicode", "")
            transliteration = greek_elem.get("translit", "")

        # Pronunciation
        pron_elem = entry.find("pronunciation")
        pronunciation = pron_elem.get("strongs", "") if pron_elem is not None else ""

        # Derivation (root info)
        deriv_elem = entry.find("strongs_derivation")
        derivation = _clean_text(_collect_text(deriv_elem)) if deriv_elem is not None else ""

        # Definition
        def_elem = entry.find("strongs_def")
        definition = _clean_text(_collect_text(def_elem)) if def_elem is not None else ""

        # KJV definition
        kjv_elem = entry.find("kjv_def")
        kjv_usage = _clean_text(_collect_text(kjv_elem)) if kjv_elem is not None else ""

        # Root Strong's from derivation or <see> references
        root_strongs = None
        # Check derivation for Hebrew or Greek root
        root_match = re.search(r"of Hebrew origin\s*\[?H?(\d+)\]?", derivation)
        if root_match:
            root_strongs = f"H{int(root_match.group(1)):04d}"
        else:
            root_match = re.search(r"from\s+G?(\d+)", derivation)
            if root_match:
                root_strongs = f"G{int(root_match.group(1)):04d}"

        root_def = definition[:500] if definition else derivation[:500]

        entries.append((
            strongs_number,
            "grc",
            original_word,
            transliteration,
            pronunciation,
            root_def,
            definition or derivation,
            kjv_usage,
            root_strongs,
            None,  # part_of_speech (not in Greek XML)
        ))

    return entries


def run():
    print("Parsing Hebrew Strong's...")
    hebrew = parse_hebrew()
    print(f"  Parsed {len(hebrew)} Hebrew entries")

    print("Parsing Greek Strong's...")
    greek = parse_greek()
    print(f"  Parsed {len(greek)} Greek entries")

    all_entries = hebrew + greek

    conn = get_connection()
    try:
        count = bulk_insert(
            conn,
            table="strongs_entries",
            columns=[
                "strongs_number", "language", "original_word", "transliteration",
                "pronunciation", "root_definition", "detailed_definition",
                "kjv_usage", "root_strongs", "part_of_speech",
            ],
            rows=all_entries,
            conflict_columns=["strongs_number"],
        )

        total = table_count(conn, "strongs_entries")
        print(f"\nStrong's: loaded {len(all_entries)} entries, DB total: {total}")

    finally:
        conn.close()


if __name__ == "__main__":
    run()

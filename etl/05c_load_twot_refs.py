"""Extract TWOT (Theological Wordbook of the OT) reference numbers from Strong's XML
and store them in strongs_entries.twot_ref.

The TWOT numbers create word-family groupings:
  - TWOT:2304 = the root word
  - TWOT:2304a, 2304b = derived forms from the same root
  - Words sharing a TWOT base number belong to the same theological word-family

Usage: python -m etl.05c_load_twot_refs
"""

import re
import xml.etree.ElementTree as ET

from .config import RAW_DATA_DIR
from .db import get_connection


HEBREW_XML = RAW_DATA_DIR / "strongs" / "hebrew" / "StrongHebrewG.xml"
NS = {"osis": "http://www.bibletechnologies.net/2003/OSIS/namespace"}


def run():
    if not HEBREW_XML.exists():
        print(f"ERROR: {HEBREW_XML} not found")
        return

    tree = ET.parse(HEBREW_XML)
    root = tree.getroot()

    mappings = []  # (strongs_number, twot_ref)

    for div in root.findall(f".//{{{NS['osis']}}}div[@type='entry']"):
        num = div.get("n")
        if not num:
            continue

        w = div.find(f"{{{NS['osis']}}}w")
        if w is None:
            continue

        twot = w.get("gloss", "").strip()
        if not twot:
            continue

        strongs_number = f"H{int(num):04d}"
        mappings.append((twot, strongs_number))

    print(f"Extracted {len(mappings)} TWOT references")

    # Analyze word families
    families = {}
    for twot_ref, snum in mappings:
        # Extract base number: "2304a" -> "2304", "4a" -> "4"
        base = re.match(r"(\d+)", twot_ref)
        if base:
            families.setdefault(base.group(1), []).append((snum, twot_ref))

    multi_member = sum(1 for f in families.values() if len(f) > 1)
    print(f"TWOT word families: {len(families)} total, {multi_member} with multiple members")

    # Show example families
    print("\nSample word families:")
    shown = 0
    for base, members in sorted(families.items(), key=lambda x: -len(x[1])):
        if len(members) >= 3 and shown < 5:
            print(f"  TWOT {base}: {', '.join(f'{s}({t})' for s, t in members[:6])}")
            shown += 1

    # Update database
    conn = get_connection()
    try:
        updated = 0
        with conn.cursor() as cur:
            for twot_ref, strongs_number in mappings:
                cur.execute(
                    "UPDATE strongs_entries SET twot_ref = %s WHERE strongs_number = %s",
                    (twot_ref, strongs_number),
                )
                updated += cur.rowcount
        conn.commit()
        print(f"\nUpdated {updated} entries with TWOT references")

    finally:
        conn.close()


if __name__ == "__main__":
    run()

"""ETL 10: Load confessions & creeds with proof-text verse references.

Sources:
  - NonlinearFruit/Creeds.json  (JSON, structured proofs for HC, WCF, WLC)
  - reformed-standards/compendium (YAML, WSC-PCA proofs + Belgic/Dort text)

Usage:
  python -m etl.10_load_confessions          # load all 6 confessions
  python -m etl.10_load_confessions --stats   # show counts only
"""

import json
import re
import sys
from pathlib import Path

import yaml

from .config import RAW_DATA_DIR, BATCH_SIZE
from .db import get_connection, bulk_insert, table_count

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

CONFESSIONS_DIR = RAW_DATA_DIR / "confessions"
CREEDS_DIR = CONFESSIONS_DIR / "Creeds.json" / "creeds"
COMPENDIUM_DIR = CONFESSIONS_DIR / "compendium" / "data"

# ---------------------------------------------------------------------------
# OSIS → DB book abbreviation mapping
# ---------------------------------------------------------------------------

OSIS_TO_DB = {
    "Gen": "Gen", "Exod": "Exo", "Lev": "Lev", "Num": "Num", "Deut": "Deu",
    "Josh": "Jos", "Judg": "Jdg", "Ruth": "Rut",
    "1Sam": "1Sa", "2Sam": "2Sa", "1Kgs": "1Ki", "2Kgs": "2Ki",
    "1Chr": "1Ch", "2Chr": "2Ch", "Ezra": "Ezr", "Neh": "Neh", "Esth": "Est",
    "Job": "Job", "Ps": "Psa", "Prov": "Pro", "Eccl": "Ecc", "Song": "Sol",
    "Isa": "Isa", "Jer": "Jer", "Lam": "Lam", "Ezek": "Eze", "Dan": "Dan",
    "Hos": "Hos", "Joel": "Joe", "Amos": "Amo", "Obad": "Oba", "Jonah": "Jon",
    "Mic": "Mic", "Nah": "Nah", "Hab": "Hab", "Zeph": "Zep", "Hag": "Hag",
    "Zech": "Zec", "Mal": "Mal",
    "Matt": "Mat", "Mark": "Mar", "Luke": "Luk", "John": "Joh",
    "Acts": "Act", "Rom": "Rom",
    "1Cor": "1Co", "2Cor": "2Co", "Gal": "Gal", "Eph": "Eph",
    "Phil": "Phi", "Col": "Col",
    "1Thess": "1Th", "2Thess": "2Th", "1Tim": "1Ti", "2Tim": "2Ti",
    "Titus": "Tit", "Phlm": "Phm", "Heb": "Heb",
    "Jas": "Jam", "1Pet": "1Pe", "2Pet": "2Pe",
    "1John": "1Jo", "2John": "2Jo", "3John": "3Jo",
    "Jude": "Jud", "Rev": "Rev",
}

# Regex for OSIS references: Book.Chapter.Verse (with optional range)
OSIS_REF_RE = re.compile(
    r"^(?P<book>[A-Z0-9][a-zA-Z]+)\.(?P<chapter>\d+)\.(?P<verse>\d+)"
    r"(?:-(?P<end_book>[A-Z0-9][a-zA-Z]+)\.(?P<end_chapter>\d+)\.(?P<end_verse>\d+))?$"
)

# Also handle comma-separated verses within same ref string: "1Cor.6.19,1Cor.6.2"
OSIS_COMMA_RE = re.compile(r"[A-Z0-9][a-zA-Z]+\.\d+\.\d+")


# ---------------------------------------------------------------------------
# Verse resolver
# ---------------------------------------------------------------------------

class VerseResolver:
    """Resolves OSIS references to verse IDs using a preloaded lookup table."""

    def __init__(self, conn):
        self.lookup = {}  # (db_abbrev, chapter, verse) → verse_id
        self._load(conn)

    def _load(self, conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT v.id, b.abbreviation, ch.chapter_number, v.verse_number
                FROM verses v
                JOIN chapters ch ON ch.id = v.chapter_id
                JOIN books b ON b.id = ch.book_id
                WHERE v.translation_id = (
                    SELECT id FROM translations WHERE abbreviation = 'KJV' LIMIT 1
                )
            """)
            for row in cur:
                self.lookup[(row[1], row[2], row[3])] = row[0]
        print(f"  Loaded {len(self.lookup):,} verse lookup entries")

    def resolve(self, osis_ref: str) -> list[int | None]:
        """Resolve an OSIS ref string to a list of verse_ids.

        Handles:
          - Single: 'Rom.8.28' → [verse_id]
          - Range: 'Rom.14.7-Rom.14.9' → [v7_id, v8_id, v9_id]
          - Comma: '1Cor.6.19,1Cor.6.2' → [v19_id, v2_id]
        """
        # Handle comma-separated refs within a single string
        if "," in osis_ref:
            individual = OSIS_COMMA_RE.findall(osis_ref)
            results = []
            for ref in individual:
                results.extend(self.resolve(ref))
            return results

        m = OSIS_REF_RE.match(osis_ref)
        if not m:
            return [None]

        book = m.group("book")
        chapter = int(m.group("chapter"))
        verse = int(m.group("verse"))
        db_abbrev = OSIS_TO_DB.get(book)
        if not db_abbrev:
            return [None]

        # Range
        if m.group("end_verse"):
            end_chapter = int(m.group("end_chapter"))
            end_verse = int(m.group("end_verse"))

            if chapter == end_chapter:
                # Same chapter range
                return [
                    self.lookup.get((db_abbrev, chapter, v))
                    for v in range(verse, end_verse + 1)
                ]
            else:
                # Cross-chapter range (rare but possible)
                results = []
                # Get max verse for start chapter (scan lookup)
                max_v = max(
                    (v for (b, c, v) in self.lookup if b == db_abbrev and c == chapter),
                    default=verse,
                )
                for v in range(verse, max_v + 1):
                    results.append(self.lookup.get((db_abbrev, chapter, v)))
                for v in range(1, end_verse + 1):
                    results.append(self.lookup.get((db_abbrev, end_chapter, v)))
                return results

        # Single verse
        return [self.lookup.get((db_abbrev, chapter, verse))]


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS confessions (
    id              SMALLSERIAL  PRIMARY KEY,
    name            VARCHAR(120) NOT NULL UNIQUE,
    abbreviation    VARCHAR(10)  NOT NULL UNIQUE,
    confession_type VARCHAR(20)  NOT NULL,
    tradition       VARCHAR(30)  NOT NULL,
    year            SMALLINT     NOT NULL,
    authors         TEXT,
    original_language VARCHAR(10),
    source_url      TEXT,
    source_repo     VARCHAR(80),
    loaded_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS confession_items (
    id                  SERIAL       PRIMARY KEY,
    confession_id       SMALLINT     NOT NULL REFERENCES confessions(id) ON DELETE CASCADE,
    parent_id           INTEGER      REFERENCES confession_items(id) ON DELETE CASCADE,
    item_number         SMALLINT     NOT NULL,
    item_type           VARCHAR(20)  NOT NULL,
    title               TEXT,
    question_text       TEXT,
    answer_text         TEXT,
    answer_with_proofs  TEXT,
    sort_order          SMALLINT     NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ci_confession ON confession_items (confession_id);
CREATE INDEX IF NOT EXISTS idx_ci_parent     ON confession_items (parent_id);
CREATE INDEX IF NOT EXISTS idx_ci_type       ON confession_items (item_type);

CREATE TABLE IF NOT EXISTS confession_proof_texts (
    id              SERIAL       PRIMARY KEY,
    item_id         INTEGER      NOT NULL REFERENCES confession_items(id) ON DELETE CASCADE,
    verse_id        INTEGER      REFERENCES verses(id),
    proof_group     VARCHAR(5)   NOT NULL,
    osis_ref        TEXT         NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cpt_item  ON confession_proof_texts (item_id);
CREATE INDEX IF NOT EXISTS idx_cpt_verse ON confession_proof_texts (verse_id);
CREATE INDEX IF NOT EXISTS idx_cpt_group ON confession_proof_texts (proof_group);

-- Views
CREATE OR REPLACE VIEW v_confession_items AS
SELECT
    ci.id AS item_id,
    c.name AS confession_name,
    c.abbreviation AS confession_abbrev,
    c.confession_type,
    ci.item_type,
    ci.item_number,
    ci.title,
    ci.question_text,
    ci.answer_text,
    p.item_number AS parent_number,
    p.title AS parent_title,
    p.item_type AS parent_type
FROM confession_items ci
JOIN confessions c ON c.id = ci.confession_id
LEFT JOIN confession_items p ON p.id = ci.parent_id;

CREATE OR REPLACE VIEW v_confession_proof_texts AS
SELECT
    cpt.id AS proof_id,
    c.abbreviation AS confession_abbrev,
    ci.item_type,
    ci.item_number,
    ci.title AS item_title,
    cpt.proof_group,
    cpt.osis_ref,
    vv.book_name,
    vv.chapter_number,
    vv.verse_number,
    vv.text AS verse_text
FROM confession_proof_texts cpt
JOIN confession_items ci ON ci.id = cpt.item_id
JOIN confessions c ON c.id = ci.confession_id
LEFT JOIN v_verses vv ON vv.verse_id = cpt.verse_id;
"""

# ---------------------------------------------------------------------------
# Confession definitions
# ---------------------------------------------------------------------------

CONFESSION_DEFS = [
    {
        "name": "Heidelberg Catechism",
        "abbreviation": "HC",
        "confession_type": "catechism",
        "tradition": "reformed",
        "year": 1563,
        "source_repo": "Creeds.json",
        "loader": "load_creeds_catechism",
        "file": "heidelberg_catechism.json",
    },
    {
        "name": "Westminster Confession of Faith",
        "abbreviation": "WCF",
        "confession_type": "confession",
        "tradition": "presbyterian",
        "year": 1647,
        "source_repo": "Creeds.json",
        "loader": "load_creeds_confession",
        "file": "westminster_confession_of_faith.json",
    },
    {
        "name": "Westminster Larger Catechism",
        "abbreviation": "WLC",
        "confession_type": "catechism",
        "tradition": "presbyterian",
        "year": 1647,
        "source_repo": "Creeds.json",
        "loader": "load_creeds_catechism",
        "file": "westminster_larger_catechism.json",
    },
    {
        "name": "Westminster Shorter Catechism",
        "abbreviation": "WSC",
        "confession_type": "catechism",
        "tradition": "presbyterian",
        "year": 1647,
        "source_repo": "compendium",
        "loader": "load_compendium_catechism",
        "file": "westminster/wsc-pca.yaml",
    },
    {
        "name": "Belgic Confession",
        "abbreviation": "BC",
        "confession_type": "confession",
        "tradition": "reformed",
        "year": 1561,
        "source_repo": "Creeds.json",
        "loader": "load_creeds_articles",
        "file": "belgic_confession_of_faith.json",
    },
    {
        "name": "Canons of Dort",
        "abbreviation": "CD",
        "confession_type": "canon",
        "tradition": "reformed",
        "year": 1618,
        "source_repo": "compendium",
        "loader": "load_compendium_canons",
        "file": "three-forms-of-unity/canons-of-dort.yaml",
    },
]

# ---------------------------------------------------------------------------
# Loader functions
# ---------------------------------------------------------------------------

def insert_confession(conn, defn: dict) -> int:
    """Insert or get the confession row, return its id."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM confessions WHERE abbreviation = %s", (defn["abbreviation"],))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            """INSERT INTO confessions (name, abbreviation, confession_type, tradition, year, source_repo)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (defn["name"], defn["abbreviation"], defn["confession_type"],
             defn["tradition"], defn["year"], defn["source_repo"]),
        )
        cid = cur.fetchone()[0]
        conn.commit()
        return cid


def insert_item(conn, confession_id: int, parent_id: int | None, item_number: int,
                item_type: str, title: str | None, question_text: str | None,
                answer_text: str | None, answer_with_proofs: str | None,
                sort_order: int) -> int:
    """Insert a confession_item row and return its id."""
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO confession_items
               (confession_id, parent_id, item_number, item_type, title,
                question_text, answer_text, answer_with_proofs, sort_order)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (confession_id, parent_id, item_number, item_type, title,
             question_text, answer_text, answer_with_proofs, sort_order),
        )
        iid = cur.fetchone()[0]
        conn.commit()
        return iid


def insert_proof_texts(conn, item_id: int, proofs: list[dict], resolver: VerseResolver) -> int:
    """Insert proof text rows for an item. Returns count inserted."""
    rows = []
    for proof in proofs:
        group = str(proof["group"])
        for ref in proof["refs"]:
            verse_ids = resolver.resolve(ref)
            for vid in verse_ids:
                rows.append((item_id, vid, group, ref))

    if not rows:
        return 0

    return bulk_insert(
        conn, "confession_proof_texts",
        ["item_id", "verse_id", "proof_group", "osis_ref"],
        rows,
        on_conflict="DO NOTHING",
    )


# --- Creeds.json catechism (HC, WLC) ---

def load_creeds_catechism(conn, defn: dict, resolver: VerseResolver):
    """Load a catechism from Creeds.json format (Q&A with Proofs array)."""
    path = CREEDS_DIR / defn["file"]
    with open(path) as f:
        data = json.load(f)

    cid = insert_confession(conn, defn)
    meta = data.get("Metadata", {})
    items = data["Data"]

    count_items = 0
    count_proofs = 0

    for i, item in enumerate(items):
        iid = insert_item(
            conn, cid,
            parent_id=None,
            item_number=item["Number"],
            item_type="question",
            title=None,
            question_text=item.get("Question"),
            answer_text=item.get("Answer"),
            answer_with_proofs=item.get("AnswerWithProofs"),
            sort_order=i,
        )
        count_items += 1

        proofs = []
        for p in item.get("Proofs", []):
            proofs.append({"group": str(p["Id"]), "refs": p.get("References", [])})
        count_proofs += insert_proof_texts(conn, iid, proofs, resolver)

    print(f"  {defn['abbreviation']}: {count_items} items, {count_proofs} proof-text links")


# --- Creeds.json confession (WCF) ---

def load_creeds_confession(conn, defn: dict, resolver: VerseResolver):
    """Load WCF from Creeds.json format (Chapter → Sections with Proofs)."""
    path = CREEDS_DIR / defn["file"]
    with open(path) as f:
        data = json.load(f)

    cid = insert_confession(conn, defn)
    chapters = data["Data"]

    count_items = 0
    count_proofs = 0
    sort = 0

    for ch in chapters:
        ch_num = int(ch["Chapter"])
        ch_title = ch.get("Title")

        # Insert chapter as parent item
        ch_id = insert_item(
            conn, cid,
            parent_id=None,
            item_number=ch_num,
            item_type="chapter",
            title=ch_title,
            question_text=None,
            answer_text=None,
            answer_with_proofs=None,
            sort_order=sort,
        )
        count_items += 1
        sort += 1

        for sec in ch.get("Sections", []):
            sec_num = sec.get("Section", sort)
            if isinstance(sec_num, str):
                sec_num = int(sec_num) if sec_num.isdigit() else sort

            sec_id = insert_item(
                conn, cid,
                parent_id=ch_id,
                item_number=sec_num,
                item_type="section",
                title=None,
                question_text=None,
                answer_text=sec.get("Content"),
                answer_with_proofs=sec.get("ContentWithProofs"),
                sort_order=sort,
            )
            count_items += 1
            sort += 1

            proofs = []
            for p in sec.get("Proofs", []):
                proofs.append({"group": str(p["Id"]), "refs": p.get("References", [])})
            count_proofs += insert_proof_texts(conn, sec_id, proofs, resolver)

    print(f"  {defn['abbreviation']}: {count_items} items, {count_proofs} proof-text links")


# --- Creeds.json articles (Belgic) ---

def load_creeds_articles(conn, defn: dict, resolver: VerseResolver):
    """Load Belgic Confession from Creeds.json (articles, no structured proofs)."""
    path = CREEDS_DIR / defn["file"]
    with open(path) as f:
        data = json.load(f)

    cid = insert_confession(conn, defn)
    articles = data["Data"]

    count_items = 0
    for i, art in enumerate(articles):
        insert_item(
            conn, cid,
            parent_id=None,
            item_number=int(art["Article"]),
            item_type="article",
            title=art.get("Title"),
            question_text=None,
            answer_text=art.get("Content"),
            answer_with_proofs=None,
            sort_order=i,
        )
        count_items += 1

    print(f"  {defn['abbreviation']}: {count_items} items, 0 proof-text links (inline refs only)")


# --- Compendium catechism (WSC-PCA) ---

def load_compendium_catechism(conn, defn: dict, resolver: VerseResolver):
    """Load WSC from compendium YAML (Q&A with verse groups)."""
    path = COMPENDIUM_DIR / defn["file"]
    with open(path) as f:
        data = yaml.safe_load(f)

    cid = insert_confession(conn, defn)
    questions = data.get("questions", [])

    count_items = 0
    count_proofs = 0

    for i, q in enumerate(questions):
        # Split answer markers like [a] [b] from text
        raw_answer = q.get("answer", "")
        # Clean answer: remove [a] markers for plain text
        clean_answer = re.sub(r"\[([a-z])\]", "", raw_answer).strip()

        iid = insert_item(
            conn, cid,
            parent_id=None,
            item_number=q.get("number", i + 1),
            item_type="question",
            title=None,
            question_text=q.get("question"),
            answer_text=clean_answer,
            answer_with_proofs=raw_answer if raw_answer != clean_answer else None,
            sort_order=i,
        )
        count_items += 1

        proofs = []
        for group_key, refs in (q.get("verses") or {}).items():
            proofs.append({"group": group_key, "refs": refs})
        count_proofs += insert_proof_texts(conn, iid, proofs, resolver)

    print(f"  {defn['abbreviation']}: {count_items} items, {count_proofs} proof-text links")


# --- Compendium canons (Dort) ---

def load_compendium_canons(conn, defn: dict, resolver: VerseResolver):
    """Load Canons of Dort from compendium YAML (heads → articles)."""
    path = COMPENDIUM_DIR / defn["file"]
    with open(path) as f:
        data = yaml.safe_load(f)

    cid = insert_confession(conn, defn)
    chapters = data.get("chapters", [])

    count_items = 0
    sort = 0

    for ch in chapters:
        ch_num = ch.get("number", sort + 1)
        ch_name = ch.get("name", "")

        head_id = insert_item(
            conn, cid,
            parent_id=None,
            item_number=ch_num,
            item_type="head",
            title=ch_name,
            question_text=None,
            answer_text=None,
            answer_with_proofs=None,
            sort_order=sort,
        )
        count_items += 1
        sort += 1

        for art in ch.get("articles", []):
            art_num = art.get("number", sort)
            insert_item(
                conn, cid,
                parent_id=head_id,
                item_number=art_num,
                item_type="article",
                title=None,
                question_text=None,
                answer_text=art.get("text", "").strip(),
                answer_with_proofs=None,
                sort_order=sort,
            )
            count_items += 1
            sort += 1

    print(f"  {defn['abbreviation']}: {count_items} items, 0 proof-text links (inline refs only)")


# ---------------------------------------------------------------------------
# Loader dispatch
# ---------------------------------------------------------------------------

LOADERS = {
    "load_creeds_catechism": load_creeds_catechism,
    "load_creeds_confession": load_creeds_confession,
    "load_creeds_articles": load_creeds_articles,
    "load_compendium_catechism": load_compendium_catechism,
    "load_compendium_canons": load_compendium_canons,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def show_stats(conn):
    """Print current table counts."""
    print("\n=== Confessions & Creeds Stats ===")
    for tbl in ["confessions", "confession_items", "confession_proof_texts"]:
        print(f"  {tbl}: {table_count(conn, tbl):,} rows")

    with conn.cursor() as cur:
        # Per-confession breakdown
        cur.execute("""
            SELECT c.abbreviation, c.name,
                   COUNT(DISTINCT ci.id) AS items,
                   COUNT(cpt.id) AS proofs,
                   COUNT(DISTINCT cpt.verse_id) FILTER (WHERE cpt.verse_id IS NOT NULL) AS unique_verses
            FROM confessions c
            LEFT JOIN confession_items ci ON ci.confession_id = c.id
            LEFT JOIN confession_proof_texts cpt ON cpt.item_id = ci.id
            GROUP BY c.id ORDER BY c.year
        """)
        print("\n  Per-confession breakdown:")
        print(f"  {'Abbrev':<6} {'Name':<40} {'Items':>6} {'Proofs':>7} {'Uniq Verses':>12}")
        print(f"  {'-'*6} {'-'*40} {'-'*6} {'-'*7} {'-'*12}")
        for row in cur:
            print(f"  {row[0]:<6} {row[1]:<40} {row[2]:>6,} {row[3]:>7,} {row[4]:>12,}")

        # Resolution rate
        cur.execute("""
            SELECT COUNT(*) AS total,
                   COUNT(verse_id) AS resolved,
                   COUNT(*) - COUNT(verse_id) AS unresolved
            FROM confession_proof_texts
        """)
        total, resolved, unresolved = cur.fetchone()
        if total > 0:
            pct = resolved / total * 100
            print(f"\n  Proof-text resolution: {resolved:,}/{total:,} ({pct:.1f}%) — {unresolved:,} unresolved")

        # Most-cited verses across confessions
        cur.execute("""
            SELECT vv.book_name, vv.chapter_number, vv.verse_number,
                   COUNT(DISTINCT c.id) AS conf_count,
                   array_agg(DISTINCT c.abbreviation ORDER BY c.abbreviation) AS cited_by
            FROM confession_proof_texts cpt
            JOIN confession_items ci ON ci.id = cpt.item_id
            JOIN confessions c ON c.id = ci.confession_id
            JOIN v_verses vv ON vv.verse_id = cpt.verse_id
            GROUP BY vv.book_name, vv.chapter_number, vv.verse_number
            HAVING COUNT(DISTINCT c.id) >= 3
            ORDER BY conf_count DESC, COUNT(*) DESC
            LIMIT 15
        """)
        rows = cur.fetchall()
        if rows:
            print(f"\n  Most-cited verses (across 3+ confessions):")
            for r in rows:
                ref = f"{r[0]} {r[1]}:{r[2]}"
                print(f"    {ref:<25} cited by {r[3]} confessions: {', '.join(r[4])}")


def main():
    stats_only = "--stats" in sys.argv

    conn = get_connection()

    if stats_only:
        show_stats(conn)
        conn.close()
        return

    print("=== ETL 10: Load Confessions & Creeds ===\n")

    # Create tables
    print("Creating tables...")
    with conn.cursor() as cur:
        cur.execute(CREATE_SQL)
        # Ensure osis_ref column is TEXT (idempotent, must drop/recreate view)
        cur.execute("DROP VIEW IF EXISTS v_confession_proof_texts CASCADE")
        cur.execute("ALTER TABLE confession_proof_texts ALTER COLUMN osis_ref TYPE TEXT")
        # Recreate views
        cur.execute(CREATE_SQL)
        conn.commit()

    # Clear existing data for idempotent re-runs
    with conn.cursor() as cur:
        cur.execute("DELETE FROM confession_proof_texts")
        cur.execute("DELETE FROM confession_items")
        cur.execute("DELETE FROM confessions")
        conn.commit()
    print("  Cleared existing data (idempotent reload)\n")

    # Build verse resolver
    print("Building verse resolver...")
    resolver = VerseResolver(conn)

    # Load each confession
    print("\nLoading confessions:")
    for defn in CONFESSION_DEFS:
        loader_fn = LOADERS[defn["loader"]]
        loader_fn(conn, defn, resolver)

    # Show stats
    show_stats(conn)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

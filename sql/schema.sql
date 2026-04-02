-- ============================================================
-- Bible Research Database Schema
-- PostgreSQL 16 + pgvector 0.6.0
-- ============================================================

-- Run as superuser:
--   CREATE DATABASE bible_research WITH ENCODING = 'UTF8';
--   \c bible_research

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;     -- pgvector for embeddings + HNSW
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- trigram indexing for text search


-- ============================================================
-- 1. CORE TEXT TABLES
-- ============================================================

-- Translation metadata (KJV, Hebrew, Greek, etc.)
CREATE TABLE translations (
    id              SMALLSERIAL  PRIMARY KEY,
    abbreviation    VARCHAR(10)  NOT NULL UNIQUE,
    name            VARCHAR(120) NOT NULL,
    language        VARCHAR(3)   NOT NULL,          -- ISO 639-3: 'eng','heb','grc'
    license         VARCHAR(60)  NOT NULL DEFAULT 'public_domain',
    source_url      TEXT,
    loaded_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 66 canonical books
CREATE TABLE books (
    id              SMALLSERIAL  PRIMARY KEY,
    name            VARCHAR(30)  NOT NULL UNIQUE,
    abbreviation    VARCHAR(6)   NOT NULL UNIQUE,
    testament       VARCHAR(2)   NOT NULL CHECK (testament IN ('OT','NT')),
    genre           VARCHAR(30)  NOT NULL,           -- Law, History, Wisdom, Prophecy, Gospel, Epistle, Apocalyptic
    book_order      SMALLINT     NOT NULL UNIQUE,    -- 1-66 canonical order
    chapter_count   SMALLINT     NOT NULL
);

-- Chapters (1,189 total)
CREATE TABLE chapters (
    id              SERIAL       PRIMARY KEY,
    book_id         SMALLINT     NOT NULL REFERENCES books(id),
    chapter_number  SMALLINT     NOT NULL,
    UNIQUE (book_id, chapter_number)
);

-- Verse text per translation
-- ~31,102 verses per translation
CREATE TABLE verses (
    id              SERIAL       PRIMARY KEY,
    chapter_id      INTEGER      NOT NULL REFERENCES chapters(id),
    verse_number    SMALLINT     NOT NULL,
    translation_id  SMALLINT     NOT NULL REFERENCES translations(id),
    text            TEXT         NOT NULL,
    UNIQUE (chapter_id, verse_number, translation_id)
);
CREATE INDEX idx_verses_chapter     ON verses (chapter_id);
CREATE INDEX idx_verses_translation ON verses (translation_id);
CREATE INDEX idx_verses_ch_trans    ON verses (chapter_id, translation_id);
CREATE INDEX idx_verses_text_trgm   ON verses USING gin (text gin_trgm_ops);


-- ============================================================
-- 2. STRONG'S CONCORDANCE
-- ============================================================

-- Unified Hebrew (H0001-H8674) + Greek (G0001-G5624) lexicon
CREATE TABLE strongs_entries (
    id                  SERIAL       PRIMARY KEY,
    strongs_number      VARCHAR(10)  NOT NULL UNIQUE,  -- 'H0001', 'G0001'
    language            VARCHAR(3)   NOT NULL CHECK (language IN ('heb','grc')),
    original_word       VARCHAR(60)  NOT NULL,          -- Hebrew/Greek characters
    transliteration     VARCHAR(80)  NOT NULL,
    pronunciation       VARCHAR(120),
    root_definition     VARCHAR(500) NOT NULL,          -- Brief one-line definition
    detailed_definition TEXT         NOT NULL,           -- Full BDB/Thayer entry
    kjv_usage           TEXT,                            -- KJV translation frequency stats
    root_strongs        VARCHAR(10),                     -- Etymology link (self-referencing)
    part_of_speech      VARCHAR(30)                      -- noun, verb, adjective, etc.
);
CREATE INDEX idx_strongs_language ON strongs_entries (language);
CREATE INDEX idx_strongs_root    ON strongs_entries (root_strongs);
CREATE INDEX idx_strongs_def_trgm ON strongs_entries USING gin (detailed_definition gin_trgm_ops);


-- ============================================================
-- 3. INTERLINEAR WORD ALIGNMENT
-- ============================================================

-- Per-word alignment: original language word + Strong's + morphology + gloss
-- Source: STEPBible TAHOT (Hebrew OT) + TAGNT (Greek NT)
-- ~305K Hebrew + ~140K Greek = ~445K rows
CREATE TABLE word_alignments (
    id                  SERIAL       PRIMARY KEY,
    verse_id            INTEGER      NOT NULL,          -- FK to verses (Hebrew/Greek source)
    word_position       SMALLINT     NOT NULL,          -- 1-based position in verse
    original_word       VARCHAR(60)  NOT NULL,          -- Hebrew/Greek as it appears
    strongs_number      VARCHAR(10)  NOT NULL,          -- Links to strongs_entries
    morphology_code     VARCHAR(30),                     -- e.g. 'HVqp3ms'
    english_gloss       VARCHAR(120) NOT NULL,          -- English translation of this word
    transliteration     VARCHAR(80),
    UNIQUE (verse_id, word_position)
);
CREATE INDEX idx_wordalign_verse   ON word_alignments (verse_id);
CREATE INDEX idx_wordalign_strongs ON word_alignments (strongs_number);
CREATE INDEX idx_wordalign_morph   ON word_alignments (morphology_code);


-- ============================================================
-- 4. CROSS-REFERENCES
-- ============================================================

-- ~340K cross-references from OpenBible.info / Treasury of Scripture Knowledge
CREATE TABLE cross_references (
    id                  SERIAL       PRIMARY KEY,
    source_verse_id     INTEGER      NOT NULL,
    target_verse_id     INTEGER      NOT NULL,
    relevance_score     REAL         NOT NULL DEFAULT 0.0
                        CHECK (relevance_score >= 0 AND relevance_score <= 1),
    ref_type            VARCHAR(20)  NOT NULL DEFAULT 'thematic',
    source_ref          VARCHAR(20)  NOT NULL,          -- Original string 'Gen.1.1'
    target_ref          VARCHAR(20)  NOT NULL,
    UNIQUE (source_verse_id, target_verse_id)
);
CREATE INDEX idx_xref_source ON cross_references (source_verse_id);
CREATE INDEX idx_xref_target ON cross_references (target_verse_id);
CREATE INDEX idx_xref_score  ON cross_references (relevance_score DESC);


-- ============================================================
-- 5. HERMENEUTICS (maps to PassageClassification in hermeneutics.py)
-- ============================================================

-- One classification per chapter
CREATE TABLE passage_classifications (
    id                  SERIAL       PRIMARY KEY,
    chapter_id          INTEGER      NOT NULL REFERENCES chapters(id) UNIQUE,
    genre               VARCHAR(40)  NOT NULL,
    genre_confidence    REAL         NOT NULL
                        CHECK (genre_confidence >= 0 AND genre_confidence <= 1),
    themes              TEXT[]       NOT NULL,           -- Postgres array, GIN-indexed
    teaching_type       VARCHAR(40)  NOT NULL,
    ethics_reasoning    TEXT         NOT NULL,
    classified_by       VARCHAR(80)  NOT NULL DEFAULT '',
    classified_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    schema_version      VARCHAR(10)  NOT NULL DEFAULT '1.0'
);
CREATE INDEX idx_pc_genre    ON passage_classifications (genre);
CREATE INDEX idx_pc_teaching ON passage_classifications (teaching_type);
CREATE INDEX idx_pc_themes   ON passage_classifications USING gin (themes);

-- Ethics relevance scores (5 rows per classification, one per ETHICS subset)
CREATE TABLE passage_ethics_scores (
    id                  SERIAL       PRIMARY KEY,
    classification_id   INTEGER      NOT NULL REFERENCES passage_classifications(id) ON DELETE CASCADE,
    ethics_subset       VARCHAR(20)  NOT NULL,
    relevance_score     REAL         NOT NULL
                        CHECK (relevance_score >= 0 AND relevance_score <= 1),
    UNIQUE (classification_id, ethics_subset)
);
CREATE INDEX idx_pes_subset ON passage_ethics_scores (ethics_subset, relevance_score DESC);

-- Distilled moral principles extracted from each passage
CREATE TABLE distilled_principles (
    id                  SERIAL       PRIMARY KEY,
    classification_id   INTEGER      NOT NULL REFERENCES passage_classifications(id) ON DELETE CASCADE,
    principle_text      TEXT         NOT NULL,
    principle_order     SMALLINT     NOT NULL DEFAULT 0,
    UNIQUE (classification_id, principle_order)
);
CREATE INDEX idx_dp_classification ON distilled_principles (classification_id);
CREATE INDEX idx_dp_text_trgm      ON distilled_principles USING gin (principle_text gin_trgm_ops);

-- Per-principle ethics mapping (inherits from parent classification, can be refined)
CREATE TABLE principle_ethics_mapping (
    id                  SERIAL       PRIMARY KEY,
    principle_id        INTEGER      NOT NULL REFERENCES distilled_principles(id) ON DELETE CASCADE,
    ethics_subset       VARCHAR(20)  NOT NULL,
    relevance_score     REAL         NOT NULL
                        CHECK (relevance_score >= 0 AND relevance_score <= 1),
    UNIQUE (principle_id, ethics_subset)
);
CREATE INDEX idx_pem_subset ON principle_ethics_mapping (ethics_subset, relevance_score DESC);


-- ============================================================
-- 6. VECTOR EMBEDDINGS (pgvector, 768-dim for BAAI/bge-base-en-v1.5)
-- ============================================================

-- Per-verse embeddings (one per verse per translation per model)
CREATE TABLE verse_embeddings (
    id              SERIAL       PRIMARY KEY,
    verse_id        INTEGER      NOT NULL REFERENCES verses(id) ON DELETE CASCADE,
    model_name      VARCHAR(80)  NOT NULL DEFAULT 'BAAI/bge-base-en-v1.5',
    embedding       vector(768)  NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (verse_id, model_name)
);
CREATE INDEX idx_verse_emb_hnsw ON verse_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Per-chapter embeddings (mean-pooled or direct)
CREATE TABLE chapter_embeddings (
    id              SERIAL       PRIMARY KEY,
    chapter_id      INTEGER      NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    translation_id  SMALLINT     NOT NULL REFERENCES translations(id),
    model_name      VARCHAR(80)  NOT NULL DEFAULT 'BAAI/bge-base-en-v1.5',
    embedding       vector(768)  NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (chapter_id, translation_id, model_name)
);
CREATE INDEX idx_chapter_emb_hnsw ON chapter_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Per-principle embeddings
CREATE TABLE principle_embeddings (
    id              SERIAL       PRIMARY KEY,
    principle_id    INTEGER      NOT NULL REFERENCES distilled_principles(id) ON DELETE CASCADE,
    model_name      VARCHAR(80)  NOT NULL DEFAULT 'BAAI/bge-base-en-v1.5',
    embedding       vector(768)  NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (principle_id, model_name)
);
CREATE INDEX idx_principle_emb_hnsw ON principle_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Per-Strong's-entry embeddings (embed the definition)
CREATE TABLE strongs_embeddings (
    id              SERIAL       PRIMARY KEY,
    strongs_id      INTEGER      NOT NULL REFERENCES strongs_entries(id) ON DELETE CASCADE,
    model_name      VARCHAR(80)  NOT NULL DEFAULT 'BAAI/bge-base-en-v1.5',
    embedding       vector(768)  NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (strongs_id, model_name)
);
CREATE INDEX idx_strongs_emb_hnsw ON strongs_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);


-- ============================================================
-- 7. KNOWLEDGE GRAPH
-- ============================================================

-- Universal edge table for heterogeneous graph
CREATE TABLE knowledge_edges (
    id              SERIAL       PRIMARY KEY,
    source_type     VARCHAR(20)  NOT NULL,  -- 'verse','chapter','principle','strongs','theme'
    source_id       INTEGER      NOT NULL,
    target_type     VARCHAR(20)  NOT NULL,
    target_id       INTEGER      NOT NULL,
    edge_type       VARCHAR(30)  NOT NULL,  -- 'cross_ref','shared_theme','shared_root','semantic_sim','principle_source','theme_member'
    weight          REAL         NOT NULL DEFAULT 1.0,
    metadata        JSONB,
    UNIQUE (source_type, source_id, target_type, target_id, edge_type)
);
CREATE INDEX idx_ke_source    ON knowledge_edges (source_type, source_id);
CREATE INDEX idx_ke_target    ON knowledge_edges (target_type, target_id);
CREATE INDEX idx_ke_edge_type ON knowledge_edges (edge_type);
CREATE INDEX idx_ke_weight    ON knowledge_edges (weight DESC);

-- Canonical theme identifiers (for graph node reference)
CREATE TABLE theme_nodes (
    id              SERIAL       PRIMARY KEY,
    theme_name      VARCHAR(40)  NOT NULL UNIQUE,
    description     TEXT
);


-- ============================================================
-- 8. USEFUL VIEWS
-- ============================================================

-- Denormalized verse view for common queries
CREATE OR REPLACE VIEW v_verses AS
SELECT
    v.id AS verse_id,
    b.name AS book_name,
    b.abbreviation AS book_abbrev,
    b.testament,
    ch.chapter_number,
    v.verse_number,
    t.abbreviation AS translation,
    t.language,
    v.text
FROM verses v
JOIN chapters ch ON ch.id = v.chapter_id
JOIN books b ON b.id = ch.book_id
JOIN translations t ON t.id = v.translation_id;

-- Denormalized classification view
CREATE OR REPLACE VIEW v_classifications AS
SELECT
    pc.id AS classification_id,
    b.name AS book_name,
    ch.chapter_number,
    pc.genre,
    pc.genre_confidence,
    pc.themes,
    pc.teaching_type,
    pc.classified_by
FROM passage_classifications pc
JOIN chapters ch ON ch.id = pc.chapter_id
JOIN books b ON b.id = ch.book_id;

-- Principles with source context
CREATE OR REPLACE VIEW v_principles AS
SELECT
    dp.id AS principle_id,
    dp.principle_text,
    dp.principle_order,
    b.name AS book_name,
    ch.chapter_number,
    pc.genre,
    pc.themes,
    pc.teaching_type
FROM distilled_principles dp
JOIN passage_classifications pc ON pc.id = dp.classification_id
JOIN chapters ch ON ch.id = pc.chapter_id
JOIN books b ON b.id = ch.book_id;

-- Word alignment with Strong's definitions
CREATE OR REPLACE VIEW v_interlinear AS
SELECT
    wa.id AS alignment_id,
    vv.book_name,
    vv.chapter_number,
    vv.verse_number,
    wa.word_position,
    wa.original_word,
    wa.transliteration,
    wa.english_gloss,
    wa.morphology_code,
    se.strongs_number,
    se.root_definition,
    se.part_of_speech
FROM word_alignments wa
JOIN v_verses vv ON vv.verse_id = wa.verse_id
LEFT JOIN strongs_entries se ON se.strongs_number = wa.strongs_number;

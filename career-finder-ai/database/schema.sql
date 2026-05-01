-- schema.sql – Career Finder AI database schema
-- Run via: sqlite3 database/career_finder.db < database/schema.sql

-- ---------------------------------------------------------------------------
-- companies
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    website     TEXT,
    city        TEXT,
    sector      TEXT,
    size        TEXT,         -- e.g. "Large", "Medium", "Startup"
    verified    INTEGER NOT NULL DEFAULT 0,  -- 1 = verified source
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- opportunities
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS opportunities (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id      INTEGER NOT NULL REFERENCES companies(id),
    title           TEXT NOT NULL,
    description     TEXT,
    city            TEXT,
    work_mode       TEXT CHECK(work_mode IN ('On-site', 'Remote', 'Hybrid')),
    program_type    TEXT CHECK(program_type IN ('COOP', 'Internship')),
    major_fit       TEXT,     -- comma-separated major codes, e.g. "CS,AI,DS"
    duration_weeks  INTEGER,
    source_url      TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    posted_at       TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- fit_scores
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fit_scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id  INTEGER NOT NULL REFERENCES opportunities(id),
    student_major   TEXT NOT NULL,
    major_fit_score REAL,
    city_score      REAL,
    work_mode_score REAL,
    interest_score  REAL,
    verified_bonus  REAL,
    composite_score REAL,
    computed_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- recommendation_feedback
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recommendation_feedback (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT,
    opportunity_id  INTEGER NOT NULL REFERENCES opportunities(id),
    student_major   TEXT,
    student_city    TEXT,
    work_mode_pref  TEXT,
    program_type    TEXT,
    rank_shown      INTEGER,  -- position in the recommendation list (1-5)
    clicked         INTEGER NOT NULL DEFAULT 0,
    applied         INTEGER NOT NULL DEFAULT 0,
    rating          INTEGER CHECK(rating BETWEEN 1 AND 5),
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_opportunities_city       ON opportunities(city);
CREATE INDEX IF NOT EXISTS idx_opportunities_work_mode  ON opportunities(work_mode);
CREATE INDEX IF NOT EXISTS idx_opportunities_program    ON opportunities(program_type);
CREATE INDEX IF NOT EXISTS idx_fit_scores_opportunity   ON fit_scores(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_feedback_session         ON recommendation_feedback(session_id);

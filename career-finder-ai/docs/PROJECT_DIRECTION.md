# Career Finder AI — Project Direction (Frozen)

**Status:** Direction freeze (audit phase)  
**Date:** 2026-05-26  
**Scope:** Documents the target regression-based recommender. Does **not** implement the regression model, parser expansion, or frontend API wiring.

---

## Final project goal

Build an **AI-powered career recommender** for Saudi computing students seeking **verified COOP and internship opportunities**. A student describes themselves in natural language; the system extracts a structured profile, compares it against a curated opportunity dataset, predicts a **0–100 recommendation score** per opportunity, ranks results, and returns explainable matches. Follow-up chat messages **update the profile** and **rerun** recommendations.

---

## End-to-end flow (target)

```
User chat message
  → parser extracts student profile fields
  → profile is compared with company/opportunity dataset
  → regression model predicts a 0–100 recommendation score (per profile–opportunity pair)
  → recommender ranks opportunities
  → UI displays results (company, role/program, score, location, work mode, program type,
     interview status, matched skills, missing skills, explanation, source link)
  → follow-up messages update the profile and rerun recommendations
```

---

## Input

**Natural language student message** (single turn or multi-turn conversation).

Example:

> I am a cybersecurity student at KFUPM in Dhahran looking for a hybrid COOP in the Eastern Province. I know Python, Linux, and network security. I prefer roles that do not require a formal interview.

---

## Parsed profile fields (target contract)

The parser should eventually populate:

| Field | Description |
|-------|-------------|
| `major` | Computing major code (e.g. CS, AI, CYS, CIS, DS, DE, CE, FT) |
| `university` | Student university |
| `city` | Current or home city |
| `preferred_locations` | List of acceptable cities/regions |
| `skills` | Technical skills (normalized list) |
| `qualifications` | Degrees, certifications, GPA bands, etc. |
| `interest` | Career interest area (e.g. Cybersecurity, Data Science) |
| `program_type` | COOP, Internship, Training, etc. |
| `work_mode` | Remote, On-site, Hybrid |
| `preferred_roles` | Role clusters or titles the student wants |
| `interview_preference` | e.g. prefers no interview, open to interview |

### Current parser (rule-based — schema phase complete)

`backend/app/parser.py` extracts all target profile fields:

- `major`, `university`, `city`, `preferred_locations`, `skills`, `qualifications`, `interest` (derived from major), `program_type`, `work_mode`, `preferred_roles`, `interview_preference`

**Not yet implemented:** multi-turn profile merge (session state), regression model training/serving, frontend API wiring.

**Regression dataset (rubric labels):** `backend/app/build_regression_dataset.py` → `data/processed/student_opportunity_regression_dataset.csv` (synthetic profiles × loaded opportunities, `target_score` 0–100).

**Regression training (prototype):** `backend/app/train_regression_model.py` → Ridge / Random Forest / Gradient Boosting artefacts under `models/`, metrics in `data/processed/regression_model_metrics.csv`. Rubric-assisted models can show near-perfect R² (label leakage from component columns).

**Fair regression evaluation:** `backend/app/train_fair_regression_model.py` → text/categorical features only (no rubric component columns), metrics in `data/processed/fair_regression_model_metrics.csv`, models `regression_text_only_*.joblib`. Live `/recommend` still uses heuristics.

---

## Dataset role

**Current verified Saudi COOP/internship opportunities** are the **opportunity source of truth**.

| Stage | Location | Role |
|-------|----------|------|
| Raw (expected) | `data/raw/companies_raw.csv`, `data/raw/opportunities_raw.csv` | Source exports before cleaning |
| Processed | `data/processed/Opportunities_Clean.xlsx` | Primary runtime load for recommender |
| Processed (CSV pipeline) | `data/processed/opportunities_clean.csv` | Output of `clean_data.py`; input to `build_training_data.py` |
| SQLite (planned / partial) | `database/schema.sql`, `database/career_finder.db` | Schema for companies, opportunities, fit_scores, feedback — **not used by `/recommend` today** |

**Runtime loading (`recommender.py`):**

1. `load_opportunities_from_xlsx()` reads `data/processed/Opportunities_Clean.xlsx` (sheet `opportunities_clean` or first sheet).
2. Column names are resolved flexibly (e.g. `company` / `company_name`, `title` / `program_name`).
3. If the file is missing or empty, **`PLACEHOLDER_OPPORTUNITIES`** (7 hard-coded Saudi companies) is used.

**Cleaning pipeline (`clean_data.py`):** normalizes cities, work modes, program types; writes CSV + data dictionary when raw files exist.

---

## ML task (target)

**Regression:** given **(student profile, opportunity)** → predict **`match_score` ∈ [0, 100]**.

This replaces the current production path of **weighted heuristic scoring** (`scoring.py`, composite in `[0.0, 1.0]`) as the primary rank signal. Heuristics may remain as features, baselines, or fallbacks during transition.

---

## Planned models

| Model | Role |
|-------|------|
| **Ridge Regression** | Linear baseline; interpretable coefficients |
| **Random Forest Regressor** or **Gradient Boosting Regressor** | Non-linear ensemble for stronger accuracy |

**Not in scope for this phase:** training or serving regression models.

---

## Planned evaluation

| Metric | Purpose |
|--------|---------|
| **MAE** | Average absolute error on held-out match scores |
| **RMSE** | Penalizes large score errors |
| **R²** | Explained variance of the target |
| **Precision@5** | Ranking quality — relevant items in top 5 |

**Current classification baseline** (`train_model.py`, `evaluate.py`): TF-IDF + Logistic Regression on fit labels **High / Medium / Low** with classification report and confusion matrix. This path is **separate** from the live recommender and remains as historical baseline work.

---

## Final output fields (API / UI contract)

Each ranked recommendation should expose:

| Field | Description |
|-------|-------------|
| `rank` | Position in ranked list (1-based) |
| `company_name` | Employer name |
| `program_name` | Program or opportunity title |
| `role_cluster` | Normalized role family |
| `city` | Opportunity location |
| `work_mode` | Remote / On-site / Hybrid |
| `program_type` | COOP / Internship / etc. |
| `interview_required` | Whether interview is required / stated |
| `match_score` | **0–100** regression score |
| `matched_skills` | Skills overlap with student profile |
| `missing_skills` | Required skills not present in profile |
| `why_recommended` | Human-readable explanation |
| `source_url` | Verified application / careers link |

### Current backend response (baseline)

`Opportunity` in `schemas.py` uses: `company`, `title`, `score` (0–1 weighted), `skills_matched`, `why_recommended` (list), `source_url`, `rank`. Missing vs target: `role_cluster`, `interview_required`, `missing_skills`, 0–100 scale, and several profile fields.

### Current frontend types (baseline)

`frontend/src/lib/types.ts` uses camelCase mock shapes (`companyName`, `programName`, `scorePercent`, `fitLevel`) — **not wired** to the backend.

---

## Multi-turn behavior (target)

1. Maintain a **session profile** accumulated across messages.
2. Each new user message **merges** into the profile (parser + optional slot-filling).
3. **Rerun** filtering, regression scoring, and ranking on every update.
4. Return updated top-N with fresh explanations.

**Current behavior:** `/recommend` accepts a **single** `message` string; each call re-parses from scratch with no server-side session. Frontend chat is **mock-only** (no API).

---

## What stays (do not delete)

| Asset | Location | Purpose |
|-------|----------|---------|
| Classification training pipeline | `build_training_data.py`, `train_model.py`, `evaluate.py` | Baseline High/Medium/Low fit classifier |
| Rule-based parser | `parser.py` | Baseline extraction; extend, do not remove |
| Weighted scoring | `scoring.py` | Baseline ranker; compare against regression |
| Placeholder opportunities | `recommender.py` | Fallback when Excel absent |
| Notebooks | `notebooks/01`–`04` | EDA and experiments |
| Existing tests | `tests/test_*.py` | Guard parser, scoring, recommender behavior |

---

## What changes next (implementation order)

1. **Schemas** — Align `ParsedProfile`, `Opportunity`, and `RecommendResponse` with target fields and 0–100 `match_score`.
2. **Parser profile** — Add university, preferred_locations, qualifications, preferred_roles, interview_preference; support profile merge for multi-turn.
3. **Regression dataset generator** — Build labelled (profile, opportunity, score) training rows from heuristics, feedback, or expert labels.
4. **Regression training** — Ridge + ensemble; save artefacts under `models/`.
5. **Recommender integration** — Load regression model for scoring; keep heuristic fallback optional.
6. **Frontend API connection** — Replace mock chat/search flows; map backend DTO to UI components.

**Explicitly out of scope for the immediate next coding phase (per direction freeze):**

- Implementing the regression model
- Redesigning the frontend
- Deleting classification files
- Breaking existing tests

---

## Current system snapshot (audit reference)

### Backend API (`backend/app/main.py`)

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/health` | Health check |
| GET | `/stats` | Placeholder stats (not from live DB) |
| POST | `/parse` | `parse_message` → `ParsedProfile` |
| POST | `/recommend` | `recommend_from_message` → top 5 |

### Recommender pipeline (today)

```
parse_message(message)
  → get_candidates() [Excel or placeholders]
  → filter_candidates(profile, candidates)
  → compute_score(profile, opp) for each  [weighted heuristic, 0–1]
  → build_recommendation_reasons()
  → sort by score, assign rank, return top_n
```

### Frontend mock usage (today)

| Area | Mock source |
|------|-------------|
| Chat recommendations | `mock-recommendations.ts` via `career-chat.tsx` |
| Shelf demo tiles | `demo-shelf-memories.ts` (from mock recommendations) |
| Search page | Empty shell; `search-composer.tsx` has no API |
| Dashboard / Model | `PlaceholderPage` only |
| Parsed profile UI | `ParsedProfileCard` exists but is **not imported** in routes |

### ML / classification files

| File | What it does |
|------|----------------|
| `build_training_data.py` | Expands opportunities × majors → `training_fit_dataset.csv` with High/Medium/Low labels |
| `train_model.py` | TF-IDF + Logistic Regression → `models/fit_classifier.joblib`, `tfidf_vectorizer.joblib` |
| `evaluate.py` | Classification metrics + confusion matrix plot |
| `models/` | Empty except `.gitkeep` (no trained artefacts committed) |

**Important:** The fit classifier is **not called** by `recommender.py` or any API endpoint.

---

## Related documentation

- Prior frontend/backend audit: `docs/audits/chat-search-recommendation-audit.md`
- Backend module map: `backend/README.md`
- Frontend notes: `frontend/README.md`
- Repository agent map: `../AGENTS.md` (parent `Career/` folder)

---

## Risks and gaps (tracked)

1. **Score scale mismatch** — Backend uses 0–1 heuristic; UI mock uses `scorePercent` 0–100; regression target is 0–100.
2. **Schema drift** — Backend snake_case vs frontend camelCase; missing `missing_skills`, `role_cluster`, `interview_required`.
3. **Parser coverage** — Five target profile fields not implemented.
4. **No session state** — Multi-turn requires profile persistence (server or client).
5. **Excel vs CSV** — Recommender reads `.xlsx`; training builder reads `.csv` from `clean_data.py` (may be out of sync if only Excel is maintained).
6. **SQLite unused** — Schema exists but `/recommend` does not query DB.
7. **Classification vs regression** — Two ML paradigms; need clear migration plan so baselines remain testable.

---

## Test baseline (direction freeze)

Run from `career-finder-ai/backend` with project venv:

```bash
.venv\Scripts\python.exe -m pytest ..\tests -v
```

All **84** tests in `test_parser.py`, `test_scoring.py`, and `test_recommender.py` must continue to pass when making incremental changes unless tests are intentionally updated for the new contract.

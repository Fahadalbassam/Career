# CareerFinder.ai Technical Guide

> **Status:** QA-2 complete. This guide reflects the current state of the project as of 2026-05-28.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [End-to-End User Flow](#2-end-to-end-user-flow)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Frontend-to-Backend API Layer](#4-frontend-to-backend-api-layer)
5. [Backend API](#5-backend-api)
6. [Parser](#6-parser)
7. [Taxonomy](#7-taxonomy)
8. [Opportunity Enrichment](#8-opportunity-enrichment)
9. [Rubric Scoring](#9-rubric-scoring)
10. [Recommender Flow](#10-recommender-flow)
11. [ML Dataset Generation](#11-ml-dataset-generation)
12. [Train/Test Split](#12-traintest-split)
13. [Fair Regression Model Training](#13-fair-regression-model-training)
14. [Rubric-Assisted Model](#14-rubric-assisted-model)
15. [Error Analysis](#15-error-analysis)
16. [Rubric vs ML Comparison](#16-rubric-vs-ml-comparison)
17. [ML Shadow Scoring](#17-ml-shadow-scoring)
18. [Terminal CLI](#18-terminal-cli)
19. [Playwright E2E Tests](#19-playwright-e2e-tests)
20. [Python/Pytest Test Suite](#20-pythonpytest-test-suite)
21. [Important Generated Files](#21-important-generated-files)
22. [Environment Variables](#22-environment-variables)
23. [How to Run](#23-how-to-run)
24. [What Not To Delete](#24-what-not-to-delete)
25. [Known Limitations](#25-known-limitations)
26. [Suggested Next Steps](#26-suggested-next-steps)
27. [File and Function Index](#file-and-function-index)

---

## 1. Project Overview

CareerFinder.ai is a **Saudi-focused career/COOP/internship recommendation prototype** for computing students. It targets students who are looking for COOP, internship, Tamheer, or training opportunities at Saudi companies.

**What it does:**

- Users enter natural language profile information (major, city, skills, work mode, program type, interest).
- The backend parses the message using a rule-based NLP parser.
- The backend ranks opportunities from `Opportunities_Clean.xlsx` using a deterministic **rubric scoring** system (0–100).
- An **optional ML shadow score** can be added for evaluation purposes (does not affect ranking).
- The frontend chat UI displays top recommendations as interactive shelf cards.
- A terminal CLI supports demo, profiling, and model metrics inspection.

**Key design principle:** Rubric scoring is the **live ranking** mechanism. ML is shadow-only until further validation.

**Key entry points:**

| Component | Entry point |
|---|---|
| Backend API | [backend/app/main.py](../backend/app/main.py) |
| Frontend chat page | [frontend/src/app/(career)/chat/page.tsx](../frontend/src/app/(career)/chat/page.tsx) |
| Recommender | [backend/app/recommender.py](../backend/app/recommender.py) |
| Terminal CLI | [scripts/careerfinder_cli.py](../scripts/careerfinder_cli.py) |

---

## 2. End-to-End User Flow

### Web UI flow

1. **User opens frontend** at `http://localhost:3000/chat`.
2. **User submits a message** in natural language (e.g. "I am a CYS student in Dammam looking for remote COOP. I know Linux and networking.").
3. **Frontend calls `/recommend`** — see [`recommendFromMessage`](../frontend/src/lib/api.ts#L8-L27) in `api.ts`.
4. **Backend receives `POST /recommend`** — see [`get_recommendations`](../backend/app/main.py#L91-L102) in `main.py`.
5. **Backend parses the message** — see [`parse_message`](../backend/app/parser.py#L450-L512) in `parser.py`.
6. **Backend loads opportunities** from `data/processed/Opportunities_Clean.xlsx` — see [`load_opportunities_from_xlsx`](../backend/app/recommender.py#L172-L276).
7. **Backend enriches opportunities** at runtime — see [`enrich_opportunity_signals`](../backend/app/opportunity_enrichment.py#L461-L549) in `opportunity_enrichment.py`.
8. **Rubric scoring ranks results** — see [`score_profile_opportunity_pair`](../backend/app/rubric.py#L578-L613) in `rubric.py`. Each opportunity gets a `match_score` (0–100).
9. **Optional ML shadow score is attached** — see [`predict_ml_scores`](../backend/app/ml_scoring.py#L191-L231) in `ml_scoring.py`. Only when `CAREERFINDER_ENABLE_ML_SCORE=true`.
10. **Top 5 results are returned** to the frontend as a `RecommendResponse`.
11. **Frontend adapts the response** — see [`toRecommendations`](../frontend/src/lib/api-adapters.ts#L98-L101) and `buildShelfMemoriesFromRecommendations`.
12. **Shelf cards are displayed** in the chat UI side panel.

### Terminal CLI flow

1. **User runs** `npm run run:terminal` (starts backend in a new window, opens CLI in another).
2. **User types a profile message** at the `You>` prompt.
3. **CLI sends `POST /recommend`** with accumulated messages — see [`post_recommend`](../scripts/careerfinder_cli.py#L669-L691).
4. **Results are rendered** as a compact table or verbose cards depending on output mode.

---

## 3. Frontend Architecture

The frontend is a **Next.js 14 app** with the App Router. Key routes are under `frontend/src/app/`.

### App Routes

| Route | File | Status | Notes |
|---|---|---|---|
| `/` | [app/page.tsx](../frontend/src/app/page.tsx) | Live | Home page — renders `<HomePage />` |
| `/chat` | [app/(career)/chat/page.tsx](../frontend/src/app/(career)/chat/page.tsx) | Live | Main chat interface — renders `<CareerChat />` |
| `/search` | `app/(career)/search/page.tsx` | Shell only | Route shell present; content not final (Phase 6 pending) |
| `/methodology` | `app/methodology/page.tsx` | Live | Static methodology overview page |
| `/login` | `app/login/page.tsx` | Auth stub | Login form UI stub; no real auth backend |
| `/signup` | `app/signup/page.tsx` | Auth stub | Signup form UI stub; no real auth backend |

### Home Page

The landing page introduces CareerFinder.ai and links to the chat. Rendered by `HomePage` component.

### Chat Page

The primary user-facing feature. The chat page at `/chat`:
- Accepts multi-turn natural language messages.
- Calls `/recommend` after each message.
- Displays assistant replies, parsed profile cards, and shelf recommendation cards.
- Maintains **anonymous session persistence** in `localStorage` (survives page refresh).
- Falls back to **mock/demo recommendations** when the backend is offline.

The core component is [`CareerChat`](../frontend/src/components/chat/career-chat.tsx#L175-L751).

### Search Page

Currently a minimal route shell. Planned to support manual filter-based search over the opportunity database in a future phase.

### Methodology Page

Static page explaining the recommendation approach.

### Login / Signup Pages

Stub UI only — no real authentication, no database writes, no cookies. The `AuthProvider` uses in-memory user state only.

---

## 4. Frontend-to-Backend API Layer

Four files in `frontend/src/lib/` handle the API integration:

### `api.ts` — HTTP client

[`frontend/src/lib/api.ts`](../frontend/src/lib/api.ts) exports a single function:

- **`recommendFromMessage(message: string): Promise<RecommendApiResponse>`** — sends `POST /recommend` with the student message. Uses `NEXT_PUBLIC_API_BASE` (defaults to `http://localhost:8000`). Throws on non-2xx status.

### `api-types.ts` — Backend response types

[`frontend/src/lib/api-types.ts`](../frontend/src/lib/api-types.ts) defines TypeScript interfaces matching the backend Pydantic schemas (snake_case, backend shape):

- **`ParsedProfileApi`** — student profile fields from the parser.
- **`OpportunityApi`** — a single opportunity with `match_score`, `score_breakdown`, `missing_skills`, `ml_score` (optional), etc.
- **`RecommendApiResponse`** — top-level response with `profile`, `recommendations`, `total_candidates`.
- **`ScoreBreakdownApi`** — per-component rubric scores.

### `api-adapters.ts` — Type mapping and shelf logic

[`frontend/src/lib/api-adapters.ts`](../frontend/src/lib/api-adapters.ts) converts backend snake_case types to frontend camelCase types and implements shelf logic:

| Function | Purpose |
|---|---|
| `toStudentProfile(profile)` | Converts `ParsedProfileApi` → `StudentProfile` |
| `toRecommendation(opportunity)` | Converts `OpportunityApi` → `Recommendation`, derives `fitLevel` from `match_score` |
| `toRecommendations(opportunities)` | Maps array using `toRecommendation` |
| `toCareerFitMemory(recommendation)` | Converts `Recommendation` → `CareerFitMemory` for shelf display |
| `mergeStudentProfiles(current, incoming)` | Merges two `StudentProfile` objects across turns (list union, scalar last-wins) |
| `buildShelfMemoriesFromRecommendations(recs, profile)` | Builds up to 6 shelf cards, split left/right by cluster |
| `shelfRevealCount(profile)` | Progressive reveal (0–6 cards) based on how many profile fields are filled |

### `chat-session.ts` — Anonymous local persistence

[`frontend/src/lib/chat-session.ts`](../frontend/src/lib/chat-session.ts) manages anonymous session storage in `localStorage`:

- **`STORAGE_KEY`** — `"careerfinder.ai.anonymousChatSession.v1"`
- **`AnonymousChatSession`** — stores `userMessages`, accumulated `profile`, and `updatedAt`.
- **`loadAnonymousChatSession()`** — loads from `localStorage`, returns `null` on parse error.
- **`saveAnonymousChatSession(session)`** — persists on every successful `/recommend` turn.
- **`clearAnonymousChatSession()`** — called by "Clean slate" button.

No cookies, no server-side writes. SSR-safe (guarded with `typeof window`).

---

## 5. Backend API

The backend is a **FastAPI** application. Entry point: [`backend/app/main.py`](../backend/app/main.py).

Start command (from `backend/` directory):
```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### CORS

CORS is configured at lines [32–41](../backend/app/main.py#L32-L41), allowing `http://localhost:3000` and `http://127.0.0.1:3000` — all methods and headers.

### Endpoints

| Method | Path | Description | Schema |
|---|---|---|---|
| `GET` | `/health` | Health check — returns `{"status": "ok", "environment": ...}` | `HealthResponse` |
| `GET` | `/stats` | Dataset statistics (placeholder values) | `StatsResponse` |
| `POST` | `/parse` | Parse a free-text message into a structured profile | `ParsedProfile` |
| `POST` | `/recommend` | Parse + score + return top 5 ranked opportunities | `RecommendResponse` |

### Response Schemas

All schemas are in [`backend/app/schemas.py`](../backend/app/schemas.py):

- **`ParsedProfile`** / **`StudentProfile`** (lines [39–105](../backend/app/schemas.py#L39-L105)) — major, university, city, preferred_locations, skills, qualifications, interest, program_type, work_mode, preferred_roles, interview_preference.
- **`Opportunity`** (lines [107–210](../backend/app/schemas.py#L107-L210)) — all fields of a ranked opportunity including `match_score` (0–100), `score` (legacy 0–1), `score_breakdown`, `role_cluster`, `interview_required`, `missing_skills`, `missing_required_skills`, `missing_preferred_skills`, `score_source`, `ml_score` (optional), `ml_score_source` (optional).
- **`RecommendResponse`** (lines [212–217](../backend/app/schemas.py#L212-L217)) — contains `profile`, `recommendations`, `total_candidates`.

---

## 6. Parser

[`backend/app/parser.py`](../backend/app/parser.py) implements a **rule-based NLP parser** that extracts structured fields from a free-text student message without requiring an external LLM.

### Entry point

```python
parse_message(message: str) -> ParsedProfile
```

See lines [450–512](../backend/app/parser.py#L450-L512).

### Extracted fields

| Field | Detection method |
|---|---|
| `major` | `MAJOR_KEYWORDS` dict (CS, AI, CYS, CIS, DS, DE, CE, FT) |
| `university` | `UNIVERSITY_KEYWORDS` dict (IAU, KFUPM, KSU, KAU, PSU) |
| `city` | Taxonomy `find_city_in_text()` — handles Saudi city aliases |
| `preferred_locations` | Multiple cities detected → all listed |
| `work_mode` | `WORK_MODE_KEYWORDS` (Remote, On-site, Hybrid) |
| `program_type` | `PROGRAM_TYPE_KEYWORDS` (COOP, Internship) plus Arabic |
| `skills` | `SKILL_KEYWORDS` list (40+ technical skills) |
| `qualifications` | `QUALIFICATION_KEYWORDS` (AWS, Azure, CEH, CCNA, GPA, etc.) |
| `preferred_roles` | `ROLE_KEYWORDS` (15 specific role titles) |
| `interest` | Text-based detection via taxonomy (overrides major default) |
| `interview_preference` | Phrase matching ("no interview", "interview is okay") |

### Normalisation pipeline

The `_normalize_text()` function (lines [217–273](../backend/app/parser.py#L217-L273)) handles:
- Lowercasing, whitespace collapse.
- Spelling variants (`on-site`, `cyber security`, `co-op`, `wfh`).
- Skill aliases delegated to `normalise_skill_aliases()` from taxonomy.
- GPA decimal preservation (`4.5` → `gpa 4_5` before punctuation stripping).

### Missing info behaviour

All fields default to `None` (scalars) or `[]` (lists). The `/recommend` endpoint and the CLI assistant reply use the missing fields to ask clarifying questions.

### Alias handling

Skill aliases (e.g. `k8s` → `kubernetes`, `infosec` → `cybersecurity`) are handled by `taxonomy.normalise_skill_aliases()`. City aliases (e.g. `alkhobar` → `Khobar`) are handled by `taxonomy.find_city_in_text()`.

---

## 7. Taxonomy

[`backend/app/taxonomy.py`](../backend/app/taxonomy.py) is the **shared vocabulary module** used by both the parser and the rubric. It is pure data + small helpers with no I/O.

### Contents

| Constant / Function | Purpose |
|---|---|
| `ROLE_CLUSTERS` | 14 canonical role cluster labels |
| `INTEREST_ALIASES` | Canonical interest label → list of free-text phrases |
| `INTEREST_TO_ROLE_CLUSTERS` | Interest label → default preferred roles when no specific title is stated |
| `INTEREST_OPPORTUNITY_KEYWORDS` | Interest label → opportunity-side keywords for rubric matching |
| `CITY_ALIASES` | Lower-case city spellings → canonical name (e.g. `alkhobar` → `Khobar`) |
| `EXTENDED_LOCATION_ALIASES` | Broader tokens (`ksa`, `saudi arabia`) used only as fallback |
| `SKILL_ALIASES` | Skill alias → canonical token (`k8s` → `kubernetes`) |
| `SOFT_SKILL_BLOCKLIST` | Tokens that should never be classified as technical skills |
| `find_city_in_text(text)` | Finds Saudi cities with longest-match-wins semantics |
| `find_interest_in_text(text)` | Finds canonical interest label; prefers "interested in X" phrasing |
| `normalise_skill_aliases(text)` | Replaces skill aliases in normalised text |
| `opportunity_keywords_for_interest(interest)` | Returns rubric-matching opportunity keywords |
| `role_clusters_for_interest(interest)` | Returns default preferred roles for an interest |

### Why taxonomy improves matching

Without taxonomy, a student saying "security focused" would not match `interest=Cybersecurity`; "alkhobar" would not match `city=Khobar`. The taxonomy ensures the parser and rubric agree on canonical labels, making scoring more consistent and the trained ML dataset cleaner.

---

## 8. Opportunity Enrichment

[`backend/app/opportunity_enrichment.py`](../backend/app/opportunity_enrichment.py) provides **runtime inferred signals** for opportunities. It runs at scoring time and never writes to disk or mutates the Excel file.

### Entry point

```python
enrich_opportunity_signals(opportunity: Opportunity) -> dict
```

See lines [461–549](../backend/app/opportunity_enrichment.py#L461-L549).

### Returned signals

```python
{
    "role_cluster":        Optional[str],   # only when opportunity.role_cluster is empty
    "inferred_interests":  List[str],        # taxonomy interest labels
    "inferred_skills":     List[str],        # lowercase skill tokens
    "required_skills":     List[str],        # from ROLE_SKILL_PROFILES
    "preferred_skills":    List[str],        # from ROLE_SKILL_PROFILES, never overlaps required
}
```

### Bucket system

Five trigger-based buckets fire when the opportunity text matches:

| Bucket | Trigger examples | Inferred interests |
|---|---|---|
| `telecom_network` | STC, Mobily, network, infrastructure, NOC | Cybersecurity, Cloud / DevOps |
| `cybersecurity` | cybersecurity, SOC, SIEM, penetration, firewall | Cybersecurity |
| `bank_fintech` | bank, fintech, Al Rajhi, Tamara, payments | FinTech, Software Development, Data Science, Cybersecurity |
| `ai_data` | AI, machine learning, data science, SDAIA, ETL | Data Science, Data Engineering |
| `software` | software engineer, backend, frontend, developer, API | Software Development |

### Role Skill Profiles

`ROLE_SKILL_PROFILES` (lines [279–326](../backend/app/opportunity_enrichment.py#L279-L326)) defines required and preferred skills for 10 role clusters (Cybersecurity, Network Security, Cloud/DevOps, Backend Engineering, Frontend Engineering, Data Engineering, Data Science, AI/Machine Learning, QA/Testing, General Computing).

These profiles are used by the rubric to:
- Weight `required` skill hits at 0.7 (vs explicit 1.0 and generic inferred 0.5).
- Weight `preferred` skill hits at 0.4.
- Order `missing_skills` as required → preferred → remaining explicit.

---

## 9. Rubric Scoring

> **Rubric score is the primary live ranking score.**

[`backend/app/rubric.py`](../backend/app/rubric.py) implements all component scorers and the composite target score.

### match_score (0–100)

`match_score` is the integer 0–100 value returned in the `/recommend` response. It is computed as `round(target_score)` where `target_score = 100 × weighted_composite`.

### Weights

```python
TARGET_WEIGHTS = {
    "major_fit_score":    0.35,
    "skill_match_score":  0.20,
    "role_interest_score": 0.15,
    "city_match_score":   0.10,
    "program_type_score": 0.10,
    "work_mode_score":    0.05,
    "verification_score": 0.03,
    "interview_score":    0.02,
}
```

### Component scorers (each returns 0.0–1.0)

| Function | Inputs | Key logic |
|---|---|---|
| `compute_major_fit_score` | profile, opp | 1.0 = exact match; 0.6 = related major; 0.3 = no info; 0.0 = no match |
| `compute_skill_match_score` | profile, opp | Per-token: explicit=1.0, inferred-required=0.7, inferred=0.5, preferred=0.4 |
| `compute_role_interest_score` | profile, opp | Direct token=1.0, cluster=0.8/0.6, family=0.6, inferred-interest=0.5, generic=0.3 |
| `compute_city_match_score` | profile, opp | Exact=1.0, Eastern Province cluster=0.7, Remote opp=0.5, no info=0.5 |
| `compute_program_type_score` | profile, opp | Exact=1.0, COOP/Internship cross-match=0.9, training partial=0.5 |
| `compute_work_mode_score` | profile, opp | Exact=1.0, Remote/Hybrid near-match=0.7 |
| `compute_verification_score` | opp | Has source URL=1.0; else 0.2 |
| `compute_interview_score` | profile, opp | Aligned preference+requirement=1.0; mismatched=0.2; no preference=0.5 |

See lines [273–547](../backend/app/rubric.py#L273-L547) for all scorer implementations.

### score_breakdown

The `score_breakdown` field in the API response contains each component's raw score (0–1). Keys: `major_fit_score`, `skill_match_score`, `role_interest_score`, `city_match_score`, `program_type_score`, `work_mode_score`, `verification_score`, `interview_score`.

### missing_skills

`compute_missing_skills()` (lines [694–733](../backend/app/rubric.py#L694-L733)) returns opportunity skills the student does not appear to have, ordered: required → preferred → remaining explicit, capped at 8.

### score (legacy)

The `score` field (0–1 float) equals `match_score / 100`. Kept for backward compatibility.

### scoring.py (legacy/test helper)

[`backend/app/scoring.py`](../backend/app/scoring.py) is an earlier, simpler scoring implementation. It is **not used in the live recommender**. It is referenced by `tests/test_scoring.py` and kept for backward compatibility and test coverage. **Do not delete it.**

---

## 10. Recommender Flow

[`backend/app/recommender.py`](../backend/app/recommender.py) — the live recommendation pipeline.

### `recommend_from_message(message, top_n=5)`

End-to-end entry point (lines [496–515](../backend/app/recommender.py#L496-L515)):

1. **Parse** — calls `parse_message(message)` → `ParsedProfile`.
2. **Load candidates** — calls `get_candidates()`.
3. **Recommend** — calls `recommend(profile, top_n)`.
4. **Return** — `RecommendResponse(profile, recommendations, total_candidates)`.

### `get_candidates()`

Lines [278–290](../backend/app/recommender.py#L278-L290). Tries to load from `Opportunities_Clean.xlsx` first (`load_opportunities_from_xlsx`). Falls back to hard-coded `PLACEHOLDER_OPPORTUNITIES` (7 companies) if the file is missing.

### `recommend(profile, top_n=5)`

Lines [401–493](../backend/app/recommender.py#L401-L493):

1. **Filter** — `filter_candidates()` keeps opportunities with source URLs, prefers major matches, then program-type matches (safe: never returns empty if filter would eliminate all).
2. **ML shadow scores** — `predict_ml_scores()` is called once (no-op when disabled).
3. **Score** — for each candidate, `score_profile_opportunity_pair()` computes all 8 rubric components + target_score.
4. **Enrich** — each opportunity copy gets `match_score`, `score`, `score_breakdown`, `role_cluster`, `interview_required`, `missing_skills`, `missing_required_skills`, `missing_preferred_skills`, `why_recommended`, `skills_matched`, `ml_score` (optional).
5. **Sort** — by `match_score` descending.
6. **Rank** — top N results get `rank` 1–N.

**Important:** Sorting always uses `match_score` (rubric). `ml_score` is attached but never affects rank.

---

## 11. ML Dataset Generation

The ML pipeline starts by generating a supervised regression dataset.

### Data sources

- **`Opportunities_Clean.xlsx`** — cleaned opportunity listings from `data/processed/`.
- **`Opportunities_Enriched.csv`** — pre-computed enrichment signals (preferred source for dataset building).
- Synthetic student profiles (40+ deterministic profiles covering all majors/cities/interest combinations).

### Build process

[`backend/app/build_regression_dataset.py`](../backend/app/build_regression_dataset.py):

1. Loads synthetic profiles via `build_synthetic_profiles()` (lines [228–743](../backend/app/build_regression_dataset.py#L228-L743)) — 50 profiles covering CS, AI, CYS, CIS, DS, DE, CE, FT.
2. Loads opportunities from `Opportunities_Enriched.csv` (preferred), then xlsx, then placeholders.
3. Calls `build_regression_rows()` — for every (profile, opportunity) pair, scores all 8 rubric components and records the `target_score`.
4. Output: `student_opportunity_regression_dataset.csv`.

Run:
```bash
cd backend
python -m app.build_regression_dataset
```

### Dataset structure

Each row represents one (profile, opportunity) pair. Key columns: `profile_id`, `chat_message`, all profile fields, all opportunity fields, 5 enriched signal columns, 8 rubric component scores, `target_score` (0–100).

### Opportunity enrichment dataset

[`backend/app/enrich_opportunities_dataset.py`](../backend/app/enrich_opportunities_dataset.py) loads `Opportunities_Clean.xlsx`, applies `enrich_opportunity_signals()` to each row, and writes `Opportunities_Enriched.csv` with five additional columns: `inferred_role_cluster`, `inferred_interests`, `inferred_skills`, `required_skills`, `preferred_skills`.

Run:
```bash
cd backend
python -m app.enrich_opportunities_dataset
```

### Generated files

| File | Generated by |
|---|---|
| `data/processed/Opportunities_Enriched.csv` | `enrich_opportunities_dataset.py` |
| `data/processed/student_opportunity_regression_dataset.csv` | `build_regression_dataset.py` |

---

## 12. Train/Test Split

[`backend/app/inspect_regression_split.py`](../backend/app/inspect_regression_split.py) creates reproducible train/test split files.

### Method

- Uses `GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)` from scikit-learn.
- Groups by `profile_id` — all rows for a given profile stay in either train **or** test, never both.
- This prevents **target leakage through profile identity**: the model cannot memorise a profile's preferred features and re-use them on its own held-out opportunities.

Run:
```bash
cd backend
python -m app.inspect_regression_split
```

### Output files

| File | Description |
|---|---|
| `data/processed/regression_train_split.csv` | ~80% rows, training profiles only |
| `data/processed/regression_test_split.csv` | ~20% rows, test profiles only |
| `data/processed/regression_split_profile_ids.csv` | Profile IDs in each split |
| `data/processed/regression_split_summary.json` | Totals, ratio, overlap check (must be `[]`) |

### No profile overlap

The `overlapping_profile_ids` field in `regression_split_summary.json` must always be `[]`. This is verified by `inspect_regression_split.py` and by the tests.

---

## 13. Fair Regression Model Training

[`backend/app/train_fair_regression_model.py`](../backend/app/train_fair_regression_model.py) trains **three leakage-safe** regression models.

### What makes it "fair"

The fair model uses **only realistic input features** — profile text, opportunity metadata, categorical fields, and count features. It does **not** include rubric component scores (`major_fit_score`, `skill_match_score`, etc.) as inputs. These are excluded via `EXCLUDED_RUBRIC_COLUMNS` (lines [75–75](../backend/app/train_fair_regression_model.py#L75-L75)).

### Feature groups

- **Categorical** (one-hot encoded): `major`, `city`, `program_type`, `work_mode`, `opportunity_program_type`, `opportunity_work_mode`, `opportunity_role_cluster`.
- **Count features**: `text_length`, `skill_token_count`, `qualification_token_count`, `preferred_role_count`, `preferred_location_count`.
- **Text** (TF-IDF, Ridge and RF only): combined concatenation of all text profile/opportunity columns excluding rubric scores.

### Three models

| Model | Architecture | Features used |
|---|---|---|
| `fair_ridge` | TF-IDF (ngram 1–2, 4000 features) → Ridge(α=1.0) | Combined text only |
| `fair_random_forest` | TF-IDF + OHE + counts → Random Forest (120 trees, max_depth=14) | Text + categorical + counts |
| `fair_gradient_boosting` | OHE + counts → Gradient Boosting (150 trees, lr=0.08, max_depth=4) | Categorical + counts only |

### Best fair model results

The best fair model is **`fair_gradient_boosting`**:

| Metric | Value |
|---|---|
| MAE | ~5.834 |
| RMSE | ~7.265 |
| R² | ~0.648 |
| Precision@5 | ~0.240 |
| `leakage_safe` | `True` |

### Model artifact

```
models/fair_gradient_boosting_model.joblib
```

This is the model used for optional ML shadow scoring in `/recommend`.

Run:
```bash
cd backend
python -m app.train_fair_regression_model
```

Outputs: `data/processed/fair_regression_model_metrics.csv`, `data/processed/fair_regression_predictions.csv`, `reports/figures/fair_regression_prediction_vs_actual.png`, and three `.joblib` model files.

---

## 14. Rubric-Assisted Model

[`backend/app/train_regression_model.py`](../backend/app/train_regression_model.py) trains a **rubric-assisted (leakage demo)** track.

> **Warning:** Do not report rubric-assisted metrics as honest model performance.

### Why it is leakage

The `target_score` label is defined as a weighted linear combination of the 8 rubric component scores. The rubric-assisted model includes those same 8 component scores as input features. Any regressor can reconstruct `target_score` nearly perfectly by learning the weights — resulting in near-zero MAE and R² ≈ 1.0.

Best rubric-assisted result: `rubric_assisted_ridge` — MAE ≈ 0.023, R² ≈ 1.000.

### Useful purpose

The rubric-assisted track serves as a **sanity check** that:
- The pipeline is correctly wired.
- The target label can be learned when leakage features are available.
- The contrast against the fair track illustrates the difference between an honest and a leaked model.

**The live `/recommend` endpoint never uses rubric-assisted models.**

---

## 15. Error Analysis

[`backend/app/analyze_model_errors.py`](../backend/app/analyze_model_errors.py) performs **ML-4 error analysis** on the best fair model.

Run:
```bash
cd backend
python -m app.analyze_model_errors
```

### Outputs

| File | Description |
|---|---|
| `data/processed/fair_model_error_analysis.csv` | All test-split rows with `absolute_error`, sorted worst-first |
| `data/processed/fair_model_worst_predictions.csv` | Top 25 worst predictions (highest error) |
| `data/processed/fair_model_best_predictions.csv` | Top 25 best predictions (lowest error) |
| `data/processed/fair_model_profile_error_summary.csv` | Per-profile mean/max error, mean target/predicted score |
| `data/processed/fair_model_error_summary.json` | JSON summary: best_model, MAE, RMSE, R², worst/best/mean/median error, profiles analyzed |

### Report examples

[`backend/app/generate_recommendation_examples.py`](../backend/app/generate_recommendation_examples.py) generates report-ready recommendation examples for 8 curated profiles from the test split.

Run:
```bash
cd backend
python -m app.generate_recommendation_examples
```

Outputs: `data/processed/report_recommendation_examples.csv` and `docs/reports/example_recommendations.md`.

---

## 16. Rubric vs ML Comparison

[`backend/app/compare_rubric_vs_ml.py`](../backend/app/compare_rubric_vs_ml.py) implements **ML-5 comparison** between live rubric scores and fair model predictions.

Run:
```bash
cd backend
python -m app.compare_rubric_vs_ml
```

### Key metrics (from test split)

| Metric | Value |
|---|---|
| Pearson correlation | ~0.833 |
| Spearman correlation | ~0.784 |
| Mean absolute difference | ~5.834 |
| Average top-5 overlap per profile | ~0.36 |

### Interpretation

- **Pearson ~0.83** — the fair model captures the broad fit pattern.
- **Top-5 overlap ~0.36** — only about 1–2 of the top 5 opportunities are ranked the same by both.
- **Conclusion:** ML correlates with the rubric but does not replicate it reliably enough for live ranking replacement yet.

### Outputs

| File | Description |
|---|---|
| `data/processed/rubric_vs_ml_comparison.csv` | Full comparison with rank_by_rubric and rank_by_ml |
| `data/processed/rubric_vs_ml_largest_disagreements.csv` | Top 25 largest score differences |
| `data/processed/rubric_vs_ml_profile_overlap.csv` | Per-profile top-5 overlap statistics |
| `data/processed/rubric_vs_ml_summary.json` | All aggregated stats |
| `docs/reports/rubric_vs_ml_comparison.md` | Report-ready narrative |

---

## 17. ML Shadow Scoring

[`backend/app/ml_scoring.py`](../backend/app/ml_scoring.py) implements optional shadow ML scoring behind a **feature flag**.

### Feature flag

```bash
CAREERFINDER_ENABLE_ML_SCORE=true
```

When not set (or set to anything other than `"true"`), `is_ml_score_enabled()` returns `False` and all ML score fields are `None`.

### How it works

1. The `predict_ml_scores(profile, opportunities)` function (lines [191–231](../backend/app/ml_scoring.py#L191-L231)) lazy-loads `models/fair_gradient_boosting_model.joblib`.
2. It constructs feature rows matching the training pipeline: 7 categorical + 5 count features.
3. It calls `model.predict(df)` and returns a `{opp.id: ml_score}` dict (scores clamped 0–100).
4. The recommender attaches `ml_score` and `ml_score_source="fair_gradient_boosting"` to each opportunity.
5. **Sorting remains by `match_score` (rubric) only — ML score never changes ranking.**

### Graceful degradation

- If the model file does not exist: logs a warning, returns all `None`.
- If prediction raises any exception: logs a warning, returns all `None`.
- `/recommend` never crashes due to ML scoring failures.

### Schema fields

In `Opportunity`:
- `score_source: str = "rubric"` — always `"rubric"` currently.
- `ml_score: Optional[int] = None` — the 0–100 shadow prediction.
- `ml_score_source: Optional[str] = None` — `"fair_gradient_boosting"` when present.

---

## 18. Terminal CLI

[`scripts/careerfinder_cli.py`](../scripts/careerfinder_cli.py) is an interactive terminal client for CareerFinder.ai.

### How to run

```bash
# From the repo root — auto-starts backend, opens CLI window:
npm run run:terminal

# Or directly (backend must already be running):
python scripts/careerfinder_cli.py
```

The `npm run run:full` command starts both backend and frontend in separate terminal windows.

### Commands

| Command | Description |
|---|---|
| `/help` | Show all available commands |
| `/profile` | Print full parsed profile (all fields) |
| `/top` or `/top N` | Show compact top 5 (or top N) recommendations |
| `/details N` | Full details for recommendation rank N (includes ML score if enabled) |
| `/open N` | Open rank N source URL in the browser |
| `/links` | Print all ranked source URLs |
| `/history` | Show numbered remembered user messages |
| `/undo` | Remove last user message and re-run recommendations |
| `/metrics` | Print fair + rubric-assisted model metrics from ML reports |
| `/model` | Print live ML shadow status (ranking stays rubric-based) |
| `/shadow` | Print rubric vs ML comparison summary from JSON |
| `/ml` | Combined ML status + best fair model + shadow recommendation |
| `/compact` | Default compact one-line-per-recommendation table |
| `/verbose` | Verbose multi-line recommendation output |
| `/split` | Side-by-side layout (requires terminal ≥ 120 columns) |
| `/clear` | Clear conversation and screen |
| `/login` | Login placeholder stub |
| `/guest` | Continue as guest |
| `/exit` | Quit |

### /metrics command

Shows best fair model (MAE, RMSE, R², Precision@k, train/test rows, leakage-safe=True) and best rubric-assisted (with leakage warning).

### /shadow command

Shows Pearson/Spearman correlation, mean absolute difference, and average top-5 overlap from `rubric_vs_ml_summary.json`.

### Multi-turn memory

Each user message is appended to `user_messages`. The accumulated messages are joined with `\n` and sent together to `/recommend` — same pattern as the web chat.

### Accidental input guard

Single letters (`n`, `y`), empty input, and `/n`-style typos are blocked and never sent to the backend.

---

## 19. Playwright E2E Tests

[`frontend/playwright.config.ts`](../frontend/playwright.config.ts) configures the **QA-2 smoke test suite**.

### Setup

Install once:
```bash
cd frontend
npx playwright install chromium
```

### Run commands

```bash
cd frontend
npm run test:e2e          # headless run
npm run test:e2e:ui       # interactive Playwright UI
```

### Configuration

The `playwright.config.ts` starts two web servers when tests run:
- **Backend:** `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` (health-checked at `/health`).
- **Frontend:** `npm run dev` (checked at `http://localhost:3000`).
- `reuseExistingServer: true` when not in CI — reuses already-running servers.
- Retries 1× in CI; timeout 60 s per test.

### Smoke test coverage (`e2e/smoke.spec.ts`)

| Test | What it checks |
|---|---|
| `home page loads` | H1 heading and "Start Career Match" link visible |
| `chat page loads` | Chat composer input and navigation link visible |
| `chat can submit a message` | Submits a real message; accepts user bubble, profile card, assistant reply, or shelf card as success |
| `search page loads` | Navigation visible; route shell renders |
| `methodology page loads` | Heading and "Methodology snapshot" text visible |
| `login page loads` | Email/password fields and Login button visible |
| `signup page loads` | Email/password/confirm fields and Create account button visible |
| `no console errors on key pages` | Navigates `/`, `/chat`, `/search`, `/methodology`; asserts zero non-benign console errors |

The chat test is flexible — it accepts backend recommendations **or** mock/demo fallback as a valid outcome, so it does not require the backend to be running.

---

## 20. Python/Pytest Test Suite

Run all tests from `career-finder-ai/`:
```bash
python -m pytest tests/ -q
```

Or from `career-finder-ai/backend/`:
```bash
python -m pytest ../tests/ -q
```

### Test files

| Test file | Purpose | Key command | Keep reason |
|---|---|---|---|
| `tests/test_parser.py` | Parser field extraction, city/skill/interest aliases, normalisation | `pytest tests/test_parser.py` | Core parser coverage; 70+ tests |
| `tests/test_recommender.py` | Rubric scoring, enrichment signals, ML-6 shadow score, end-to-end recommend | `pytest tests/test_recommender.py` | Primary integration coverage; 57+ tests |
| `tests/test_scoring.py` | Legacy `scoring.py` scorers (major fit, city, work mode, etc.) | `pytest tests/test_scoring.py` | Legacy scorer stability; 39 tests |
| `tests/test_regression_dataset.py` | Dataset builder, synthetic profiles, split files, enriched CSV | `pytest tests/test_regression_dataset.py` | ML dataset pipeline; 16 tests |
| `tests/test_fair_regression_training.py` | Leakage guard, feature building, pipeline training, metrics helpers | `pytest tests/test_fair_regression_training.py` | Fair model training; 22 tests |
| `tests/test_regression_training.py` | Rubric-assisted track path names, pipeline structure | `pytest tests/test_regression_training.py` | Rubric-assisted sanity; 9 tests |
| `tests/test_model_error_analysis.py` | Error analysis frame, profile summary, JSON output | `pytest tests/test_model_error_analysis.py` | ML-4 error analysis; 6 tests |
| `tests/test_rubric_vs_ml_comparison.py` | Comparison frame, overlap calculation, summary JSON | `pytest tests/test_rubric_vs_ml_comparison.py` | ML-5 comparison; 3 tests |
| `tests/test_cli_ml_commands.py` | CLI `/metrics`, `/model`, `/shadow`, `/ml` command output | `pytest tests/test_cli_ml_commands.py` | CLI ML commands; 8 tests |

---

## 21. Important Generated Files

| File path | Generated by | Used by | Keep reason |
|---|---|---|---|
| `data/processed/Opportunities_Clean.xlsx` | Manual curation | `recommender.py` (live), `build_regression_dataset.py` | Primary opportunity data source for `/recommend` |
| `data/processed/Opportunities_Enriched.csv` | `enrich_opportunities_dataset.py` | `build_regression_dataset.py` | Pre-computed enrichment for faster dataset builds |
| `data/processed/student_opportunity_regression_dataset.csv` | `build_regression_dataset.py` | `inspect_regression_split.py`, training scripts | Full training data |
| `data/processed/regression_train_split.csv` | `inspect_regression_split.py` | Both training scripts | Training set (80%) |
| `data/processed/regression_test_split.csv` | `inspect_regression_split.py` | Both training scripts, error analysis, comparison | Test set (20%) |
| `data/processed/regression_split_summary.json` | `inspect_regression_split.py` | `compare_regression_models.py`, `compare_rubric_vs_ml.py` | Split metadata, overlap verification |
| `data/processed/fair_regression_model_metrics.csv` | `train_fair_regression_model.py` | `compare_regression_models.py`, `analyze_model_errors.py`, CLI | Fair model performance metrics |
| `data/processed/fair_regression_predictions.csv` | `train_fair_regression_model.py` | `analyze_model_errors.py`, `compare_rubric_vs_ml.py`, `generate_recommendation_examples.py` | Per-row hold-out predictions |
| `data/processed/rubric_assisted_regression_model_metrics.csv` | `train_regression_model.py` | `compare_regression_models.py` | Leakage demo metrics |
| `data/processed/rubric_assisted_regression_predictions.csv` | `train_regression_model.py` | (archival) | Leakage demo predictions |
| `data/processed/model_metrics_report.csv` | `compare_regression_models.py` | Course report | Combined fair + rubric-assisted metrics |
| `data/processed/fair_model_error_summary.json` | `analyze_model_errors.py` | CLI `/metrics`, course report | Best fair model error stats |
| `data/processed/rubric_vs_ml_summary.json` | `compare_rubric_vs_ml.py` | CLI `/shadow`, course report | Correlation + overlap stats |
| `docs/reports/*.md` | Various ML scripts | Course report, evaluators | Report-ready narrative documents |
| `reports/figures/*.png` | Training scripts | Visual inspection, course report | Prediction vs actual scatter plots |
| `models/fair_gradient_boosting_model.joblib` | `train_fair_regression_model.py` | `ml_scoring.py` (optional shadow) | Live ML shadow scoring artifact |

---

## 22. Environment Variables

| Variable | Where set | Purpose |
|---|---|---|
| `APP_ENV` | Backend `.env` or shell | Runtime environment label (e.g. `development`, `production`). Returned by `/health`. |
| `DATABASE_URL` | Backend `.env` (placeholder) | Placeholder for future database connection. Not used by any current code path. |
| `NEXT_PUBLIC_API_BASE` | `frontend/.env.local` | Frontend API base URL. Defaults to `http://localhost:8000`. Override for staging/production. |
| `CAREERFINDER_ENABLE_ML_SCORE` | Shell / `.env` | Set to `true` to enable optional ML shadow score on `/recommend`. Off by default. Does not affect ranking. |
| `CAREERFINDER_API_BASE` | Shell | Terminal CLI base URL. Defaults to `http://127.0.0.1:8000`. |

The `.env.example` at the repo root may contain AWS placeholder variables for a future cloud deployment. These are not wired to any current code.

---

## 23. How to Run

### Backend only

```bash
cd career-finder-ai/backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend only

```bash
cd career-finder-ai/frontend
npm run dev
```

### Terminal CLI (auto-starts backend)

```bash
# From career-finder-ai/ (repo root with package.json)
npm run run:terminal
```

### Full stack (backend + frontend in separate windows)

```bash
npm run run:full
```

### Backend tests

```bash
cd career-finder-ai
python -m pytest tests/ -q
```

Or specific suites:
```bash
python -m pytest tests/test_cli_ml_commands.py tests/test_recommender.py -q
```

### Frontend lint

```bash
cd career-finder-ai/frontend
npm run lint
```

### Frontend build

```bash
cd career-finder-ai/frontend
npm run build
```

### Frontend E2E tests

```bash
cd career-finder-ai/frontend
npx playwright install chromium   # first time only
npm run test:e2e
npm run test:e2e:ui                # interactive
```

### ML pipeline (in order)

```bash
cd career-finder-ai/backend

# 1. Enrich opportunities
python -m app.enrich_opportunities_dataset

# 2. Build regression dataset
python -m app.build_regression_dataset

# 3. Inspect and save split files
python -m app.inspect_regression_split

# 4. Train fair models (Track A)
python -m app.train_fair_regression_model

# 5. Train rubric-assisted models (Track B — leakage demo)
python -m app.train_regression_model

# 6. Compare models and generate report
python -m app.compare_regression_models

# 7. Error analysis
python -m app.analyze_model_errors

# 8. Generate recommendation examples
python -m app.generate_recommendation_examples

# 9. Rubric vs ML comparison
python -m app.compare_rubric_vs_ml
```

---

## 24. What Not To Delete

The following files are critical for the live system, tests, or ML artifacts:

| File / Directory | Reason |
|---|---|
| `backend/app/scoring.py` | Legacy scorer used by `tests/test_scoring.py` (39 tests). Tests will break. |
| `backend/app/rubric.py` | Live scoring engine. Deleting breaks `/recommend` entirely. |
| `data/processed/Opportunities_Clean.xlsx` | Primary opportunity data. Without it `/recommend` falls back to 7 placeholder records. |
| `data/processed/fair_regression_model_metrics.csv` | Required by CLI `/metrics` and `compare_regression_models.py`. |
| `data/processed/rubric_vs_ml_summary.json` | Required by CLI `/shadow`. |
| `data/processed/fair_model_error_summary.json` | Required by `analyze_model_errors` tests. |
| `data/processed/regression_train_split.csv` / `regression_test_split.csv` | Required by training scripts and tests. Deleting forces GroupShuffleSplit fallback (different random seed risk). |
| `models/fair_gradient_boosting_model.joblib` | Required for `CAREERFINDER_ENABLE_ML_SCORE=true`. Without it, ML score is silently disabled. |
| `models/rubric_assisted_*.joblib` | Required by `tests/test_regression_training.py`. |
| `tests/` | All test files. All active; deletion will lower test confidence. |
| `docs/reports/` | Referenced by the course report. |
| `notebooks/` | If present — course-required Jupyter notebooks. |
| `database/` | If present — DB schema/migration files for future auth. |

---

## 25. Known Limitations

1. **Synthetic profiles.** The ML training data uses 50 deterministic synthetic profiles, not real student interactions. The model is calibrated to patterns that exist in these profiles.

2. **Target score generated by rubric.** The `target_score` label is computed by the same rubric used for live ranking. This means the ML model is learning to replicate a heuristic, not real user outcomes or employer feedback.

3. **ML score is shadow only.** The fair ML model correlates with the rubric (Pearson ~0.83) but has average top-5 overlap of only ~0.36. It has not been A/B tested against real user behaviour. Sorting remains by rubric `match_score`.

4. **Search page not final.** The `/search` route is a shell. Filter-based search (Phase 6) has not been implemented.

5. **Auth is a stub.** Login and signup pages accept form input but use in-memory state only — no real authentication, no cookies, no database, no password hashing.

6. **Dashboard and model pages not final.** No student dashboard, recruiter view, or admin panel exists yet.

7. **Data may need continuous updates.** `Opportunities_Clean.xlsx` is a curated static snapshot. Real usage would require a data pipeline to refresh listings.

8. **Real user feedback not yet incorporated.** No click-through, application, or acceptance data has been collected. The rubric is based on expert-designed heuristics, not feedback loops.

9. **Small opportunity pool.** The current dataset has a limited number of opportunity records. Results improve with more listings.

---

## 26. Suggested Next Steps

| Priority | Item |
|---|---|
| Report | Assemble the final course report from existing `docs/reports/` markdown files |
| Demo | Prepare a 10-minute demo script covering CLI + web chat + ML metrics |
| Frontend | Optionally display `ml_score` in the chat UI alongside rubric `match_score` (behind same feature flag) |
| Auth | Implement real authentication (Auth-2: HttpOnly sessions, backend `/auth/*` endpoints, middleware) |
| Search | Implement filter-based `/search` page (Phase 6) with keyword, city, major, role_cluster, program_type, work_mode filters |
| Recruiter | Add recruiter/admin view to post and manage opportunities |
| Real feedback | Integrate application click-through logging and user preference signals to improve ML target |
| Continuous data | Add a data pipeline or scraper to refresh `Opportunities_Clean.xlsx` regularly |

---

# File and Function Index

## Backend API

| Area | File | Function / Class / Attribute | Purpose |
|---|---|---|---|
| API entry | [main.py](../backend/app/main.py#L1-L103) | `app` (FastAPI instance) | Application root, CORS, routes |
| Health | [main.py](../backend/app/main.py#L48-L51) | `health_check` | `GET /health` |
| Stats | [main.py](../backend/app/main.py#L58-L67) | `get_stats` | `GET /stats` — placeholder dataset stats |
| Parse | [main.py](../backend/app/main.py#L74-L84) | `parse_student_message` | `POST /parse` |
| Recommend | [main.py](../backend/app/main.py#L91-L102) | `get_recommendations` | `POST /recommend` — main endpoint |

## Backend Schemas

| Area | File | Function / Class / Attribute | Purpose |
|---|---|---|---|
| Request | [schemas.py](../backend/app/schemas.py#L13-L33) | `ParseRequest`, `RecommendRequest` | Input validation |
| Profile | [schemas.py](../backend/app/schemas.py#L39-L105) | `StudentProfile`, `ParsedProfile` | Structured student profile |
| Opportunity | [schemas.py](../backend/app/schemas.py#L107-L210) | `Opportunity` | Full opportunity response with all score fields |
| Response | [schemas.py](../backend/app/schemas.py#L212-L217) | `RecommendResponse` | Top-level `/recommend` response |

## Backend Parser / Taxonomy

| Area | File | Function / Class / Attribute | Purpose |
|---|---|---|---|
| Parser | [parser.py](../backend/app/parser.py#L450-L512) | `parse_message` | Main parser entry point |
| Normalize | [parser.py](../backend/app/parser.py#L217-L273) | `_normalize_text` | Lowercasing, alias substitution, GPA preservation |
| Taxonomy | [taxonomy.py](../backend/app/taxonomy.py#L60-L151) | `INTEREST_ALIASES` | Canonical interest → phrase list |
| Taxonomy | [taxonomy.py](../backend/app/taxonomy.py#L311-L351) | `CITY_ALIASES` | Saudi city alias normalisation |
| Taxonomy | [taxonomy.py](../backend/app/taxonomy.py#L361-L372) | `SKILL_ALIASES` | Skill alias normalisation |
| Taxonomy | [taxonomy.py](../backend/app/taxonomy.py#L400-L421) | `normalise_skill_aliases` | Apply skill alias substitutions |
| Taxonomy | [taxonomy.py](../backend/app/taxonomy.py#L424-L457) | `find_city_in_text` | Find cities with longest-match precedence |
| Taxonomy | [taxonomy.py](../backend/app/taxonomy.py#L460-L480) | `find_interest_in_text` | Find canonical interest; handles "interested in X" phrasing |

## Backend Scoring / Recommender

| Area | File | Function / Class / Attribute | Purpose |
|---|---|---|---|
| Rubric weights | [rubric.py](../backend/app/rubric.py#L46-L55) | `TARGET_WEIGHTS` | Scoring component weights |
| Score pair | [rubric.py](../backend/app/rubric.py#L578-L613) | `score_profile_opportunity_pair` | All 8 component scores + target_score |
| Major fit | [rubric.py](../backend/app/rubric.py#L273-L290) | `compute_major_fit_score` | 0 / 0.3 / 0.6 / 1.0 based on major match |
| Skill match | [rubric.py](../backend/app/rubric.py#L293-L338) | `compute_skill_match_score` | Layered explicit/inferred/preferred scoring |
| Role interest | [rubric.py](../backend/app/rubric.py#L356-L435) | `compute_role_interest_score` | Cluster/taxonomy/family/generic fallback |
| Missing skills | [rubric.py](../backend/app/rubric.py#L694-L733) | `compute_missing_skills` | Required → preferred → explicit ordering |
| Enrichment | [opportunity_enrichment.py](../backend/app/opportunity_enrichment.py#L461-L549) | `enrich_opportunity_signals` | Runtime inferred signals (5 buckets) |
| Role profiles | [opportunity_enrichment.py](../backend/app/opportunity_enrichment.py#L279-L326) | `ROLE_SKILL_PROFILES` | Required/preferred skills per 10 role clusters |
| Recommender | [recommender.py](../backend/app/recommender.py#L401-L493) | `recommend` | Filter → ML shadow → rubric score → sort → rank |
| E2E recommend | [recommender.py](../backend/app/recommender.py#L496-L515) | `recommend_from_message` | Parse + recommend pipeline |
| Load xlsx | [recommender.py](../backend/app/recommender.py#L172-L276) | `load_opportunities_from_xlsx` | Load opportunities from Excel |
| Legacy scorer | [scoring.py](../backend/app/scoring.py#L286-L307) | `compute_score` | Legacy composite scorer (not live; test reference only) |

## ML Pipeline

| Area | File | Function / Class / Attribute | Purpose |
|---|---|---|---|
| Dataset | [build_regression_dataset.py](../backend/app/build_regression_dataset.py#L228-L743) | `build_synthetic_profiles` | 50 deterministic synthetic profiles |
| Dataset | [build_regression_dataset.py](../backend/app/build_regression_dataset.py#L750-L823) | `build_regression_rows`, `build_regression_dataset` | (profile, opportunity) pair generation |
| Enrich CSV | [enrich_opportunities_dataset.py](../backend/app/enrich_opportunities_dataset.py#L1-L50) | `main` | Adds 5 enrichment columns to Opportunities_Enriched.csv |
| Split | [inspect_regression_split.py](../backend/app/inspect_regression_split.py#L1-L60) | `compute_split` | GroupShuffleSplit by profile_id, 80/20 |
| Fair train | [train_fair_regression_model.py](../backend/app/train_fair_regression_model.py#L460-L533) | `train_all_fair_models` | Ridge / RF / GB without rubric features |
| Fair features | [train_fair_regression_model.py](../backend/app/train_fair_regression_model.py#L173-L197) | `build_fair_feature_frame` | Feature engineering: OHE + counts + text |
| Leakage guard | [train_fair_regression_model.py](../backend/app/train_fair_regression_model.py#L211-L215) | `assert_no_rubric_features` | Prevents rubric columns from entering model inputs |
| Rubric-assisted | [train_regression_model.py](../backend/app/train_regression_model.py#L475-L562) | `train_all_models` | Leakage demo track (not honest model) |
| Compare models | [compare_regression_models.py](../backend/app/compare_regression_models.py#L226-L265) | `main` | Merges metrics CSVs, writes report |
| Error analysis | [analyze_model_errors.py](../backend/app/analyze_model_errors.py#L193-L238) | `run_error_analysis` | Worst/best predictions, profile summaries |
| Examples | [generate_recommendation_examples.py](../backend/app/generate_recommendation_examples.py#L375-L406) | `run_generate_examples` | Course-report recommendation examples |
| Rubric vs ML | [compare_rubric_vs_ml.py](../backend/app/compare_rubric_vs_ml.py#L332-L372) | `run_rubric_vs_ml_comparison` | Correlation, overlap, disagreement analysis |
| ML shadow | [ml_scoring.py](../backend/app/ml_scoring.py#L60-L67) | `is_ml_score_enabled`, `get_ml_score_source` | Feature flag helpers |
| ML shadow | [ml_scoring.py](../backend/app/ml_scoring.py#L191-L231) | `predict_ml_scores` | Batch prediction returning `{opp_id: ml_score}` |
| ML features | [ml_scoring.py](../backend/app/ml_scoring.py#L111-L184) | `_build_feature_row` | Constructs 12-column feature dict for live inference |

## Frontend

| Area | File | Function / Class / Attribute | Purpose |
|---|---|---|---|
| Home | [app/page.tsx](../frontend/src/app/page.tsx) | `Home` | Root route |
| Chat | [app/(career)/chat/page.tsx](../frontend/src/app/(career)/chat/page.tsx) | `ChatPage` | `/chat` route |
| Chat component | [career-chat.tsx](../frontend/src/components/chat/career-chat.tsx#L175-L751) | `CareerChat` | Main chat UI, multi-turn memory, backend integration |
| Chat logic | [career-chat.tsx](../frontend/src/components/chat/career-chat.tsx#L286-L427) | `runAssistantTurn` | Sends to `/recommend`, handles turn state, shelf update |
| Reply logic | [career-chat.tsx](../frontend/src/components/chat/career-chat.tsx#L73-L144) | `buildAssistantReply` | Context-aware assistant reply based on missing fields |
| API client | [api.ts](../frontend/src/lib/api.ts#L8-L27) | `recommendFromMessage` | `POST /recommend` HTTP call |
| Type adapters | [api-adapters.ts](../frontend/src/lib/api-adapters.ts#L41-L101) | `toStudentProfile`, `toRecommendation`, `toRecommendations` | Backend → frontend type conversion |
| Shelf adapter | [api-adapters.ts](../frontend/src/lib/api-adapters.ts#L367-L385) | `buildShelfMemoriesFromRecommendations` | Builds up to 6 shelf cards with L/R split |
| Profile merge | [api-adapters.ts](../frontend/src/lib/api-adapters.ts#L200-L238) | `mergeStudentProfiles` | Merges profile across chat turns |
| Session | [chat-session.ts](../frontend/src/lib/chat-session.ts#L12-L41) | `loadAnonymousChatSession`, `saveAnonymousChatSession`, `clearAnonymousChatSession` | localStorage persistence |
| API types | [api-types.ts](../frontend/src/lib/api-types.ts#L1-L54) | `ParsedProfileApi`, `OpportunityApi`, `RecommendApiResponse` | Backend response type definitions |

## CLI

| Area | File | Function / Class / Attribute | Purpose |
|---|---|---|---|
| Main loop | [careerfinder_cli.py](../scripts/careerfinder_cli.py#L1183-L1414) | `main` | Interactive REPL with command dispatch |
| API call | [careerfinder_cli.py](../scripts/careerfinder_cli.py#L669-L691) | `post_recommend` | `POST /recommend` (stdlib urllib) |
| Metrics | [careerfinder_cli.py](../scripts/careerfinder_cli.py#L212-L256) | `build_metrics_lines` | Reads fair + rubric-assisted metrics CSVs |
| Shadow | [careerfinder_cli.py](../scripts/careerfinder_cli.py#L301-L320) | `build_shadow_lines` | Reads `rubric_vs_ml_summary.json` |
| ML summary | [careerfinder_cli.py](../scripts/careerfinder_cli.py#L323-L354) | `build_ml_summary_lines` | Combined ML status + metrics |
| Compact table | [careerfinder_cli.py](../scripts/careerfinder_cli.py#L854-L871) | `format_compact_recommendations_table` | Fixed-width top-N table |
| Score change | [careerfinder_cli.py](../scripts/careerfinder_cli.py#L605-L662) | `build_score_change_notes` | Explains ranking changes between turns |

## Tests

| Area | File | Key test groups | Purpose |
|---|---|---|---|
| Parser | [tests/test_parser.py](../tests/test_parser.py) | Major/city/skill/interest/alias extraction | Validate parser correctness |
| Recommender | [tests/test_recommender.py](../tests/test_recommender.py) | Rubric scores, enrichment, missing skills, ML shadow | Validate live recommendation pipeline |
| Legacy scorer | [tests/test_scoring.py](../tests/test_scoring.py) | Major fit, city, work mode, composite | Validate legacy scoring.py |
| Dataset | [tests/test_regression_dataset.py](../tests/test_regression_dataset.py) | Synthetic profiles, build rows, split files | Validate ML dataset pipeline |
| Fair training | [tests/test_fair_regression_training.py](../tests/test_fair_regression_training.py) | Leakage guard, pipeline, metrics | Validate fair model training |
| Rubric-assisted | [tests/test_regression_training.py](../tests/test_regression_training.py) | Path names, pipeline structure | Validate rubric-assisted sanity |
| Error analysis | [tests/test_model_error_analysis.py](../tests/test_model_error_analysis.py) | Error frame, profile summary, JSON | Validate ML-4 error analysis |
| Comparison | [tests/test_rubric_vs_ml_comparison.py](../tests/test_rubric_vs_ml_comparison.py) | Comparison frame, overlap, summary | Validate ML-5 comparison |
| CLI ML | [tests/test_cli_ml_commands.py](../tests/test_cli_ml_commands.py) | `/metrics`, `/model`, `/shadow`, `/ml` output | Validate CLI ML command output |

## Reports / Data

| Area | File | Generated by | Purpose |
|---|---|---|---|
| Model metrics | [docs/reports/model_metrics_summary.md](../docs/reports/model_metrics_summary.md) | `compare_regression_models.py` | Fair vs rubric-assisted comparison report |
| ML results | [docs/reports/ml_results_summary.md](../docs/reports/ml_results_summary.md) | Manual + `analyze_model_errors.py` | Course report ML results section |
| Rubric vs ML | [docs/reports/rubric_vs_ml_comparison.md](../docs/reports/rubric_vs_ml_comparison.md) | `compare_rubric_vs_ml.py` | Correlation and overlap report |
| Examples | [docs/reports/example_recommendations.md](../docs/reports/example_recommendations.md) | `generate_recommendation_examples.py` | Curated recommendation examples |
| Tracker | [docs/tracking/IMPLEMENTATION_TRACKER.md](../docs/tracking/IMPLEMENTATION_TRACKER.md) | Manual | Feature implementation history |
| Change log | [docs/tracking/CHANGE_LOG.md](../docs/tracking/CHANGE_LOG.md) | Manual | Chronological change log |
| Test log | [docs/tracking/TEST_LOG.md](../docs/tracking/TEST_LOG.md) | Manual | Test run records |

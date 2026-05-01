# Agent instructions — Career (CareeFinder) repository

Read this file first when working in this repository.

## Where the real project lives

- The **Git repository root** here is only a thin wrapper (`README.md` with the project title).
- **All application code, tests, database scripts, notebooks, environment templates, and detailed documentation are under:**

  **`career-finder-ai/`**

  There is no separate top-level folder named `career`; the implementation package is **`career-finder-ai`**. When cloning locally, the repo folder is often named `Career`; paths look like `Career/career-finder-ai/...`.

For full setup, architecture, API shapes, data rules, ML plan, and workflow, start with **`career-finder-ai/README.md`**, then the READMEs in each subfolder below.

---

## Folder map (what each area is for)

| Location | Purpose |
|----------|---------|
| **`career-finder-ai/`** | **Career Finder AI** — Saudi COOP/internship recommender: cleaned dataset, ML fit classifier, explainable ranking, parser for student questions, optional future LLM/UI. Entire base stack can run locally. |
| **`career-finder-ai/backend/`** | **FastAPI service** — HTTP API (`/health`, `/stats`, `/parse`, `/recommend`), SQLite access, rule-based parser, scoring/ranking, data cleaning and training scripts (`clean_data`, `build_training_data`, `train_model`, `evaluate`). See **`backend/README.md`** for module-to-file mapping. |
| **`career-finder-ai/database/`** | **SQLite schema and seeds** — `schema.sql`, `seed_example.sql`; local DB file is intended at `database/career_finder.db` (gitignored). |
| **`career-finder-ai/frontend/`** | **UI (placeholder)** — Planned Next.js + TypeScript + Tailwind + shadcn/ui; **do not prioritize** until backend recommender is solid. See **`frontend/README.md`**. |
| **`career-finder-ai/notebooks/`** | **Jupyter work** — EDA, model experiments, recommendation tests (e.g. `01_data_audit`, `02_eda`, `03_model_experiments`, `04_recommendation_tests`). |
| **`career-finder-ai/tests/`** | **pytest** — Parser, scoring, recommender tests (`test_parser.py`, `test_scoring.py`, `test_recommender.py`). |
| **`career-finder-ai/.vscode/`** | **Editor recommendations** — Suggested VS Code extensions for Python/Jupyter/frontend tooling. |

Data pipeline layout (when present; described in main README): raw/interim/processed under expected `data/` conventions inside **`career-finder-ai`** — cleaning via **`backend`** scripts, not by editing raw files manually.

---

## Task ↔ area (from project README)

Use this to route changes to the right place:

| Task / responsibility | Primary location |
|----------------------|------------------|
| Dataset cleaning, data dictionary | `career-finder-ai/backend/app/clean_data.py`, data folders per README, notebooks **`01_data_audit`**, **`02_eda`** |
| ML training & evaluation | `career-finder-ai/backend/app/train_model.py`, `evaluate.py`, **`build_training_data.py`**, notebook **`03_model_experiments`** |
| Recommendation engine, scoring, API behavior | `career-finder-ai/backend/app/recommender.py`, `scoring.py`, `main.py`, **`tests/`** |
| Parser / structured filters from student text | `career-finder-ai/backend/app/parser.py`, tests |
| Database schema / seed data | `career-finder-ai/database/` |
| Frontend / chat UI (later) | `career-finder-ai/frontend/` |
| Reports, docs, QA | Root **`README.md`** is minimal; extend **`career-finder-ai/README.md`** and repo docs as needed |

Suggested feature branches from the main README (for context only): `feature/dataset-cleaning`, `feature/ml-model`, `feature/recommender`, `feature/frontend`, `feature/report-docs`.

---

## Quick commands (run from `career-finder-ai` unless noted)

- Backend: `cd career-finder-ai/backend` → venv, `pip install -r requirements.txt`, `uvicorn app.main:app --reload`
- Tests: `cd career-finder-ai/backend` → `pytest` (or run from project with paths as documented in README)
- DB init: apply `database/schema.sql` and `database/seed_example.sql` to local SQLite as in **`career-finder-ai/README.md`**

Do **not** commit `.env`, `.db` files, or secrets (see main project README).

# Backend – Career Finder AI

FastAPI backend for the AI-Powered Career Finder.

---

## Quick Start

Run these from the **`career-finder-ai`** repository root unless noted.

### Backend API

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend
```

Then open: <http://127.0.0.1:8000/docs>

### Terminal CLI

```bash
python scripts/careerfinder_cli.py
```

### Frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Use a **full** `npm install` (not `--omit=dev`) so `@playwright/test` is present for `npm run build`. On PowerShell, if scripts are blocked, use `npm.cmd run dev` / `npm.cmd run build`.

### Final demo smoke (no HTTP)

```bash
python scripts/final_demo_smoke.py
```

See `docs/reports/final_demo_script.md` and `docs/reports/final_qa_lock.md`.

### Virtual environment (first-time setup)

**Windows**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then use the uvicorn command above from the repo root.

---

## Running Tests

```bash
cd backend
pytest
```

---

## Module Overview

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app with all endpoints |
| `app/config.py` | Environment variable configuration |
| `app/database.py` | SQLite connection helpers (planned; not used by `/recommend` yet) |
| `app/schemas.py` | Pydantic request/response models |
| `app/parser.py` | Rule-based student message parser |
| `app/taxonomy.py` | City/interest/skill aliases and role clusters |
| `app/opportunity_enrichment.py` | Runtime opportunity signal enrichment |
| `app/rubric.py` | **Live scoring** — rubric used by `/recommend` and the regression dataset |
| `app/recommender.py` | Ranking engine (loads `data/processed/Opportunities_Clean.xlsx`) |
| `app/ml_scoring.py` | Optional ML shadow score when `CAREERFINDER_ENABLE_ML_SCORE=true` |
| `app/scoring.py` | Legacy weighted score helpers (still covered by `tests/test_scoring.py`) |
| `app/build_regression_dataset.py` | ML regression dataset builder |
| `app/train_fair_regression_model.py` | Fair (leakage-safe) regression training |
| `app/train_regression_model.py` | Rubric-assisted regression training (leakage demo) |

**Live `/recommend` behaviour:** ranking uses rubric `match_score` only. Set `CAREERFINDER_ENABLE_ML_SCORE=true` to attach optional `ml_score` from `models/fair_gradient_boosting_model.joblib`; sorting is unchanged.

Offline pipelines also include `clean_data.py`, `build_training_data.py`, `train_model.py`, and `evaluate.py` (older classifier track).

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Backend health check |
| GET | `/stats` | Basic dataset statistics |
| POST | `/parse` | Parse student message into filters |
| POST | `/recommend` | Return top 5 recommendations |

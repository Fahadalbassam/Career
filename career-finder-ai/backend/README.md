# Backend – Career Finder AI

FastAPI backend for the AI-Powered Career Finder.

---

## Quick Start

### Windows

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### macOS / Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open: <http://127.0.0.1:8000/docs>

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
| `app/database.py` | SQLite connection helpers |
| `app/schemas.py` | Pydantic request/response models |
| `app/parser.py` | Rule-based student message parser |
| `app/recommender.py` | Scoring and ranking engine |
| `app/scoring.py` | Individual score components |
| `app/clean_data.py` | Dataset cleaning pipeline |
| `app/build_training_data.py` | Training dataset builder |
| `app/train_model.py` | TF-IDF + Logistic Regression trainer |
| `app/evaluate.py` | Model evaluation and metrics |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Backend health check |
| GET | `/stats` | Basic dataset statistics |
| POST | `/parse` | Parse student message into filters |
| POST | `/recommend` | Return top 5 recommendations |

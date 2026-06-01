# AI-Powered Career Finder for Saudi COOP and Internship Opportunities

---

## Project Summary

**CareerFinder.ai** recommends COOP and internship opportunities for Saudi computing students. The implemented system combines:

- A **cleaned, verified dataset** of Saudi COOP/internship opportunities
- A **rule-based parser** that extracts structured profile fields from natural-language input
- An **explainable rubric-based ranking engine** (live recommendations; transparent score breakdown)
- **Supervised regression ML** trained and evaluated offline (0–100 score prediction; optional shadow comparison; does not replace live rubric ranking)
- A **Next.js frontend**, **FastAPI backend**, and **terminal CLI** for demos and testing

The stack runs **locally** without external LLM or cloud API dependencies.

---

## Problem Statement

Students in Saudi Arabia often struggle to find suitable COOP and internship opportunities because information is scattered across:

- Company career portals
- LinkedIn job listings
- University placement boards
- Government portals (Human Resources Development Fund, etc.)

This project centralises that information and recommends the most suitable opportunities for each student based on their individual profile — major, city, skills, work mode preference, and program type.

---

## Target Users

| Major | Code |
|-------|------|
| Computer Science | CS |
| Artificial Intelligence | AI |
| Cybersecurity | CYS |
| Computer Information Systems | CIS |
| Data Science | DS |
| Data Engineering | DE |
| Computer Engineering | CE |
| FinTech | FT |

---

## Main Features

- **Rule-based student question parser** — major, city, skills, work mode, program type, and related fields
- **Rubric-based live ranking** — weighted, explainable 0–100 `match_score` with per-component breakdown
- **Supervised regression ML** — fair and rubric-assisted models for evaluation and report metrics (see `docs/reports/`)
- **Top recommendations** with `why_recommended`, matched/missing skills, and verified source links
- **Web UI** (`/`, `/chat`, `/search`, `/methodology`, `/model`) and **terminal CLI** wired to `/parse` and `/recommend`

---

## System Architecture

```
Student message (web or CLI)
      │
      ▼
Rule-based parser  →  structured profile
      │
      ▼
Candidate opportunities (cleaned dataset)
      │
      ▼
Rubric scoring  →  live ranking (0–100 match_score, breakdown, explanations)
      │
      ├─ optional ML shadow score (evaluation / comparison only)
      │
      ▼
Top recommendations  →  FastAPI  →  Next.js UI / terminal CLI
```

Offline ML pipeline (reproducibility): regression dataset build → fair/rubric-assisted model training → metrics and rubric-vs-ML comparison reports in `docs/reports/`.

---

## Required Software Installation

Before running the project, each team member should install:

### Required

| Tool | Purpose | Download |
|------|---------|----------|
| **Git** | Version control | https://git-scm.com |
| **GitHub Desktop** or Git CLI | Git workflow | https://desktop.github.com |
| **VS Code** | Recommended IDE | https://code.visualstudio.com |
| **Python 3.11+** | Backend runtime | https://www.python.org |
| **DB Browser for SQLite** | View local database | https://sqlitebrowser.org |
| **Node.js LTS** | Frontend only (later) | https://nodejs.org |

> ⚠️ On Windows, check **"Add Python to PATH"** during installation.

### Recommended (Optional)

| Tool | Purpose |
|------|---------|
| **Anaconda / Miniconda** | Conda environment management |
| **Postman or Insomnia** | API endpoint testing |

> 🚫 Do **not** install Python packages globally. Always use a virtual environment.

---

## VS Code Extensions

VS Code will automatically suggest extensions when you open this project (from `.vscode/extensions.json`).

You can also install them manually:

| Extension | ID |
|-----------|-----|
| Python | `ms-python.python` |
| Pylance | `ms-python.vscode-pylance` |
| Jupyter | `ms-toolsai.jupyter` |
| Ruff | `charliermarsh.ruff` |
| Black Formatter | `ms-python.black-formatter` |
| ESLint | `dbaeumer.vscode-eslint` |
| Prettier | `esbenp.prettier-vscode` |
| Tailwind CSS IntelliSense | `bradlc.vscode-tailwindcss` |
| SQLite Viewer | `qwtel.sqlite-viewer` |
| GitHub Pull Requests | `github.vscode-pull-request-github` |
| GitHub Copilot | `github.copilot` |
| GitHub Copilot Chat | `github.copilot-chat` |

> 📝 Extensions are **not** stored inside the project. Only the recommendation list is stored. Each teammate installs them locally.

---

## Local Backend Setup

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

Then open: **http://127.0.0.1:8000/docs**

The interactive Swagger UI lets you test all endpoints directly in the browser.

### Final demo stack (SPRINT-4 — from `career-finder-ai/`)

**Terminal-focused documentation:** [career-finder-ai/docs/README_TERMINAL.md](career-finder-ai/docs/README_TERMINAL.md) — CLI commands, rubric vs ML pipeline, datasets, and presentation demo script.

```bash
# Backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend

# Terminal CLI (second terminal)
python scripts/careerfinder_cli.py

# Frontend (optional)
cd frontend
npm install
npm run dev
```

Use a **full** `npm install` (not `--omit=dev`) because Playwright is a devDependency required for `npm run build`. On PowerShell, use `npm.cmd` if `npm` scripts are blocked.

Automated lock checks: `python scripts/final_demo_smoke.py`. Walkthrough: `career-finder-ai/docs/reports/final_demo_script.md`.

---

## Running Tests

```bash
cd backend
pytest
```

---

## Database Setup

The project starts with **SQLite** for local development — no database server required.

**Schema location:** `database/schema.sql`

**Local database file:** `database/career_finder.db`

> ⚠️ **Important:** Do **not** commit `.db` files to GitHub. They are excluded by `.gitignore`.

### Initialise the database

```bash
# Using sqlite3 CLI
sqlite3 database/career_finder.db < database/schema.sql
sqlite3 database/career_finder.db < database/seed_example.sql
```

### Recommended local tools

- **DB Browser for SQLite** — https://sqlitebrowser.org
- **SQLite Viewer** VS Code extension — `qwtel.sqlite-viewer`

### Later migration options

- **PostgreSQL** for production
- **Supabase** for cloud-hosted PostgreSQL

---

## Dataset Rules

```
data/raw/          ← Raw dataset files (never manually edit)
data/interim/      ← Intermediate processing steps
data/processed/    ← Final cleaned outputs used by the model
```

> 🚫 **Never manually edit the original raw dataset.** All cleaning must be done through scripts.

### Expected cleaned outputs

| File | Description |
|------|-------------|
| `companies_clean.csv` | Cleaned companies |
| `opportunities_clean.csv` | Cleaned opportunities |
| `training_fit_dataset.csv` | Labelled ML training data |
| `missing_values_report.csv` | Per-column missing value counts |
| `data_dictionary.xlsx` | Column descriptions and samples |

### Run the cleaning pipeline

```bash
cd backend
python -m app.clean_data
python -m app.build_training_data
```

---

## ML Plan

### Task

**Fit Level Classification** — given an opportunity and a student major, predict:

- **High** — strong match
- **Medium** — acceptable match
- **Low** — poor match

### Feature engineering

| Input | Source |
|-------|--------|
| Opportunity title | `opportunities.title` |
| Company name | `companies.name` |
| Program type | `opportunities.program_type` |
| Student major | Profile input |

Features are combined into a single text string and vectorised with **TF-IDF**.

### Models to compare

| Model | Notes |
|-------|-------|
| TF-IDF + Logistic Regression | Baseline (implemented) |
| TF-IDF + Linear SVM | Fast and accurate for text |
| Random Forest | Optional comparison |

### Evaluation metrics

| Metric | Description |
|--------|-------------|
| Accuracy | Overall correct predictions |
| Macro Precision | Precision averaged across classes |
| Macro Recall | Recall averaged across classes |
| Macro F1-score | Harmonic mean of precision and recall |
| Confusion Matrix | Visual breakdown of predictions |

### Recommendation evaluation

| Metric | Description |
|--------|-------------|
| Precision@5 | How many of top 5 are relevant |
| nDCG@5 | Normalised discounted cumulative gain (optional) |

### Train and evaluate

```bash
cd backend
python -m app.train_model
python -m app.evaluate
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Check if backend is running |
| `GET` | `/stats` | Return basic dataset statistics |
| `POST` | `/parse` | Parse student message into structured filters |
| `POST` | `/recommend` | Return top 5 recommendations |

### GET /health

```json
{
  "status": "ok",
  "environment": "development"
}
```

### GET /stats

```json
{
  "total_companies": 7,
  "total_opportunities": 7,
  "available_cities": ["Riyadh", "Jeddah", "Dammam", "Dhahran"],
  "available_majors": ["CS", "AI", "CYS", "CIS", "DS", "DE", "CE", "FT"],
  "available_work_modes": ["On-site", "Remote", "Hybrid"]
}
```

### POST /parse

**Request:**

```json
{
  "message": "I am a cybersecurity student in Dammam looking for remote COOP"
}
```

**Response:**

```json
{
  "major": "CYS",
  "city": "Dammam",
  "interest": "Cybersecurity",
  "work_mode": "Remote",
  "program_type": "COOP",
  "skills": []
}
```

### POST /recommend

**Request:**

```json
{
  "message": "I am a cybersecurity student in Dammam looking for remote COOP"
}
```

**Response:**

```json
{
  "profile": {
    "major": "CYS",
    "city": "Dammam",
    "interest": "Cybersecurity",
    "work_mode": "Remote",
    "program_type": "COOP",
    "skills": []
  },
  "recommendations": [
    {
      "id": 2,
      "company": "STC",
      "title": "Cybersecurity Internship",
      "city": "Riyadh",
      "work_mode": "Hybrid",
      "program_type": "Internship",
      "major_fit": ["CYS", "CS", "CE"],
      "source_url": "https://www.stc.com.sa/careers",
      "score": 0.7125
    }
  ],
  "total_candidates": 7
}
```

---

## Frontend Setup

```bash
cd career-finder-ai/frontend
npm install
npm run dev
```

See `career-finder-ai/frontend/README.md` for routes and components. Run `npm run lint` and `npm run build` before submission.

---

## Environment Variables

Copy `.env.example` to `.env`:

**Windows:**
```bash
copy .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

> 🚫 **Never push `.env` to GitHub.** It is excluded by `.gitignore`.

---

## Team Workflow

### Branch structure

| Branch | Purpose |
|--------|---------|
| `main` | Stable releases only |
| `dev` | Shared integration branch |
| `feature/dataset-cleaning` | Data cleaning work |
| `feature/ml-model` | ML training and evaluation |
| `feature/recommender` | Recommendation engine |
| `feature/frontend` | UI development |
| `feature/report-docs` | Reports and documentation |

### Rules

- 🚫 Do **not** push directly to `main`
- Each task should use its own feature branch
- Open **pull requests into `dev`**
- Merge `dev` into `main` only when stable
- **Pull before starting work**
- **Commit small changes often**

---

## Suggested Team Responsibilities

| Member | Responsibility |
|--------|---------------|
| **Member 1** | Dataset cleaning and data dictionary |
| **Member 2** | ML model training and evaluation |
| **Member 3** | Recommendation engine and backend logic |
| **Member 4** | Frontend UI, CLI, and integration QA |
| **Member 5** | Report, README, QA, and project management |

---

## Commit Message Style

Use simple, descriptive commit messages:

```
feat: add parser endpoint
fix: correct city matching logic
docs: update setup instructions
test: add scoring tests
data: add cleaned dataset sample
model: train logistic regression baseline
```

---

## Project Timeline

| Phase | Goal |
|-------|------|
| **Phase 1** | Repo setup, dataset cleaning, README |
| **Phase 2** | EDA and baseline ML model |
| **Phase 3** | Recommendation engine |
| **Phase 4** | Chat-style demo |
| **Phase 5** | Evaluation, final report, presentation |

---

## Security Notes

> ⚠️ Keep these rules at all times:

- 🚫 Do **not** commit `.env`
- 🚫 Do **not** commit API keys or tokens
- 🚫 Do **not** commit AWS credentials
- 🚫 Do **not** commit local database `.db` files
- 🚫 Do **not** commit large model files unless necessary
- ✅ Use `.env.example` for shared configuration templates

---

## Troubleshooting

### `python` is not recognized

**Solution:** Install Python 3.11+ and make sure **"Add Python to PATH"** is checked during Windows installation.

### `pip install` fails

**Solution:** Upgrade pip first:

```bash
python -m pip install --upgrade pip
```

### `uvicorn` command not found

**Solution:** Make sure the virtual environment is **activated** and requirements are installed:

```bash
# Windows
.venv\Scripts\activate
pip install -r requirements.txt

# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

### `ModuleNotFoundError`

**Solution:** Run commands from the `backend/` directory and ensure the virtual environment is activated.

### SQLite database not found

**Solution:** Initialise the database from the schema file:

```bash
sqlite3 database/career_finder.db < database/schema.sql
```

### Frontend command fails

**Solution:** Install [Node.js LTS](https://nodejs.org) then run:

```bash
cd frontend
npm install
```

---

## Definition of Done

### ✅ Dataset is done when:
- Companies and opportunities are split into separate files
- Duplicates removed
- Cities normalised (English names)
- Work modes normalised (On-site / Remote / Hybrid)
- Program types normalised (COOP / Internship)
- Fit labels normalised (High / Medium / Low)
- Missing values report created
- Data dictionary created

### ✅ ML is done when:
- Training dataset exists in `data/processed/`
- At least two models trained and compared
- Metrics table exists (accuracy, F1, precision, recall)
- Confusion matrix saved in `reports/figures/`
- Best model saved in `models/`

### ✅ Recommender is done when:
- Student profile input works end-to-end
- Top 5 results return with scores
- Scores are explainable
- Source links appear for each result

### ✅ App is done when:
- Backend runs with `uvicorn`
- Parser endpoint works
- Recommendation endpoint works
- All tests pass (`pytest`)
- README setup instructions work from a clean clone

---

## Do Not Do Yet

> Keep the scope focused. Avoid these premature steps:

- 🚫 Do **not** start with Docker
- 🚫 Do **not** start with deployment
- 🚫 Do **not** start with PostgreSQL
- 🚫 Do **not** train a custom LLM
- 🚫 Do **not** build a beautiful frontend before the recommender works

---

## License

This project is licensed under the [MIT License](LICENSE).

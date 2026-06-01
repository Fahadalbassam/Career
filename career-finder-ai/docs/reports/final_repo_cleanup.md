# FINAL-REPO-CLEANUP-1 — Repository cleanup report

**Date:** 2026-06-01  
**Purpose:** Prepare the CareerFinder.ai repository for final academic submission by removing internal development artifacts and misleading documentation, without changing application behavior, ML models, or datasets.

---

## Files and folders removed

| Category | Paths |
|----------|--------|
| Internal tracking | `docs/tracking/` (`CHANGE_LOG.md`, `DECISION_LOG.md`, `IMPLEMENTATION_TRACKER.md`, `TEST_LOG.md`) |
| Planning / prompts | `docs/planning/` (auth, integration, roadmap, search plan, `PROJECT_CONTEXT.md`, `PROMPT_CONTEXT.md`) |
| Internal audit | `docs/audits/chat-search-recommendation-audit.md` |
| Direction freeze (superseded) | `docs/PROJECT_DIRECTION.md` |
| Sprint / QA scratch reports | `docs/reports/sprint_1_*`, `sprint_2_*`, `sprint_3_*`, `final_qa_lock.md`, `final_qa_sweep.md`, `final_recommendation_quality_sweep.md` |
| Agent IDE file | `frontend/CLAUDE.md` |
| Unused debug script | `check_excel_loading.py` (one-off Excel probe; not referenced by tests or demo) |

**Untracked (removed from Git index, kept locally if present):** `career-finder-ai/.vscode/settings.json`

---

## Files and folders kept

| Category | Paths |
|----------|--------|
| Backend / frontend / CLI | All `backend/app/`, `frontend/src/`, `scripts/careerfinder_cli.py`, demo and audit scripts (`final_demo_smoke.py`, `debug_score_breakdown.py`, `recommendation_quality_sweep.py`) |
| Tests | `career-finder-ai/tests/` |
| Data & ML artifacts | `data/processed/*`, `reports/figures/*`, notebooks |
| Submission docs | Root `README.md`, `docs/README_TERMINAL.md`, `docs/PROJECT_TECHNICAL_GUIDE.md`, `docs/reports/ml_results_summary.md`, `model_metrics_summary.md`, `rubric_vs_ml_comparison.md`, `example_recommendations.md`, `final_demo_script.md`, `score_audit.md`, demo capture `.txt` files |
| New QA summary | `docs/reports/final_qa_summary.md` |
| Config templates | `.env.example`, `requirements.txt`, `package.json` / lockfiles |

---

## `.gitignore` updates

**Root (`.gitignore`):** `.cursor/`, `.vscode/settings.json`, `.env` / `.env.*` with `!.env.example`, OS cruft.

**Project (`career-finder-ai/.gitignore`):** Expanded to exclude virtualenvs, Python/Node caches, coverage, Playwright output, logs/temp/backup patterns, and internal doc paths (`docs/tracking/`, `docs/planning/`, `docs/audits/`, scratch/prompt/context folders, `Pasted*` files).

---

## Secret scan result

| Check | Result |
|-------|--------|
| Tracked `.env` files | **None** — only `career-finder-ai/.env.example` (placeholders) |
| Real API keys / tokens in source | **None found** |
| Bedrock/OpenAI credentials in repo | **Removed from `.env.example`**; unused `BEDROCK_*` env vars remain in `config.py` as inert defaults (no runtime use) |

**Action required if local `.env` exists:** Keep it untracked; never push.

---

## Documentation corrections

| Area | Change |
|------|--------|
| Root `README.md` | Describes rule-based parser, rubric live ranking, regression ML for evaluation; removed optional LLM/Bedrock feature claims; updated architecture diagram |
| `.env.example` | Removed AWS Bedrock section; added optional `CAREERFINDER_ENABLE_ML_SCORE` comment |
| `backend/requirements.txt` | Removed Bedrock-oriented comment |
| `parser.py` module docstring | Clarified live system is rule-based only |

`docs/README_TERMINAL.md` and `docs/PROJECT_TECHNICAL_GUIDE.md` already state **no external LLM** in the live path.

---

## Verification results (post-cleanup)

| Step | Command | Result |
|------|---------|--------|
| Backend tests | `python -m pytest -q` (from `career-finder-ai/`) | **402 passed** |
| Frontend lint | `npm run lint` | **Pass** |
| Frontend build | `npm run build` | **Pass** (Next.js 16.2.4) |
| Demo smoke | `python scripts/final_demo_smoke.py` | **PASS (4/4)** |
| CLI | `scripts/careerfinder_cli.py` | Starts; requires guest/login choice (interactive); covered by smoke + pytest CLI tests |

---

## Known limitations (unchanged)

- Live ranking remains **rubric-based**; ML is evaluation/shadow only by default.
- Auth is stub-only; dataset is curated spreadsheet, not live job scraping.
- See `docs/reports/final_qa_summary.md` for demo-safe inputs and presentation boundaries.

---

## Behavior confirmation

- **No** changes to scoring weights, parser logic, recommender ranking, trained model files, or processed datasets.
- **No** ML retraining.
- Cleanup limited to documentation, `.gitignore`, removal of internal artifacts, and one unused debug script.

---

## Repository readiness

The repository is **ready to push** after review of this commit. Run the verification commands above on a clean clone before submission.

# SPRINT-4 — Final QA lock (CareerFinder.ai)

Lock report for presentation and reproducible demo. **No ML retraining, no dataset edits, no rubric weight changes, no score inflation** in this sprint.

---

## Scope of SPRINT-4

| Deliverable | Path |
|-------------|------|
| Final demo script | `docs/reports/final_demo_script.md` |
| Backend smoke script | `scripts/final_demo_smoke.py` |
| QA lock report | `docs/reports/final_qa_lock.md` (this file) |
| Tracking updates | `docs/tracking/CHANGE_LOG.md`, `IMPLEMENTATION_TRACKER.md`, `TEST_LOG.md` |

**Out of scope (explicit):** ML retrain, dataset file changes, frontend redesign, auth/recruiter/search, new role taxonomy logic, rubric weight changes, artificial score boosts.

**HOTFIX-4.1 (2026-06-01):** Compact terminal header; greeting/noise guard (`input_intent.py`); `recommend_from_message` returns empty `recommendations` when input is not recommendation-worthy; CLI checks `/health` before chat. No scoring/rubric/ML changes.

**HOTFIX-4.2 (2026-06-01):** Interview preference parsing and multi-turn persistence (follow-up “interview preference would be in person”); API/APIs skill alias → `apis`; missing-skills alias cleanup; assistant stops asking for interview preference when set. No ML/dataset/`TARGET_WEIGHTS`/ranking changes.

---

## Backend pytest

**Command:**

```bash
cd career-finder-ai
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py \
  tests/test_input_intent.py tests/test_assistant_reply.py tests/test_cli_ml_commands.py \
  tests/test_scoring.py tests/test_role_inference.py tests/test_recommendation_explanation.py -q
```

**Result:** **315 passed** in ~22s (2026-05-31 lock run).

---

## Frontend lint / build

**Commands:**

```bash
cd career-finder-ai/frontend
npm run lint
npm run build
```

**Notes:**

- Full `npm install` required (not `--omit=dev`) for Playwright types during build.
- On PowerShell, use `npm.cmd` if execution policy blocks `npm` scripts.

**Result:** **pass** / **pass** (ESLint clean; Next.js 16.2.4 production build).

---

## `final_demo_smoke.py`

**Command:**

```bash
cd career-finder-ai
python scripts/final_demo_smoke.py
```

**Checks:**

1. Role-unknown message → guided discovery / role-direction choices  
2. SQL-only → ambiguous, clarifying question, no forced high-confidence role  
3. Khobar + Riyadh/Jeddah → home city + flexible locations  
4. Full cyber COOP demo → recommendations, rubric scores, sort order, details formatter, missing-skill sanity  

**Result:** **PASS (4/4 checks)** (2026-05-31 lock run).

**Top recommendation (full demo):** **Bank Albilad — Cooperative Training Program — 86%**, `score_source=rubric`.

---

## Manual demo scenarios

| # | Input / command | Pass criteria |
|---|-----------------|---------------|
| 1 | `I don't know what role I want` | Role-direction choices in assistant |
| 2 | `I know SQL` | Clarifying question; no single forced role |
| 3 | Khobar + Riyadh/Jeddah flexibility | Khobar home; Riyadh/Jeddah accepted |
| 4 | Full cyber Khobar COOP message | Top-5 sorted; rubric; Bank Albilad ~86% typical |
| 5 | `/details 1` | Structured breakdown; honest location/interview |
| 6 | `/reset` | Logo + cleared session |

Script: `docs/reports/final_demo_script.md`

---

## Known limitations (state clearly in demo)

1. **Live ranking is rubric-based; ML is evaluated/shadow** — default `score_source=rubric`; optional `ml_score` does not reorder.
2. **Opportunities depend on dataset quality** — curated spreadsheet, not exhaustive Saudi market coverage.
3. **Broad locations (e.g. Saudi Arabia) are not exact city matches** — Khobar student vs national listing → partial location score; say aloud.
4. **Interview details may be “Not stated”** — partial credit; do not claim the company confirmed interviews.
5. **Some program titles are generic** (e.g. “Cooperative Training Program”) — skill/role fit uses enrichment + rubric, not job-title exactness.
6. **No real-time scraping** — course prototype; URLs and text from cleaned dataset.

---

## Safe demo input

Use the **canonical message** in `final_demo_script.md` (CS + Khobar + cybersecurity COOP + SQL/MongoDB/Linux/networking/SIEM + on-site + interview + Security Operations). It is regression-tested and produces stable rubric ranking on the current dataset.

**Also safe for short vignettes:**

- Guided discovery and SQL ambiguity (scenarios 1–2)  
- Location flexibility phrase (scenario 3)  
- `/details 1`, `/reset`, `/help`

---

## What not to claim during presentation

- Do **not** say ML drives live ranking by default.  
- Do **not** guarantee COOP placement, interviews, or certificates.  
- Do **not** imply listings are always in the student’s exact city.  
- Do **not** invent requirements, salaries, or deadlines not in the dataset.  
- Do **not** present rubric-assisted regression metrics (near-perfect R²) as honest production performance — fair model only for ML evaluation.  
- Do **not** promise auth, recruiter portal, or full search — out of scope.

---

## Prior sprint baseline (pre–SPRINT-4)

- SPRINT-1: terminal UX + location flexibility  
- SPRINT-1.1: frontend build / Playwright devDependency  
- SPRINT-2: role-family intelligence + guided questioning  
- SPRINT-3: recommendation explanation + `/details` clarity  
- Verified before lock: **315** pytest, lint/build pass, Bank Albilad **86%** #1 on canonical demo input

---

## Confirmation checklist

- [x] pytest group green (315)  
- [x] `final_demo_smoke.py` PASS (4/4)  
- [x] `npm run lint` / `npm run build` pass  
- [ ] Manual scenario 4 + `/details 1` once on CLI (presenter dry-run)  
- [x] No changes to model files, raw/processed datasets, or `TARGET_WEIGHTS` in SPRINT-4

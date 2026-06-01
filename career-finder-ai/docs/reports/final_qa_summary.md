# CareerFinder.ai — Final QA Summary

Submission-ready quality assurance summary for the implemented system. No scoring, ranking, parser, dataset, or model artifact changes were made for this document.

---

## Test status

### Backend (`pytest`)

**Command** (from `career-finder-ai/`):

```bash
python -m pytest -q
```

**Expected:** Full test suite passes (parser, recommender, scoring, regression training, CLI ML commands, input robustness, assistant replies, role inference, recommendation explanations).

### Frontend

**Commands** (from `career-finder-ai/frontend/`):

```bash
npm run lint
npm run build
```

**Notes:** Use a full `npm install` (not `--omit=dev`) so Playwright types resolve during production build.

### Demo smoke

**Command** (from `career-finder-ai/`):

```bash
python scripts/final_demo_smoke.py
```

**Checks:** Role-unknown guidance, ambiguous SQL input, location flexibility, canonical cybersecurity COOP demo with rubric scores and `/details` formatting.

### Terminal CLI

**Command:**

```bash
python scripts/careerfinder_cli.py
```

Use the canonical demo message documented in `docs/reports/final_demo_script.md`.

---

## Frontend build status

- **Lint:** ESLint clean on the Next.js App Router frontend.
- **Build:** Production build succeeds (static routes for home, chat, search, methodology, model, auth stubs).

---

## Backend integration status

- **FastAPI** serves `/health`, `/stats`, `/parse`, `/recommend`.
- **Live ranking** uses the explainable rubric (`score_source=rubric` by default).
- **ML regression** is trained and evaluated offline; optional shadow `ml_score` does not reorder live results unless explicitly enabled for comparison.

---

## Known limitations

1. **Live ranking is rubric-based** — ML is for evaluation, metrics, and optional shadow comparison.
2. **Dataset coverage** — Curated spreadsheet; not an exhaustive Saudi market feed.
3. **Location matching** — Broad regions (e.g. national listings) may score as partial city matches.
4. **Interview fields** — May be `Not stated` when the source listing lacks detail.
5. **Generic program titles** — Fit uses enrichment and rubric signals, not exact job-title matching.
6. **No live scraping** — Opportunities and URLs come from the cleaned dataset.
7. **Auth is stub-only** — Login/signup UI without server-side accounts.

---

## Safe demo input

Use the **canonical message** in `docs/reports/final_demo_script.md` (computing student, Khobar, cybersecurity COOP, skills, work mode, interview preference). It is regression-tested and yields stable rubric ordering on the current dataset (typically Bank Albilad Cooperative Training Program near the top at ~86%).

**Short vignettes:** guided discovery (“I don't know what role I want”), SQL ambiguity (“I know SQL”), location flexibility (Khobar + Riyadh/Jeddah), `/details 1`, `/reset`, `/help`.

---

## What to state in presentation

- Rule-based parser + rubric ranking + supervised regression **evaluation**.
- Explainable scores and honest limitations (location partial credit, interview unknowns).
- Do **not** claim external LLM/API integration, guaranteed placement, or that ML alone drives live ranking.

---

## Supporting reports

| Report | Purpose |
|--------|---------|
| `ml_results_summary.md` | ML training and evaluation overview |
| `model_metrics_summary.md` | Fair vs rubric-assisted metrics |
| `rubric_vs_ml_comparison.md` | Live rubric vs ML score comparison |
| `example_recommendations.md` | Sample ranked outputs |
| `final_demo_script.md` | Step-by-step demo walkthrough |
| `score_audit.md` | Rubric breakdown audit for a canonical profile |

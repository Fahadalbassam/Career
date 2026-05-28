# FINAL-DEMO-LOCK-1 — Final demo script (CareerFinder.ai)

Use this script for the course presentation, live demo, and final report walkthrough.

---

## 1. Project explanation (one paragraph)

**CareerFinder.ai** is a hybrid AI recommender for **Saudi COOP and internship opportunities** aimed at **computing students** (CS, AI, CYS, CIS, DS, DE, CE, FinTech). Students describe themselves in plain language; a rule-based parser builds a structured profile; the system ranks verified opportunities from a curated dataset. **Live ranking uses a transparent rubric** (`match_score` / `score_source=rubric`) with per-component breakdown, matched skills, missing skills, and reasons. A **fair ML regression model** was trained and evaluated for the ML course requirement; optional **ML shadow scoring** can be enabled but **does not replace** live ranking because top-5 overlap with the rubric is only ~36%. **Scores are conservative and explainable** (typical strong matches land in the low–mid 80s). **Recommendations do not guarantee acceptance.**

---

## 2. Exact demo input

Paste this into the **terminal CLI** (`npm run run:terminal` or `python scripts/careerfinder_cli.py`) or the **web chat** at `/chat`:

```
I am a CS student in Khobar looking for cybersecurity COOP. I know SQL, MongoDB, Linux, networking, and SIEM. I prefer on-site and I want an interview. I want to work in Security Operations.
```

---

## 3. Expected parsed profile

| Field | Expected value |
|---|---|
| Major | CS |
| City | Khobar |
| Interest | Cybersecurity |
| Program type | COOP |
| Work mode | On-site |
| Skills | sql, mongodb, linux, networking, cybersecurity, siem |
| Preferred roles | Security Operations |
| Interview preference | Interview preferred |

---

## 4. Expected top recommendation behavior

- **At least five** recommendations returned (`total_candidates` ≈ 173).
- Sorted by **`match_score` descending** (not ML).
- Typical top row: **Bank Albilad — Cooperative Training Program — 86%** (Cybersecurity cluster).
- Next rows often **84%** (SFDA, Al Rajhi Takaful, NHC) then **82%** — order may vary slightly by dataset but scores stay sorted.
- `score_source=rubric`; ML shadow off by default (`ML score: not available` in `/details 1`).

---

## 5. How to explain the 86% score

The score is a **match score between the student profile and each opportunity**, not profile completeness.

For **Bank Albilad #1 (~86%)**, say:

1. **Location (50% of location component):** listing city is broad **Saudi Arabia**, not Khobar — partial credit only.
2. **Skill fit (~60%):** student has strong cyber stack, but the posting is a **generic bank COOP** enriched with backend + cyber requirements; tokens like **mongodb** may not appear in posting text; **siem** counts at inferred-preferred weight.
3. **Role/interest (100%):** Cybersecurity interest and Security Operations preference align with inferred cluster.
4. **Interview (55%):** student wants an interview; posting says **Not stated** — partial credit, not full.
5. **Not a bug:** 86% is **conservative and explainable**, not artificially capped.

**Live audit:** `python scripts/debug_score_breakdown.py` prints the component table. See `docs/reports/score_audit.md`.

---

## 6. How to explain rubric vs ML

| Topic | What to say |
|---|---|
| Live ranking | **Rubric `match_score` is primary** — deterministic, explainable, powers `/recommend` and CLI. |
| ML regression | Trained on profile–opportunity pairs to **predict** rubric `target_score` (course requirement). Best fair model: `fair_gradient_boosting` (MAE ≈ 5.8, R² ≈ 0.65). |
| Shadow score | Optional `ml_score` when `CAREERFINDER_ENABLE_ML_SCORE=true`; **sorting unchanged**. |
| Why not ML-only? | Top-5 overlap rubric vs ML ≈ **0.36** on hold-out; correlation is moderate but lists diverge — not safe to replace rubric yet. |
| Rubric-assisted track | **Leakage demo only** (near-perfect metrics) — do not report as honest performance. |

CLI: `/model`, `/shadow`, `/metrics`, `/ml`. Reports: `docs/reports/rubric_vs_ml_comparison.md`, `docs/reports/ml_results_summary.md`.

---

## 7. Professor Q&A

### Is this ML or just filtering?

**Both, by design.** Parsing and filtering narrow candidates; **ranking is a weighted rubric** (major, skills, role, location, program, work mode, verification, interview). **ML regression** was trained/evaluated separately; it can shadow-score but **does not drive** default ranking.

### Why not use ML directly for live ranking?

- ML was trained to predict the **same rubric label**, not hire outcomes.
- Hold-out **top-5 overlap ~36%** — ML would reorder the shortlist unpredictably.
- Rubric gives **score_breakdown** and stable demo copy; required for explainability in the report.

### Why are scores in the 80s?

The score measures **fit to a specific listing**, not “how complete” the student profile is. Broad location, generic COOP titles, partial skill overlap, and unstated interview policy **intentionally** keep strong matches in the **low–mid 80s**. Scores are **conservative and explainable**.

### What did the model learn?

The fair model uses **text + categoricals** (no rubric components) to approximate rubric `target_score`. It captures broad patterns (cyber vs software, COOP vs internship) but with **MAE ~5.8** and limited top-5 agreement.

### What are the limitations?

- Curated dataset; not all Saudi employers.
- Rubric labels, not real acceptance data.
- No guarantee of placement; **recommendations do not guarantee acceptance**.
- Auth, recruiter portal, and full search are **out of scope** for this deliverable.
- Optional LLM layer not required for the demo.

---

## 8. `/details 1` checklist (terminal or API)

After the demo message, run **`/details 1`** and confirm:

- [ ] **Score breakdown** (major, location, program, work mode, role, skill, source, interview)
- [ ] **Matched skills** (e.g. cybersecurity)
- [ ] **Missing skills** — legitimate gaps (e.g. python, apis, git, soc) — **not** `cybersecurity fundamentals` when student already has `cybersecurity`
- [ ] **Why recommended** bullets
- [ ] **Score source:** rubric
- [ ] Verified **source URL**

---

## 9. Backup plan if frontend fails

1. **Terminal CLI:** `npm run run:terminal` (starts backend if needed) → guest → paste demo input → `/details 1`.
2. **Score breakdown script:** `python scripts/debug_score_breakdown.py` (no server required).
3. **Report files:** `docs/reports/score_audit.md`, `docs/reports/final_qa_sweep.md`, `docs/reports/rubric_vs_ml_comparison.md`, `docs/reports/ml_results_summary.md`.
4. **CLI capture:** `docs/reports/final_demo_lock_capture.txt` (FINAL-DEMO-LOCK-1 run).

---

## 10. Quick commands

```bash
# Backend (if not already running)
cd career-finder-ai/backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal demo
cd career-finder-ai
python scripts/careerfinder_cli.py

# Audit script (no HTTP)
python scripts/debug_score_breakdown.py

# Tests (FINAL-DEMO-LOCK-1)
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py tests/test_assistant_reply.py tests/test_cli_ml_commands.py -q
cd frontend && npm run lint && npm run build
```

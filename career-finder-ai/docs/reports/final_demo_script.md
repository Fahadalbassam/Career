# SPRINT-4 — Final demo script (CareerFinder.ai)

Presentation-ready walkthrough for terminal CLI, optional web chat, and professor Q&A.

---

## How to start the stack

### 1. Backend (from repository root `career-finder-ai/`)

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend
```

Open API docs: http://127.0.0.1:8000/docs

### 2. Terminal CLI (second terminal, same repo root)

```bash
python scripts/careerfinder_cli.py
```

At the prompt, choose **guest** (or press Enter if guest is default). Commands accumulate profile across turns like the web chat.

### 3. Frontend (optional, third terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000/chat

**Install note:** Use a **full** `npm install` (not `--omit=dev`). Next.js type-checks `playwright.config.ts` during `npm run build`; `@playwright/test` is a devDependency.

**PowerShell:** If `npm` scripts are blocked, use `npm.cmd` (e.g. `npm.cmd run dev`, `npm.cmd run build`).

**HOTFIX-4.1 — Terminal header and input guards**

- Startup shows a **compact** banner (`CareerFinder ● ai`), not the wide ASCII logo.
- If you run `python scripts/careerfinder_cli.py` without the backend, the CLI exits early with the uvicorn command (`--app-dir backend`). `npm run run:terminal` still auto-starts the API.
- Safe to type `hey` or `ehy` during a live demo — you get a short assistant prompt only (no empty profile, no “Scanned 173…”, no weak Top 5).
- `I don't know what role I want` and `I know SQL` show **role guidance** until enough profile signal exists.

**HOTFIX-4.2 — Interview preference + API skills**

- After the main profile turn, say `interview preference would be in person` — compact profile shows **Interview pref.** (`Interview preferred: In person`); assistant should **not** repeat “Tell me your interview preference.”
- Say `i know API` — skills include **`apis`**; `/details 1` should not list `api` / `apis` / REST API variants as missing when you already stated API knowledge.
- Work mode vs interview: `I want my COOP to be onsite or hybrid` sets work mode only; interview phrases stay separate.

### 4. Automated smoke (no manual typing)

```bash
python scripts/final_demo_smoke.py
```

---

## Demo scenario 1 — Guided discovery

**Input:**

```
I don't know what role I want
```

**Expected:**

- Assistant shows **role-direction choices** (Analyst, Engineer/Developer, Security/Operations, Infrastructure/Cloud, AI/Data Science).
- No forced single role family; discovery mode guided question (numbered options).
- Recommendations may be empty or generic until the student adds major/skills — that is correct.

---

## Demo scenario 2 — Ambiguous skill

**Input:**

```
I know SQL
```

**Expected:**

- Assistant does **not** force one role (e.g. “you are a Data Engineer”).
- One **clarifying question** (interest, tools, or type of work).
- Role-family inference stays **ambiguous** until more signal is added.

---

## Demo scenario 3 — Location flexibility

**Input:**

```
I'm in Khobar but I don't mind going to Riyadh or Jeddah for COOP
```

**Expected:**

- **Khobar** recognized as home/city.
- **Riyadh** and **Jeddah** in acceptable (or preferred) locations.
- `location_flexibility` = flexible (or moderate).
- Profile card / `/profile` shows flexibility fields when using CLI.

---

## Demo scenario 4 — Full recommendation (canonical demo)

**Input:**

```
I am a CS student in Khobar looking for cybersecurity COOP. I know SQL, MongoDB, Linux, networking, and SIEM. I prefer on-site and I want an interview. I want to work in Security Operations.
```

**Expected parsed profile (summary):**

| Field | Value |
|-------|--------|
| Major | CS |
| City / home | Khobar |
| Interest | Cybersecurity |
| Program | COOP |
| Work mode | On-site |
| Skills | sql, mongodb, linux, networking, cybersecurity, siem |
| Preferred roles | Security Operations |
| Interview | Interview preferred |

**Expected ranking:**

- At least **five** recommendations, sorted by **`match_score` descending**.
- **`score_source=rubric`** on every row (ML shadow off by default).
- Typical **#1:** **Bank Albilad — Cooperative Training Program — ~86%** (Cybersecurity cluster). Exact order may vary slightly by dataset; scores stay sorted.
- Scores are **conservative** (strong fits often low–mid 80s), not inflated.

---

## Demo scenario 5 — Details view

**Command:**

```
/details 1
```

**Expected sections:**

- Basic info (company, title, city, program, work mode, source URL)
- Why matched (bullets)
- Score breakdown (qualitative components)
- Matched skills
- Missing / recommended skills (no false gaps for skills the student already has)
- Next best action (concrete, not “add more technical skills”)
- **Score source: rubric**
- Honest notes when location is broad (**Saudi Arabia** ≠ exact Khobar) or interview is **Not stated**

---

## Demo scenario 6 — Reset demo

**Command:**

```
/reset
```

**Expected:**

- Branded logo/header shown again.
- Session cleared: no accumulated messages, profile, or last recommendations.
- Welcome / home messaging.

(`/home` behaves the same as `/reset`. `/clear` only clears the screen — session kept.)

---

## Talking points (presentation)

1. **Rubric score is live ranking** — `match_score` and sort order come from the transparent rubric (`score_source=rubric`).
2. **ML model is evaluated / shadow scoring** — fair gradient boosting trained for the course; optional `CAREERFINDER_ENABLE_ML_SCORE=true` attaches `ml_score` without changing sort order.
3. **Score is conservative and explainable** — ~86% reflects partial location, generic COOP titles, and unstated interview policy; `/details 1` and `scripts/debug_score_breakdown.py` show why.
4. **Broad Saudi Arabia location is not exact Khobar** — location component gives partial credit; say this aloud when showing Bank Albilad city field.
5. **Interview not stated is handled honestly** — student may want an interview; posting may say **Not stated** → partial interview score, honest copy in details.
6. **No opportunity details are invented** — requirements and URLs come from the curated dataset; assistant does not guarantee placement or certificates.

**CLI extras for Q&A:** `/model`, `/shadow`, `/metrics`, `/ml` (read processed ML artifacts).

---

## Professor Q&A (short)

| Question | Answer |
|----------|--------|
| ML or rules? | **Hybrid:** parser + rubric rank live; ML predicts rubric label for evaluation/shadow. |
| Why not ML-only ranking? | Hold-out top-5 overlap rubric vs ML ≈ **36%**; rubric gives breakdown and stable demo. |
| Why 80s not 99%? | Fit to **this listing**, not profile completeness. |
| Limitations? | Curated dataset, no hire-outcome labels, no auth/search/recruiter, no live scraping. |

---

## Backup if frontend fails

1. Terminal CLI only: backend + `python scripts/careerfinder_cli.py` → scenarios above.
2. `python scripts/final_demo_smoke.py` — deterministic PASS/FAIL.
3. `python scripts/debug_score_breakdown.py` — component table for Bank Albilad scenario.
4. Reports: `docs/reports/final_qa_lock.md`, `docs/reports/score_audit.md`, `docs/reports/rubric_vs_ml_comparison.md`.
5. Capture: `docs/reports/final_demo_lock_capture.txt` (prior lock run).

---

## Verification commands (SPRINT-4 lock)

```bash
cd career-finder-ai
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py \
  tests/test_assistant_reply.py tests/test_cli_ml_commands.py tests/test_scoring.py \
  tests/test_role_inference.py tests/test_recommendation_explanation.py -q
python scripts/final_demo_smoke.py
cd frontend
npm run lint
npm run build
```

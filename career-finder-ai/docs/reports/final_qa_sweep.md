# FINAL-QA-1 — Final robustness and recommendation quality sweep

**Date/time:** 2026-05-28 (local run, ~18:40–19:00)

**Scope:** End-to-end functionality, input robustness, recommendation quality, Playwright, frontend build, terminal CLI, optional ML shadow score. No ranking logic changes. No model retraining.

---

## Commands run

| Step | Command | Result |
|---|---|---|
| Backend robustness + core | `python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_cli_ml_commands.py tests/test_input_robustness.py -q` | **185 passed** (~21s) |
| Quality sweep report | `python scripts/recommendation_quality_sweep.py` | Report written (8 Pass, 2 Review, 0 Fail) |
| Playwright | `cd frontend && npm run test:e2e` | **11 / 11 passed** (~32s) |
| Playwright headed | `npx playwright test e2e/smoke.spec.ts --headed --project=chromium` | **11 / 11 passed** (~21s) |
| Frontend lint | `cd frontend && npm run lint` | **Pass** |
| Frontend build | `cd frontend && npm run build` | **Pass** |
| Manual `/recommend` | `POST http://127.0.0.1:8000/recommend` (cybersecurity Khobar COOP message) | **200 OK** — `major=CS`, `city=Khobar`, 5 recs, `score_source=rubric`, sorted by `match_score` desc |
| ML shadow | `CAREERFINDER_ENABLE_ML_SCORE=true` + `recommend_from_message(...)` | `ml_score=51`, `ml_score_source=fair_gradient_boosting`, `score_source=rubric`, ranking by `match_score` (82% top); flag unset after check |
| Terminal demo | Piped CLI: guest → `/metrics` → `/model` → `/shadow` → `n` → vague → complete → `/details 1` → `/exit` | **Pass** (see notes) |

---

## Backend tests

- **New file:** `tests/test_input_robustness.py` (50 tests)
- **Total FINAL-QA-1 backend run:** 185 passed
- Covers: accidental/tiny input, vague input, partial profiles, four strong complete profiles, contradictory/messy input, CLI `is_accidental_input` guard, rubric contract (`score_source`, sorted `match_score`, score bounds)

---

## Playwright

- Extended `frontend/e2e/smoke.spec.ts` with **chat input robustness** describe block (3 tests)
- Full suite: **11 passed** (8 original smoke + 3 robustness)
- Headed Chromium run: **passed** (same 11 tests)

---

## Frontend lint / build

- `npm run lint` — no errors
- `npm run build` — Next.js production build succeeded (11 static routes)

---

## Terminal demo

- **`n`:** accidental-input guard — no `/recommend` call
- **`I need internship`:** asks for major; low ~44% scores; program type `Internship` parsed
- **Complete cybersecurity Khobar COOP:** `major=CS`, `city=Khobar`, skills listed; top ~82%; `/details 1` shows rubric breakdown and missing skills
- **`/metrics`, `/model`, `/shadow`:** printed fair model metrics, shadow disabled by default on server, rubric-vs-ML summary
- **Capture:** `docs/reports/final_terminal_demo_capture.txt` (optional local artifact)

---

## ML shadow check

With `CAREERFINDER_ENABLE_ML_SCORE=true` (Python direct call, not server env):

| Check | Result |
|---|---|
| `ml_score` present | Yes (all 5 opportunities scored) |
| `ml_score_source` | `fair_gradient_boosting` |
| `score_source` | `rubric` |
| Ranking | By `match_score` descending (82% top, not ML 51%) |
| ML replaces `match_score` | No |

Flag unset after test so default demo remains rubric-only.

---

## Input robustness scenarios (backend tests)

| Group | Verdict | Notes |
|---|---|---|
| Accidental (`n`, `y`, `.`, `ok`) | **Pass** | No crash; incomplete profile; no fake >85% top score for single-char |
| Vague internship / coop / help | **Pass** | Missing major/city/skills; program type may parse |
| Partial (CS, Riyadh, Python, cyber interest) | **Pass** | Extracts present fields only |
| Strong complete (4 profiles) | **Pass** | Fields parsed; top match relevant; rubric sorted |
| Contradictory / messy | **Pass** | No crash; dual-city picks one city; cyber phrase can override explicit CS major |

---

## Recommendation quality sweep

**Report:** `docs/reports/final_recommendation_quality_sweep.md`

| Verdict | Count |
|---|---|
| Pass | 8 |
| Review | 2 |
| Fail | 0 |

**Review items (documented, not fixed in this pass):**

1. **Software/backend complete profile** — top match title is generic COOP/IT trainee rather than explicit “software engineer” wording (dataset/ranking specificity, not a crash).
2. **Contradictory interests** — parser sets `major=CYS` when message also says `CS` and mixed AI/cyber interests (`parser.py` keyword precedence).

---

## Bugs found

None blocking presentation. No code fixes required for crashes or ranking corruption.

---

## Fixes made (this pass)

| File | Change |
|---|---|
| `tests/test_input_robustness.py` | **New** — robustness test suite |
| `scripts/recommendation_quality_sweep.py` | **New** — generates quality table report |
| `frontend/e2e/smoke.spec.ts` | **Extended** — 3 chat robustness tests |
| `docs/reports/final_recommendation_quality_sweep.md` | **Generated** |
| `docs/reports/final_qa_sweep.md` | **This report** |
| `docs/tracking/*` | Updated for FINAL-QA-1 |

**No changes** to `parser.py`, `rubric.py`, `recommender.py`, or frontend UI components beyond Playwright tests.

---

## Known issues (carry to report / future work)

1. **Parser:** Explicit “my major is CS” can lose to earlier “cyber security” phrase (`major=CYS`). Document in methodology/limitations.
2. **Parser:** “data science student” + “machine learning” may set `major=AI` while `interest=Data Science` (acceptable but worth noting).
3. **Software COOP ranking:** Strong JS/React profile can surface generic IT/COOP titles at top — Review, not Fail.
4. **Phase 4 tracker (T-013):** Dedicated `confidence.ts` follow-up module still pending; `buildAssistantReply` in chat already asks for missing fields.
5. **ML shadow in terminal `/details`:** Shows “not available” unless backend process started with `CAREERFINDER_ENABLE_ML_SCORE=true`.

---

## Final verdict

**Ready for course presentation / final report**

The system works end-to-end (web chat, API, terminal CLI), handles weak and accidental input without crashing, asks for missing information in chat/CLI, returns reasonable recommendations for strong profiles, keeps rubric as the live ranker with optional ML shadow, and passes automated backend + Playwright + lint/build checks.

**Remaining work for presentation (non-blocking):**

- Slide deck / demo script using the cybersecurity Khobar COOP walkthrough
- Reference `docs/reports/final_recommendation_quality_sweep.md` and `docs/PROJECT_TECHNICAL_GUIDE.md` in the written report
- Optional: enable `CAREERFINDER_ENABLE_ML_SCORE=true` on backend during live demo to show shadow scores in `/details`
- Optional: complete T-013/T-014/T-015 if course rubric requires search page or dedicated confidence module

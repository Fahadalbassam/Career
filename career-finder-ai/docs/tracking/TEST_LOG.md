# TEST_LOG

What has been verified, how, and what is still pending. This file should be updated after every test run. **Never claim a test passed unless it was actually executed.**

---

## Known prior test runs

These reflect what is recorded in prior conversations and audit notes. They were **not re-run as part of creating this document.**

- **Backend parser / scoring / recommender / regression-dataset tests previously reported as passing.** Recorded result: **125 / 125** under `career-finder-ai/tests/` covering `test_parser.py`, `test_scoring.py`, `test_recommender.py`, `test_regression_dataset.py`.
- **Model-training tests require additional environment dependencies** such as `joblib` and `python-dotenv`. They have not been verified in this branch and may fail without those installed.

The above bullets are an inherited claim and must be re-verified before being treated as authoritative again. See "Future test commands" below for the exact commands.

---

## Tests run during the Phase 0 documentation pass

**None.** Phase 0 created Markdown files only. No application code was modified, no formatters were run, no test suite was executed.

---

## Pending verification (Phase 1 onwards)

| Phase | Test | Command | Expected outcome |
|---|---|---|---|
| 1 | Backend CORS preflight | `curl -i -X OPTIONS http://localhost:8000/recommend -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: POST"` | Response contains `Access-Control-Allow-Origin: http://localhost:3000` |
| 1 | Backend `/recommend` happy path | `curl -i -X POST http://localhost:8000/recommend -H "Content-Type: application/json" -d '{"message":"AI student in Riyadh COOP"}'` | 200 OK with a non-empty `recommendations` array containing `match_score` |
| 1 | Frontend network round-trip | Manual: open `/chat`, send a message, inspect DevTools → Network | `POST /recommend` returns 200 with the expected JSON shape |
| 2 | Adapter unit tests | TBD — `npm test` once Vitest/Jest is set up | `toRecommendation`, `toCareerFitMemory`, `toStudentProfile` produce stable output against a fixture |
| 3 | Visual smoke of Fit Shelf | Manual: send progressively richer messages and confirm shelves repopulate per the progressive-reveal table | 0 → 1 → 3 → 4 → 6 cards as required fields fill |
| 4 | Follow-up question logic | Manual scripted conversation per `ROADMAP.md` Phase 4 | One focused question per missing required field; recommendations only emit when profile is complete |
| 5 | Multi-turn profile merge | Frontend unit test for `mergeParsedProfiles` | Two-turn `["I am a CYS student", "in Dammam, Linux, Python"]` produces the same result as the concatenated single-turn message |
| 6 | `/opportunities/search` filter combinations | Backend `pytest` for the new endpoint | Each filter narrows the result set; `verified_only=true` excludes opportunities with empty `source_url`; `min_match_score` is respected |

---

## Future test commands (placeholders)

```bash
# Backend, from career-finder-ai/
pytest tests -q

# Backend with verbose output and specific module
pytest tests/test_recommender.py -vv

# Backend, model-training tests (require joblib, python-dotenv)
pytest tests/test_regression_training.py tests/test_fair_regression_training.py

# Frontend (once a test runner is installed)
cd frontend
npm test
npm run lint
npm run build
```

When any of these commands is actually executed, record the result here with the date, the command, and the pass / fail summary. Do not record runs that did not happen.

---

## 2026-05-28 — ML-2A taxonomy + parser/rubric verification

| Suite | Command | Result | Notes |
|---|---|---|---|
| Parser | `pytest tests/test_parser.py -x --tb=short` | **67 passed** | Includes 18 new ML-2A tests covering `alkhobar` / `al khobar` / `al-khobar` / `jedda` / `ad dammam` city aliases, `security focused` / `cyber security` / `dev ops` / `cloud infrastructure` interest detection, the CS-student-with-security-focus override case, `pen testing` / `k8s` / `dev ops` / `infosec` / `ci cd` skill aliases, security-skill persistence, explicit-role-keeps-priority over cluster fallback, and Cloud / DevOps cluster role seeding. |
| Recommender | `pytest tests/test_recommender.py -x --tb=short` | **34 passed** | Includes 4 new ML-2A tests: cybersecurity-interest outscores generic-software opportunity (cluster match), Cloud / DevOps interest matches a cloud opportunity via cluster keywords, partial match (≈0.6) when only `skills_list` contains a cluster keyword, and end-to-end `recommend_from_message` with `alkhobar` → `Khobar` and `city_match_score == 1.0` against a fixture Khobar opportunity. |
| Regression dataset | `pytest tests/test_regression_dataset.py -x --tb=short` | **9 passed** | Synthetic-profile builder and rubric column shape unchanged; existing scoring formula still produces `target_score=100` for a fully-aligned profile/opportunity pair. |
| Scoring | `pytest tests/test_scoring.py --tb=short` | **39 passed** | Untouched but rerun to confirm `compute_role_interest_score` cluster pass does not regress any prior rubric scenarios. |
| All non-training | `pytest tests/ --ignore=tests/test_regression_training.py --ignore=tests/test_fair_regression_training.py --tb=short` | **149 passed** | Aggregate run across parser / recommender / scoring / regression-dataset. Model-training tests still excluded (require `joblib`, `python-dotenv` and run for tens of minutes). |

**Manual CLI smoke test.** Backend booted via `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` after clearing `backend/app/__pycache__/` to ensure the new `taxonomy.py` is imported. Inputs piped to `python scripts/careerfinder_cli.py`:

1. `I am a CS student in alkhobar looking for security focused opportunities` → parsed `Major: CS`, `City: Khobar`, `Interest: Cybersecurity`, `Preferred roles: Cybersecurity, SOC Analyst, Network Security, Penetration Testing`. Assistant follow-up correctly asked for technical skills.
2. `I know Linux, networking, Docker, and penetration testing` → skills persisted as `docker, linux, networking, penetration testing`. Top-5 recommendations leaned security/networking (Help AG Cybersecurity Internship 67 %, Cisco NetVersity 65 %, InnovationTeam Java Microservices 62 %, TrendAI CyberGATE 61 %, SFDA COOP 59 %) with matched-skill chips for `networking`, `penetration testing`, and `docker`.

No frontend UI, auth, database, or recommender response-contract changes were made or required.

---

## 2026-05-28 — ML-2B practical recommender hardening verification

| Suite | Command | Result | Notes |
|---|---|---|---|
| Parser | `python -m pytest tests/test_parser.py -q` | **70 passed** | Includes 3 new ML-2B regression tests: `security focused` still maps to `Cybersecurity`; `alkhobar` still normalises to `Khobar`; `"I want role in DevOps"` parses to `interest=Cloud / DevOps`, `devops` skill, `Cloud / DevOps` preferred role. |
| Recommender | `python -m pytest tests/test_recommender.py -q` | **39 passed** | Includes 5 new ML-2B tests: telecom opp gets inferred network / security / cloud signals; enrichment respects existing `role_cluster`; security profile outscores generic software via inferred signals; DevOps profile scores cloud opp above data opp; inferred skills (weight 0.5) do not overpower explicit skills (weight 1.0). |
| Regression dataset | `python -m pytest tests/test_regression_dataset.py -q` | **9 passed** | Synthetic-profile builder and rubric column shape unchanged. Existing fully-aligned profile/opportunity pair still scores `target_score=100`. |
| Scoring | `python -m pytest tests/test_scoring.py -q` | **39 passed** | Unchanged. Rerun to confirm the new inferred-skill weighting and inferred-interest 0.5 fallback do not regress any prior rubric scenarios. |
| All non-training | `python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_regression_dataset.py tests/test_scoring.py -q` | **157 passed** | Aggregate run across parser / recommender / scoring / regression-dataset. |

**Manual CLI walkthrough.** Backend booted via `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Inputs piped to `python scripts/careerfinder_cli.py`:

1. `N` → CLI printed `"That looks accidental. Type a full message, /help, /details 1, or /exit."` — no `/recommend` call.
2. `/n` → same accidental-input message — no `/recommend` call.
3. `im a cs student in alkhobar, and im looking for security focused opportunities.` → parsed `Major: CS`, `City: Khobar`, `Interest: Cybersecurity`. Top-1: Cisco NetVersity (Saudi Networking Academy) — 70 %.
4. `I know SQL` → `Skills: sql` added. Score-change note: `"New skills added: sql."`. Top-1 shifted to InnovationTeam Java Microservices Intern — 76 %.
5. `I want role in DevOps` → `Skills: sql, devops`. Top-1 shifted to Bosch Software Development — 69 %, Tabby Intern DevOps Engineer appeared at #2 (66 %). Score-change notes: `"Note: Your top score dropped because the new details made the search more specific."` and `"New skills added: devops."`.
6. `/history` → printed three numbered real messages (no `N` or `/n` was remembered).
7. `/undo` → removed `"I want role in DevOps"`, silently reran with the two remaining messages, restored the prior top-5 (InnovationTeam 76 %, HungerStation 74 %, Tabby Backend 72 %, Bank Albilad 69 %, Laverne 68 %).
8. `/exit` → clean shutdown.

**What was NOT verified.** Frontend UI, auth, database persistence, search page, model training — none changed in ML-2B.

---

## 2026-05-28 — ML-2B.1 required vs preferred skill enrichment verification

| Suite | Command | Result | Notes |
|---|---|---|---|
| Parser | `python -m pytest tests/test_parser.py -q` | **70 passed** | Unchanged from ML-2B; rerun to confirm parser is unaffected by the new enrichment fields. |
| Recommender | `python -m pytest tests/test_recommender.py -q` | **48 passed** | Includes 9 new ML-2B.1 tests: Cybersecurity / Cloud / DevOps profile shape, enrichment carries required/preferred for cyber opps, title-only fallback for `"Cloud Engineer COOP"`, required-weighted-higher-than-preferred-only, explicit-skill-still-beats-required-inferred, missing-skills ordered required→preferred, missing lists exclude student skills, `recommend()` populates `missing_required_skills` and `missing_preferred_skills`. |
| Regression dataset | `python -m pytest tests/test_regression_dataset.py -q` | **9 passed** | Unchanged. `TARGET_WEIGHTS` and `compute_target_score` formula identical, so the supervised dataset shape is preserved. |
| Scoring | `python -m pytest tests/test_scoring.py -q` | **39 passed** | Unchanged. Rerun to confirm the new 0.7 / 0.4 inferred weights inside `compute_skill_match_score` do not regress any prior rubric scenarios. |
| All non-training | `python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_regression_dataset.py tests/test_scoring.py -q` | **166 passed** | Aggregate run. |

**Manual CLI walkthrough (Part F).** Backend booted via `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Inputs piped to `python scripts/careerfinder_cli.py`:

1. `"im a cs student in alkhobar looking for security focused opportunities"` → parsed `Major: CS, City: Khobar, Interest: Cybersecurity`. Top-5: Cisco NetVersity 70 %, Saudi FDA 67 %, Bank Albilad 67 %, NHC 67 %, Deloitte 64 %. Compact `Missing` column already shows required-leaning gaps (`networking, linux, security fundamentals`) on the cyber-leaning opportunities.
2. `"I know Linux and networking"` → skills `[linux, networking]`. **Scores moved logically:** Cisco NetVersity 70→79, Deloitte 64→74, Schneider Electric joins at 74, Saudi FDA 67→73, Bank Albilad 67→73. CLI prints `"New skills added: linux, networking."`. Deloitte `/details 2` Missing skills line reads `security fundamentals, cybersecurity fundamentals, firewall, siem, incident response, network monitoring, soc, penetration testing` — required (security fundamentals, cybersecurity fundamentals) appear **before** preferred (firewall, siem, …). 8-item cap honored.
3. `"I know penetration testing too"` → skills `[linux, networking, penetration testing]`. Top-5: Cisco 75 %, **Help AG Cybersecurity Intern 73 %** (newly into top), Saudi FDA 71 %, Bank Albilad 71 %, NHC 71 %. Help AG `/details 2` Missing skills: `security fundamentals, cybersecurity fundamentals, firewall, siem, incident response, network monitoring, soc, vulnerability assessment` — `penetration testing` correctly absent (student now has it), required-before-preferred ordering preserved, matched skills include `networking, penetration testing`.

**Expected behaviour confirmed.** A user who provides more "required-for-role" skills sees logical score gains and a smaller / more actionable missing-skills list. Preferred-only matches still contribute (0.4 weight) but cannot dominate.

**What was NOT verified.** Frontend UI, auth, database persistence, search page, model training — none changed in ML-2B.1.

## 2026-05-28 — ML-2C enriched dataset metadata pass and split inspection

| Suite | Command | Result | Notes |
|---|---|---|---|
| Regression dataset | python -m pytest tests/test_regression_dataset.py -q | **16 passed** | 7 new ML-2C tests added: enriched builder creates CSV, enriched output has required columns, regression dataset includes enriched columns, split inspection creates output files, no profile_id overlap, ratio ~80/20, summary JSON has expected keys. |
| Recommender | python -m pytest tests/test_recommender.py -q | **48 passed** | Unchanged from ML-2B.1. |
| Parser | python -m pytest tests/test_parser.py -q | **70 passed** | Unchanged. |
| Scoring | python -m pytest tests/test_scoring.py -q | **39 passed** | Unchanged. |
| All non-training | python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_regression_dataset.py tests/test_scoring.py -q | **173 passed** | Aggregate run. |

**Split inspection results.** 
egression_split_summary.json confirmed:
- overlapping_profile_ids: []
- 	rain_ratio: ≈ 0.80
- 	est_ratio: ≈ 0.20
- split_method: GroupShuffleSplit

**What was NOT verified.** Frontend UI, auth, database persistence, search page, model training — none changed in ML-2C.

---

## 2026-05-28 — ML-3 Regression model training (fair + rubric-assisted)

| Suite | Command | Result | Notes |
|---|---|---|---|
| Fair regression training | `pytest tests/test_fair_regression_training.py -v` | **22 passed** | New tests: leakage guard (4 tests), feature building (5 tests), metrics helpers (3 tests), output path names (2 tests), integration tests on small fixture (6 tests), compare_regression_models unit tests (2 tests). |
| Rubric-assisted regression training | `pytest tests/test_regression_training.py -v` | **9 passed** | Updated: path assertions changed to `rubric_assisted_*` names; `TRACK_LABEL` assertion added. |
| Regression dataset | `pytest tests/test_regression_dataset.py -v` | **16 passed** | Unchanged from ML-2C. |
| All three suites | `pytest tests/test_fair_regression_training.py tests/test_regression_training.py tests/test_regression_dataset.py -v` | **47 passed** | Aggregate run. |

**Training scripts executed.**

```
python -m app.train_fair_regression_model
python -m app.train_regression_model
python -m app.compare_regression_models
```

All three completed without error.

**Artifacts verified (all present):**

| Artifact | Status |
|---|---|
| models/fair_ridge_model.joblib | OK |
| models/fair_random_forest_model.joblib | OK |
| models/fair_gradient_boosting_model.joblib | OK |
| models/rubric_assisted_ridge_model.joblib | OK |
| models/rubric_assisted_random_forest_model.joblib | OK |
| models/rubric_assisted_gradient_boosting_model.joblib | OK |
| data/processed/fair_regression_model_metrics.csv | OK |
| data/processed/fair_regression_predictions.csv | OK |
| data/processed/rubric_assisted_regression_model_metrics.csv | OK |
| data/processed/rubric_assisted_regression_predictions.csv | OK |
| data/processed/model_metrics_report.csv | OK |
| docs/reports/model_metrics_summary.md | OK |
| reports/figures/fair_regression_prediction_vs_actual.png | OK |

**Metrics summary.**

Fair models (leakage-safe):

| Model | MAE | RMSE | R² | P@5 |
|---|---|---|---|---|
| fair_gradient_boosting | 5.834 | 7.265 | 0.648 | 0.240 |
| fair_random_forest | 7.374 | 9.048 | 0.454 | 0.220 |
| fair_ridge | 10.311 | 12.186 | 0.009 | 0.180 |

Rubric-assisted (leakage demo — NOT the honest result):

| Model | MAE | RMSE | R² | P@5 | leakage_safe |
|---|---|---|---|---|---|
| rubric_assisted_ridge | 0.023 | 0.028 | 1.000 | 0.240 | False |
| rubric_assisted_gradient_boosting | 0.630 | 0.909 | 0.994 | 0.240 | False |
| rubric_assisted_random_forest | 1.918 | 3.093 | 0.936 | 0.240 | False |

**Split (from regression_split_summary.json):** train=6,574 rows / 38 profiles, test=1,730 rows / 10 profiles, GroupShuffleSplit by profile_id, no overlap.

**What was NOT verified.** Frontend UI, auth, database persistence, search page, `/recommend` live scoring — none changed in ML-3. Models not integrated into live API.

---

## ML-4 — Error analysis and report examples (2026-05-28)

**Command (from `career-finder-ai/`):**

```bash
cd backend
python -m app.analyze_model_errors
python -m app.generate_recommendation_examples
pytest tests/test_model_error_analysis.py -q
pytest tests/test_fair_regression_training.py -q
pytest tests/test_regression_dataset.py -q
```

**Result:** All commands succeeded.

| Suite | Result |
|---|---|
| `tests/test_model_error_analysis.py` | 6 / 6 passed |
| `tests/test_fair_regression_training.py` | 22 / 22 passed |
| `tests/test_regression_dataset.py` | 16 / 16 passed |
| **Total** | **44 / 44 passed** |

**Artifacts verified.**

| File | OK |
|---|---|
| `data/processed/fair_model_error_analysis.csv` | Yes |
| `data/processed/fair_model_worst_predictions.csv` | Yes |
| `data/processed/fair_model_best_predictions.csv` | Yes |
| `data/processed/fair_model_profile_error_summary.csv` | Yes |
| `data/processed/fair_model_error_summary.json` | Yes |
| `data/processed/report_recommendation_examples.csv` | Yes |
| `docs/reports/example_recommendations.md` | Yes |
| `docs/reports/ml_results_summary.md` | Yes |

**Error analysis summary (`fair_gradient_boosting`, test split):** mean AE 5.834, median AE 5.280, worst AE 25.709, best AE 0.001, 10 profiles, 1,730 test rows.

**Examples:** 8 profiles, 40 CSV rows (top-5 per profile), markdown report generated.

**What was NOT verified.** Live `/recommend` integration, frontend, auth, search. No model retraining.

---

## ML-5 — Rubric vs ML score comparison (2026-05-28)

**Command (from `career-finder-ai/`):**

```bash
cd backend
python -m app.compare_rubric_vs_ml
pytest tests/test_rubric_vs_ml_comparison.py -q
pytest tests/test_model_error_analysis.py -q
pytest tests/test_fair_regression_training.py -q
```

**Result:** All commands succeeded.

| Suite | Result |
|---|---|
| `tests/test_rubric_vs_ml_comparison.py` | 3 / 3 passed |
| `tests/test_model_error_analysis.py` | 6 / 6 passed |
| `tests/test_fair_regression_training.py` | 22 / 22 passed |
| **Total** | **31 / 31 passed** |

**Comparison summary (`fair_gradient_boosting`, 1,730 test rows, 10 profiles):**

| Metric | Value |
|---|---|
| Mean absolute difference | 5.834 |
| Median absolute difference | 5.280 |
| Max absolute difference | 25.709 |
| Pearson correlation | 0.833 |
| Spearman correlation | 0.784 |
| Average top-5 overlap | 0.360 |

**Artifacts:** `rubric_vs_ml_comparison.csv`, `rubric_vs_ml_largest_disagreements.csv`, `rubric_vs_ml_profile_overlap.csv`, `rubric_vs_ml_summary.json`, `docs/reports/rubric_vs_ml_comparison.md`.

**Recommendation recorded:** Keep rubric as primary live score; use ML as secondary/shadow score first — do not replace ranking yet.

**What was NOT verified.** `/recommend` shadow field, frontend, auth, search.

---

## ML-6 — Optional ML shadow score (2026-05-28)

**Commands (from `career-finder-ai/`):**

```bash
cd backend
pytest tests/test_recommender.py -q
pytest tests/test_fair_regression_training.py -q
pytest tests/test_rubric_vs_ml_comparison.py -q
```

**Result:** All suites passed.

| Suite | Result |
|---|---|
| `tests/test_recommender.py` | 57 / 57 passed (9 new ML-6 tests) |
| `tests/test_fair_regression_training.py` | 22 / 22 passed |
| `tests/test_rubric_vs_ml_comparison.py` | 3 / 3 passed |
| **Total** | **82 / 82 passed** |

**ML-6 test coverage:**

| Test | Description |
|---|---|
| `test_ml6_disabled_by_default_score_source_is_rubric` | Flag unset → score_source="rubric", ml_score=None |
| `test_ml6_disabled_ranking_still_by_match_score` | Flag unset → ranking still by rubric match_score |
| `test_ml6_disabled_no_model_load` | Flag unset → recommend succeeds, no model load exception |
| `test_ml6_enabled_attaches_ml_score` | Flag true + monkeypatched predictor → ml_score attached, ml_score_source set |
| `test_ml6_enabled_ranking_still_by_rubric_match_score` | Flag true → ranking follows rubric, not ML score |
| `test_ml6_enabled_score_source_always_rubric` | Flag true → score_source always "rubric" |
| `test_ml6_predictor_raises_recommend_still_succeeds` | Predictor raises → /recommend still returns rubric results |
| `test_ml6_predictor_returns_none_values` | Predictor returns None → ml_score and ml_score_source are None |
| `test_ml6_schema_backward_compat_existing_fields_still_present` | Existing fields (match_score, score, score_breakdown) unaffected |
| `test_ml6_opportunity_schema_has_new_fields` | Schema defaults: score_source="rubric", ml_score=None, ml_score_source=None |

**Feature flag behaviour:**

- `CAREERFINDER_ENABLE_ML_SCORE` unset or `false` → `/recommend` behaves as before ML-6; no model loaded.
- `CAREERFINDER_ENABLE_ML_SCORE=true` → `fair_gradient_boosting_model.joblib` lazy-loaded on first request; `ml_score`, `ml_score_source`, `score_source` attached; ranking unchanged.

**What was NOT verified.** Frontend UI, auth, search, model retraining. CLI display verified by code inspection only (not executed interactively).

---

## 2026-05-28 — ML-7 terminal model/metrics inspection commands

**Command:**

```bash
cd career-finder-ai
pytest tests/test_cli_ml_commands.py -q
```

**Result:** 8 / 8 passed.

| Test | Description |
|---|---|
| `test_metrics_includes_fair_best_model` | `/metrics` lines include fair_gradient_boosting + leakage warning |
| `test_metrics_missing_fair_file` | Missing CSV → guidance message + expected path |
| `test_model_status_disabled` | Flag unset → disabled + env hint |
| `test_model_status_enabled` | Flag true → enabled + sorting note |
| `test_shadow_summary` | Shadow lines include correlations + recommendation |
| `test_shadow_missing_file` | Missing JSON → safe message |
| `test_ml_summary_combines_status_and_fair` | `/ml` combines status + best fair model |
| `test_details_ml_score_not_available` | `/details` prints "not available" when ml_score is None |

**Manual CLI checks (piped):**

1. `/metrics` — fair `fair_gradient_boosting` metrics print; rubric-assisted section includes leakage warning.
2. `/model` — shows ML shadow enabled/disabled from env; states ranking unchanged.
3. `/shadow` — Pearson/Spearman/top-5 overlap from `rubric_vs_ml_summary.json`.
4. `/ml` — combined status + best fair MAE.
5. `/details 1` without ML flag — `ML score: not available`, `Score source: rubric`.

**What was NOT verified.** Interactive `npm run run:terminal` with live backend + `CAREERFINDER_ENABLE_ML_SCORE=true` end-to-end (acceptable per task; automated tests cover CLI logic).

---

## 2026-05-28 — CLEAN-1 low-risk repo housekeeping

**Commands:**

```bash
cd career-finder-ai
python -m pytest tests/test_cli_ml_commands.py tests/test_recommender.py -q
cd frontend && npm run lint
cd frontend && npm run build
```

**Result:** 66 / 66 passed (`test_cli_ml_commands.py` 8 + `test_recommender.py` 58). `npm run lint` — OK. `npm run build` — OK.

**Scope verified:** No application code changed; archived files not referenced by tests. Recommender and CLI ML command suites remain green.

**What was NOT changed.** Live ranking, UI, models, active processed datasets, test files.

---

## 2026-05-28 — QA-2 Playwright frontend smoke tests

**Setup (one-time per machine):**

```bash
cd career-finder-ai/frontend
npm install
npx playwright install chromium
```

**Commands:**

```bash
cd career-finder-ai/frontend
npm run lint
npm run build
npm run test:e2e
```

**Coverage:**

| Test | Route / behaviour |
|---|---|
| home page loads | `/` — CareerFinder.ai hero + CTA |
| chat page loads | `/chat` — composer placeholder |
| chat can submit a message | `/chat` — send profile message; expects user bubble, parsed profile, assistant text, or shelf/demo outcome |
| search page loads | `/search` — nav shell (page body intentionally minimal) |
| methodology page loads | `/methodology` — heading + snapshot |
| login page loads | `/login` — email/password form |
| signup page loads | `/signup` — signup form |
| no console errors on key pages | `/`, `/chat`, `/search`, `/methodology` — filters benign dev/HMR noise |

**Backend webServer:** Yes — `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` with health check `http://127.0.0.1:8000/health`.

**Result:** 8 / 8 passed (`npm run test:e2e`, ~15s with dual webServer). `npm run lint` — OK. `npm run build` — OK.

**Flaky area fixed:** Chat submit initially matched hidden Fit Shelf demo text containing "COOP"; assertions now scoped to `main` with `expect().toPass()`. Login/signup use visible text (CardTitle is not a heading role).

---

## DOC-1 — Technical guide created (2026-05-28)

**What changed:** `docs/PROJECT_TECHNICAL_GUIDE.md` created. Tracking docs updated. No application code changed.

**Tests run:** No tests were re-run for DOC-1 (documentation only). All prior test results remain valid.

**What to run to verify the project is clean:**

```bash
# Backend
cd career-finder-ai
python -m pytest tests/test_cli_ml_commands.py tests/test_recommender.py -q

# Frontend
cd career-finder-ai/frontend
npm run lint
npm run build
```

---

## FINAL-QA-1 — Robustness and recommendation quality sweep (2026-05-28)

**What changed:** `tests/test_input_robustness.py` (new), `scripts/recommendation_quality_sweep.py` (new), `frontend/e2e/smoke.spec.ts` (+3 chat robustness tests), reports under `docs/reports/`.

### Backend

```bash
cd career-finder-ai
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_cli_ml_commands.py tests/test_input_robustness.py -q
```

**Result:** **185 passed** in ~21s.

### Recommendation quality sweep

```bash
cd career-finder-ai
python scripts/recommendation_quality_sweep.py
```

**Result:** `docs/reports/final_recommendation_quality_sweep.md` — **8 Pass, 2 Review, 0 Fail**.

### Playwright

```bash
cd career-finder-ai/frontend
npm run test:e2e
npx playwright test e2e/smoke.spec.ts --headed --project=chromium
```

**Result:** **11 / 11 passed** (headless ~32s; headed ~21s).

**New e2e tests:**

| Test | Behaviour |
|---|---|
| handles accidental tiny input | `/chat` + `n` — no crash; assistant/profile prompt visible |
| handles vague internship input | `I need internship` — assistant or parsed profile |
| handles complete cybersecurity Khobar COOP | full message — recommendation/profile/shelf signal |

### Frontend production

```bash
cd career-finder-ai/frontend
npm run lint
npm run build
```

**Result:** both **passed**.

### Manual `/recommend` + ML shadow

- `POST /recommend` with cybersecurity Khobar COOP message → 200, `major=CS`, `city=Khobar`, sorted rubric scores.
- `CAREERFINDER_ENABLE_ML_SCORE=true` (direct Python): `ml_score` present, `score_source=rubric`, ranking unchanged.

### Terminal CLI (piped demo)

Guest → `/metrics` → `/model` → `/shadow` → accidental `n` → vague → complete profile → `/details 1` → `/exit`.

**Result:** accidental ignored; vague asks for major; complete profile returns ~82% top matches; no crash.

---

## 2026-05-29 — FINAL-POLISH-1

```bash
cd career-finder-ai
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py tests/test_assistant_reply.py tests/test_cli_ml_commands.py -q
```

**Result:** **196 passed** in ~22s.

```bash
cd frontend
npm run lint
npm run build
npm run test:e2e
```

**Result:** lint pass (0 errors); build pass; e2e pass (run after implementation).

**Parser manual check (combined terminal conversation):** `parse_message` on six-turn Khobar cybersecurity script → `mongodb` in skills, `interview_preference=Interview preferred`, `work_mode=On-site`, `Security Operations` in `preferred_roles`.

---

## 2026-05-29 — SCORE-AUDIT-1

```bash
cd career-finder-ai
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py tests/test_assistant_reply.py tests/test_cli_ml_commands.py -q
python scripts/debug_score_breakdown.py
cd frontend
npm run lint
npm run build
```

**Result:** **202 passed** in ~24s. Debug script: rank #1 Bank Albilad **86%**; missing skills no longer include fundamentals when `cybersecurity` is on profile. Lint pass; build pass.

**New tests:** `test_score_audit_*` in `test_recommender.py`; `test_assistant_uses_concrete_missing_skills_*` in `test_assistant_reply.py`.

---

## 2026-05-29 — FINAL-DEMO-LOCK-1

```bash
cd career-finder-ai
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py tests/test_assistant_reply.py tests/test_cli_ml_commands.py -q
python scripts/debug_score_breakdown.py
# Terminal demo (backend on :8000)
python scripts/careerfinder_cli.py  # piped: guest → demo message → /details 1 → /exit
cd frontend
npm run lint
npm run build
```

**Result:** **202 passed** in ~23s. Debug script: Bank Albilad **86%** rank #1; missing skills exclude fundamentals when `cybersecurity` present. Terminal capture: `docs/reports/final_demo_lock_capture.txt` — profile + top 5 (86/84/84/84/82) + `/details 1` with score breakdown. Lint pass; build pass.

**E2E:** Not re-run in this lock pass (optional; prior FINAL-QA-1: 11/11 passed).

---

## 2026-05-31 — SPRINT-1

```bash
cd career-finder-ai/backend
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py \
  tests/test_assistant_reply.py tests/test_cli_ml_commands.py tests/test_scoring.py -q
cd ../frontend
npm run lint
npm run build
```

**Result:** **254 passed** in ~34s. Lint pass (0 errors). Build fails TypeScript check: `playwright.config.ts` cannot resolve `@playwright/test` (devDependency not installed in this environment; pre-existing).

**New/updated tests:** SPRINT-1 location parser cases in `test_parser.py`; location scoring ordering in `test_scoring.py`; CLI help/reset/home/clear smoke in `test_cli_ml_commands.py`.

---

## 2026-05-31 — SPRINT-1.1 (frontend build fix)

```bash
cd career-finder-ai/frontend
npm install
npm run lint
npm run build
cd ../backend
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py \
  tests/test_assistant_reply.py tests/test_cli_ml_commands.py tests/test_scoring.py -q
```

**Result:** `npm install` added missing dev packages (including `@playwright/test`). **Lint pass.** **Build pass** (Next.js 16.2.4, TypeScript check includes `playwright.config.ts` successfully). **254 pytest passed** in ~14s.

**Note:** `@playwright/test` was already in `package.json` / `package-lock.json`; no manifest edits required. Use full `npm install` (not `--omit=dev`) before `npm run build`.

---

## 2026-05-31 — SPRINT-2

```bash
cd career-finder-ai
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py \
  tests/test_assistant_reply.py tests/test_cli_ml_commands.py tests/test_scoring.py \
  tests/test_role_inference.py -q
cd frontend
npm run lint
npm run build
```

**Result:** **301 passed** in ~15s. Lint pass. Build pass (Next.js 16.2.4).

**New tests:** `tests/test_role_inference.py` — SQL ambiguity, role stacks (Power BI, Airflow, full stack, cyber ops, cloud/devops), game-dev + security transition, discovery mode, assistant one-question rule, `match_score` / `score_source=rubric` integrity.

**Confirmation:** No ML retrain. No dataset changes. Ranking remains rubric-based.

---

## 2026-05-31 — SPRINT-3

```bash
cd career-finder-ai/backend
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py \
  tests/test_assistant_reply.py tests/test_cli_ml_commands.py tests/test_scoring.py \
  tests/test_role_inference.py tests/test_recommendation_explanation.py -q
cd ../frontend
npm run lint
npm run build
```

**Result:** **315 passed** in ~19s. Lint pass. Build pass (Next.js 16.2.4).

**New tests:** `tests/test_recommendation_explanation.py` — `/details` sections, missing-skill alias cleanup (cybersecurity, SIEM, Power BI, Node.js), next-best-action concreteness, broad location honesty, interview not stated, role-family evidence, sort/score integrity.

**Manual CLI:** guest → cyber Khobar COOP demo → `/details 1` — Bank Albilad 86%, broad location + interview not stated, concrete missing skills, structured breakdown.

**Confirmation:** No ML retrain. No dataset changes. Ranking rubric-based. Scores not artificially raised.

---

## 2026-05-31 — SPRINT-4

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

**Result:** **315 passed** in ~22s. `final_demo_smoke.py` → **PASS (4/4)** — Bank Albilad **86%** #1, `score_source=rubric`. `npm run lint` pass; `npm run build` pass (Next.js 16.2.4).

**New automation:** `scripts/final_demo_smoke.py` — discovery, SQL ambiguity, location flexibility, full demo rubric/sort/details/missing-skills checks.

**Docs:** `docs/reports/final_demo_script.md`, `docs/reports/final_qa_lock.md`.

**Confirmation:** No ML retrain. No dataset changes. No rubric weight changes. Ranking `score_source=rubric`.

---

## 2026-06-01 — HOTFIX-4.1

```bash
cd career-finder-ai
python -m pytest tests/test_cli_ml_commands.py tests/test_parser.py tests/test_recommender.py \
  tests/test_assistant_reply.py tests/test_recommendation_explanation.py tests/test_role_inference.py \
  tests/test_input_robustness.py tests/test_input_intent.py -q
python scripts/final_demo_smoke.py
cd frontend
npm run lint
npm run build
```

**New tests:** `tests/test_input_intent.py` — compact header (no ASCII logo), greeting/noise detection, gating on `/recommend`, full demo still recommends, backend-unavailable message includes `--app-dir backend`.

**Manual CLI:** `hey` / `ehy` → assistant prompt only (no Scanned / Top 5); `I know SQL` and `I don't know what role I want` → guidance without weak Top 5; full cyber Khobar COOP demo → Bank Albilad ~86%, `score_source=rubric`.

**Confirmation:** No ML retrain. No dataset/rubric/scoring/taxonomy changes.

---

## 2026-06-01 — HOTFIX-4.2

```bash
cd career-finder-ai
python -m pytest tests/test_parser.py tests/test_cli_ml_commands.py tests/test_assistant_reply.py \
  tests/test_recommender.py tests/test_recommendation_explanation.py tests/test_input_intent.py \
  tests/test_input_robustness.py -q
python scripts/final_demo_smoke.py
cd frontend
npm run lint
npm run build
```

**New/updated tests:** `tests/test_parser.py` — HOTFIX-4.2 interview phrases, COOP onsite/hybrid vs interview, API/`REST APIs` → `apis`, multi-turn merge; `tests/test_assistant_reply.py` — no interview prompt when preference set, dry-run rubric sort, API missing-skill alias coverage.

**Manual CLI:** Full Khobar security/devops profile → follow-up `interview preference would be in person` shows interview pref. and assistant stops asking; `i know API` adds `apis` and clears API alias from missing skills on `/details 1`.

**Confirmation:** No ML retrain. No dataset/rubric-weight/ranking changes.

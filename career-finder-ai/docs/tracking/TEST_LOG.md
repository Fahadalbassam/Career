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

# FINAL-DEMO-AUDIT-1 — Post SCORE-AUDIT-2 demo verification

**Date:** 2026-06-02  
**Scope:** Demo-focused audit on the canonical cybersecurity COOP message. No new features, ML retrain, rubric weight changes, or UI redesign.

---

## Demo input

```text
I am a CS student in Khobar looking for cybersecurity COOP. I know SQL, MongoDB, Linux, networking, and SIEM. I prefer on-site and I want an interview. I want to work in Security Operations.
```

---

## Parsed profile

| Field | Value |
|---|---|
| Major | CS |
| City | Khobar |
| Interest | Cybersecurity |
| Program type | COOP |
| Work mode | On-site |
| Preferred roles | Security Operations |
| Interview preference | Interview preferred |
| Skills | sql, linux, networking, cybersecurity, siem, mongodb |

Interview preference is stored separately from work mode (`work_mode=On-site`, `interview_preference=Interview preferred`).

---

## Top 5 results (rubric ranking)

| Rank | Score | Company | Program (short) | Location | Work mode | Interview |
|---:|---:|---|---|---|---|---|
| 1 | 84% | Saudi Food & Drug Authority (SFDA) | COOP training (2025–2026 intake) | Saudi Arabia | In person | Not stated |
| 2 | 84% | Bank Albilad | Cooperative Training Program | Saudi Arabia | In person | Not stated |
| 3 | 84% | NHC | COOP Trainee | Saudi Arabia | In person | Not stated |
| 4 | 79% | Bank Albilad | Cooperative and Summer Training Program | Riyadh | In person | Not stated |
| 5 | 79% | Banque Saudi Fransi (BSF) | COOP Training | Riyadh | In person | Not stated |

Recommendations are sorted by `match_score` descending. All scores are in **0–100** with `score_source=rubric`.

---

## Why the top score is ~84% (correct, not inflated)

Weighted rubric on the #1 opportunity (SFDA):

| Component | Score | Weight | Contribution |
|---|---:|---:|---:|
| Major fit | 1.00 | 35% | 35.0 |
| Skill match | 0.50 | 20% | 10.0 |
| Role/interest | 1.00 | 15% | 15.0 |
| City/location | 0.50 | 10% | 5.0 |
| Program type | 1.00 | 10% | 10.0 |
| Work mode | 1.00 | 5% | 5.0 |
| Verification | 1.00 | 3% | 3.0 |
| Interview | 0.55 | 2% | 1.1 |
| **Total** | | | **~84.1 → 84%** |

**Positive factors:** strong major, role/interest, program type, work mode, verified source.

**Limiting factors (shown in `/details`):**

- Partial skill overlap (1 matched, 7 SOC/security gaps such as ITIL, soc, incident response).
- Broad location (`Saudi Arabia` vs student `Khobar`), not an exact city match.
- Interview requirements **not stated** on the source — preference is scored neutrally, not as a confirmed interview match.

After SCORE-AUDIT-2, the headline score dropped from ~90% to ~84% because skill scoring is opportunity-centric (no dilution from extra student tokens) and location/skill gaps are reflected honestly.

---

## Interview preference behavior

| Check | Result |
|---|---|
| Parser keeps interview separate from work mode | Pass (`test_parse_interview_in_person_sets_preference_not_work_mode`, demo message) |
| Interview scored on `interview_score`, work mode on `work_mode_score` | Pass (distinct breakdown keys) |
| `interview_required=Not stated` not presented as interview match | Pass — `/details` says source does not state interview requirements; limiting-factor text clarifies neutral scoring |
| Explanation copy | Pass — no “interview match” when requirement is Not stated |

---

## Missing skills behavior

| Check | Result |
|---|---|
| Owned skills not listed as missing | Pass (sql, linux, networking, siem, mongodb, cybersecurity excluded) |
| Cyber SOC stack prioritized | Pass — ITIL, soc, penetration testing, incident response, vulnerability assessment, firewall, network monitoring |
| Backend noise suppressed | Pass — python, apis, git not in missing list for this profile |

---

## UI / CLI wording changes

| Area | Change |
|---|---|
| CLI compact table header | `City` → **`Location`** (values may be Saudi Arabia, Multiple, Remote, or city names; internal city matching unchanged) |
| `/details` | New **Why this score** section with positive and limiting factors |
| Assistant | Uses concrete missing skills via `build_next_best_action` (e.g. “Strengthen ITIL, soc, penetration testing…”) |

No frontend layout redesign; recommendation card still uses “City” for expanded cards (profile card “City” is the student’s home city).

---

## Tests run

```bash
cd backend
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py tests/test_assistant_reply.py tests/test_cli_ml_commands.py tests/test_recommendation_explanation.py -q
```

**Result:** 246 passed, 4 skipped (2026-06-02).

```bash
cd frontend
npm run lint
npm run build
```

**Result:** lint clean; Next.js build succeeded (2026-06-02).

---

## Files touched

- `backend/app/recommendation_explanation.py` — score summary, interview fit wording
- `scripts/careerfinder_cli.py` — compact column label
- `tests/test_recommendation_explanation.py`, `tests/test_recommender.py`, `tests/test_cli_ml_commands.py`
- `docs/reports/final_demo_audit.md`, `docs/tracking/CHANGE_LOG.md`, `docs/tracking/TEST_LOG.md`

# Sprint 2 — Role-family intelligence, skill taxonomy, and guided questioning

**Date:** 2026-05-31  
**Scope:** Smarter role-direction guidance for Saudi COOP/internship students. No ML retrain, no dataset edits, no ranking overhaul.

---

## What changed

| Area | Files | Summary |
|------|-------|---------|
| Role taxonomy | `backend/app/role_families.py` (new) | 14 role families with keywords, skill tiers, interests, majors, explanations, guided questions |
| Role inference | `backend/app/role_inference.py` (new) | `infer_role_families()`, discovery mode, transition paths, `format_role_directions()` |
| Assistant / CLI | `backend/app/assistant_reply.py`, `scripts/careerfinder_cli.py` | At most one clarifying question; role directions in assistant block; discovery when user says "idk" |
| Parser skills | `backend/app/parser.py`, `backend/app/taxonomy.py` | Unity, Unreal, Airflow, game-development interest aliases |
| Recommendations | `backend/app/recommender.py` | Optional transparent `Role-family match: …` reason line only (no score change) |
| Tests | `tests/test_role_inference.py` (new) | Sprint-2 inference, assistant, and score-integrity cases |
| Docs | This file, `docs/tracking/*` | Sprint report and tracker updates |

**Not changed:** `TARGET_WEIGHTS`, ML model artifacts, raw/processed dataset files, frontend UI design, auth/search/recruiter features.

---

## Role family taxonomy (14 families)

1. Software Engineering  
2. Backend Engineering  
3. Frontend Engineering  
4. Full Stack Development  
5. Data Analysis  
6. Data Engineering  
7. Data Science / Machine Learning  
8. Cybersecurity Operations  
9. Security Engineering  
10. Cloud / DevOps / Infrastructure  
11. QA / Testing  
12. Business / Systems Analysis  
13. Game Development  
14. Product / Technical Coordination  

Each family in `role_families.py` defines:

- **keywords** — text overlap signals  
- **foundational_skills** — weak alone (e.g. SQL, Python, Git)  
- **differentiating_skills** — medium signal (e.g. React, Node, Power BI)  
- **signature_skills** — strong signal (e.g. SIEM, Airflow, Unity)  
- **related_interests**, **related_majors**, **role_titles**  
- **explanation** — one sentence for the student  
- **suggested_questions** — used when the profile is ambiguous  

---

## Skill categories and weights

Inference uses tiered weights (no single broad skill dominates):

| Category | Weight | Meaning |
|----------|--------|---------|
| Foundational | 0.15 | Useful across roles; SQL alone does not pick one family |
| Differentiating | 0.35 | Separates similar roles (e.g. React vs Power BI) |
| Signature | 0.55 | Strong role signal (e.g. SIEM, Airflow, Unity) |

Interest alignment (+0.5), preferred role (+0.2–0.3), and major (+0.12) add context. Confidence is capped at 1.0. Families below 0.10 are omitted; at most five are returned.

---

## How ambiguous skills are handled

- **One foundational skill (SQL):** Multiple families may appear with low confidence; no family should exceed ~0.35 from SQL alone. A suggested clarifying question is offered.  
- **Clear stacks:** Differentiating + signature skills raise the top family (see examples below).  
- **Skill vs interest conflict:** `current_strength_family` and `target_interest_family` are set; `transition_paths` and one conflict question (strengths vs target direction).  
- **Discovery:** Phrases like "idk", "I don't know what role I want", or an empty signal set trigger guided discovery with five work-type choices.  
- **Recommendations:** Still returned when mandatory profile fields exist; guidance does not block ranking.

---

## Examples

### SQL alone

**Input:** skills `["sql"]`  
**Behavior:** Broad possible directions; top confidence stays low; no forced single role.

### SQL + Power BI + dashboards

**Input:** skills `["sql", "power bi", "excel"]`, interest aligned with data/reporting  
**Behavior:** **Data Analysis** rises to the top.

### SQL + Python + Airflow + pipelines

**Input:** skills `["sql", "python", "airflow"]` (+ pipeline phrasing in message)  
**Behavior:** **Data Engineering** on top.

### SQL + Node.js + React + APIs

**Input:** skills `["sql", "node", "react"]`  
**Behavior:** **Full Stack Development** and/or **Backend Engineering** lead.

### SIEM + Linux + networking + cybersecurity interest

**Input:** security operations skills + Cybersecurity interest  
**Behavior:** **Cybersecurity Operations** on top with evidence (SIEM, Linux, networking).

### Docker + Kubernetes + CI/CD + AWS

**Input:** `["docker", "kubernetes", "cicd", "aws"]`  
**Behavior:** **Cloud / DevOps / Infrastructure** on top.

### Security interest + Unity / game development

**Input:** skills `["unity", "c++", "c#"]`, interest **Cybersecurity**  
**Behavior:** Strength → Game Development; interest → security family; transition paths listed; guided question asks strengths vs target — not a fake high cyber match from Unity alone.

### "I don't know what role I want"

**Input:** message contains discovery phrase  
**Behavior:** `discovery_mode=True`; five-choice guided question; assistant headline uses that guidance (recommendations not blocked once profile is complete).

---

## Terminal / assistant display

When the profile is complete enough for recommendations, the assistant block may include:

```
Possible role directions:
  1. Data Analysis — 72%
     Evidence: sql, power bi, Data Science interest
  ...
Recommended next question:
  "Do you prefer analyzing information, building systems, ..."
```

Discovery and conflict cases follow the rules in Parts C and D of the sprint spec (one question per reply).

---

## Recommendation integration (Part E)

- Ranking remains **`match_score` 0–100**, sorted descending.  
- **`score_source`** remains **`rubric`**.  
- **`_role_family_reason()`** may append a reason such as `Role-family match: Data Analysis (72% confidence)` when opportunity text overlaps the top inferred family — **display only**, no weight change.

---

## Tests run

From `career-finder-ai/`:

```bash
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py \
  tests/test_assistant_reply.py tests/test_cli_ml_commands.py tests/test_scoring.py \
  tests/test_role_inference.py -q
```

**Result:** **301 passed** (~15s).

```bash
cd frontend
npm run lint
npm run build
```

**Result:** lint pass; build pass (Next.js 16.2.4).

---

## Known limitations

- Role inference is **rule-based**, not trained on hiring outcomes; confidence is heuristic, not calibrated probability.  
- Opportunity `role_cluster` in the dataset may not align with all 14 family names — reason lines only appear when keywords overlap.  
- Frontend chat uses the same backend paths but was **not redesigned** in this sprint; terminal and `assistant_reply` are the primary surfaces for role-direction copy.  
- Arabic / mixed-language discovery phrases are only covered where listed in `DISCOVERY_PHRASES`.  
- Very sparse profiles still depend on mandatory-field prompts (major, skills, city, program type, work mode) before strong recommendations.

---

## Confirmation

| Item | Status |
|------|--------|
| ML model retrained | **No** |
| Dataset files changed | **No** |
| `TARGET_WEIGHTS` changed | **No** |
| Live ranking | **Rubric-based `match_score`** |
| Scores artificially raised | **No** |

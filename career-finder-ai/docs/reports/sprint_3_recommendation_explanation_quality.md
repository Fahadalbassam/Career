# SPRINT-3 — Recommendation explanation quality

## What changed

### New module: `backend/app/recommendation_explanation.py`

Centralizes human-readable explanation formatting for:

- `/details` terminal sections (basic info, why matched, score breakdown, skills, next best action)
- Assistant next-best-action copy (`build_next_best_action`)

### Terminal CLI (`scripts/careerfinder_cli.py`)

- `/details N` now renders six structured sections instead of a flat field dump.
- Passes the live session profile into details so location/interview wording reflects student context.

### Missing-skill cleanup (`backend/app/rubric.py`)

- Expanded alias coverage for missing-skills display only (no rubric weight changes):
  - `cybersecurity` ≈ `cyber security`, `security fundamentals`, `cybersecurity fundamentals`
  - `siem` ≈ `SIEM` (case)
  - `networking` ≈ `network security` (where listed as related)
  - `powerbi` ≈ `Power BI`
  - `nodejs` ≈ `Node.js`
  - `k8s` ≈ `Kubernetes`
- Uses compact token comparison (`powerbi`, `nodejs`) plus taxonomy `SKILL_ALIASES`.

### Assistant replies (`backend/app/assistant_reply.py`)

- Next-best-action uses concrete missing skills when available.
- Avoids generic “more technical skills” when the recommendation lists specific gaps.

### Recommendation reasons (`backend/app/recommender.py`)

- Softer, defensible language (“This appears to fit…”, “Skill overlap…”, broad/regional location notes).
- Does not change `match_score` or ranking.

## Before / after explanation behavior

| Area | Before | After |
|------|--------|-------|
| `/details` | Flat list of fields + one-line breakdown percentages | Structured sections: basic info → why matched → qualitative breakdown → skills → next action |
| Location copy | Often implied exact city match | Explicit: exact / regional / broad / not stated |
| Interview | Field only | Field + honest “source does not state interview requirements” when applicable |
| Missing skills | Some false positives (fundamentals when student has cybersecurity) | Alias-aware; user’s exact skills never listed as missing |
| Next best action | Generic skill-gap suggestions | Concrete: “Strengthen python, apis, git…” or location/interview/profile prompts |

## `/details` structure

1. **Basic opportunity info** — rank, company, program, match score, score source, ML shadow (if any), location, work mode, program type, interview status, source link, role cluster.
2. **Why this matched** — major/interest fit, role-family evidence (when present), skill overlap, location/program/work-mode honesty, source confidence.
3. **Score breakdown** — qualitative labels from existing `score_breakdown` (strong/partial/weak; exact/broad/not stated). No invented precision.
4. **Matched skills** — up to 8 from `skills_matched`.
5. **Missing / recommended skills** — from `missing_skills`, alias-filtered.
6. **Next best action** — context-specific guidance.

## Missing-skill cleanup rules

- If the user has the exact skill, it must not appear as missing.
- Normalize aliases via compact tokens + `_STUDENT_SKILL_SATISFIES` + taxonomy `SKILL_ALIASES`.
- Broader skills stay separate when genuinely different (e.g. `penetration testing` vs `networking`).
- Display-only — `TARGET_WEIGHTS` and `match_score` unchanged.

## Next-best-action rules

| Condition | Action text |
|-----------|-------------|
| Concrete `missing_skills` | “Strengthen X, Y, Z for this role direction.” |
| Broad/regional location vs student city | “Confirm whether this opportunity is available in your preferred city (Khobar).” |
| Interview not stated + user has preference | “Check the source link or /details 1 to confirm interview requirements.” |
| Missing profile fields | “Add your preferred role, city, or work mode to improve ranking.” |
| Source URL present, otherwise complete | “Review the source link and confirm application requirements.” |

## Example (demo input)

**Input:**

> I am a CS student in Khobar looking for cybersecurity COOP. I know SQL, MongoDB, Linux, networking, and SIEM. I prefer on-site and I want an interview. I want to work in Security Operations.

**Top match:** Bank Albilad Cooperative Training Program — **86%** (`score_source: rubric`)

**`/details 1` highlights:**

- Broad location match (Saudi Arabia vs Khobar) — not exact city.
- Interview status: Not stated — source does not state interview requirements.
- Matched skills: cybersecurity (plus rubric skill overlap from listing text).
- Missing: python, apis, git, soc, … (SIEM/Linux/networking not falsely listed).
- Next best action: Strengthen python, apis, git for this role direction.
- Role-family evidence appears in assistant block; score breakdown shows strong major/role, broad location, partial skills.

## Tests run

```bash
cd career-finder-ai/backend
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py \
  tests/test_assistant_reply.py tests/test_cli_ml_commands.py tests/test_scoring.py \
  tests/test_role_inference.py tests/test_recommendation_explanation.py -q
```

**Result:** 315 passed.

```bash
cd career-finder-ai/frontend
npm run lint    # pass
npm run build   # pass
```

**Manual CLI:** guest → demo cyber COOP message → `/details 1` — structured sections render correctly; broad location and interview honesty confirmed.

## Known limitations

- Location/program/work-mode labels derive from rubric component scores, not free-text parsing of postings.
- `skills_matched` still uses substring search in listing text; enrichment-layer required/preferred skills are reflected in missing lists and rubric scoring but not always in matched display.
- Role-family evidence depends on Sprint-2 inference confidence and keyword overlap with opportunity title/cluster.
- Frontend cards were not redesigned; API `why_recommended` wording is softer but shelf UI unchanged.

## Confirmation

- **ML not retrained**
- **Dataset files not changed**
- **Ranking remains rubric-based** (`match_score`, `score_source=rubric`)
- **Scores were not artificially raised** — explanation clarity only

# SCORE-AUDIT-2 — git/apis skill dilution on Bank Albilad COOP

**Date:** 2026-06-02  
**Scope:** Explain why adding `git` and `apis` lowered the top match from 90% to 89%, fix monotonic skill scoring, align missing skills with role-cluster priority. No rubric weight changes, no ML retrain, no UI redesign.

---

## Profiles compared

| Field | Value |
|---|---|
| Major | CS |
| University | IAU |
| City | Khobar |
| Interest | Cybersecurity |
| Program type | COOP |
| Work mode | On-site |
| Preferred roles | Security Operations |
| Interview preference | Interview preferred: In person |

| | Profile A (before) | Profile B (after) |
|---|---|---|
| Skills | sql, linux, networking, cybersecurity | + git, apis |

Reproduce: `python scripts/debug_score_breakdown.py`

---

## Top result before / after (pre-fix behavior)

| | Profile A | Profile B |
|---|---|---|
| Company | Bank Albilad | Bank Albilad |
| Program | Cooperative Training Program | Cooperative Training Program |
| Match % | **90** | **89** |
| Skill component | 0.775 | 0.750 |

---

## Exact reason the score dropped (bug)

**Root cause:** `compute_skill_match_score` used **student-token dilution**:

```text
skill_score = sum(per-student-token weights) / len(student_skill_tokens)
```

- Profile A: 4 tokens → weighted sum ≈ 3.1 → **0.775**
- Profile B: 6 tokens (adds git, apis) → weighted sum ≈ 4.5 → **0.750**

`git` and `apis` matched backend **required** skills from the bank bucket enrichment (weight 0.7 each), but the **denominator grew by 2**, so the average fell by 0.025. At 20% rubric weight that is **−0.5 points** on `target_score` (89.6 → 89.1 → displayed 90 → 89).

No other rubric component changed (role/interest, city, program, work mode, interview were identical).

**This was a bug:** adding skills that match the opportunity should not lower skill score (no explicit negative rule).

---

## What was fixed

| Area | Change |
|---|---|
| `backend/app/rubric.py` | Opportunity-centric skill score: `matched_weight / total_opportunity_weight`; extra student skills ignored |
| `backend/app/rubric.py` | Skill layers: explicit `skills_list` → interest-filtered role profiles → bucket inferred fallback |
| `backend/app/rubric.py` | `compute_missing_skills` uses same layering; backend profile skills filtered out for cyber-focused students |
| `backend/app/rubric.py` | Aliases for `git`, `api`/`apis` in missing-skills coverage |
| `backend/app/opportunity_enrichment.py` | `fired_role_skill_profile_keys()` for profile filtering |
| `backend/app/recommender.py` | `skills_matched` via `compute_profile_skills_matched()` |
| `scripts/debug_score_breakdown.py` | Side-by-side Profile A / B breakdown |
| `tests/test_recommender.py` | SCORE-AUDIT-2 regression tests |

**Rubric weights unchanged.**

---

## Results after fix

| | Profile A | Profile B |
|---|---|---|
| Match % | **84** | **84** |
| Skill component | 0.50 | 0.50 |
| Missing skills (top gaps) | ITIL, siem, soc, penetration testing, … | Same |

- **Monotonicity:** B skill score ≥ A (equal here); total score no longer drops when adding git/apis.
- **Skill score 0.50:** Bank Albilad declares explicit `skills_list`: `ITIL`, `Cybersecurity Fundamentals`. Student covers fundamentals via `cybersecurity` alias → **1 of 2** explicit skills → 50% skill component (by design, not capped).
- **Missing skills:** No longer lists `python`, `apis`, `git` for this cyber + Security Operations profile; prioritizes SOC stack gaps (siem, soc, incident response, …).

---

## Was a bug found?

**Yes** — student-token averaging caused non-monotonic skill scores when irrelevant or backend-bucket skills were added to the profile.

---

## Conclusion

The **90 → 89** drop in terminal testing was caused by **skill-score dilution**, not worse fit. After SCORE-AUDIT-2, adding git/apis does not reduce skill or total score for the same opportunity. Absolute match % for this listing is **84%** with the corrected explicit-skill scoring layer (conservative, explainable: broad location, generic COOP title, ITIL gap, interview not stated).

---

## Prior audit

See SCORE-AUDIT-1 section in git history for the complete SIEM/MongoDB terminal profile (`score_audit.md` previously covered SCORE-AUDIT-1 only).

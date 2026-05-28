# SCORE-AUDIT-1 — Cybersecurity COOP profile score audit

**Date:** 2026-05-29  
**Scope:** Explain 86% top match and validate `missing_skills` for a complete cybersecurity profile. No rubric weight changes, no ML retrain, no ranking changes.

---

## Test profile (exact terminal input)

```
I am a CS student in Khobar looking for cybersecurity COOP. I know SQL, MongoDB, Linux, networking, and SIEM. I prefer on-site and I want an interview. I want to work in Security Operations.
```

### Parsed profile

| Field | Value |
|---|---|
| Major | CS |
| City | Khobar |
| Interest | Cybersecurity |
| Program type | COOP |
| Work mode | On-site |
| Skills | sql, linux, networking, cybersecurity, siem, mongodb |
| Preferred roles | Security Operations |
| Interview preference | Interview preferred |

---

## Top 5 results (live rubric, `score_source=rubric`)

| Rank | Company | Title | Match % | City | Role cluster |
|---:|---|---|---:|---|---|
| 1 | Bank Albilad | Cooperative Training Program | **86** | Saudi Arabia | Cybersecurity |
| 2 | Saudi Food & Drug Authority (SFDA) | COOP training (First semester 2025-2026 intake) | 84 | Saudi Arabia | Cybersecurity |
| 3 | Al Rajhi Takaful | Cooperative Training Program | 84 | Riyadh | Cybersecurity |
| 4 | NHC | COOP Trainee | 84 | Saudi Arabia | Cybersecurity |
| 5 | (varies by dataset load) | … | 83–84 | … | … |

Reproduce: `python scripts/debug_score_breakdown.py`

---

## Why rank #1 is 86% (not 95+)

**Bank Albilad — Cooperative Training Program** → rubric `target_score` **86.1** → displayed **86%**.

| Component | Score (0–1) | Weight | Points |
|---|---:|---:|---:|
| Major fit | 1.00 | 35% | 35.00 |
| Skill fit | 0.60 | 20% | 12.00 |
| Role/interest fit | 1.00 | 15% | 15.00 |
| Location fit | 0.50 | 10% | 5.00 |
| Program fit | 1.00 | 10% | 10.00 |
| Work mode fit | 1.00 | 5% | 5.00 |
| Source confidence | 1.00 | 3% | 3.00 |
| Interview fit | 0.55 | 2% | 1.10 |
| **Total** | | | **86.10** |

### Explainable limitations (by design)

1. **Location (0.50):** Opportunity city is broad **Saudi Arabia**, not Khobar. `FLEXIBLE_CITIES` partial match applies; not a perfect city hit.
2. **Skill fit (0.60):** Student skills are strong, but the listing is a **generic bank COOP** enriched with Backend + Cybersecurity role profiles. Tokens such as **mongodb** do not appear in the opportunity text; **siem** only counts at the inferred-preferred weight (0.4) in the per-token average. Bank bucket also adds **python / apis / git** requirements unrelated to the student's stated stack.
3. **Role/interest (1.00):** Interest cluster and Security Operations preference align with inferred **Cybersecurity** cluster — full credit here.
4. **Interview (0.55):** Student wants an interview; listing text yields **Not stated** → partial credit (0.55), not 1.0.
5. **Title specificity:** Generic “Cooperative Training Program”, not an explicit SOC / Security Operations posting — role score is boosted by enrichment, not by an exact SOC title match.

The score is **conservative and explainable**; it is not artificially capped. A near-perfect score would require tighter city alignment, explicit SOC/security title language, stated interview policy, and higher explicit skill overlap on the posting.

---

## Missing skills — valid or bug?

### Before fix

`missing_skills` incorrectly listed **cybersecurity fundamentals** and **security fundamentals** even though the student lists **cybersecurity**. **siem**, **linux**, and **networking** were already excluded correctly.

### Root cause

`compute_missing_skills` used **exact** string equality against role-profile required skills. “cybersecurity” ≠ “cybersecurity fundamentals” / “security fundamentals”.

### Fix (display only)

Added `_student_covers_skill()` in `backend/app/rubric.py`:

- Exact match (unchanged)
- Alias map: `cybersecurity` → fundamentals / security fundamentals / infosec
- Prefix overlap for tokens ≥ 5 chars (e.g. `cybersecurity` in `cybersecurity fundamentals`)

**Rubric weights and `match_score` were not changed.**

### After fix (rank #1)

```
missing_skills: python, apis, git, soc, penetration testing, incident response, vulnerability assessment, firewall
```

These are **legitimate gaps** for a bank COOP enriched with backend + cyber profiles. They are not skills the student already listed.

| Student skill | Should satisfy | Result |
|---|---|---|
| cybersecurity | cybersecurity fundamentals, security fundamentals | Yes (fixed) |
| siem | siem | Yes (unchanged) |
| linux | linux | Yes (unchanged) |
| networking | networking | Yes (unchanged) |

---

## Changes made

| Area | Change |
|---|---|
| `backend/app/rubric.py` | `_student_covers_skill()` for missing-skills alias/prefix coverage |
| `backend/app/assistant_reply.py` | Use top `missing_skills`; concrete `/details 1` wording |
| `frontend/src/lib/assistant-reply.ts` | Mirror concrete missing-skill wording in chat |
| `scripts/debug_score_breakdown.py` | Audit script for this profile |
| `scripts/careerfinder_cli.py` | `/details` shows compact score breakdown |
| Tests | SCORE-AUDIT-1 cases in `test_recommender.py`, `test_assistant_reply.py` |

---

## Conclusion

**A bug was found and fixed** in `missing_skills` display (fundamentals shown despite `cybersecurity` on the profile).

**The 86% score is conservative/explainable, not artificially capped.** Main drags: broad location, generic COOP title, partial skill overlap against enriched backend+cyber requirements, and interview-not-stated.

---

## Demo / report recommendation

- Run `python scripts/debug_score_breakdown.py` live to show the component table.
- Use CLI `/details 1` to show breakdown + real missing skills (python, soc, …).
- State clearly: ranking remains `match_score` from rubric; `score_source=rubric`; no ML retrain.

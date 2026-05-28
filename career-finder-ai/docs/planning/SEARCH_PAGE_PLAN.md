# SEARCH_PAGE_PLAN

`/search` is a **manual, structured search** over the curated opportunity database. It is a separate surface from `/chat` but reuses the same animated composer, the same shelf rail, and the same `RecommendationCard` for results.

---

## What search is for

- COOP opportunities
- Internship opportunities
- Tamheer
- Training programs
- Companies (filter by company name)
- Cities in Saudi Arabia
- Majors (CS, AI, CYS, CIS, DS, DE, CE, FT)
- Role clusters (Software Engineering, Cybersecurity, Data Science, Data Engineering, ML Engineering, Cloud Engineering, …)
- Skills (Python, SQL, Linux, networking, AWS, …)
- Work mode (Remote, On-site, Hybrid)
- Interview status (Required / Not required / Not stated)
- Verified opportunities (those with a `source_url`)

---

## What search is *not* for (now)

- Not for **users** — no sign-up, no login, no profiles.
- Not for **ratings** — no stars, thumbs, reviews.
- Not for **recruiters** — no employer-facing posting form, no employer dashboard.
- Not for **accounts** — no saved-searches-on-server, no email digests.
- Not for **company reviews** — no glass-door-style content.
- Not for **salary disclosure** — no salary filter, no salary surfaces.

The search page is a deterministic filter over a static dataset. Anything beyond that is a later phase.

---

## Planned filters

All filters are optional. Combining filters narrows results. Submitting with no filters returns the full ranked dataset.

| Filter | Type | Source / values | Notes |
|---|---|---|---|
| `keyword` | free text | anything the user types before a `/` | matched against `title`, `company`, `requirements`, `skills_list` |
| `company` | single string | matched against `Opportunity.company` | case-insensitive substring |
| `city` | single string | curated `SAUDI_LOCATIONS` list | exact match (case-insensitive) |
| `major` | single string | one of `CS, AI, CYS, CIS, DS, DE, CE, FT` | matches when in `Opportunity.major_fit` |
| `role_cluster` | single string | values produced by `rubric.infer_role_cluster` | matched against the inferred role cluster |
| `program_type` | single string | `COOP \| Internship \| Tamheer \| Training` | normalised via `rubric._normalize_program_type` |
| `work_mode` | single string | `Remote \| On-site \| Hybrid` | exact match (case-insensitive) |
| `skill` | list of strings | repeated chips, e.g. `Python, SQL, Linux` | each skill must appear in `Opportunity.skills_list` or `requirements` |
| `interview_required` | single string | `Required \| Not required \| Not stated` | matched against `infer_interview_required(opp)` |
| `min_match_score` | int 0–100 | numeric input or slider | server scores each opportunity against a synthetic `ParsedProfile` built from the active filters; only `match_score ≥ min_match_score` is returned |
| `verified_only` | boolean | toggle | when true, only opportunities with a non-empty `source_url` are returned |

Plus a one-shot button:

- **"Apply my chat profile filters"** — appears only when `CareerChromeContext.lastChatProfile` exists. Clicking it pre-populates chips for `city`, `major`, `program_type`, `work_mode`, plus one `skill` chip per skill in the chat profile.

---

## UI behaviour

- The existing morphed composer at the top of `/search` keeps its slash-command + chip-token UX. Extend `data/search-filter-options.ts` with the new chip kinds above.
- Below the composer, render a grid of results using the existing `RecommendationCard`.
- Empty state: "No matches — relax a filter."
- Loading state: reuse the existing `searchComposerBusy` + shelf skeleton.
- Saved-to-shelf behaviour from `/chat` is shared via `CareerChromeContext.savedShelfMemoriesOldestFirst`. The shelf rail on `/search` is reserved for saves, not for results.

---

## Backend coupling

New endpoint:

```
POST /opportunities/search
```

Request:

```python
class SearchRequest(BaseModel):
    keyword: Optional[str] = None
    company: Optional[str] = None
    city: Optional[str] = None
    major: Optional[str] = None
    role_cluster: Optional[str] = None
    program_type: Optional[str] = None
    work_mode: Optional[str] = None
    skills: List[str] = []
    interview_required: Optional[str] = None
    min_match_score: int = 0
    verified_only: bool = False
```

Response: `List[Opportunity]` (already includes `match_score`, `score_breakdown`, `role_cluster`, `interview_required`, `missing_skills`, `why_recommended`, `skills_matched`, `source_url`).

Implementation reuses `recommender.get_candidates()` for the source pool, applies filters, then scores each remaining candidate against a synthetic `ParsedProfile` built from the search filters (so the displayed `match_score` reflects the searcher's intent). The synthetic profile lets us keep the same rubric module for both `/recommend` and `/opportunities/search`.

---

## Result card behaviour

- Same `RecommendationCard` component as the rest of the app.
- Front: rank, company, title, `ScoreBadge`, MetaRows (city, program type, work mode).
- Body: matched skills, `why_recommended` (joined with `" • "`).
- Footer: `SourceButton` bound to `source_url`.
- Optional rows added in Phase 2: `role_cluster`, `interview_required`, `missing_skills`.

No new visual primitive is introduced.

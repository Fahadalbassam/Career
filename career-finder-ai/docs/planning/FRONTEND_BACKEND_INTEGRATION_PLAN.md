# FRONTEND_BACKEND_INTEGRATION_PLAN

How the existing FastAPI backend should plug into the existing Next.js chat surface **without** redesigning any visual element.

---

## Backend-to-frontend field mapping

Source: `backend/app/schemas.py::Opportunity` (snake_case) and `ParsedProfile`.
Target: existing camelCase types in `frontend/src/lib/types.ts` plus a handful of new optional fields.

### Recommendation (`Opportunity` → UI)

| Backend field | Type | Frontend destination | Notes |
|---|---|---|---|
| `rank` | `int` | `RecommendationCard` rank pill, shelf row index | already 1-based |
| `company` | `str` | `RecommendationCard.companyName`, shelf card title (combined with `title`) | |
| `title` | `str` | `RecommendationCard.programName`, shelf title | |
| `city` | `str` | `RecommendationCard` MetaRow + shelf back | |
| `work_mode` | `str` | `RecommendationCard` MetaRow + shelf back | |
| `program_type` | `str` | `RecommendationCard` MetaRow | |
| `major_fit` | `List[str]` | optional chip row on `RecommendationCard` | |
| `requirements` | `str` | optional secondary copy in `RecommendationCard` body | |
| `skills_list` | `List[str]` | reference set used together with `missing_skills` on the card back | |
| `source_url` | `str` | `SourceButton.href` + "Open posting" link on shelf back | |
| `score` (0–1) | `float` | **ignored by UI** | kept only for backend backward compatibility |
| **`match_score` (0–100)** | `int` | `ScoreBadge.scorePercent`, shelf `matchConfidence`, "X% match" chip | **bind directly — no rescaling** |
| **`score_breakdown`** | `Dict[str, float]` | "Why this score" detail inside shelf back (Phase 4+) | keys map to rubric components; multiply each by its `TARGET_WEIGHTS[key]` to show contribution |
| **`role_cluster`** | `str` | small uppercase chip on the **front** of every card (above title), and used to assign **left vs right** shelf | |
| **`interview_required`** | `"Required" \| "Not required" \| "Not stated"` | row on shelf back + filter chip on `/search` | |
| **`missing_skills`** | `List[str]` | "Skills to learn" chips on shelf back; drives right-shelf "growth fit" selection | first 3 shown on card |
| **`why_recommended`** | `List[str]` | shelf back detail (join with `" • "`), and `RecommendationCard` body | ⚠ this is a **list** now — must be joined |
| **`skills_matched`** | `List[str]` | shelf front tags (first 3) + `RecommendationCard` matched chips | |

### Parsed profile (`ParsedProfile` → `ParsedProfileCard`)

| Backend | Existing UI field | Action |
|---|---|---|
| `major` | `major` | keep |
| `city` | `city` | keep |
| `interest` | `interest` | keep |
| `work_mode` | `workMode` | rename via adapter |
| `program_type` | `programType` | rename via adapter |
| `skills` | `skills` | keep |
| `university` | — | **add optional row** |
| `preferred_locations` | — | **add optional row** (badges) |
| `qualifications` | — | **add optional row** (badges) |
| `preferred_roles` | — | **add optional row** (badges) |
| `interview_preference` | — | **add optional row** (`"No interview preferred"` / `"Interview okay"` / dash) |

All additions are **optional** so demo data and existing tests do not break.

---

## Chat centre behaviour

The middle column stays as today: user bubbles (`bg-primary`) and assistant bubbles (`bg-muted`). Each user turn now triggers one of three assistant responses:

1. **Follow-up question.** Asked when a required profile field is missing. One focused question per turn. Examples:
   - "Which computing major are you in — CS, AI, CYS, CIS, DS, DE, CE, or FinTech?"
   - "Which city should I prioritise — Riyadh, Jeddah, Dammam, Khobar, Dhahran…?"
2. **Status update.** Sent after a successful `/recommend`. One short line: "Top match: Aramco Digital — AI & DS COOP, 92%. Open any card to flip it."
3. **Refinement acknowledgment.** Sent when the user adds a constraint ("no interview", "remote only"): "Re-ranked. 2 of 5 now meet 'no interview'."

The existing inline `ActiveFinalizedFitCard` (the compact pill with Finalize/Refine buttons) is kept but used only when the user explicitly says "save this one" / "pin this one". The card visual itself is unchanged.

The chat does **not** end. There is no terminal "thanks, goodbye" state.

---

## Left side card behaviour

- Purpose: **current best matches**.
- Source: top entries from `/recommend` sorted by `match_score`, descending.
- Selection rule: take the first K opportunities where `match_score ≥ 70` and where each occupies a different `role_cluster` than the one immediately above it when possible (avoids three identical clusters).
- Visual: rendered through the existing `CareerFitShelf` left rail (3 rows × up to 3 piled cards). The newest result is the front card; older results pile behind.

---

## Right side card behaviour

- Purpose: **alternative / growth matches**.
- Source: next entries from `/recommend` after the left set, preferring:
  - opportunities whose `role_cluster` differs from the left set, OR
  - opportunities whose `missing_skills` length is small (1–2) so the student sees a realistic growth path.
- Visual: rendered through the existing `CareerFitShelf` right rail. Same widget, same animation.

---

## Progressive card reveal

Cards are not shown all at once. They appear as the profile becomes more complete. Required field set: `major`, `city`, `program_type`, `work_mode`, `skills (≥1)`.

| Required fields filled | Left cards | Right cards |
|---|---|---|
| 0 | 0 (no shelves) | 0 |
| 1–2 | 1 | 0 |
| 3 | 2 | 1 |
| 4 | 2 | 2 |
| 5+ | 3 | 3 |

The order in which cards are inserted into the shelf state is `L1, R1, L2, R2, L3, R3`. The existing `buildShelfRowStacks()` round-robin already lands that sequence in the 3 + 3 slot grid, so no animation changes are needed.

---

## Card front fields

(Already supported by `FitShelfWidget`. Keep this layout.)

- Company/program name (single line, line-clamped to 2)
- `role_cluster` — small uppercase chip
- `match_score` — `ScoreBadge`
- Top matched skills — first 3 from `skills_matched` rendered as outline badges

---

## Card back fields

(Add to the existing `FitShelfWidget` back face — do **not** change the front.)

- Title (already shown)
- `match_score` — "X% match" chip (already shown)
- **`why_recommended` joined with `" • "`** — scrollable detail (already shown for free-text reason)
- City · work mode · `role_cluster` line
- Interview status row (`Interview: Required / Not required / Not stated`)
- Missing skills row — first 3 chips
- Source / apply link — "Open posting →" bound to `source_url`

---

## API files needed

New files on the frontend (none on the backend other than CORS in Phase 1 and `/opportunities/search` in Phase 6):

- `frontend/src/lib/api.ts`
  - `recommendFromMessage(message: string): Promise<RecommendApiResponse>`
  - `parseMessage(message: string): Promise<ParsedProfileApi>`
  - `getStats(): Promise<StatsApi>`
  - `searchOpportunities(req: SearchRequest): Promise<OpportunityApi[]>` (Phase 6)
- `frontend/src/lib/api-types.ts` *(or appended to `lib/types.ts`)* — snake_case mirror types.
- `frontend/src/lib/api-adapters.ts`
  - `toRecommendation(opp: OpportunityApi): Recommendation`
  - `toCareerFitMemory(opp: OpportunityApi): CareerFitMemory`
  - `toStudentProfile(p: ParsedProfileApi): StudentProfile`
  - `mergeParsedProfiles(prev, next): ParsedProfileApi` (Phase 5)
- `frontend/.env.local` — `NEXT_PUBLIC_API_BASE=http://localhost:8000`.

Backend:

- `backend/app/main.py` — add `CORSMiddleware` with `allow_origins=["http://localhost:3000"]`, `allow_methods=["*"]`, `allow_headers=["*"]`.

---

## Risk notes

1. **CORS.** Without `CORSMiddleware`, every browser-side `fetch` silently fails. Fix first, before any frontend work.
2. **`why_recommended` is a list now.** The existing frontend `Recommendation.whyRecommended` is a single `string`. Forgetting the `.join(" • ")` will print `["a","b","c"]` literally.
3. **Case style mismatch.** Backend is snake_case, frontend is camelCase. Never mutate existing types in place — add new types alongside and funnel everything through `api-adapters.ts`.
4. **Animation fragility.** `fit-shelf-widget.tsx`, `fit-shelf.tsx`, `fit-shelf-layout.ts`, and `career-route-shell.tsx` are tightly coupled. Add fields to the **back** of the card only; do not reorder or restyle the **front** layout or the 3 × 3 grid geometry.
5. **Demo shelf cards.** `DEMO_SHELF_GLOBAL_SIX` is wired into `buildAllShelfCardsOldestFirst` and the home→chat slide-in expects the shelves to be populated. Replace them only after the first real `/recommend` returns; do not delete them unconditionally.
6. **Stateless backend.** `/recommend` and `/parse` see only a single `message: str`. Multi-turn memory has to live on the client (Phase 5). Sending only the latest message will drop earlier fields.
7. **Match-score band copy.** `RecommendationCard.fitBadgeVariant` keys off the `fitLevel` string. The adapter must produce stable strings: "Strong fit" ≥ 85, "Good fit" 70–84, "Moderate fit" 50–69, "Growth fit" < 50.
8. **Don't call `/parse` on every keystroke.** Only on send. Debounce search inputs at ≥ 250 ms.
9. **Empty Excel.** When `data/processed/Opportunities_Clean.xlsx` is missing, the recommender falls back to 7 hardcoded placeholders. Search will look thin until the Excel is restored.
10. **Confidence honesty.** When `top match_score < 60`, the assistant must say what is missing instead of pretending the result is strong.

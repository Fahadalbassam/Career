# ROADMAP

Phased plan for taking CareerFinder.ai from "backend works, frontend is mocked" to "real chat-based recommender with a working manual search page". Each phase is independently shippable.

Hard rules that apply to every phase:

- Do not redesign the UI.
- Do not replace the home or methodology pages.
- Do not remove the chat centre + side-shelf concept.
- Do not introduce user accounts, ratings, or recruiter features.

---

## Phase 0 — Documentation and tracking setup

**Goal.** Lock down project identity, integration plan, and tracking surface so every later phase has a single source of truth.

**Files likely touched.**

- `docs/planning/PROJECT_CONTEXT.md`
- `docs/planning/ROADMAP.md`
- `docs/planning/FRONTEND_BACKEND_INTEGRATION_PLAN.md`
- `docs/planning/SEARCH_PAGE_PLAN.md`
- `docs/planning/PROMPT_CONTEXT.md`
- `docs/tracking/IMPLEMENTATION_TRACKER.md`
- `docs/tracking/CHANGE_LOG.md`
- `docs/tracking/DECISION_LOG.md`
- `docs/tracking/TEST_LOG.md`

**Acceptance criteria.**

- All nine documentation files exist under `docs/planning/` and `docs/tracking/`.
- Every later phase in this roadmap is referenced from at least one document.
- No application code (under `backend/app/` or `frontend/src/`) is modified.

**Tests / checks.**

- Manual review of each file.
- `git status` shows only `docs/` additions.

---

## Phase 1 — Connect chat to backend

**Goal.** Prove the network contract end-to-end without changing any visual surface. After this phase, the chat still looks identical but every user turn now produces a real backend call whose response is visible in the Network tab and `console.log`.

**Files likely touched.**

- `backend/app/main.py` — add `CORSMiddleware` for `http://localhost:3000`.
- `frontend/src/lib/api.ts` *(new)* — `recommendFromMessage`, `parseMessage`, `getStats`.
- `frontend/src/lib/api-types.ts` *(new, or appended to `lib/types.ts`)* — snake_case mirror types for `Opportunity`, `ParsedProfile`, `RecommendResponse`.
- `frontend/.env.local` *(new)* — `NEXT_PUBLIC_API_BASE=http://localhost:8000`.
- `frontend/src/components/chat/career-chat.tsx` — inside `runAssistantTurn`, call `recommendFromMessage(text)` in a `try/catch`. On success keep using the existing mock UI path. On failure also fall back to mock so the demo never breaks.

**Acceptance criteria.**

- `curl http://localhost:8000/recommend -X POST -H "Content-Type: application/json" -d '{"message":"AI student in Riyadh COOP"}'` returns a populated `recommendations` array.
- Hitting send in `/chat` shows a successful 200 to `/recommend` in DevTools → Network.
- No visual change. No new UI elements rendered. The 3-then-finalize mock cadence still works as a fallback.

**Tests / checks.**

- Manual: open `/chat`, send "AI student in Riyadh COOP", check Network tab.
- Existing backend tests still pass (`pytest career-finder-ai/tests`).

---

## Phase 2 — Render real recommendations in chat

**Goal.** Map the backend response into the existing UI types so the `ActiveFinalizedFitCard` and shelf cards stop using `mockRecommendations`.

**Files likely touched.**

- `frontend/src/lib/api-adapters.ts` *(new)* — `toRecommendation(opp)`, `toCareerFitMemory(opp)`, `toStudentProfile(parsed)`.
- `frontend/src/lib/types.ts` — extend `CareerFitMemory` and `StudentProfile` with new optional fields (`roleCluster`, `interviewRequired`, `missingSkills`, `sourceUrl`, `workMode`, `city`, `programType`, `university`, `preferredLocations`, `qualifications`, `preferredRoles`, `interviewPreference`). All optional → no breaking changes.
- `frontend/src/components/chat/career-chat.tsx` — replace `mockRecommendations[…]` with adapter output.
- `frontend/src/components/recommendations/recommendation-card.tsx` — add optional rows for `role_cluster`, `interview_required`, `missing_skills`.
- `frontend/src/components/chat/parsed-profile-card.tsx` — add optional rows for `university`, `preferred_locations`, `qualifications`, `preferred_roles`, `interview_preference`.

**Acceptance criteria.**

- The first finalized card in chat shows real values from `/recommend` (real company, real `match_score`, real `why_recommended` joined with `•`).
- `ParsedProfileCard` (when rendered) shows real parsed fields.
- The `match_score` value (0–100) drives the existing `ScoreBadge` directly. No rescaling.
- Existing animations and existing card visual layout are untouched.

**Tests / checks.**

- Manual: chat with three different messages (CS student, CYS student, AI student) and confirm cards reflect different rankings.
- Adapter unit tests (optional, in `frontend/`) for `toRecommendation` against a fixture payload.

---

## Phase 3 — Turn side cards into real Fit Shelf

**Goal.** The two side shelves become a true Fit Shelf:

- **Left** = current best matches (top by `match_score`).
- **Right** = alternative / growth matches (differing `role_cluster`, or low `missing_skills` count).

**Files likely touched.**

- `frontend/src/components/chat/career-chat.tsx` — after each `/recommend`, replace `savedShelfMemoriesOldestFirst` with the new top-K in `L1, R1, L2, R2, L3, R3` order so the existing round-robin in `fit-shelf-layout.ts` lands them in the right slots.
- `frontend/src/components/chat/fit-shelf-widget.tsx` — extend the **back** of the card with: `city · work_mode · role_cluster` line, `Interview: …`, "Skills to learn:" chips (first 3), and an "Open posting →" link bound to `source_url`. **Front face is untouched.**
- `frontend/src/data/demo-shelf-memories.ts` — keep the demo six only as a pre-conversation placeholder. Replace with real cards as soon as the first `/recommend` succeeds.

**Progressive reveal table** (drives how many cards are visible):

| Filled required fields | Left cards | Right cards |
|---|---|---|
| 0 | 0 | 0 |
| 1–2 | 1 | 0 |
| 3 | 2 | 1 |
| 4 | 2 | 2 |
| 5+ | 3 | 3 |

Required fields: `major`, `city`, `program_type`, `work_mode`, `skills (≥1)`.

**Acceptance criteria.**

- Left shelf shows top-K real opportunities sorted by `match_score`.
- Right shelf shows alternatives / growth matches.
- Cards still flip, still tilt, still slide-in via the existing animation; only the back content changed.
- Progressive reveal works: an empty chat shows zero shelf cards, a fully-specified profile shows 3 + 3.

**Tests / checks.**

- Manual: send increasingly detailed messages and confirm shelf populates step by step.
- Visual regression: shelves still 3 × 3, still flippable.

---

## Phase 4 — Add missing-info follow-up questions

**Goal.** When the parsed profile is missing a required field, the assistant asks **one focused question** instead of returning a weak ranking. When confidence is low, the assistant **says what is missing** rather than pretending the match is strong.

**Files likely touched.**

- `frontend/src/components/chat/career-chat.tsx` — add a small local follow-up table (`major → "Which computing major…"`, `city → "Which city…"`, etc.).
- `frontend/src/lib/confidence.ts` *(new)* — derive `profileCompleteness` (0–1) and a copy phrase (`Strong fit` / `Decent matches` / `Not enough information yet`).
- Optionally: `frontend/src/components/chat/career-chat.tsx` adds a one-line status bubble after each successful `/recommend` summarising "Top match: X — Y%".

**Acceptance criteria.**

- Sending "I am a CYS student" produces a follow-up question, not a ranked list.
- Sending "I am a CYS student in Dammam with Linux, Python, networking, looking for remote COOP" produces a ranked list.
- When `top match_score < 60`, the assistant copy explicitly lists what additional information would help (e.g. "add a skill or two", "tell me your preferred work mode").
- Conversation never ends. The assistant always offers a next step.

**Tests / checks.**

- Manual scripted conversation (the README example flow).
- Unit test for the follow-up question selector in `frontend/`.

---

## Phase 5 — Add multi-turn profile memory

**Goal.** Profile fields parsed in earlier turns are preserved when later turns add more information. Refinement intents ("no interview", "remote only", "Riyadh only") update the profile and re-rank.

**Files likely touched.**

- `frontend/src/components/chat/career-chat.tsx` — keep an `accumulatedProfile: ParsedProfileApi` in state.
- `frontend/src/lib/api-adapters.ts` — add `mergeParsedProfiles(prev, next)` ("non-empty wins, lists union").
- `frontend/src/lib/intent.ts` *(new)* — detect refinement phrases locally ("without interview", "remote only", "in Riyadh", "show more", "alternatives") and patch the accumulated profile.
- `frontend/src/components/career/career-nav-context.tsx` — expose `lastChatProfile` on the chrome context so `/search` can read it.

**Acceptance criteria.**

- Two-turn conversation `["I am a CYS student", "in Dammam, Linux, Python"]` produces the same recommendations as the single concatenated message — major is not lost between turns.
- "Show me ones without an interview" reorders existing recommendations so `interview_required === "Not required"` items move to the top, without a new backend call when possible.
- `/search` page can now display an **"Apply my chat profile filters"** button (wiring is Phase 6, but the data must already be available here).

**Tests / checks.**

- Manual multi-turn conversation.
- Unit tests for `mergeParsedProfiles` and the intent detector.

---

## Phase 6 — Build search page database search

**Goal.** `/search` becomes a manual structured search over the opportunity database — no users, no ratings, no recruiter accounts.

**Files likely touched.**

- `backend/app/main.py` — new endpoint `POST /opportunities/search`.
- `backend/app/schemas.py` — new `SearchRequest` model.
- `backend/app/recommender.py` or new `backend/app/search.py` — filter + rank against a synthetic `ParsedProfile` derived from the search filters.
- `frontend/src/lib/api.ts` — add `searchOpportunities(req)`.
- `frontend/src/data/search-filter-options.ts` — extend with `company`, `role_cluster`, `program_type`, `work_mode`, `skill`, `interview_required`, `min_match_score`, `verified_only`.
- `frontend/src/components/career/search-composer.tsx` — add chip kinds for the new filters.
- `frontend/src/app/(career)/search/page.tsx` — replace the empty `<div />` with a results grid using the existing `RecommendationCard`.

Planned filters (see `SEARCH_PAGE_PLAN.md` for details):

- `keyword`, `company`, `city`, `major`, `role_cluster`, `program_type`, `work_mode`, `skill`, `interview_required`, `min_match_score`, `verified_only`

Plus an **"Apply my chat profile filters"** button that reads from `CareerChromeContext.lastChatProfile` (added in Phase 5).

**Acceptance criteria.**

- Submitting "Riyadh + Internship + Cybersecurity" on `/search` returns a populated grid of `RecommendationCard`s.
- Filters can be combined; results re-rank by `match_score` against the synthetic profile.
- `verified_only` excludes opportunities with no `source_url`.
- `min_match_score` slider gates results client-side or server-side.
- No user accounts, no ratings, no recruiter UI is introduced.

**Tests / checks.**

- Backend tests for `/opportunities/search` filter combinations.
- Manual: tour each filter chip kind in the composer.

---

## Phase 7 — Dashboard / model / report-ready outputs

**Goal.** Expose the dataset and the rubric for internal review without redirecting development effort away from /chat and /search. This phase is **not** user-facing polish; it is reviewability.

**Files likely touched.**

- `backend/app/main.py` — `GET /stats` already exists; extend it with counts per role_cluster, per city, per program_type.
- `frontend/src/app/dashboard/page.tsx` — minimal read-only view of `GET /stats`. No new visual identity, reuses existing cards.
- `frontend/src/app/model/page.tsx` — minimal read-only view of the rubric weights and per-component breakdown for a sample profile.
- Optional Jupyter notebook(s) under `career-finder-ai/notebooks/` reporting on the regression dataset.

**Acceptance criteria.**

- `/dashboard` renders counts and totals from `GET /stats` without crashing.
- `/model` renders the rubric weights and a sample `score_breakdown`.
- No new UI primitives. Reuses Card / Badge / Separator.

**Tests / checks.**

- Manual: load each route, confirm no console errors.

---

## Phase 8 — Final testing and cleanup

**Goal.** Lock down the product before any wider rollout: kill dead code, document the public surface, run the full test suite, and lint.

**Files likely touched.**

- Remove `data/mock-recommendations.ts` and `data/demo-shelf-memories.ts` once they are no longer referenced anywhere.
- Trim unused imports across `frontend/src/components/`.
- Add a top-level `README.md` section for "Running locally" (backend + frontend together).
- Ensure `.gitignore` excludes `frontend/.next/`.

**Acceptance criteria.**

- `pytest career-finder-ai/tests` passes locally on a fresh clone.
- `npm run lint` and `npm run build` succeed for the frontend.
- No imports point to deleted mock modules.
- Documentation in `docs/planning/` and `docs/tracking/` is up to date.

**Tests / checks.**

- Full backend `pytest` run.
- Frontend `next build`.
- Manual smoke test of all four routes: `/`, `/chat`, `/search`, `/methodology`.

# PROJECT_CONTEXT

## Project name

**CareerFinder.ai**

## What CareerFinder.ai is

A chat-based AI recommender that helps Saudi computing students find suitable **COOP, internship, Tamheer, training, and early-career opportunities**. The student describes themselves in natural language, the system extracts a structured profile, compares it against a curated opportunity dataset, and returns ranked explainable matches with a **0–100 match score**. As the conversation continues, the profile is updated and recommendations are re-ranked.

## What CareerFinder.ai is *not* (yet)

- Not a job board for the general public.
- Not a recruiter-facing tool.
- Not a user-account system. No sign-up, login, profiles-on-server, or saved-history-per-user.
- Not a ratings/reviews platform for companies.
- Not a salary or benefits database.
- Not a resume-builder or interview-prep product.
- Not a full-time job search engine (focus is internship-class opportunities first).

## Target users

Saudi university students (undergraduate and very-early-graduate) looking for:

- COOP
- Internship
- Tamheer
- Training programs
- Early-career / entry-level computing roles tied to one of the supported majors

## Target majors

- Computer Science (CS)
- Artificial Intelligence (AI)
- Cybersecurity (CYS)
- Computer Information Systems (CIS)
- Data Science (DS)
- Data Engineering (DE)
- Computer Engineering (CE)
- FinTech (FT) — when the opportunity is computing-adjacent

## Main user flow

1. User opens **/chat** (the primary surface).
2. User describes themselves in free text (major, city, skills, preferences, etc.).
3. The system **parses the message** into a structured profile.
4. The system checks for missing important fields.
5. If important fields are missing → the assistant asks one focused follow-up question instead of producing a weak result.
6. As soon as the profile is rich enough, the system calls **/recommend** and updates the side **Fit Shelf** with ranked opportunities.
7. The student can refine ("show me ones without an interview", "only Riyadh", "remote only", "what would push these into the 80s?") and recommendations re-rank.
8. The student may switch to **/search** to manually browse the opportunity database with structured filters.

The chat does **not** end after one turn. It keeps the conversation going until the user decides to leave.

## Current backend status

The FastAPI backend at `career-finder-ai/backend/` exposes:

- `GET /health`
- `GET /stats`
- `POST /parse` — returns `ParsedProfile`
- `POST /recommend` — returns `RecommendResponse { profile, recommendations, total_candidates }`

Each recommendation (an `Opportunity`) now includes:

- `rank`
- `company`
- `title`
- `city`
- `work_mode`
- `program_type`
- `major_fit`
- `requirements`
- `skills_list`
- `source_url`
- `score` — legacy 0–1
- `match_score` — new **0–100**
- `why_recommended` — list of strings
- `skills_matched`
- `role_cluster`
- `interview_required` — `"Required" | "Not required" | "Not stated"`
- `missing_skills`
- `score_breakdown` — per-rubric-component scores (0–1)

Rubric logic is centralised in `backend/app/rubric.py` and shared between the live recommender and the regression-dataset builder.

**CORS is not configured yet.** The frontend cannot call the backend from `http://localhost:3000` until `CORSMiddleware` is added.

## Current frontend status

Next.js (App Router) at `career-finder-ai/frontend/`:

- **Home page** — finished, visually frozen.
- **Methodology page** — finished, visually frozen.
- **Chat page** — strong visual identity already built (centre conversation + two animated side shelves). Behaviour is **mocked**: `mockRecommendations`, a 4-second fake assistant delay, and a "3 replies then 1 finalized card" demo gating loop.
- **Search page** — file exists but renders an empty `<div />`. The morphed `SearchComposer` UI (slash commands, chip tokens) is real; submit is fake.
- **Side shelves** (`fit-shelf.tsx`, `fit-shelf-widget.tsx`) — 3-row × 3-pile-deep grid per side, with metal surface, tilt, hover lift, and click-to-flip. Already supports front and back faces. Currently fed by `DEMO_SHELF_GLOBAL_SIX` plus user-finalized cards.
- **RecommendationCard** (`components/recommendations/recommendation-card.tsx`) — exists, not currently used by chat. Reserved for `/search` results.
- **ParsedProfileCard** (`components/chat/parsed-profile-card.tsx`) — exists, not wired in yet.

The frontend is **not connected to the backend** at all yet — no `lib/api.ts`, no `fetch` calls, no `NEXT_PUBLIC_API_BASE`.

## Non-negotiable UI rules

These are hard constraints. They apply to every future change.

- **Do not redesign** the visual identity. The black/white minimal CareerFinder.ai aesthetic stays.
- **Do not remove** the centre-chat + side-card-shelf concept.
- **Do not replace** the home page.
- **Do not replace** the methodology page.
- **Do not remove or rebuild** the 3D shelf tilt, hover lift, flip animation, or the home↔chat↔search choreography in `career-route-shell.tsx`.
- **Do not** introduce new component libraries or visual frameworks.
- **Do not** add login, accounts, or ratings UI.
- Backend field shapes are the source of truth. The frontend adapts to the backend, not the other way around.
- When extending shelf cards, add fields to the **back** of the card. Do not change the **front** layout.

# PROMPT_CONTEXT

Short, AI-prompt-ready snapshot of the project. Keep this file under one screen.

## Project identity

**CareerFinder.ai** — chat-based AI recommender for **Saudi computing students** looking for **COOP, internships, Tamheer, training, and early-career opportunities**. Supported majors: CS, AI, CYS, CIS, DS, DE, CE, FinTech. Primary surface is `/chat`. Secondary surface is `/search` (manual filter over the opportunity database).

## Current status

- Backend (FastAPI, `career-finder-ai/backend/`) is upgraded: `/recommend` returns 0–100 `match_score`, `score_breakdown`, `role_cluster`, `interview_required`, `missing_skills`, `why_recommended` (list), `skills_matched`, `source_url`. CORS enabled for `localhost:3000`.
- Frontend (Next.js App Router, `career-finder-ai/frontend/`) is visually finished for `/`, `/chat`, `/methodology`. `/search` is a stub. Chat calls real `/recommend` with multi-turn memory in `localStorage`.
- **Terminal dev shortcuts** (repo root): `npm run run:terminal` (auto-start backend + interactive CLI → `/recommend`); `npm run run:full` (backend + frontend dev servers). CLI: `scripts/careerfinder_cli.py`. Login in CLI is stub only.
- Shared rubric lives in `backend/app/rubric.py`. Backend tests for parser, scoring, recommender, and regression dataset are present under `career-finder-ai/tests/`.

## Current next phase

**Phase 1 — Connect chat to backend.** Concretely:

1. Add `CORSMiddleware` to `backend/app/main.py` for `http://localhost:3000`.
2. Create `frontend/src/lib/api.ts` with `recommendFromMessage`, `parseMessage`, `getStats`.
3. Add `frontend/.env.local` with `NEXT_PUBLIC_API_BASE=http://localhost:8000`.
4. In `frontend/src/components/chat/career-chat.tsx::runAssistantTurn`, call `recommendFromMessage(text)` in a `try/catch`. Keep the existing mock UI as fallback. No visual change yet.

## Rules for not redesigning the UI

- Do not redesign the black/white minimal CareerFinder.ai visual identity.
- Do not remove the chat centre + side-shelf concept.
- Do not replace the home or methodology pages.
- Do not change the **front** layout of `FitShelfWidget`. Add new fields to the **back** only.
- Do not change the 3 × 3 shelf geometry, the tilt, the flip, or the home↔chat↔search choreography.
- Do not introduce login, accounts, ratings, recruiter UI, or salary surfaces.
- Do not add new component libraries.

## Important backend response fields

Each `Opportunity` returned by `POST /recommend`:

- `rank`, `company`, `title`, `city`, `work_mode`, `program_type`
- `major_fit` (list), `requirements`, `skills_list` (list), `source_url`
- `score` (0–1, legacy), **`match_score` (0–100)** — bind to UI directly, no rescaling
- **`why_recommended`** — `List[str]` (join with `" • "` before rendering)
- `skills_matched` (list)
- **`role_cluster`** — drives left-vs-right shelf assignment and a small chip on the card front
- **`interview_required`** — `"Required" | "Not required" | "Not stated"`
- **`missing_skills`** (list) — drives the "Skills to learn" chips on the card back
- **`score_breakdown`** — per-rubric-component scores in [0, 1]

The parsed profile (`POST /parse` and `recommendation.profile`) includes: `major`, `university`, `city`, `preferred_locations`, `skills`, `qualifications`, `interest`, `program_type`, `work_mode`, `preferred_roles`, `interview_preference`.

## Current recommended next implementation task

**Phase 4 follow-up questions in chat** (or Phase 6 search page) — see `docs/planning/ROADMAP.md`. Terminal runner is done (`npm run run:terminal`, `npm run run:full`).

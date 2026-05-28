# CHANGE_LOG

Chronological log of substantive changes to the repository. Newest at the bottom.

---

## 2026-05-27 — Backend recommendation response upgrade

**Where.** `backend/app/schemas.py`, `backend/app/recommender.py`.

**What changed.**

- `Opportunity` (Pydantic model) gained the following fields:
  - `match_score: int` — new 0–100 score derived from the shared rubric.
  - `score_breakdown: Dict[str, float]` — per-component scores in [0, 1] (`major_fit_score`, `skill_match_score`, `role_interest_score`, `city_match_score`, `program_type_score`, `work_mode_score`, `verification_score`, `interview_score`).
  - `role_cluster: str` — inferred role family used for left-vs-right shelf grouping and for the front-of-card chip.
  - `interview_required: "Required" | "Not required" | "Not stated"` — inferred from the opportunity text.
  - `missing_skills: List[str]` — opportunity skills the student does not yet list.
- The legacy `score: float` (0–1) is kept for backward compatibility and equals `match_score / 100`.
- `recommend()` and `recommend_from_message()` populate the new fields and sort by `match_score` descending.

**Why.** The frontend `ScoreBadge`, the shelf back face, and the upcoming follow-up logic all need explicit 0–100 confidence plus the per-component breakdown to honestly describe why a match is strong or weak.

---

## 2026-05-27 — Shared rubric module

**Where.** `backend/app/rubric.py` (new). Referenced from `backend/app/recommender.py` and `backend/app/build_regression_dataset.py`.

**What changed.**

- Centralised the component scorers in one module: `compute_major_fit_score`, `compute_skill_match_score`, `compute_role_interest_score`, `compute_city_match_score`, `compute_program_type_score`, `compute_work_mode_score`, `compute_verification_score`, `compute_interview_score`, plus `compute_target_score` and `score_profile_opportunity_pair`.
- Added inference helpers `infer_role_cluster`, `infer_interview_required`, `infer_verified_opportunity`, and `compute_missing_skills`.
- Exposed `TARGET_WEIGHTS`, `RELATED_MAJORS`, `ROLE_CLUSTER_PATTERNS`, `ROLE_FAMILY_KEYWORDS`, `ROLE_EXACT_KEYWORDS`, and `SCORE_BREAKDOWN_KEYS` as the public contract.

**Why.** Without a shared module, the recommender and the regression-dataset builder were drifting in their scoring logic, which would have made the trained model disagree with the live API. The rubric now has one definition.

---

## 2026-05-27 — Frontend / backend integration audit

**Where.** `docs/audits/chat-search-recommendation-audit.md`.

**What changed.**

- Documented which surfaces are real vs mocked on the frontend (home / methodology = real; chat = mocked behaviour; search = empty stub).
- Mapped each new backend `Opportunity` field to the corresponding existing frontend surface (`ScoreBadge`, MetaRows, shelf front, shelf back, `SourceButton`).
- Identified the four highest risks: missing CORS, snake_case vs camelCase drift, `why_recommended` is a list (not a string) now, and the shelf animation fragility.
- Proposed Phase 1–6 plan and the single best next implementation task (CORS + `lib/api.ts` + chat wiring with mock fallback).

**Why.** Phase 0 needs a concrete picture of what is wired vs not wired before any code lands.

---

## 2026-05-27 — Documentation and tracking setup

**Where.** `docs/planning/` and `docs/tracking/` (new).

**What changed.**

- Created `docs/planning/PROJECT_CONTEXT.md`, `ROADMAP.md`, `FRONTEND_BACKEND_INTEGRATION_PLAN.md`, `SEARCH_PAGE_PLAN.md`, `PROMPT_CONTEXT.md`.
- Created `docs/tracking/IMPLEMENTATION_TRACKER.md`, `CHANGE_LOG.md`, `DECISION_LOG.md`, `TEST_LOG.md`.
- No application code modified.

**Why.** Phase 0 of `ROADMAP.md`. Locks the project identity, the integration contract, and the tracking surface before any frontend wiring begins.

---

## 2026-05-27 — Phase 1 backend connection proof

**Where.** `backend/app/main.py`, `frontend/src/lib/api.ts`, `frontend/src/lib/api-types.ts`, `frontend/.env.local`, `frontend/src/components/chat/career-chat.tsx`.

**What changed.**

- Added FastAPI `CORSMiddleware` for `http://localhost:3000` and `http://127.0.0.1:3000`.
- Added frontend API types (`api-types.ts`) and client (`api.ts`) with `recommendFromMessage`.
- Chat `runAssistantTurn` now POSTs to `/recommend` and logs the response (or error) to the browser console.
- UI rendering intentionally unchanged — mock assistant flow, shelf cards, and finalize behaviour remain as before.

**Why.** Prove the browser can reach the backend before Phase 2 maps and renders real recommendation data.

---

## 2026-05-27 — Phase 2 backend response mapping

**Where.** `frontend/src/lib/api-adapters.ts` (new), `frontend/src/lib/types.ts`, `frontend/src/components/chat/career-chat.tsx`, `backend/app/main.py` (startup command doc), `docs/tracking/IMPLEMENTATION_TRACKER.md`.

**What changed.**

- Added `api-adapters.ts` with `toStudentProfile`, `toRecommendation`, and `toRecommendations` — converts snake_case backend payloads to existing frontend camelCase types; joins `why_recommended` with `" • "`; maps `match_score` → `scorePercent` and derives `fitLevel` bands.
- Chat now uses the top real backend recommendation in the finalized-fit card when `/recommend` succeeds; mock recommendations remain the fallback when the backend is offline.
- Compact `ParsedProfileCard` renders after assistant replies when backend profile data is available.
- UI layout, animations, side shelves, and finalize/refine flow intentionally unchanged.
- Backend startup command documented as `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` (port 8001 fallback via `NEXT_PUBLIC_API_BASE` if needed).

**Why.** Phase 2 goal: show real recommendation content in the existing chat UI without redesigning it. Side Fit Shelf remains Phase 3; follow-up questions Phase 4.

---

## 2026-05-27 — Phase 3.2 Chat layout and response copy hardening

**Where.** `frontend/src/components/chat/career-chat.tsx`, `frontend/src/components/chat/parsed-profile-card.tsx`, `frontend/src/app/(career)/layout.tsx`, `docs/tracking/IMPLEMENTATION_TRACKER.md`, `docs/tracking/CHANGE_LOG.md`.

**What changed.**

- Added `buildAssistantReply` helper to `career-chat.tsx`. It produces one focused message per turn: acknowledges soft-skills-only input and asks for technical skills; asks for the single most important missing field (major → city → skills → program type → work mode); reports a strong/good/early match by name and score when the backend returns recommendations. The static "Thanks — I'm using that…" constant is removed.
- `ChatEntry` standard variant now carries `replyText: string`; the reply is computed once at the moment the 4 s timer resolves and stored in the entry so rerenders are stable.
- `ParsedProfileCard` subtitle no longer says "(mock)" or "(mock preview)". Compact variant now reads "Fields inferred from your chat message." and the full variant reads "Structured fields inferred from your conversation."
- Career grouped layout (`(career)/layout.tsx`) had `pt-4 pb-10 md:pt-5 md:pb-12` removed. The fixed composer is not in flow, so these paddings were pure dead space; removing them lets the chat area fill the full height below the navbar.
- `CareerChat` outer column div had `pb-48 md:pb-52` removed for the same reason. The messages content div now uses `pb-40 md:pb-44` (160/176 px), which is sufficient to clear the fixed composer (~116 px from bottom) plus the keyboard caption hint.
- No shelf, animation, flip, tilt, or search layout changes.

**Why.** The static reply was unhelpful regardless of what the user said. The "mock" label was confusing once real backend data is in use. The layout dead-zone was making the usable chat area unnecessarily short on mobile.

---

## 2026-05-27 — Phase 3.1 Fit Shelf hardening

**Where.** `frontend/src/lib/types.ts`, `frontend/src/lib/api-adapters.ts`, `frontend/src/components/chat/fit-shelf-layout.ts`, `frontend/src/components/chat/career-chat.tsx`, `docs/tracking/IMPLEMENTATION_TRACKER.md`, `docs/tracking/CHANGE_LOG.md`.

**What changed.**

- Added `source?: "backend" | "demo" | "manual"` to `CareerFitMemory`. `toCareerFitMemory` sets `"backend"`. The manual-finalize helper `recommendationToMemory` sets `"manual"`. Demo tiles remain `undefined`.
- `usesBackendShelfTiles` in `fit-shelf-layout.ts` now tests `m.source === "backend"` instead of `m.rank != null`, so mock recommendations with numeric `rank` can no longer incorrectly suppress demo shelf tiles.
- `runAssistantTurn` in `career-chat.tsx` now captures the current turn id and clears backend refs before the fetch begins. The async closure checks the turn id on resolve/reject, dropping stale or post-clean-slate responses silently.
- `countProfileFieldsFilled` now counts `interest` and `preferredRoles` alongside the previous six fields, improving progressive reveal for students who provide interest or role preferences.
- `buildShelfMemoriesFromRecommendations` floors reveal count at 1 when the backend returns results, so a real response never falls back to demo tiles due to a sparse parse.
- Shelf front layout, flip, tilt, stack, and 3-row geometry are unchanged.

**Why.** Three correctness issues identified in Phase 3 review: rank-based backend detection was unreliable, stale async responses could corrupt shelf state, and a sparse parse could prevent real cards from appearing at all.

---

## 2026-05-28 — Auth-0 / Auth-1 frontend auth shell (stubbed)

**Where.** `docs/planning/AUTH_PLAN.md` (new), `docs/tracking/DECISION_LOG.md`, `docs/tracking/IMPLEMENTATION_TRACKER.md`, `docs/tracking/CHANGE_LOG.md`, `frontend/src/lib/auth.ts` (new), `frontend/src/components/auth/auth-provider.tsx` (new), `frontend/src/components/providers.tsx`, `frontend/src/app/login/page.tsx` (new), `frontend/src/app/signup/page.tsx` (new), `frontend/src/components/layout/navbar.tsx`.

**What changed.**

- **Auth-0:** Created `AUTH_PLAN.md` with current auth state, recommended HttpOnly opaque-session architecture, route access matrix, future database tables, anonymous import flow, logout behavior, security mitigations, and phases Auth-0 through Auth-7. Added decisions D-011 (no localStorage auth tokens), D-012 (middleware + server route protection), D-013 (opt-in profile import), D-014 (backend auth deferred to Auth-2).
- **Auth-1:** Added stub `lib/auth.ts` (`loginStub`, `signupStub`, `logoutStub`, `User` type) with no backend calls and no token persistence. Added `AuthProvider` / `useAuth()` with in-memory `user` state only. Wrapped app via `Providers`. Added `/login` and `/signup` pages (email + password forms, redirect to `/` on success). Navbar: `login` link → `/login`; when stub-logged-in shows display name/email and `logout` (does not clear anonymous chat `localStorage`). `LoginCardDialog` left unchanged.

**What did NOT change.** No backend `/auth/*` endpoints, no `users`/`sessions` tables, no password hashing, no cookies, no `middleware.ts`, no OAuth, no chat recommendation logic, no UI redesign.

**Why.** Establishes the frontend auth contract and documentation before Auth-2 introduces real security.

---

## 2026-05-28 — Phase 4A Multi-turn profile memory and anonymous local persistence

**Where.** `frontend/src/lib/chat-session.ts` (new), `frontend/src/lib/api-adapters.ts`, `frontend/src/components/chat/career-chat.tsx`, `backend/app/parser.py`, `docs/tracking/IMPLEMENTATION_TRACKER.md`, `docs/tracking/CHANGE_LOG.md`, `docs/tracking/DECISION_LOG.md`.

**What changed.**

**Frontend — multi-turn memory (`career-chat.tsx`, `api-adapters.ts`):**
- Added `userMessagesRef` that accumulates every user message sent this session.
- Every send now builds `combinedMessage = userMessages.join("\n")` and sends that to `/recommend` instead of only the latest message.
- Added `mergeStudentProfiles(current, incoming)` to `api-adapters.ts`: merges two `StudentProfile` objects — scalar fields favour the latest non-empty value; list fields (`skills`, `preferredLocations`, `qualifications`, `preferredRoles`) are unioned and deduplicated case-insensitively; skills always fall back to `["Not stated"]` rather than empty.
- `mergedProfileRef` accumulates the merged profile across all turns; it is used for both the `ParsedProfileCard` display and for `buildAssistantReply`.

**Frontend — anonymous session storage (`chat-session.ts`):**
- New `chat-session.ts` exports `STORAGE_KEY`, `AnonymousChatSession`, `loadAnonymousChatSession()`, `saveAnonymousChatSession()`, `clearAnonymousChatSession()`.
- Uses `localStorage` only; SSR-safe (`typeof window` guard); try/catch on `JSON.parse` ignores corrupted storage.
- Session is saved after every successful `/recommend` turn; cleared on clean slate.
- On first mount the session is hydrated (no old chat bubbles — only the profile and message history are restored silently).

**Frontend — `buildAssistantReply` strict priority (`career-chat.tsx`):**
- Moved all "missing critical info" checks **above** match-score praise. Old order let "Strong match found" fire even with no major or skills.
- New order: (1) backend failed → fallback, (2) major missing, (3) no technical skills / soft-skills-only, (4) city + preferred locations both missing, (5) program type missing, (6) work mode missing, (7) score ≥ 85 → strong match, (8) score 70–84 → good match, (9) score < 70 → low confidence, (10) default.

**Backend — parser skill aliases and normalization (`parser.py`):**
- Added to `SKILL_KEYWORDS`: `kubernetes`, `cloud`, `devops`, `networking`, `cybersecurity`, `penetration testing`, `prompt engineering`, `software testing`, `qa`, `soc`, `siem`, `infrastructure`.
- Added to `_normalize_text`: `dev ops` → `devops`; `pen testing` / `pentesting` → `penetration testing`; `machine-learning` → `machine learning`; `prompt testing` → `prompt engineering`; `devsecops` → `devops`; `k8s` → `kubernetes`.
- Added `INTEREST_KEYWORDS` dict and `_find_interest_from_text()` function. When a student explicitly states a domain interest (e.g. "interested in security infrastructure"), the text-based interest overrides the major-derived default.

**What did NOT change.** No UI redesign. No Search/Home/Methodology changes. No user accounts. No database writes. No geolocation. No cookies. Mock fallback intact. All animations unchanged.

**Why.** The chat was re-parsing only the latest message, causing it to forget fields stated in earlier turns (e.g. major on turn 1 was invisible after turn 2). Students need the system to remember what they said and build a progressively richer profile without repeating themselves.

---

## 2026-05-27 — Phase 3 real Fit Shelf cards

**Where.** `frontend/src/lib/api-adapters.ts`, `frontend/src/lib/types.ts`, `frontend/src/components/chat/career-chat.tsx`, `frontend/src/components/chat/fit-shelf-widget.tsx`, `frontend/src/components/chat/fit-shelf.tsx`, `frontend/src/components/chat/fit-shelf-layout.ts`, `docs/tracking/IMPLEMENTATION_TRACKER.md`.

**What changed.**

- Side shelves now use backend recommendations after a successful `/recommend` response (up to six cards: left = strong matches ≥70%, right = alternates/growth; interleaved L1–R3).
- Demo shelf tiles remain the fallback before any successful backend response or when the backend fails.
- `toCareerFitMemory` / `buildShelfMemoriesFromRecommendations` map `Recommendation` → `CareerFitMemory` with progressive reveal by profile completeness.
- Shelf card **back** can show role cluster, city, work mode, program type, interview status, missing skills (first 3), and an apply link when `sourceUrl` is present.
- UI design intentionally unchanged (front layout, tilt, flip, stack, 3-row geometry).

**Why.** Phase 3 goal: wire the existing side shelves to real recommender output without redesigning the chat shell.

---

## 2026-05-28 — Phase ML-Terminal: terminal recommender runner

**Where.** `scripts/careerfinder_cli.py`, `scripts/run-terminal.ps1`, `scripts/run-full.ps1`, `scripts/run-terminal.cmd`, `scripts/run-full.cmd`, `package.json` (repo root), `docs/tracking/*`, `docs/planning/PROMPT_CONTEXT.md`.

**What changed.**

- **`npm run run:terminal`** — PowerShell launcher checks `/health`, auto-starts the FastAPI backend in a new window if needed, then opens the interactive Python CLI (`careerfinder_cli.py`) in another window. CLI prints the CareerFinder.ai ASCII logo, guest/login stub choice, accumulated multi-turn messages to `POST /recommend`, parsed profile, assistant-style follow-up copy, and top-5 recommendations.
- **`npm run run:full`** — Opens backend (`uvicorn` on `http://127.0.0.1:8000`) and frontend (`npm run dev` on `http://localhost:3000`) in separate PowerShell windows.
- **`.cmd` aliases** — `scripts\run-terminal.cmd` and `scripts\run-full.cmd` for double-click or direct invocation on Windows.

**What did NOT change.** No frontend UI. No real auth. No database persistence. No Search/Home/Methodology changes. No recommendation algorithm changes.

**Why.** Developers need a fast terminal path to exercise the same `/recommend` contract as `/chat` without opening the browser, plus a one-command way to boot the full local stack.

---

## 2026-05-28 — Phase ML-Terminal-UX: compact terminal recommender output

**Where.** `scripts/careerfinder_cli.py`, `docs/tracking/IMPLEMENTATION_TRACKER.md`, `docs/tracking/CHANGE_LOG.md`.

**What changed.**

- Default turn output is **compact**: summary profile (major, university, city, interest, program type, work mode, skills only), assistant reply, one-line top-5 rows (`Rank | Score | Company | Program | City | Mode | Missing`), and `Scanned N opportunities.`
- New commands: `/details N`, `/open N` (browser via `webbrowser`), `/links`, `/top N`, `/compact`, `/verbose`, `/split` (side-by-side when terminal ≥ 120 cols).
- `latest_profile` and `latest_recommendations` kept in memory for drill-down commands.
- Long values truncated with `truncate()` using `shutil.get_terminal_size()`.

**What did NOT change.** No frontend UI, auth, database, or recommender scoring changes.

**Why.** Full verbose cards pushed the input prompt off-screen; developers need a scannable default with opt-in detail.

---

## 2026-05-28 — Phase ML-2A: role taxonomy + parser normalisation + rubric cluster scoring

**Where.** `backend/app/taxonomy.py` (new), `backend/app/parser.py`, `backend/app/rubric.py`, `tests/test_parser.py`, `tests/test_recommender.py`, `docs/tracking/*`.

**What changed.**

- **New module `app.taxonomy`.** Single source of truth for role clusters, interest aliases, city aliases, and skill aliases. Pure data plus three small helpers (`find_city_in_text`, `find_interest_in_text`, `normalise_skill_aliases`). No I/O, no dependency on the rest of the app. Imported by both `app.parser` and `app.rubric`.
  - Role clusters: `Cybersecurity`, `SOC Analyst`, `Network Security`, `Penetration Testing`, `Software Engineering`, `Backend Engineering`, `Frontend Engineering`, `Full Stack Engineering`, `Data Engineering`, `Data Science`, `AI / Machine Learning`, `Cloud / DevOps`, `QA / Testing`, `General Computing`.
  - Interest aliases (canonical → phrases): `Cybersecurity` (`security focused`, `infosec`, `pen testing`, `soc`, `incident response`, …), `Cloud / DevOps` (`dev ops`, `k8s`, `kubernetes`, `infrastructure`, `ci cd`, …), `Software Development` (`software`, `backend`, `frontend`, `full stack`, `apis`, …), `Data Engineering` (`etl`, `data pipelines`, …), `Data Science` (`machine learning`, `ai`, `ml`, `nlp`, …), `QA/Testing`, `FinTech`.
  - Interest → opportunity-side keywords (for rubric matching) including legacy labels (`Artificial Intelligence`, `Information Systems`, `Computer Engineering`).
  - City aliases: `alkhobar` / `al khobar` / `al-khobar` → `Khobar`; `ad dammam` / `ad-dammam` → `Dammam`; `ar riyadh` / `ar-riyadh` → `Riyadh`; `jedda` → `Jeddah`; `al dhahran` / `al-dhahran` → `Dhahran`; plus existing Saudi cities. Broader location tokens (`remote`, `ksa`, `saudi arabia`) are kept in a separate `EXTENDED_LOCATION_ALIASES` dict and are NOT applied as primary-city detection so they cannot stomp on work-mode parsing for messages such as "looking for a remote COOP".
  - Skill aliases: `dev ops` → `devops`, `k8s` → `kubernetes`, `pen testing` / `pentesting` → `penetration testing`, `cyber security` / `infosec` → `cybersecurity`, `prompt testing` → `prompt engineering`, `ci cd` / `cicd` → `cicd`, `reactjs` → `react`.
- **Parser (`app.parser`).**
  - City detection now uses `find_city_in_text` from the taxonomy → multi-spelling Saudi cities normalise to their canonical form.
  - Skill-alias normalisation is now delegated to `normalise_skill_aliases` (parser still keeps `machine learning` / `devsecops` / `powerbi` / `scikit-learn` cleanups inline because they run before the alias pass).
  - Interest detection now uses `find_interest_in_text` from the taxonomy with earliest-match + longest-tie-break semantics. Explicit text interest still overrides the major default.
  - When an interest is detected but no specific job title is present, `preferred_roles` is seeded from `INTEREST_TO_ROLE_CLUSTERS` (e.g. `interest=Cybersecurity` → `["Cybersecurity", "SOC Analyst", "Network Security", "Penetration Testing"]`). Explicitly detected roles always win.
  - Added new skill keywords: `network security`, `incident response`, `vulnerability assessment`, `cicd`.
- **Rubric (`app.rubric`).** `compute_role_interest_score` gained an ML-2A cluster pass:
  - If `profile.interest` is in the taxonomy, opportunity-side cluster keywords are checked. A hit in the title / inferred role cluster returns **0.8**; a hit only in the requirements / `skills_list` returns **0.6** (partial match).
  - The existing direct-token, ROLE_EXACT_KEYWORDS, family-overlap, and `0.3` generic-technical-term fallback paths remain in place. A cybersecurity-focused student no longer gets over-boosted on a plain software listing — that case still returns `0.3`.
- **Tests.** 18 new parser tests (city aliases, security-focused interest, skill aliases, cluster role seeding) and 4 new recommender tests (cybersecurity-vs-software cluster scoring, Cloud / DevOps cluster, partial-match-via-skills-only, alkhobar end-to-end via `recommend_from_message`).

**What did NOT change.**

- Frontend UI (chat, fit shelf, search, parsed-profile card) untouched.
- Auth / login surface unchanged.
- `/recommend` response shape unchanged (no new required fields).
- No database persistence added.
- No ML model training, integration, or weight changes.
- Existing rubric weights and existing `compute_*` scorers other than `compute_role_interest_score` are byte-identical.

**Why.** The parser previously sent a CS student saying "security focused" to the Software Development cluster and dropped "alkhobar" entirely, which led to weak / off-topic recommendations. ML-2A fixes the parser/rubric quality before any model training so the supervised dataset and the live API agree on canonical labels.

**Test results.** `pytest tests/test_parser.py` → 67/67 passed. `pytest tests/test_recommender.py` → 34/34 passed. `pytest tests/test_regression_dataset.py` → 9/9 passed. `pytest tests/test_scoring.py` → 39/39 passed. Manual CLI smoke test (`npm run run:terminal` equivalent via piped input) verified `major=CS`, `city=Khobar`, `interest=Cybersecurity` for "I am a CS student in alkhobar looking for security focused opportunities", and skills persist (`docker, linux, networking, penetration testing`) after the second turn with security-leaning top recommendations (Help AG Cybersecurity Intern, Cisco NetVersity, TrendAI CyberGATE, National Cybersecurity Authority).

---

## 2026-05-28 — Phase ML-2B: practical recommender hardening for course-demo quality

**Where.** `backend/app/opportunity_enrichment.py` (new), `backend/app/rubric.py`, `scripts/careerfinder_cli.py`, `tests/test_parser.py`, `tests/test_recommender.py`, `docs/tracking/*`.

**What changed.**

### Backend — opportunity enrichment layer

- **New module `app.opportunity_enrichment`.** Pure-Python runtime inference. `enrich_opportunity_signals(opportunity)` returns `{"role_cluster", "inferred_interests", "inferred_skills"}`. The source Excel is never mutated; no database persistence.
- **Five buckets** (priority order):
  - `telecom_network` — triggers include STC / Mobily / Zain / telecom / network / infrastructure / NOC. Inferred interests `[Cybersecurity, Cloud / DevOps]`. Inferred skills `[networking, network security, cybersecurity, linux, cloud]`.
  - `cybersecurity` — triggers include cybersecurity / SOC / SIEM / pentest / vulnerability / incident response / firewall. Inferred interests `[Cybersecurity]`. Inferred skills include `cybersecurity, soc, siem, network security, penetration testing, linux, incident response, vulnerability assessment, networking`.
  - `bank_fintech` — triggers include bank / fintech / Al Rajhi / SNB / Riyad Bank / STCpay / Tabby / Tamara / payments. Inferred interests `[FinTech, Software Development, Data Science, Cybersecurity]`. Inferred skills `[sql, python, api, cybersecurity, data analysis]`.
  - `ai_data` — triggers include AI / machine learning / data science / data engineering / SDAIA / Wakeb / NLP / ETL. Inferred interests `[Data Science, Data Engineering]`. Inferred skills `[python, sql, machine learning, data analysis]`.
  - `software` — triggers include software engineer / backend / frontend / full stack / developer / web development / APIs. Inferred interests `[Software Development]`. Inferred skills `[python, api, sql, git]`.
- **Role cluster** is only proposed when the opportunity does not already declare one. Multiple buckets may fire simultaneously — their `inferred_skills` and `inferred_interests` are unioned (order-preserving, case-insensitive dedupe).

### Backend — rubric integration

- **`compute_skill_match_score` (rubric.py).** Per-token weighted match: 1.0 for an explicit hit in the opportunity's title / requirements / declared `skills_list` / inferred role cluster, 0.5 for an inferred-only hit in `enrich_opportunity_signals(opp)["inferred_skills"]`. Final score still `sum / len(tokens)` and clamped in `[0, 1]`. Inferred skills can help a borderline match but cannot outrank an opportunity that names the skill explicitly.
- **`compute_role_interest_score` (rubric.py).** Added a new weak-signal path: if the profile's `interest` appears in `enrich_opportunity_signals(opp)["inferred_interests"]`, return `0.5`. Inserted between the role-family overlap (0.6) and the generic-technical fallback (0.3). The existing direct-token (1.0), ROLE_EXACT_KEYWORDS (1.0), taxonomy cluster (0.8 / 0.6), and family overlap (0.6) paths are unchanged.
- **Rubric weights are unchanged.** `TARGET_WEIGHTS` is byte-identical. Only the per-component definitions of `skill_match_score` and `role_interest_score` learned about secondary inferred signals.

### Terminal — accidental input guard, /undo, /history (Part A)

- `is_accidental_input(line)` flags empty / single-letter (`"n"`, `"y"`, `"Y"`) / `/n`, `/y` style typos. The CLI prints `"That looks accidental. Type a full message, /help, /details 1, or /exit."` and never calls `/recommend` or appends the input to the message history.
- `/undo` removes the last accepted user message. If at least one remains, the CLI silently reruns `/recommend` with the trimmed combined message; if none remain, the latest profile and recommendations are cleared.
- `/history` prints numbered remembered user messages (real input only — accidental input never reaches the list).

### Terminal — loading pattern (Part B)

- After each accepted message the CLI echoes the input (`> {message}`), prints a 3-step text spinner (`Analyzing profile.` → `..` → `...` over ~1 s), then prints `Calling POST http://127.0.0.1:8000/recommend ...`. The spinner falls back to a single line when stdout is not a TTY so piped / captured runs stay clean.

### Terminal — fixed-width compact table (Part C)

- `_compact_column_widths(width)` returns widths for `rank=4`, `score=6`, `company=28`, `program=32`, `city=14`, `mode=12`, `missing=remaining`. On narrow terminals the company and program columns shrink proportionally while keeping `missing >= 12`. Header and rows are joined with a two-space gutter so columns stay aligned. Row contents are truncated with `truncate(...)` and an ellipsis.
- Tip line changed from `"Tip: /details N for full info · /open N to open link · /links for URLs"` to `"Commands: /details 1 | /open 1 | /links | /undo | /history | /help"`.

### Terminal — clearer assistant output (Part D)

- Section headers use `=== Label ===` (rendered bold via ANSI when `sys.stdout.isatty()` and the terminal supports it; plain text otherwise). Applied to `Profile`, `Assistant`, `Top N (compact)`, `Details #N`, `Ranked links`, and `History`.
- The old `--- Profile ---` / `Assistant>` / `--- Top N (compact) ---` lines are replaced.

### Terminal — score-change explanation (Part G)

- After each backend response the CLI compares the new top score and profile to the previous turn and emits short notes:
  - top score dropped 5+ points → `"Note: Your top score dropped because the new details made the search more specific."`
  - interest changed → `"Interest changed from X to Y, so results were reranked."`
  - new skills detected → `"New skills added: a, b."`
  - city / work mode / program type changed → one-line note each.

### Tests added

- **`test_parser.py`** (+3): `security focused` still maps to `Cybersecurity`; `alkhobar` still normalises to `Khobar`; `"I want role in DevOps"` parses to `interest=Cloud / DevOps`, `devops` skill, and `Cloud / DevOps` preferred role.
- **`test_recommender.py`** (+5): telecom opportunity receives inferred network / security / cloud signals; enrichment does not override an existing `role_cluster`; security-focused profile scores a telecom opp above generic software via inferred signals; DevOps profile scores cloud opp above data opp; inferred skills score below explicit skills for the same profile.

**What did NOT change.**

- Frontend UI (chat, fit shelf, search, parsed-profile card, login).
- Auth / login surface.
- `/recommend` response shape — no new required fields.
- No database persistence.
- No model training or weight changes.
- Rubric `TARGET_WEIGHTS` byte-identical.

**Why.** Course-demo readiness. Before ML-2B the recommender could silently re-rank when a student added a detail without explaining why; the dataset had weak metadata so security-focused students saw plain software listings inflated by generic-term fallbacks; the terminal accepted single-keystroke typos as real messages. ML-2B closes those four gaps without retraining anything.

**Test results.** `pytest tests/test_parser.py` → 70/70 passed. `pytest tests/test_recommender.py` → 39/39 passed. `pytest tests/test_regression_dataset.py` → 9/9 passed. `pytest tests/test_scoring.py` → 39/39 passed. Manual CLI walkthrough (backend running on `127.0.0.1:8000`): `N` → accidental message; `/n` → accidental message; `"im a cs student in alkhobar, and im looking for security focused opportunities."` → `major=CS, city=Khobar, interest=Cybersecurity`, top match Cisco NetVersity 70 %; `"I know SQL"` → `skills=[sql]`, "New skills added: sql." note; `"I want role in DevOps"` → `skills=[sql, devops]`, top match Bosch SDE 69 %, "Note: Your top score dropped because the new details made the search more specific." + "New skills added: devops."; `/history` → three numbered real messages; `/undo` → removes the last message and reruns showing the prior top-5.

---

## 2026-05-28 — Phase ML-2B.1: required vs preferred role-skill profile enrichment

**Where.** `backend/app/opportunity_enrichment.py`, `backend/app/rubric.py`, `backend/app/recommender.py`, `backend/app/schemas.py`, `tests/test_recommender.py`, `docs/tracking/*`.

**What changed.**

### Backend — role skill profiles (Part A)

- **New constant `ROLE_SKILL_PROFILES`** in `opportunity_enrichment.py`. Ten simple course-demo profiles, each with `required` and `preferred` skill lists:
  - `Cybersecurity` — required: linux, networking, cybersecurity fundamentals; preferred: siem, soc, penetration testing, incident response, vulnerability assessment.
  - `Network Security` — required: networking, linux, security fundamentals; preferred: firewall, siem, incident response, network monitoring.
  - `Cloud / DevOps` — required: linux, docker, git; preferred: kubernetes, ci/cd, aws, azure, terraform, cloud.
  - `Backend Engineering` — required: python, apis, sql, git; preferred: docker, testing, cloud, rest apis.
  - `Frontend Engineering` — required: javascript, html, css, react; preferred: typescript, ui testing, apis.
  - `Data Engineering` — required: sql, python, etl; preferred: pipelines, spark, data warehouse, bi.
  - `Data Science` — required: python, sql, data analysis; preferred: machine learning, statistics, pandas, visualization.
  - `AI / Machine Learning` — required: python, machine learning, data analysis; preferred: nlp, llm, model training, tensorflow, pytorch.
  - `QA / Testing` — required: testing, documentation, problem solving; preferred: test automation, qa, selenium, api testing.
  - `General Computing` — required: problem solving, basic programming; preferred: git, sql, communication.
- Each ML-2B bucket gained `skill_profile_keys` so when a bucket fires it also fires the right role profile(s) — e.g. `telecom_network` fires `[Network Security, Cybersecurity]`, `cybersecurity` fires `[Cybersecurity, Network Security]`, `ai_data` fires `[AI / Machine Learning, Data Engineering]`.
- New helper `_skill_profile_keys_from_opportunity(opp)` scans the opportunity's combined text (company + title + role_cluster + requirements + skills_list) against a curated needle list (`_ROLE_CLUSTER_TO_PROFILE_KEY`, ordered most-specific-first) and returns every matching profile key. This catches opportunities whose role signal lives in the dataset's requirements / skills_list rather than the title (e.g. a Deloitte internship whose skills_list says "Networking Fundamentals").

### Backend — extended enrichment (Part B)

- `enrich_opportunity_signals(opportunity)` now returns five keys:
  - `role_cluster` (existing — only set when the opportunity does not declare one)
  - `inferred_interests` (existing)
  - `inferred_skills` (existing)
  - `required_skills` (new) — union of `required` lists from every fired profile, lowercase, deduped.
  - `preferred_skills` (new) — union of `preferred` lists from every fired profile, lowercase, deduped, never overlapping with `required_skills` (required wins).

### Backend — scoring weights (Part C)

- `compute_skill_match_score` per-token weights (`TARGET_WEIGHTS` unchanged):
  - Explicit hit in title / requirements / declared skills_list / inferred role cluster → 1.0.
  - **New:** inferred required-skill hit → 0.7.
  - Generic inferred-skill hit (in `inferred_skills` but not required / preferred) → 0.5.
  - **New:** inferred preferred-skill hit → 0.4.
  - Check order: explicit → required → generic → preferred. A skill that is "preferred for this role" AND in the bucket-derived inferred pool counts as the higher 0.5, so the cap stays sensible while pure preferred-only hits stay weak.
- Maximum inferred-only skill score per token is 0.7, so enriched signals alone can never push the skill component to 1.0.

### Backend — missing-skills ordering (Part D)

- `compute_missing_skills(profile, opportunity, *, max_count=8)` now orders gaps as:
  1. Missing **required** skills from the role profile.
  2. Missing **preferred** skills from the role profile.
  3. Any remaining explicit `opportunity.skills_list` entries the student doesn't have.
- Capped at 8 entries (`MISSING_SKILLS_MAX = 8`). Case-insensitive dedupe. Noise tokens (`Not stated`, `nan`, `n/a`, empty) filtered.
- Two new sibling helpers expose the split:
  - `compute_missing_required_skills(profile, opp)` — only the profile-derived required gaps.
  - `compute_missing_preferred_skills(profile, opp)` — only the profile-derived preferred gaps (never overlaps with required).

### Backend — schema additions

- `Opportunity` schema gained two optional list fields:
  - `missing_required_skills: List[str]` — populated by the recommender. Empty when the opp does not map to a known role profile.
  - `missing_preferred_skills: List[str]` — companion to required. Never overlaps with required.
- Both default to `[]` so existing callers / tests / TypeScript adapters are unaffected. The frontend `OpportunityApi` type was intentionally left untouched per the "no UI changes" constraint — extra JSON keys are ignored by the existing adapter.

### Recommender

- `recommend()` now populates `missing_required_skills` and `missing_preferred_skills` on every returned opportunity in addition to the existing `missing_skills`.

### Tests added (Part E)

- **`test_recommender.py`** (+9):
  - Profile shape: Cybersecurity required/preferred contains Linux/networking/cybersecurity fundamentals + SIEM/SOC/penetration testing.
  - Profile shape: Cloud / DevOps required/preferred contains Linux/Docker/Git + Kubernetes/CI-CD/AWS/cloud.
  - Enrichment carries Cybersecurity required/preferred for a cyber opp; preferred never overlaps with required.
  - Title-only fallback: `"Cloud Engineer COOP"` (no requirements, no skills_list) still picks up the Cloud / DevOps profile.
  - Required-weighted-higher-than-preferred: profile knowing only `linux` (required) outscores profile knowing only `firewall` (preferred-only) against the same cyber opp, with scores ≈ 0.7 vs ≈ 0.4.
  - Explicit > inferred: explicit `linux` in skills_list scores 1.0, inferred-only scores ~0.7.
  - Ordering: missing_skills puts required gaps before preferred gaps; companion lists never overlap.
  - Exclusion: student-has `linux` is removed from all three missing lists.
  - End-to-end: `recommend()` populates the new schema fields with non-overlapping required / preferred gaps.

**What did NOT change.**

- Frontend UI (chat, fit shelf, search, parsed-profile card, login).
- Auth / login surface.
- `/recommend` response shape gains two optional fields (default `[]`) — no breaking change.
- No database persistence.
- No model training or rubric weight changes (`TARGET_WEIGHTS` byte-identical).
- The ML-2B opportunity enrichment buckets and ML-2B CLI behaviour are unchanged.

**Why.** Course-demo readiness. Before ML-2B.1 every inferred-skill match counted the same (0.5), so a student who learned a high-signal "required for the role" skill (e.g. Linux for a cybersecurity role) saw the same lift as adding a niche preferred skill. Required-vs-preferred weighting now reflects the realistic intuition that students need the core skills first, and the missing-skills list now nudges them toward the most impactful gaps before the nice-to-haves.

**Test results.** `pytest tests/test_parser.py` → 70/70 passed. `pytest tests/test_recommender.py` → 48/48 passed. `pytest tests/test_regression_dataset.py` → 9/9 passed. `pytest tests/test_scoring.py` → 39/39 passed.

**Manual CLI walkthrough.** Backend booted on `127.0.0.1:8000`. Inputs piped to `python scripts/careerfinder_cli.py`:

1. `"im a cs student in alkhobar looking for security focused opportunities"` → `major=CS, city=Khobar, interest=Cybersecurity`. Top-5: Cisco NetVersity 70 %, Saudi FDA 67 %, Bank Albilad 67 %, NHC 67 %, Deloitte 64 %.
2. `"I know Linux and networking"` → skills `[linux, networking]`. **Scores jumped:** Cisco 70→79, Deloitte 64→74, Schneider new at 74, Saudi FDA 67→73, Bank Albilad 67→73. Score-change note: `"New skills added: linux, networking."`. Deloitte `/details 2` Missing skills: `security fundamentals, cybersecurity fundamentals, firewall, siem, incident response, network monitoring, soc, penetration testing` — required (security fundamentals, cybersecurity fundamentals) **before** preferred (firewall, siem, …).
3. `"I know penetration testing too"` → skills `[linux, networking, penetration testing]`. Top-5: Cisco 75 %, **Help AG Cybersecurity Intern 73 %** (newly surfaced into top), Saudi FDA 71 %, Bank Albilad 71 %, NHC 71 %. Help AG `/details 2` Missing skills: `security fundamentals, cybersecurity fundamentals, firewall, siem, incident response, network monitoring, soc, vulnerability assessment` — student's `penetration testing` correctly removed from missing; required before preferred preserved; matched skills now include `networking, penetration testing`.

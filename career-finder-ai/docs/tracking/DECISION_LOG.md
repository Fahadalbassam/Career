# DECISION_LOG

Architectural and product decisions that constrain every later phase. New decisions append to the bottom with a date and rationale.

---

## D-001 — Keep the existing frontend visual identity

**Decision.** The black/white minimal CareerFinder.ai aesthetic, the home hero, the methodology page, the chat composer, the side-shelf 3D tilt + flip, and the home↔chat↔search animation choreography are **frozen**. Any future change adds to the **back** of cards or to off-screen logic, never to the **front** layout.

**Why.** The visual surface is already production-quality and emotionally tied to the brand. Re-doing it would be expensive and high-risk. The product story is clearer when the brand stays consistent across the wiring work.

**Date.** 2026-05-27.

---

## D-002 — Chat is the primary experience

**Decision.** `/chat` is the main surface. Everything else (search, dashboard, model) is supplementary. Onboarding flows, marketing copy, and the home CTA all funnel into `/chat`.

**Why.** A conversational interface is the cheapest way to elicit a structured profile from a non-technical Saudi student without forcing a long signup form. It also lets the system ask for missing information naturally.

**Date.** 2026-05-27.

---

## D-003 — Side cards become a real Fit Shelf

**Decision.** The two side shelves in the chat layout are not decoration. They are the **primary output surface** of the recommender. The left rail shows current best matches; the right rail shows alternative / growth matches. Cards update progressively as the profile becomes more complete.

**Why.** Putting the ranked output beside the conversation lets the student see recommendations evolve turn by turn without breaking flow. It also reuses the strongest visual element already built.

**Date.** 2026-05-27.

---

## D-004 — Search is manual opportunity search only for now

**Decision.** `/search` is a structured filter over the opportunity database. It is not a user-facing app for sign-up, ratings, recruiter accounts, or community features. Filters are: `keyword`, `company`, `city`, `major`, `role_cluster`, `program_type`, `work_mode`, `skill`, `interview_required`, `min_match_score`, `verified_only`.

**Why.** Students sometimes want to browse without describing themselves. Anything beyond filtering is scope creep at this stage and would compete with `/chat` for product focus.

**Date.** 2026-05-27.

---

## D-005 — No users, ratings, recruiters, or accounts (yet)

**Decision.** The product ships **without** any of: sign-up, login, persisted user profiles, ratings, reviews, recruiter dashboards, employer posting forms, saved-searches-on-server, email digests. All chat state lives in the client session.

**Why.** Each of those surfaces adds significant compliance, moderation, and storage cost. The current goal is to prove that the recommender helps Saudi students; auth and community can come later.

**Date.** 2026-05-27.

---

## D-006 — Backend uses 0–100 `match_score`

**Decision.** The recommendation score exposed to the frontend is an integer **0–100** named `match_score`. The legacy 0–1 `score` is kept only for backend backward compatibility and equals `match_score / 100`. The UI binds `match_score` directly to `ScoreBadge.scorePercent`. No rescaling on the frontend.

**Why.** A 0–100 number reads naturally to a student ("87% match") and matches the existing `ScoreBadge` design without modification. Two different scales would inevitably drift.

**Date.** 2026-05-27.

---

## D-007 — Frontend maps snake_case backend fields to camelCase UI types via an adapter

**Decision.** The backend stays snake_case (Python convention). The frontend stays camelCase (TypeScript / React convention). The bridge is a single `frontend/src/lib/api-adapters.ts` module that converts snake_case `Opportunity` / `ParsedProfile` payloads into the existing camelCase `Recommendation` / `StudentProfile` types. New fields are added as **optional** on the camelCase types so existing components keep compiling.

**Why.** Editing types in place would silently break `RecommendationCard`, `ParsedProfileCard`, `ActiveFinalizedFitCard`, and `recommendationToMemory`. An adapter is the safe migration path.

**Date.** 2026-05-27.

---

## D-009 — Anonymous users store chat profile in browser localStorage

**Decision.** When no user account exists, the accumulated session profile (merged `StudentProfile` from all turns) and the list of user messages are persisted to `localStorage` under the key `careerfinder.ai.anonymousChatSession.v1`. No cookies are used for full profile storage. No profile data is sent to a database at this stage.

**Why.** Students routinely refresh the browser or navigate away mid-session. Losing the accumulated profile on every reload forces them to repeat themselves, which is a core UX failure. localStorage is zero-friction, works without an account, and keeps all data on the client. Cookies are not used because they add unnecessary server-round-trip complexity and a smaller storage limit.

**Future.** When user accounts (login) are implemented, the local session data can be synced to the server as part of the sign-in flow, then the localStorage entry can be cleared.

**Date.** 2026-05-28.

---

## D-010 — Logged-in database persistence deferred to accounts phase

**Decision.** Database persistence of the student profile is explicitly deferred until user accounts are implemented (a later phase). The current implementation is client-side only. This ensures no GDPR/PDPA compliance work is needed now and keeps the architecture simple.

**Date.** 2026-05-28.

---

## D-011 — Auth uses backend-issued opaque HttpOnly sessions, not localStorage tokens

**Decision.** When real authentication is implemented, the session identifier is an opaque server-side value stored in an `HttpOnly` cookie (`cf_session`). JavaScript must not read or persist auth tokens. `localStorage` is reserved for the anonymous chat profile only (`careerfinder.ai.anonymousChatSession.v1`).

**Why.** Tokens in `localStorage` are exfiltratable by any XSS bug. HttpOnly cookies keep the session credential out of the JS attack surface. Opaque session IDs (not JWTs in the browser) simplify revocation on logout.

**Date.** 2026-05-28.

---

## D-012 — Protected routes enforced by middleware and server, not UI hiding only

**Decision.** Routes such as `/dashboard`, `/profile`, `/saved`, and `/settings` must be protected by Next.js `middleware.ts` (redirect unauthenticated users) **and** by FastAPI `Depends(get_current_user)` on every sensitive API. Hiding nav links is cosmetic only and is not sufficient protection.

**Date.** 2026-05-28.

---

## D-013 — Anonymous-to-logged-in profile import is opt-in

**Decision.** When a user logs in with a non-empty anonymous `localStorage` profile, the app must ask before importing it to the server account. Options: Import & save, Discard local, Keep local only. Never auto-import silently (shared-device risk).

**Date.** 2026-05-28.

---

## D-014 — Full backend auth deferred until Auth-2

**Decision.** Auth-0 and Auth-1 deliver documentation and a stubbed frontend shell only (`lib/auth.ts`, `AuthProvider`, `/login`, `/signup`). No `users` or `sessions` tables, no password hashing, no cookies, no middleware, and no `/auth/*` endpoints until Auth-2.

**Why.** Locks the frontend auth API (`useAuth`) and route policy before introducing a security surface. Auth-1 can be reviewed and demoed without risking half-wired credentials.

**Date.** 2026-05-28.

---

## D-008 — Use incremental implementation phases

**Decision.** Ship in eight numbered phases (see `docs/planning/ROADMAP.md`):

0. Documentation and tracking setup
1. Connect chat to backend
2. Render real recommendations in chat
3. Turn side cards into real Fit Shelf
4. Add missing-info follow-up questions
5. Add multi-turn profile memory
6. Build search page database search
7. Dashboard / model / report-ready outputs
8. Final testing and cleanup

Each phase is independently shippable and has its own acceptance criteria.

**Why.** The animation system is fragile and the backend is stateless; a single big-bang wiring pass would risk both correctness and visual regressions. Phased delivery means each surface can be verified before the next is touched.

**Date.** 2026-05-27.

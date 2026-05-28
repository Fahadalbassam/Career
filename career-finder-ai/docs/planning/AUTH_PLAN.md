# AUTH_PLAN — Authentication, Sessions, and Route Protection

Single reference for how CareerFinder.ai will handle login, logout, route protection, and user-data persistence. **Auth-0 and Auth-1 are documentation + stubbed frontend only.** Real security lands in Auth-2 onward.

---

## 1. Current auth state (as of Auth-1)

| Area | Status |
|---|---|
| Real login / signup | **No** — stubbed in `frontend/src/lib/auth.ts` |
| Login UI | **Yes** — `/login`, `/signup` pages + legacy `LoginCardDialog` (dialog unchanged) |
| Backend auth endpoints | **No** — only `/health`, `/stats`, `/parse`, `/recommend` |
| `users` / `sessions` tables | **No** |
| Next.js `middleware.ts` | **No** |
| Auth tokens in localStorage | **No** — never for auth |
| Anonymous chat profile | **Yes** — `careerfinder.ai.anonymousChatSession.v1` in localStorage |
| CORS | `allow_credentials=True` with explicit origins — ready for cookies later |

---

## 2. Recommended architecture

**FastAPI is the auth source of truth.** The Next.js app is a client; it does not issue sessions.

| Concern | Choice |
|---|---|
| Session identifier | Opaque random `session_id` (e.g. `secrets.token_urlsafe(32)`) stored server-side |
| Client transport | `HttpOnly` cookie `cf_session` — **not readable by JavaScript** |
| Auth tokens in localStorage | **Forbidden** — XSS cannot exfiltrate HttpOnly cookies |
| Anonymous profile | **localStorage only** — `chat-session.ts`; separate from auth |
| API calls when logged in | `fetch(..., { credentials: "include" })` from `lib/api.ts` |
| CSRF | Double-submit: non-HttpOnly `cf_csrf` cookie + `X-CSRF-Token` header on mutating requests (Auth-2+) |
| JWT in browser | **Not used** for v1 — revocation and CSRF are simpler with opaque sessions |
| NextAuth / Clerk | **Deferred** — adds a second identity layer; revisit for OAuth |

**Logout** invalidates the row in `sessions` (`revoked_at`) and clears the cookie (`Max-Age=0`). A stolen cookie value must not work after logout.

**Protected routes** are enforced in three layers (Auth-3+):

1. **Server** — FastAPI `Depends(get_current_user)` returns 401 without a valid session.
2. **Middleware** — `middleware.ts` redirects unauthenticated users before render.
3. **UI** — hide nav links only; never rely on UI alone.

---

## 3. Route access matrix

| Route | Policy | Enforcement (when built) |
|---|---|---|
| `/` | Public | — |
| `/chat` | Public | Anonymous chat always allowed |
| `/search` | Public | — |
| `/methodology` | Public | — |
| `/login`, `/signup` | Public | Redirect to `/` if already authed |
| `/forgot-password` | Public | Later |
| `/dashboard` | **Protected** | Middleware + `/auth/me` |
| `/profile` | **Protected** | Same |
| `/saved` | **Protected** | Same |
| `/settings` | **Protected** | Same |
| `/model` | Public for now | Protect if user-specific metrics appear |
| `/admin/*` | **Admin-only** | `user.role === "admin"` |

Public API: `/health`, `/stats`, `/parse`, `/recommend`, `/auth/signup`, `/auth/login`.

Authenticated API: `/auth/logout`, `/auth/me`, `/me/*`.

---

## 4. Database tables (Auth-2+, not created yet)

```sql
users (
  id, email UNIQUE, email_verified, password_hash,
  display_name, role DEFAULT 'student',
  created_at, last_login_at
)

sessions (
  id,                    -- cookie value
  user_id REFERENCES users,
  csrf_token,
  user_agent, ip_hash,
  created_at, last_seen_at, expires_at, revoked_at
)

user_chat_profiles (
  user_id PRIMARY KEY,
  major, university, city, preferred_locations JSON,
  skills JSON, qualifications JSON, interest,
  program_type, work_mode, preferred_roles JSON,
  interview_preference, updated_at
)

saved_recommendations (
  id, user_id, opportunity_id, snapshot_json, note, saved_at
)

user_recommendation_feedback (
  id, user_id, opportunity_id, rating, helpful, comment, created_at
)

conversation_summaries (
  id, user_id, summary, turn_count, started_at, ended_at
)
```

**Not stored:** full raw chat transcripts, plaintext passwords, OTPs after use, raw IP addresses, resume binaries in SQLite (later: object store).

---

## 5. Anonymous → logged-in import flow (Auth-5)

1. User chats anonymously; profile in `localStorage` (`chat-session.ts`).
2. User logs in; server sets HttpOnly session cookie.
3. `GET /auth/me` returns `{ user, hasServerProfile }`.
4. If local anonymous profile is non-empty and server profile is empty → **opt-in modal**:
   - **Import & save** → `POST /me/chat-profile/import` → `clearAnonymousChatSession()` on success.
   - **Discard** → clear local only.
   - **Keep local only** → no server write; user can import later from settings.
5. If server profile already exists → offer **Merge** or **Keep server profile** (default: keep server).
6. **Never auto-import silently** (shared-device risk).

---

## 6. Logout behavior (Auth-6)

1. `POST /auth/logout` with credentials + CSRF header.
2. Server sets `sessions.revoked_at`.
3. Server `Set-Cookie: cf_session=; Max-Age=0; HttpOnly; Secure; SameSite=Lax`.
4. Client clears in-memory auth (`useAuth`: `user = null`).
5. Clear user-scoped client caches (saved recs, dashboard data).
6. **Do not** call `clearAnonymousChatSession()` unless user confirms.
7. Redirect to `/`.
8. Optional: `BroadcastChannel` so other tabs clear auth state.

---

## 7. Security risks and mitigations

| Risk | Mitigation |
|---|---|
| Tokens in localStorage | Never store auth tokens there; HttpOnly cookie only |
| XSS | No `dangerouslySetInnerHTML`; CSP when auth ships |
| Session fixation | New session id on every successful login |
| Stale session after logout | `revoked_at` checked on every request |
| Client-only protection | Middleware + server `Depends` + UI |
| CSRF | `SameSite=Lax` + CSRF double-submit token |
| Password storage | Argon2/bcrypt via passlib; never log passwords |
| Brute force | Rate-limit login per IP/email; generic error messages |
| IDOR | All `/me/*` scoped to `current_user.id` only |
| Email enumeration | Ambiguous signup responses |

---

## 8. Implementation phases

| Phase | Goal | Status |
|---|---|---|
| **Auth-0** | Audit + this plan + ADRs D-011–D-014 | **Done** (this document) |
| **Auth-1** | Stub `lib/auth.ts`, `AuthProvider`, `/login`, `/signup`, navbar | **Done** (no backend) |
| **Auth-2** | FastAPI `/auth/*`, `users` + `sessions`, password hash, HttpOnly cookie | Pending |
| **Auth-3** | `middleware.ts`, CSRF, `get_current_user` | Pending |
| **Auth-4** | `user_chat_profiles` + server persistence for logged-in users | Pending |
| **Auth-5** | Opt-in anonymous profile import modal | Pending |
| **Auth-6** | Full logout + multi-tab sync | Pending |
| **Auth-7** | pytest + frontend tests for auth paths | Pending |

---

## 9. Exact next task after Auth-1

**Auth-2 — Backend auth and session endpoints.**

1. Add `users` and `sessions` tables to `database/schema.sql`.
2. Add `passlib[bcrypt]` (or `argon2-cffi`) to `requirements.txt`.
3. Implement `backend/app/auth.py`: `POST /auth/signup`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`.
4. Issue `cf_session` HttpOnly cookie on login; revoke on logout.
5. Wire `frontend/src/lib/auth.ts` to real endpoints with `credentials: "include"`.
6. Do **not** add middleware until cookie round-trip works in Postman and browser.

Do not start Auth-3 until Auth-2 cookie login/logout/me is verified end-to-end.

---

## Related files

| Layer | Files |
|---|---|
| Stub (now) | `frontend/src/lib/auth.ts`, `frontend/src/components/auth/auth-provider.tsx` |
| Pages | `frontend/src/app/login/page.tsx`, `frontend/src/app/signup/page.tsx` |
| Anonymous | `frontend/src/lib/chat-session.ts` |
| Future backend | `backend/app/auth.py`, `backend/app/security.py`, `backend/app/deps.py` |
| Future protection | `frontend/middleware.ts` |
| Decisions | `docs/tracking/DECISION_LOG.md` D-011–D-014 |

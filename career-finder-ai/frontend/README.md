# Career Finder AI — Frontend

Next.js (App Router) UI for **Career Finder AI**: Saudi COOP and internship recommendations for computing students.

**`/chat`** calls the FastAPI backend (`POST /recommend` via `src/lib/api.ts`). If the backend is unreachable, demo/mock shelf content still appears. **Auth** pages are stubs (no real login). **`/search`**, **`/dashboard`**, and **`/model`** are not final product surfaces yet.

## Prerequisites

- [Node.js](https://nodejs.org/) (LTS recommended)
- npm (bundled with Node)

## Install dependencies

From this directory (`career-finder-ai/frontend`):

```bash
npm install
```

This installs **devDependencies** as well (including `@playwright/test`). Next.js type-checks `playwright.config.ts` during `npm run build`, so a production-only install (`npm install --omit=dev`) will fail the build. Use a full install before `npm run build` or `npm run test:e2e`.

## Run the development server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The app uses the Next.js App Router under `src/app/`.

Other scripts:

- `npm run build` — production build
- `npm run start` — serve production build
- `npm run lint` — ESLint
- `npm run test:e2e` — Playwright smoke tests (starts backend + dev server; run `npx playwright install chromium` once)
- `npm run test:e2e:ui` — Playwright UI mode

## Pages

| Route | Description |
|-------|-------------|
| `/` | Marketing-style home: hero, CTAs to chat and search, three feature cards |
| `/chat` | Career-match chat (backend `/recommend` + Fit Shelf; mock fallback if API down) |
| `/search` | Shell route — structured search UI not wired yet |
| `/dashboard` | Placeholder for saved progress and history |
| `/model` | Placeholder for model documentation |
| `/methodology` | Methodology and data explainers |
| `/login`, `/signup` | Auth stub pages |

Global chrome: top **Career Finder AI** navbar with links to all of the above. The root layout wraps the tree with shadcn/ui **`TooltipProvider`** for tooltip primitives.

## Stack

- **Next.js** (App Router), **React**, **TypeScript**
- **Tailwind CSS** v4 and **shadcn/ui** (Radix-based components in `src/components/ui/`)

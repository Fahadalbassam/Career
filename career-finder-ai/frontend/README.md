# Career Finder AI — Frontend

Next.js (App Router) UI for **Career Finder AI**: Saudi COOP and internship recommendations for computing students. This package currently ships **layout, navigation, and placeholder routes** only — no backend, auth, or database calls yet.

## Prerequisites

- [Node.js](https://nodejs.org/) (LTS recommended)
- npm (bundled with Node)

## Install dependencies

From this directory (`career-finder-ai/frontend`):

```bash
npm install
```

## Run the development server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The app uses the Next.js App Router under `src/app/`.

Other scripts:

- `npm run build` — production build
- `npm run start` — serve production build
- `npm run lint` — ESLint

## Pages

| Route | Description |
|-------|-------------|
| `/` | Marketing-style home: hero, CTAs to chat and search, three feature cards |
| `/chat` | Placeholder for the future career-match conversation |
| `/search` | Placeholder for manual browsing / filters |
| `/dashboard` | Placeholder for saved progress and history |
| `/model` | Placeholder for model documentation |
| `/methodology` | Placeholder for methodology and data explainers |

Global chrome: top **Career Finder AI** navbar with links to all of the above. The root layout wraps the tree with shadcn/ui **`TooltipProvider`** for tooltip primitives.

## Stack

- **Next.js** (App Router), **React**, **TypeScript**
- **Tailwind CSS** v4 and **shadcn/ui** (Radix-based components in `src/components/ui/`)

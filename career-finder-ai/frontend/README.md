# Frontend – Career Finder AI

> **Status: Placeholder – Do not build yet.**

The final frontend UI for Career Finder AI may use the following stack:

- **Next.js** (React framework)
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui** component library

---

## ⚠️ Build Order – Frontend comes last

Please complete the following steps **before** starting frontend development:

1. ✅ Dataset cleaning (`data/` + `backend/app/clean_data.py`)
2. ✅ ML model training (`backend/app/train_model.py`)
3. ✅ Recommender engine (`backend/app/recommender.py`)
4. ✅ Backend API working and tested (`backend/app/main.py`)
5. 🔜 **Then** start frontend polish

---

## When Ready – Setup Commands

```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app
npx shadcn@latest init
npx shadcn@latest add button card input badge select textarea separator tabs dialog
```

---

## Planned Pages

| Page | Description |
|------|-------------|
| `/` | Landing page with search/chat input |
| `/results` | Top 5 recommendation cards |
| `/opportunity/[id]` | Opportunity detail page |
| `/about` | Project info and team |

---

## Notes

- The backend API will be consumed via `fetch` / `axios` from the Next.js frontend.
- Environment variable `NEXT_PUBLIC_API_URL` will point to the FastAPI backend.
- Components will use `shadcn/ui` for consistent, accessible UI elements.

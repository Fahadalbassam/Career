# SPRINT-1 — Terminal UX and location flexibility

## What changed

### Terminal CLI (`scripts/careerfinder_cli.py`)

- Replaced header with the wide CareerFinder ASCII logo (white ANSI when supported).
- Brand line `CareerFinder ● ai` with a light-green dot (●) under the logo.
- Subtitle: Saudi COOP & internship recommender for computing students.
- **`/reset`** and **`/home`**: clear screen, wipe session messages/profile/recommendations, return to logo + welcome menu (like restarting the CLI).
- **`/clear`**: clear screen and redraw header only; session state is kept (documented in `/help`).
- **`/help`**: updated command list per sprint spec (existing commands retained under “Also available”).
- Profile block shows **City/Home city**, **Preferred locations**, **Acceptable locations**, and **Location flexibility** when parsed.

### Parser (`backend/app/parser.py`, `backend/app/schemas.py`, `backend/app/taxonomy.py`)

- Optional fields: `home_city`, `acceptable_locations`, `location_flexibility` (plus existing `city`, `preferred_locations`).
- Phrase-aware location resolution: home (“I’m in”, “I live in”), flexibility (“don’t mind”, “idm”, “can travel to”, “fine with”, …), “looking for coops in …”, Eastern Province → Dammam/Khobar/Dhahran.
- City aliases unchanged in taxonomy (`alkhobar` → Khobar, etc.).

### Scoring (`backend/app/rubric.py`, `backend/app/scoring.py`)

- Live rubric `compute_city_match_score`: preferred/home/exact **1.0**, acceptable **0.85**, Eastern Province cluster **0.7**, Saudi Arabia/Multiple/remote opp **0.5**, not stated **0.3**, no match **0.0**.
- Legacy `scoring.city_match_score` aligned for unit tests.

## Why location flexibility matters

Students often live in one city but accept COOPs elsewhere. Strict binary city matching hid strong Riyadh/Jeddah roles for flexible Khobar/Dammam users. Graduated location scoring keeps Eastern Province priority while still surfacing strong out-of-region matches.

## Example parsed profiles

| Input | Key fields |
|-------|------------|
| I'm in Khobar but I don't mind going to Riyadh or Jeddah for COOP | `city`/`home_city`: Khobar; `preferred_locations`: [Khobar]; `acceptable_locations`: [Riyadh, Jeddah]; `location_flexibility`: flexible |
| I'm looking for COOPs in Riyadh | `city`: Riyadh |
| I live in Dammam but Riyadh is fine | `home_city`: Dammam; `acceptable_locations`: [Riyadh]; flexibility moderate/flexible |
| I prefer Eastern Province but I can travel to Jeddah | `preferred_locations`: Dammam, Khobar, Dhahran; `acceptable_locations`: [Jeddah] |
| Alkhobar | `city`: Khobar |

## Tests run

```bash
cd career-finder-ai/backend
python -m pytest tests/test_parser.py tests/test_recommender.py tests/test_input_robustness.py \
  tests/test_assistant_reply.py tests/test_cli_ml_commands.py tests/test_scoring.py -q
```

**Result:** 254 passed.

```bash
cd career-finder-ai/frontend
npm run lint    # pass
npm run build   # fails: missing @playwright/test types (pre-existing Playwright config in TS check path)
```

## Known limitations

- “Open to internships in Riyadh and Jeddah” is treated as preferred cities, not flexibility (by design).
- Region aliases beyond Eastern Province are not expanded.
- CLI logo colors depend on ANSI/Windows Terminal; fallback text remains readable without color.
- Frontend build still type-checks `playwright.config.ts` without devDependency installed in this environment.

## ML and ranking

- **No ML retraining.**
- **Ranking remains rubric-based** (`match_score`, `score_source=rubric`).
- No change to `TARGET_WEIGHTS`; only `compute_city_match_score` rules were extended.

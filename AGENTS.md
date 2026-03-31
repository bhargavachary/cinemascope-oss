# AGENTS.md — CinemaScope (movies-series-tracker)

Personal Movies and TV Series watchlist manager.
Static frontend (no build step) + Python admin backend.

---

## Architecture

```
index.html              ← main watchlist UI (static, plain HTML/CSS/JS — no bundler)
table.html              ← alternate table view
style.css / css/        ← styles
script.js / js/app.js   ← frontend logic
data/                   ← JSON data files — source of truth (scripts read/write here)
scripts/
  fetch_ratings.py      ← fetch OMDB/TMDB ratings
  fetch_assets.py       ← fetch posters (Indian-first priority)
  fetch_posters.py      ← poster fetching variant
  enhance_library.py    ← enrich metadata
server.py               ← Flask local admin server (OMDB_API_KEY env var, port 8080)
requirements.txt        ← requests, flask
```

---

## Environment

```bash
conda activate base   # use base conda env — do NOT use the legacy venv/ directory
```

- `OMDB_API_KEY` must come from environment variable — never hardcoded
- Frontend is static — open `index.html` in browser or serve via `server.py`

---

## Commands

```bash
conda activate base
OMDB_API_KEY=your_key python3 server.py   # admin server at localhost:8080
python3 scripts/fetch_ratings.py          # refresh ratings
python3 scripts/fetch_assets.py           # refresh posters (Indian-first)
```

---

## Rules

- `index.html` and `table.html` are **intentionally self-contained** — no bundler, no npm
- `data/` JSON files are the **source of truth** — scripts read/write them; never hardcode data in HTML
- **Indian-first poster fetching** priority — maintain in `fetch_assets.py` and `fetch_posters.py`
- `OMDB_API_KEY` from environment only — never commit it
- Do **not** add a build system or npm
- Do **not** split static HTML into components
- The `venv/` directory is legacy — always use `conda activate base`

---

## Owner

**D K Bhargav Achary** — sole maintainer.

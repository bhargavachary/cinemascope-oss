# movies-series-tracker (CinemaScope) — Claude Context

Personal Movies and TV Series watchlist manager. Static frontend with Python admin backend.
No framework — plain HTML/CSS/JS frontend, Flask local admin server.

## Architecture
```
index.html      ← main watchlist UI (static, no build step)
table.html      ← alternate table view
style.css       ← global styles
script.js       ← frontend JS
data/           ← JSON data files (source of truth — scripts read/write here)
js/app.js       ← additional frontend logic
css/            ← additional stylesheets
scripts/
  fetch_ratings.py      ← fetch OMDB/TMDB ratings
  fetch_assets.py       ← fetch posters (Indian-first priority)
  fetch_posters.py      ← poster fetching variant
  enhance_library.py    ← enrich metadata
  screenshot_preview.py
  export_codebase.py
  update_readme.py
server.py       ← Flask local admin server (OMDB_API_KEY env var required, port 8080)
requirements.txt ← requests, flask
```

## Environment
- Python — use `base` conda env (no dedicated env; a `venv/` dir exists but ignore it — use conda)
  ```bash
  conda activate base
  ```
- `OMDB_API_KEY` env var required for server and rating scripts — never hardcode it
- Frontend is static — open `index.html` directly in browser or serve via Flask

## Common Tasks
```bash
conda activate base
OMDB_API_KEY=your_key python3 server.py   # admin server at localhost:8080
python3 scripts/fetch_ratings.py          # refresh ratings
python3 scripts/fetch_assets.py           # refresh posters
```

## Key Rules
- `index.html` and `table.html` are intentionally self-contained — no bundler, no npm
- `data/` JSON files are the source of truth — scripts read/write them; never hardcode data in HTML
- Indian-first poster fetching priority — maintain this in `fetch_assets.py` and `fetch_posters.py`
- `OMDB_API_KEY` must come from environment, never hardcoded in source

## Do Not
- Do not add a build system or npm to this project
- Do not split the static HTML files into components
- Do not commit API keys
- Do not use the `venv/` directory — it's legacy; use conda

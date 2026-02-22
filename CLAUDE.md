# movies-series-tracker (CinemaScope) — Claude Context

Personal Movies and TV Series watchlist manager. Static frontend with Python admin backend.
No framework — plain HTML/CSS/JS frontend, Flask local admin server.

## Architecture
```
index.html      ← main watchlist UI (static, no build step)
table.html      ← alternate table view
style.css       ← global styles
script.js       ← frontend JS
data/           ← JSON data files (watchlist, metadata)
js/app.js       ← additional frontend logic
css/            ← additional stylesheets
scripts/
  fetch_ratings.py     ← fetch OMDB/TMDB ratings
  fetch_assets.py      ← fetch posters and assets
  enhance_library.py   ← enrich metadata
  screenshot_preview.py
  export_codebase.py
  update_readme.py
server.py       ← Flask local admin server (OMDB_API_KEY env var required)
requirements.txt ← requests, flask
```

## Environment
- Python — use conda env for this project
- `OMDB_API_KEY` env var required for server and rating scripts — never hardcode it
- Frontend is static — open `index.html` directly in browser or via server

## Common Tasks
```bash
OMDB_API_KEY=your_key python3 server.py    # start admin server at localhost:8080
python3 scripts/fetch_ratings.py           # refresh ratings
python3 scripts/fetch_assets.py            # refresh posters
```

## Key Rules
- `index.html` and `table.html` are intentionally self-contained — no bundler, no npm
- Data files in `data/` are the source of truth — scripts read/write them, never hardcode data in HTML
- Indian-first poster fetching priority — maintain this in `fetch_assets.py`
- `OMDB_API_KEY` must come from environment, never from code

## Do Not
- Do not add a build system or npm to this project
- Do not split the static HTML files into components
- Do not commit API keys

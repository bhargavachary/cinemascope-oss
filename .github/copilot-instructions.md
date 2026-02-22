# Copilot Instructions — movies-series-tracker (CinemaScope)

Static HTML/CSS/JS watchlist frontend + Flask Python admin backend. No framework, no bundler.

## Stack
- Frontend: plain HTML, CSS, JS — no npm, no build step
- Backend: Python / Flask (conda `base` env)
- Data: JSON files in `data/` — source of truth

## Rules
- Do not add a build system, bundler, or npm to this project
- Do not split `index.html` or `table.html` into components
- `data/` JSON files are the source of truth — scripts read/write them; never hardcode data in HTML
- `OMDB_API_KEY` must come from environment — never hardcode it
- Indian-first poster fetching priority — preserve this in `fetch_assets.py` and `fetch_posters.py`
- Use `conda activate base` — ignore the `venv/` directory (legacy)
- Never commit API keys

## Style
- Vanilla JS — no jQuery, no frameworks
- Python: PEP 8, `pathlib.Path` for file ops

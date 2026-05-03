# CinemaScope — Project Documentation

A concise, working documentation dump for the CinemaScope (movies-series-tracker) codebase.
This file collects repository layout, architecture, data schema, scripts, conventions, and developer commands — intended as a single reference for working on the project.

---

## Overview

- Purpose: Personal movies & TV series watchlist manager with a visual (mosaic) frontend and a small Flask admin backend.
- Frontend: static HTML/CSS/JS — no bundler or npm.
- Backend: Python (Flask) admin server for local metadata refresh and edits.
- Data: JSON files in `data/` are the source of truth.

---

## Quickstart (local)
1. Activate environment (project convention):

```
conda activate base
```

2. Install Python dependencies (if needed):

```
pip install -r requirements.txt
```

3. Run the local admin server (requires OMDB API key for metadata lookups):

```
OMDB_API_KEY=your_key python3 server.py
# opens admin server at http://localhost:8080
```

4. Useful one-off scripts:

```
python3 scripts/fetch_assets.py     # download posters (Indian-first priority)
python3 scripts/fetch_posters.py    # alternate poster pipeline / optimize images
python3 scripts/fetch_ratings.py    # placeholder/emulation for ratings aggregation
python3 scripts/enhance_library.py  # add inferred fields like language/genres
python3 scripts/update_readme.py    # regenerate README.md from data/library.json
```

Notes:
- Do NOT commit `OMDB_API_KEY` or `TMDB_API_KEY`. Both must come from the environment.
- The `venv/` dir is legacy; use `conda activate base` as the canonical environment.

---

## Enrichment Pipeline (CinemaScope Recommendation Pipe)

A 6-phase pipeline that enriches the library with IDs, multi-source ratings,
India OTT streaming availability, weighted scoring, and hidden sub-genre tags.

### Required environment variables

| Variable        | Used by                              | Purpose                                   |
|-----------------|--------------------------------------|-------------------------------------------|
| `TMDB_API_KEY`  | id_resolver, data_harvester, ott_locator, server.py | TMDB search, metadata, watch providers |
| `OMDB_API_KEY`  | data_harvester, server.py            | IMDb / RT / Metacritic ratings            |

### Run the full pipeline (one-shot)

```bash
TMDB_API_KEY=... OMDB_API_KEY=... python3 scripts/enrich_library.py \
    --run-pipeline --auto

# Rebuild manifest so the frontend picks up new fields:
python3 scripts/fetch_assets.py
```

### Phase-by-phase reference

**Phase 1 — Identity Lock** (`scripts/id_resolver.py`):
Resolves `tmdb_id` and `imdb_id` for all entries missing them.
Fuzzy-matches titles against TMDB (confidence threshold 0.92).
Stores `original_title` (regional variant) separately when it differs.

**Phase 2 — Multi-Source Harvesting** (`scripts/data_harvester.py`):
- Tier 1 (TMDB): genres, release_date, runtime, original_language, overview.
- Tier 2 (OMDB): IMDb rating + votes, Rotten Tomatoes %, Metascore.
- Tier 3 (Letterboxd): average /5 rating (HTML scrape, gracefully skipped if blocked).
- Writes to `data/temp_enrichment.json` (staging — never touches `library.json` directly).

**Phase 3 — India OTT Discovery** (`scripts/ott_locator.py`):
Uses TMDB Watch Providers (powered by JustWatch) for the `IN` region.
Adds `streaming_in` (array of `{provider, type, logo_url}`) and `justwatch_url` to staged entries.

**Phase 4+5 — Normalise, Score & Merge** (`scripts/enrich_library.py`):
- Normalises all ratings to 0–10 (`norm_imdb`, `norm_rt`, `norm_letterboxd`, `norm_metascore`).
- `weighted_score` = `(IMDb×0.4) + (RT×0.3) + (Letterboxd×0.3)` with genre-adjusted weights.
- Expands `hidden_tags` via a genre→cinephile-tag classifier.
- Adds `last_enriched` UTC timestamp. Merge protocol: `overrides.json` > existing > scraped.
- **Streaming Lifecycle** ("Prune with a Memory"):
  - **Plan to Watch** items: Strict pruning — UI shows only current providers (from TMDB API).
  - **Watched** items: Archival mode — current providers displayed + disappeared ones saved to `metadata_history.past_providers` with `last_pruned` timestamp.
  - Rationale: In the volatile Indian OTT market, stale data (showing a title on Netflix when it's not) damages trust. For unwatched content, accuracy > history. For watched content, history aids future subscription auditing.
- Removes staging file after successful merge.

**Phase 6 — Maintenance**:
- `--stale-days N` skips entries enriched within N days.
- Weekly cron pattern: `enrich_library.py --run-pipeline --auto` on Sunday nights.
- Frontend modal shows "Synced Xd ago" automatically once manifest is rebuilt.

### New fields added to `library.json`

`tmdb_id`, `imdb_id`, `original_title`, `tmdb_poster_url`, `imdb_rating`, `rotten_tomatoes`,
`metascore`, `letterboxd_rating`, `norm_imdb`, `norm_rt`, `norm_letterboxd`, `norm_metascore`,
`weighted_score`, `hidden_tags`, `streaming_in`, `justwatch_url`, `last_enriched`, `metadata_history`.

### Frontend data flow

1. `enrich_library.py` writes enriched fields to `data/library.json`.
2. `fetch_assets.py` rebuilds `assets/manifest.json` (spreads all item fields).
3. `script.js` loads manifest at boot → populates `enrichmentData` per title.
4. Each movie object gets `streaming_in`, `weighted_score`, `last_enriched` merged in.
5. Modal shows OTT provider badges (colour-coded by type), weighted score chip, and sync timestamp.

### Admin enrich endpoint

`POST /api/enrich/<id>` — full per-item enrichment from admin UI (requires `TMDB_API_KEY`).
Returns enriched item JSON. Supersedes the simpler `/api/refresh_metadata/<id>`.

---

## Streaming Lifecycle Strategy: "Prune with a Memory"

The Indian OTT market is volatile—content rotates between providers constantly.
Showing stale availability data (e.g. "Available on Netflix" when it's not) damages user trust faster than showing no data.

### The problem

1. **Click Frustration**: User sees a title on Netflix in your app, opens the app, finds it's gone. Trust drops.
2. **License windows**: Movies move between Hotstar ↔ Prime ↔ Zee5 frequently.
3. **Refresh lag**: TMDB provider data can lag 24–48 hours behind reality.

### The solution: Status-aware provider handling

When `enrich_library.py` runs Phase 3+4, it compares old `streaming_in` against new TMDB results:

| Item Status | Old Provider Missing | Behavior | Rationale |
|---|---|---|---|
| Plan to Watch | Netflix → gone | Delete from `streaming_in` | Keep UI high-trust; user hasn't seen it yet. |
| Watched | Netflix → gone | Delete from `streaming_in`; save to `metadata_history.past_providers` | Historic record aids future subscription auditing ("SonyLIV gave me good value in Q3 2025"). |

### Field structure

**Active** (shown in modal):
```json
"streaming_in": [
  {"provider": "Netflix", "type": "flatrate", "provider_id": 8, "logo_url": "..."},
  {"provider": "Prime", "type": "flatrate", "provider_id": 119, ...}
]
```

**Archived** (only for Watched items; hidden from UI):
```json
"metadata_history": {
  "past_providers": ["HBO Max", "Lionsgate Play"],
  "last_pruned": "2026-05-03T18:42:01+00:00"
}
```

### Future: subscription audit & insights

Once you have 6–12 months of enrichment history:
- Query `metadata_history.past_providers` across your "Watched" items
- Build a "Subscription ROI" view: "SonyLIV provided 47 watched titles; Prime provided 112"
- Helps inform annual subscription renewal decisions

---

## Repo layout (top-level)

- `index.html` — main static UI (Mosaic + List views)
- `table.html` — redirect/alternate table view (keeps UI self-contained)
- `style.css`, `css/` — stylesheets
- `script.js`, `js/app.js` — frontend logic (index.html uses `script.js`)
- `data/` — JSON data files (source of truth)
  - `library.json` — primary library entries
  - `overrides.json` — optional manual overrides (local edits may also use localStorage)
- `assets/` — static assets
  - `manifest.json` — poster manifest generated by `scripts/fetch_assets.py`
  - `posters/` — downloaded poster image files
- `scripts/` — helpful management scripts: fetching, enhancing, README generator
- `server.py` — small Flask admin server exposing `/api/*` endpoints
- `requirements.txt` — Python dependencies
- `.github/copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md` — project guidance and rules

---

## Data model (data/library.json)

The library is a JSON array of objects. Typical fields (observed in current `data/library.json`):

```json
{
  "id": 13,
  "title": "Ronth",
  "type": "Movie",
  "status": "Plan to Watch",
  "rating": 0,
  "tags": [],
  "imdbID": "tt33294533",
  "language": "Hindi",
  "genres": [],
  "plot": "Two patrol officers...",
  "runtime": "122 min",
  "imdbRating": "7.1",
  "metascore": "N/A",
  "rottenTomatoes": null,
  "wikipedia": null,
  "src": "ronth.jpg",
  "has_poster": true
}
```

Field descriptions:
- `id` (number): unique numeric id used by server endpoints.
- `title` (string): display title.
- `type` (string): `Movie` or `Series`.
- `status` (string): `Watched`, `Plan to Watch`, `Recommended`, etc.
- `rating` (number): internal personal rating (0 means unset).
- `tags` (array[string]): freeform tags used by UI and scripts.
- `imdbID` (string|null): IMDb ID if known (e.g. `tt1234567`).
- `language` (string): language inferred or set (English, Hindi, Malayalam, etc.).
- `genres` (array[string]): genre hints.
- `plot`, `runtime`, `imdbRating`, `metascore`, `rottenTomatoes`, `wikipedia`: optional metadata populated by `server.py` metadata refresh or scripts.
- `src` (string): poster filename (relative to `assets/posters/` in manifest entries).
- `has_poster` (bool): whether a poster file exists locally.

The frontend also reads `assets/manifest.json` which contains per-item poster metadata (`title`, `src`, `has_poster`) used at boot for poster resolution.

Overrides: user overrides can be persisted in `data/overrides.json` (and the UI also uses `localStorage` key `metadata_overrides_v1`).

---

## Backend — `server.py`

Purpose: serve static files and provide a tiny admin API used by local development and the admin UI.

Key behaviour & endpoints (see `server.py`):

- `GET /api/health` — simple health check.
- `GET /api/library` — returns the entire `data/library.json` payload.
- `POST /api/library` — add an item (auto-increments `id`).
- `PUT /api/library/<id>` — update an item by id.
- `DELETE /api/library/<id>` — delete an item.
- `POST /api/refresh_metadata/<id>` — runs the `refresh_metadata()` flow for a single item; calls OMDB first (when `OMDB_API_KEY` is present), then falls back to Wikidata + Wikipedia for plot/runtime/wikipedia link.

Important implementation notes (from `server.py`):
- If `OMDB_API_KEY` is missing, OMDB requests are skipped gracefully.
- `refresh_metadata()` uses both OMDB and Wikidata/Wikipedia fallback to improve plots and runtime, and writes results back to `data/library.json`.
- Server listens on `PORT` env var (default 8080) and prints the running URL when started.

---

## Asset pipeline & poster strategy

Scripts and priority (see `scripts/fetch_assets.py`):

Poster search priority (Indian-first):
1. iTunes India (country=in)
2. iTunes US (country=us)
3. Wikipedia REST API (infobox thumbnails)
4. OMDB API (if `OMDB_API_KEY` present)
5. SVG placeholder written by script as a last resort

Outputs:
- `assets/posters/` — downloaded poster files (jpg/svg/etc.)
- `assets/manifest.json` — JSON array where each item is the library entry plus `src` and `has_poster` fields. Frontend `script.js` reads `assets/manifest.json` at boot to populate the poster manifest.

Alternate poster tooling: `scripts/fetch_posters.py` is an alternative pipeline that fetches using OMDB when possible and converts images to optimized formats (WebP).

---

## Frontend

- `index.html` — main UI: mosaic (poster-first) and list (table) views, with filtering, sorting, and a modal details view.
- `script.js` — primary UI controller (loads inline dataset or `assets/manifest.json`, resolves posters via manifest, provides modal and table behaviors).
- `js/app.js` — additional/alternate app logic (more modular controller used in some builds); the repo contains both but `index.html` uses `script.js` in current configuration.
- UI features: grid and list views, filters by status, theme toggle, export CSV (local-only), poster fallbacks via TMDB_MAP and Unsplash list, and local edit/refresh hooks when served locally.

Local-only admin tooling: When served from `localhost`, additional local controls are shown (export, import, edit mode). The admin refresh button triggers the `/api/refresh_metadata/<id>` endpoint.

Poster resolution in the frontend follows this order (see `script.js`):
1. `assets/manifest.json` local poster mapping (`posterManifest`).
2. Inline `TMDB_MAP` lookup mapping for popular titles.
3. Unsplash-based fallback pool.

The UI uses `localStorage` key `metadata_overrides_v1` to apply per-title overrides; `scripts/update_readme.py` and `scripts/enhance_library.py` can be used to permanently apply inferred enhancements.

---

## Scripts (summary)

- `scripts/fetch_assets.py` — Indian-first poster downloader; writes `assets/manifest.json`.
- `scripts/fetch_posters.py` — alternate poster fetch + image optimization pipeline (uses Pillow).
- `scripts/fetch_ratings.py` — placeholder structure for scraping/aggregating ratings from multiple external sources (Metacritic, Letterboxd, IMDb, MovieLens); contains stub functions and usage notes.
- `scripts/enhance_library.py` — infer `language` and `genres` from titles/tags and add `imdbID` placeholder fields; updates `data/library.json`.
- `scripts/update_readme.py` — regenerates `README.md` from `data/library.json` (used to keep README in sync).
- `scripts/screenshot_preview.py`, `scripts/export_codebase.py`, `scripts/ui_validator.py` — project helpers (see scripts directory for details).

---

## Conventions & rules (project policy)

- Do not add a build system, bundler, or npm.
- `index.html` and `table.html` must remain self-contained static files.
- `data/` JSON files are the source of truth — do not hardcode data into HTML.
- `OMDB_API_KEY` must come from environment — never hardcode it or commit it.
- Prioritize Indian-first poster fetching in the asset scripts.
- Use `conda activate base` (the repo's documented environment) — ignore the `venv/` directory.
- Python style: PEP 8, use `pathlib.Path` for file operations.

Those rules are documented in `.github/copilot-instructions.md`, `AGENTS.md`, and `CLAUDE.md` — consult them for governance and owner notes.

---

## API endpoints (quick reference)

- `GET /api/library` — read full library JSON
- `POST /api/library` — append a new item (expects `title` at minimum)
- `PUT /api/library/<id>` — replace/update item by id
- `DELETE /api/library/<id>` — remove item
- `POST /api/refresh_metadata/<id>` — fetch and merge metadata for an item (OMDB -> Wikidata -> Wikipedia fallback)

Server CLI:

```
OMDB_API_KEY=your_key python3 server.py
```

Optional: change port with `PORT` environment variable.

---

## Suggested maintenance tasks

- Run `python3 scripts/update_readme.py` after major library edits to refresh `README.md`.
- Run `python3 scripts/fetch_assets.py` (or `fetch_posters.py`) to ensure `assets/posters/` and `assets/manifest.json` are up to date.
- Run `python3 scripts/enhance_library.py` to add inferred `language`/`genres` fields.
- Use `OMDB_API_KEY` and the admin server to run `POST /api/refresh_metadata/<id>` for improved metadata.

---

## Owner & contact

Project owner / maintainer: D K Bhargav Achary

---

## Next steps (how I can help)

- I can: generate a visual ER/schema diagram for `library.json`, convert `assets/manifest.json` into a small SQLite index for faster server queries, or create a developer checklist for contributor onboarding. Tell me which you'd like next.

---

Generated by an automated repository scan — review and edit as needed.

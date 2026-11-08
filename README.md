# CinemaScope

> **Personal, zero-bloat movies & TV series watchlist manager with an Indian-first regional lens.**

[![Frontend](https://img.shields.io/badge/frontend-vanilla%20HTML%2FCSS%2FJS-brightgreen.svg)](index.html)
[![Backend](https://img.shields.io/badge/backend-Flask%20%28Python%203%29-blue.svg)](server.py)
[![Architecture](https://img.shields.io/badge/architecture-no%20build%20step%20%7C%20static%20ready-orange.svg)](AGENTS.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. What CinemaScope Does

CinemaScope is a personal entertainment library and watchlist manager designed for cinephiles who value speed, aesthetics, and privacy. It features dual viewing modes:

- **Mosaic View (Poster-First):** Immersive, high-resolution poster wall with ambient glassmorphism, responsive grid layout, and instant interactive modals.
- **Table / List View:** Dense, sortable data table for rapid sorting by IMDb rating, runtime, release year, or watch status.
- **OTT Availability Locator:** Tracks streaming platforms in India (Netflix, Amazon Prime, Disney+ Hotstar, JioCinema, SonyLIV, Zee5, Aha, Sun NXT, Hoichoi, etc.).
- **Multi-Source Enrichment:** Enriches titles with Rotten Tomatoes critic consensus, IMDb scores, awards, and regional language tags.

---

## 2. Why It Exists

Commercial watchlist platforms (IMDb, Letterboxd, Trakt) are heavily cluttered with ads, tracking scripts, slow single-page framework bundles, and generic international recommendations that bury regional Indian cinema gems (Odia, Malayalam, Tamil, Telugu, Marathi).

**CinemaScope's Philosophy:**
- **Zero Build Step:** Plain HTML, CSS, and vanilla JS. No Webpack, Vite, or node_modules.
- **Single Source of Truth:** `data/library.json` drives the entire platform. Edit the JSON directly or via the local Flask admin GUI.
- **Offline & Resilience First:** Seamlessly operates offline with built-in metadata fallbacks even when external APIs are unreachable.
- **Regional First:** Prioritizes authentic regional language cinema alongside global classics.

---

## 3. Implementation Status

| Feature | Status | Description |
|---|---|---|
| **Mosaic / Grid View** | **Production-Ready** | Responsive CSS grid with poster fallback cascade, status chips, and glass hover effects. |
| **Table / List View** | **Production-Ready** | Compact sortable view toggled in-place without page reload. |
| **Local Admin Server** | **Production-Ready** | Lightweight Flask API (`server.py`) on port 8080 with CRUD and metadata endpoints. |
| **Metadata Enrichment** | **Production-Ready** | Multi-source pipeline (`scripts/enrich_library.py`, `scripts/ott_locator.py`). |
| **Static Hosting** | **Production-Ready** | Fully hostable on GitHub Pages or Cloudflare Pages without a server. |
| **Poster Harvester** | *Stable* | Indian-first poster scraping with TMDB CDN fallback. |

---

## 4. Architecture

```text
┌────────────────────────────────────────────────────────┐
│                 data/library.json                      │
│              (Single Source of Truth)                  │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
   (Direct read)│                        │(Admin CRUD / refresh)
                ▼                        ▼
┌───────────────────────────┐    ┌───────────────────────────┐
│    Static Web Client      │    │    server.py (Flask API)  │
│  index.html · script.js   │    │    localhost:8080         │
│  (Mosaic & List Views)    │    └─────────────┬─────────────┘
└───────────────────────────┘                  │
                                               ▼
                                 ┌───────────────────────────┐
                                 │    Enrichment Pipeline    │
                                 │  scripts/id_resolver.py   │
                                 │  scripts/data_harvester.py│
                                 │  scripts/ott_locator.py   │
                                 └───────────────────────────┘
```

---

## 5. Quick Start & Usage

### Option A: Static Mode (Zero Installation)
Simply open `index.html` in any modern web browser or serve via Python's built-in HTTP server:
```bash
python3 -m http.server 8000
# Open http://localhost:8000
```

### Option B: Local Admin Server (With Live Enrichment)
To enable on-the-fly metadata fetching, OTT lookup, and browser editing:
```bash
pip install -r requirements.txt
OMDB_API_KEY=your_key_here python3 server.py
# Open http://localhost:8080
```

### Running Automated Tests
```bash
python3 -m unittest discover -s tests -v
```

---

## 6. Library Statistics

- **Total Library Titles**: 63
- **Watched**: 37
- **Plan to Watch**: 18
- **Recommended**: 8
- **Currently Watching**: 0
- **Movies**: 48
- **Series**: 15
- **Average IMDb Rating (Watched)**: ⭐ 9.5/10

---

## 7. Curated Library Highlights

## ✅ Watched

### Breaking Bad
- **Type**: Series
- **Rating**: ⭐ 10/10
- **Tags**: Classic

### Maharaja
- **Type**: Movie
- **Rating**: ⭐ 9/10
- **Tags**: Tamil, Thriller

### Game of Thrones
- **Type**: Series
- **Tags**: Classic

### Chernobyl
- **Type**: Series
- **Tags**: Miniseries

### The Shawshank Redemption
- **Type**: Movie
- **Tags**: Classic

### Forrest Gump
- **Type**: Movie
- **Tags**: Classic

### Interstellar
- **Type**: Movie
- **Tags**: Sci-Fi

### Spirited Away
- **Type**: Movie
- **Tags**: Anime

### Wall-E
- **Type**: Movie
- **Tags**: Animation

### A Beautiful Mind
- **Type**: Movie
- **Tags**: Drama

### Prison Break
- **Type**: Series
- **Tags**: Action

### Westworld
- **Type**: Series
- **Tags**: Sci-Fi

### Jurassic Park
- **Type**: Movie
- **Tags**: Action

### Die Hard
- **Type**: Movie
- **Tags**: Action

### Spider-Man
- **Type**: Movie
- **Tags**: Superhero

### Spider-Man 2
- **Type**: Movie
- **Tags**: Superhero

### James Bond Movies
- **Type**: Series
- **Tags**: Action, Spy

### Harry Potter Series
- **Type**: Series
- **Tags**: Fantasy

### Drishyam
- **Type**: Series
- **Tags**: Thriller

### 12th Fail
- **Type**: Movie
- **Tags**: Drama

### 3 Idiots
- **Type**: Movie
- **Tags**: Comedy, Drama

### Taare Zameen Par
- **Type**: Movie
- **Tags**: Drama

### The Night Manager
- **Type**: Series
- **Tags**: Thriller

### Dilli Dark
- **Type**: Movie

### Stolen
- **Type**: Movie

### Nishaanchi
- **Type**: Movie

### Sister Midnight
- **Type**: Movie

### Anora
- **Type**: Movie

### Haq
- **Type**: Movie

### Homebound
- **Type**: Movie

### Lokah Ch 1: Chandra
- **Type**: Movie

### Hrudayapoorvam
- **Type**: Movie

### Jugnuma: The Fable
- **Type**: Movie

### Ponman
- **Type**: Movie

### Su From So
- **Type**: Movie

### Sarvam Maya
- **Type**: Movie

### Aan Paavam Pollathathu
- **Type**: Movie

## 🌟 Recommended

### Kishkindha Kaandam
- **Type**: Movie
- **Tags**: Malayalam, Mystery

### Bramayugam
- **Type**: Movie
- **Tags**: Malayalam, Folk Horror

### Kohrra
- **Type**: Series
- **Tags**: Noir, Investigation

### Sector 36
- **Type**: Movie
- **Tags**: Hindi, Thriller

### Severance
- **Type**: Series
- **Tags**: Sci-Fi, Thriller

### Dark
- **Type**: Series
- **Tags**: Sci-Fi, Time Travel

### Shōgun
- **Type**: Series
- **Tags**: Political, Epic

### Article 15
- **Type**: Movie
- **Tags**: Hindi, Crime, Drama

## 📝 Plan to Watch

### Kantara: Legend Chapter 1
- **Type**: Movie
- **Tags**: Upcoming, Folklore, Action

### Bison
- **Type**: Movie
- **Tags**: Mari Selvaraj Project

### Kaantha
- **Type**: Movie

### Freedom at Midnight
- **Type**: Series

### Mirai
- **Type**: Movie

### Dhurandhar
- **Type**: Movie

### Maranamass
- **Type**: Movie
- **Tags**: Dark Comedy, Crime

### Pravinkoodu Shappu
- **Type**: Movie

### Raat Akeli Hai
- **Type**: Movie
- **Tags**: Noir, Mystery

### Ground Zero
- **Type**: Movie

### Vash Level 2
- **Type**: Movie

### Mithya
- **Type**: Series

### Ronth
- **Type**: Movie

### Thalavara
- **Type**: Movie

### Bou Buttu Bhuta
- **Type**: Movie

### Daman
- **Type**: Movie
- **Tags**: Odia Drama

### Madharaasi
- **Type**: Movie

### Retro
- **Type**: Movie

---

*This README is automatically generated from `data/library.json`*

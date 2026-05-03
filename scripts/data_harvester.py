#!/usr/bin/env python3
"""
Phase 2 — Multi-Source Data Harvesting
=======================================
Tiered metadata acquisition:

  Tier 1 — TMDB API       : genres, release_date, runtime, original_language,
                             overview, high-res poster path
  Tier 2 — OMDB API       : IMDb rating + votes, Rotten Tomatoes %, Metascore,
                             director, actors, awards (single JSON call)
  Tier 3 — Letterboxd     : average audience rating out of 5 (HTML scrape;
                             gracefully skipped on any error or block)

Writes enriched data to data/temp_enrichment.json (staging file).
Never writes directly to library.json.

Usage:
    TMDB_API_KEY=... OMDB_API_KEY=... python3 scripts/data_harvester.py
    TMDB_API_KEY=... OMDB_API_KEY=... python3 scripts/data_harvester.py --skip-letterboxd
    TMDB_API_KEY=... OMDB_API_KEY=... python3 scripts/data_harvester.py --id tt1234567

Set FORCE_REFRESH=1 to re-harvest entries that already have data.
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests")
    sys.exit(1)

BASE_DIR      = Path(__file__).parent.parent
LIBRARY_FILE  = BASE_DIR / "data" / "library.json"
STAGING_FILE  = BASE_DIR / "data" / "temp_enrichment.json"

TMDB_KEY      = os.environ.get("TMDB_API_KEY", "")
OMDB_KEY      = os.environ.get("OMDB_API_KEY", "")
FORCE_REFRESH = os.environ.get("FORCE_REFRESH", "0") == "1"

TMDB_BASE     = "https://api.themoviedb.org/3"
TMDB_IMG      = "https://image.tmdb.org/t/p/w500"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


# ─── Tier 1: TMDB ─────────────────────────────────────────────────────────────

def _tmdb_get(path: str, params: dict | None = None) -> dict:
    p = {"api_key": TMDB_KEY, "language": "en-US", **(params or {})}
    r = requests.get(f"{TMDB_BASE}{path}", params=p, timeout=10)
    r.raise_for_status()
    return r.json()


def harvest_tmdb(item: dict) -> dict:
    """Fetch TMDB detail record for an item with a known tmdb_id."""
    tmdb_id = item.get("tmdb_id")
    if not tmdb_id or not TMDB_KEY:
        return {}

    media = "movie" if item.get("type", "Movie") == "Movie" else "tv"
    try:
        d = _tmdb_get(f"/{media}/{tmdb_id}")
    except Exception as exc:
        print(f"    [T1-err] {item['title']}: {exc}")
        return {}

    genres       = [g["name"] for g in d.get("genres", [])]
    poster_path  = d.get("poster_path")
    poster_url   = (TMDB_IMG + poster_path) if poster_path else None

    if media == "movie":
        runtime      = d.get("runtime")
        release_date = d.get("release_date", "")
        orig_title   = d.get("original_title", item["title"])
        orig_lang    = d.get("original_language", "")
    else:
        runtimes     = d.get("episode_run_time") or []
        runtime      = runtimes[0] if runtimes else None
        release_date = d.get("first_air_date", "")
        orig_title   = d.get("original_name", item["title"])
        orig_lang    = d.get("original_language", "")

    return {
        "tmdb_poster_url":  poster_url,
        "release_date":     release_date,
        "year":             release_date[:4] if release_date else item.get("year"),
        "runtime_min":      runtime,
        "original_language": orig_lang,
        "original_title":   orig_title if orig_title != item["title"] else item.get("original_title", item["title"]),
        "genres":           genres,
        "tmdb_vote_avg":    d.get("vote_average"),
        "tmdb_vote_count":  d.get("vote_count"),
        "overview":         d.get("overview") or "",
    }


# ─── Tier 2: OMDB ─────────────────────────────────────────────────────────────

def harvest_omdb(item: dict) -> dict:
    """Fetch OMDB record for IMDb / RT / Metacritic ratings in one call."""
    if not OMDB_KEY:
        return {}

    params = {"apikey": OMDB_KEY, "plot": "short"}
    imdb_id = item.get("imdbID") or item.get("imdb_id")
    if imdb_id and imdb_id.startswith("tt"):
        params["i"] = imdb_id
    else:
        params["t"] = item["title"]
        params["type"] = "movie" if item.get("type", "Movie") == "Movie" else "series"

    try:
        r = requests.get("https://www.omdbapi.com/", params=params, timeout=10)
        r.raise_for_status()
        d = r.json()
    except Exception as exc:
        print(f"    [T2-err] {item['title']}: {exc}")
        return {}

    if d.get("Response") != "True":
        return {}

    ratings = {x["Source"]: x["Value"] for x in d.get("Ratings", [])}
    rt_raw  = ratings.get("Rotten Tomatoes", "")

    return {
        "imdb_rating":     d.get("imdbRating") or "",
        "imdb_votes":      d.get("imdbVotes")  or "",
        "metascore":       d.get("Metascore")  or "",
        "rotten_tomatoes": rt_raw,
        "plot":            d.get("Plot")       or "",
        "runtime":         d.get("Runtime")    or "",
        "imdbID":          d.get("imdbID")     or imdb_id or "",
        "director":        d.get("Director")   or "",
        "actors":          d.get("Actors")     or "",
        "awards":          d.get("Awards")     or "",
        "country":         d.get("Country")    or "",
    }


# ─── Tier 3: Letterboxd ───────────────────────────────────────────────────────

def _lb_slug(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9 ]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return s


def harvest_letterboxd(item: dict, skip: bool = False) -> dict:
    """
    Scrape Letterboxd average rating (out of 5) for a Movie entry.
    Returns {} on any error or if `skip` is True.
    """
    if skip or item.get("type") != "Movie":
        return {}
    try:
        slug = _lb_slug(item["title"])
        url  = f"https://letterboxd.com/film/{slug}/"
        r    = requests.get(url, headers={"User-Agent": UA}, timeout=12)
        if r.status_code != 200:
            return {}

        # Try meta tag first: <meta name="twitter:data2" content="3.52 out of 5">
        m = re.search(
            r'twitter:data2["\s]+content="([0-9.]+)\s+out of 5"', r.text
        )
        if not m:
            # Fallback: JSON-LD ratingValue
            m = re.search(r'"ratingValue"\s*:\s*"?([0-9.]+)"?', r.text)

        if m:
            raw = float(m.group(1))
            return {
                "letterboxd_rating": round(raw, 2),  # /5 scale — normalised later
                "letterboxd_url":    url,
            }
    except Exception:
        pass
    return {}


# ─── Orchestrator ─────────────────────────────────────────────────────────────

def harvest_item(item: dict, skip_lb: bool = False) -> dict:
    enrichment: dict = {}

    print(f"  📡  {item['title']:<50}", end="", flush=True)

    if TMDB_KEY:
        t1 = harvest_tmdb(item)
        enrichment.update({k: v for k, v in t1.items() if v is not None})
        print(" T1", end="", flush=True)
        time.sleep(0.25)

    if OMDB_KEY:
        t2 = harvest_omdb(item)
        enrichment.update({k: v for k, v in t2.items() if v})
        print(" T2", end="", flush=True)
        time.sleep(0.25)

    t3 = harvest_letterboxd(item, skip=skip_lb)
    if t3:
        enrichment.update(t3)
        print(" T3", end="", flush=True)

    time.sleep(0.5)
    print()
    return enrichment


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-source data harvester.")
    parser.add_argument(
        "--skip-letterboxd", action="store_true",
        help="Skip Tier-3 Letterboxd scraping",
    )
    parser.add_argument(
        "--id", metavar="ITEM_ID", type=int, default=None,
        help="Harvest a single item by its library id",
    )
    args = parser.parse_args()

    with open(LIBRARY_FILE, encoding="utf-8") as fh:
        library = json.load(fh)

    if args.id:
        library = [i for i in library if i["id"] == args.id]
        if not library:
            print(f"No item with id={args.id}")
            sys.exit(1)

    print(f"🔬  Data Harvester — {len(library)} items")
    if not TMDB_KEY:
        print("⚠️   TMDB_API_KEY not set — Tier 1 skipped.")
    if not OMDB_KEY:
        print("⚠️   OMDB_API_KEY not set — Tier 2 skipped.")
    if args.skip_letterboxd:
        print("ℹ️   Tier 3 (Letterboxd) disabled.")
    print()

    # Load existing staging file to do an incremental update when re-running
    if STAGING_FILE.exists() and not FORCE_REFRESH:
        with open(STAGING_FILE, encoding="utf-8") as fh:
            staged = {e["id"]: e for e in json.load(fh)}
    else:
        staged = {}

    enriched_list = []
    for item in library:
        enriched = staged.get(item["id"], dict(item))

        # Skip if already harvested (unless FORCE_REFRESH)
        already_done = (
            enriched.get("imdb_rating") or enriched.get("genres")
        ) and not FORCE_REFRESH
        if already_done:
            print(f"  ⏭️   {item['title']:<50} (cached)")
            enriched_list.append(enriched)
            continue

        new_data = harvest_item(item, skip_lb=args.skip_letterboxd)
        # Merge: enriched fields fill gaps in the existing entry
        merged = {**enriched, **{k: v for k, v in new_data.items() if v}}
        enriched_list.append(merged)

    STAGING_FILE.write_text(
        json.dumps(enriched_list, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n✓  Staging file written → {STAGING_FILE.name}")
    print("   Next: python3 scripts/ott_locator.py")


if __name__ == "__main__":
    main()

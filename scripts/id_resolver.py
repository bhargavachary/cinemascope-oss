#!/usr/bin/env python3
"""
Phase 1 — Identity Lock: TMDB / IMDb ID Resolution
====================================================
Resolves `tmdb_id` and `imdb_id` for every library entry that lacks them.
Handles Indian regional titles by searching both the display title and any
alternative spellings the TMDB search returns.

The "India Slug" rule: if the TMDB `original_title` differs from the entry
title, both are stored so downstream scrapers can try the regional variant.

Usage:
    TMDB_API_KEY=... python3 scripts/id_resolver.py
    TMDB_API_KEY=... python3 scripts/id_resolver.py --auto       # auto-match ≥92%
    TMDB_API_KEY=... python3 scripts/id_resolver.py --dry-run    # preview only
    TMDB_API_KEY=... python3 scripts/id_resolver.py --force      # re-resolve all
"""

import argparse
import json
import os
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests")
    sys.exit(1)

BASE_DIR     = Path(__file__).parent.parent
LIBRARY_FILE = BASE_DIR / "data" / "library.json"

TMDB_KEY  = os.environ.get("TMDB_API_KEY", "")
TMDB_BASE = "https://api.themoviedb.org/3"

# Auto-confirm a match when fuzzy confidence reaches this threshold.
AUTO_CONFIRM_THRESHOLD = 0.92


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _normalize(s: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", s.lower())).strip()


def _fuzzy(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def _tmdb_get(path: str, params: dict | None = None) -> dict:
    p = {"api_key": TMDB_KEY, "language": "en-US", **(params or {})}
    r = requests.get(f"{TMDB_BASE}{path}", params=p, timeout=10)
    r.raise_for_status()
    return r.json()


def _search_tmdb(title: str, media_type: str) -> list:
    endpoint = "/search/movie" if media_type == "Movie" else "/search/tv"
    try:
        data = _tmdb_get(endpoint, {"query": title, "include_adult": False})
        return data.get("results", [])
    except Exception as exc:
        print(f"    TMDB search error for '{title}': {exc}")
        return []


def _external_ids(tmdb_id: int, media_type: str) -> str | None:
    """Return IMDb ID (e.g. 'tt1234567') from TMDB external_ids endpoint."""
    endpoint = f"/{'movie' if media_type == 'Movie' else 'tv'}/{tmdb_id}/external_ids"
    try:
        return _tmdb_get(endpoint).get("imdb_id")
    except Exception:
        return None


def _score_candidates(title: str, results: list, media_type: str) -> list:
    t_field  = "title"          if media_type == "Movie" else "name"
    ot_field = "original_title" if media_type == "Movie" else "original_name"
    scored = []
    for r in results[:8]:
        score = max(
            _fuzzy(title, r.get(t_field, "")),
            _fuzzy(title, r.get(ot_field, "")),
        )
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


# ─── Resolution logic ─────────────────────────────────────────────────────────

def resolve_item(item: dict, *, auto: bool) -> dict | None:
    """
    Find tmdb_id / imdb_id for one library entry.
    Returns a dict of fields to merge into the entry, or None if unresolved.
    """
    title      = item["title"]
    media_type = item.get("type", "Movie")
    results    = _search_tmdb(title, media_type)
    if not results:
        print(f"  ✗  No TMDB results for '{title}'")
        return None

    scored   = _score_candidates(title, results, media_type)
    best_sc, best = scored[0]
    t_field  = "title"          if media_type == "Movie" else "name"
    ot_field = "original_title" if media_type == "Movie" else "original_name"

    def _build(r: dict) -> dict:
        tmdb_id    = r["id"]
        imdb_id    = item.get("imdbID") or _external_ids(tmdb_id, media_type)
        year       = (r.get("release_date") or r.get("first_air_date") or "")[:4]
        orig_title = r.get(ot_field, title)
        return {
            "tmdb_id":        tmdb_id,
            "imdb_id":        imdb_id,
            # Keep imdbID as the backward-compatible canonical field
            "imdbID":         imdb_id or item.get("imdbID"),
            # Store original regional title only when it differs from display title
            "original_title": orig_title if orig_title != r.get(t_field) else title,
            "year":           year or item.get("year"),
        }

    if auto and best_sc >= AUTO_CONFIRM_THRESHOLD:
        result = _build(best)
        print(
            f"  ✔  '{title}' → '{best.get(t_field)}' "
            f"(conf={best_sc:.2f}, tmdb={result['tmdb_id']})"
        )
        return result

    # ── Interactive selection ──────────────────────────────────────────────
    print(f"\n  ?  '{title}' — top matches:")
    for i, (sc, r) in enumerate(scored[:3]):
        yr = (r.get("release_date") or r.get("first_air_date") or "")[:4]
        print(
            f"      [{i+1}] {r.get(t_field, '?')!r:<40} ({yr})  "
            f"conf={sc:.2f}  tmdb={r['id']}"
        )
    print("      [s] Skip")
    while True:
        choice = input("  Select [1/2/3/s]: ").strip().lower()
        if choice == "s":
            return None
        if choice in ("1", "2", "3"):
            idx = int(choice) - 1
            if idx < len(scored):
                return _build(scored[idx][1])


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve TMDB / IMDb IDs for all library entries."
    )
    parser.add_argument(
        "--auto", action="store_true",
        help=f"Auto-confirm matches with confidence ≥ {AUTO_CONFIRM_THRESHOLD}",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print resolved IDs without writing library.json",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-resolve even entries that already have tmdb_id",
    )
    args = parser.parse_args()

    if not TMDB_KEY:
        print("Error: TMDB_API_KEY environment variable not set.")
        sys.exit(1)

    with open(LIBRARY_FILE, encoding="utf-8") as fh:
        library = json.load(fh)

    total   = len(library)
    updated = 0

    print(f"🔑  ID Resolver — {total} entries\n")

    for item in library:
        already = item.get("tmdb_id") and (item.get("imdb_id") or item.get("imdbID"))
        if already and not args.force:
            continue

        resolved = resolve_item(item, auto=args.auto)
        if resolved:
            item.update(resolved)
            updated += 1

        time.sleep(0.3)   # polite rate-limit

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"\n{prefix}Resolved {updated} / {total} entries.")

    if not args.dry_run and updated:
        with open(LIBRARY_FILE, "w", encoding="utf-8") as fh:
            json.dump(library, fh, indent=4, ensure_ascii=False)
            fh.write("\n")
        print(f"✓  Saved → {LIBRARY_FILE.name}")


if __name__ == "__main__":
    main()

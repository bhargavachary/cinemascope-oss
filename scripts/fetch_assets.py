#!/usr/bin/env python3
"""
Static Site Generator — Asset Pipeline
=======================================
Reads data/library.json → Fetches real posters via OMDB API
→ Generates styled fallback placeholders → Produces assets/manifest.json

Usage:
    export OMDB_API_KEY=your_key_here
    python3 scripts/fetch_assets.py

    # Placeholder-only mode (no API key):
    python3 scripts/fetch_assets.py

Get a free OMDB key: https://www.omdbapi.com/apikey.aspx
"""

import argparse
import json
import os
import sys
import time
import textwrap
from difflib import SequenceMatcher
from pathlib import Path
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont
# ─── Path Resolution ────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR
LIBRARY_PATH = PROJECT_ROOT / "data" / "library.json"
OVERRIDES_PATH = PROJECT_ROOT / "data" / "overrides.json"
OUTPUT_DIR   = PROJECT_ROOT / "assets" / "posters"
MANIFEST_PATH = PROJECT_ROOT / "assets" / "manifest.json"

# ─── Configuration ──────────────────────────────────────────
TARGET_WIDTH  = 300
POSTER_RATIO  = 1.5          # Standard movie poster height/width
TARGET_HEIGHT = int(TARGET_WIDTH * POSTER_RATIO)  # 450
OMDB_API_KEY  = os.environ.get("OMDB_API_KEY", "")
REQUEST_DELAY = 0.25          # Seconds between API calls (rate‑limit guard)

WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
WIKIPEDIA_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

# ─── Color Palette for Placeholders ────────────────────────
PALETTE = [
    "#1a1a2e", "#16213e", "#0f3460", "#533483",
    "#2b2d42", "#3d405b", "#5f0f40", "#0b132b",
    "#1b2838", "#2d3436", "#34495e", "#2c3e50",
    "#1d3557", "#283618", "#3c1642", "#0d1b2a",
]
ACCENTS = [
    "#e63946", "#457b9d", "#2a9d8f", "#e9c46a",
    "#f4a261", "#6366f1", "#ec4899", "#14b8a6",
]

# ─── Title Overrides (manual fixes for ambiguous titles) ───
TITLE_OVERRIDES = {
    "James Bond Movies":          "Casino Royale",
    "Harry Potter Series":        "Harry Potter and the Sorcerer's Stone",
    "Kantara: Legend Chapter 1":  "Kantara",
    "Lokah Ch 1: Chandra":       None,       # No known OMDB entry
    "Vash Level 2":              None,
}

# Optional metadata overrides (streaming / wikipedia / manual fixes)
METADATA_OVERRIDES = {
    # "Title": {"streaming_name": "Netflix", "streaming_url": "https://netflix.com", "wikipedia": "https://..."}
}


# ═══════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════

def clean_title(title):
    """Apply overrides, then strip common subtitle noise."""
    if title in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[title]
    return title


def normalize_title(value):
    return "".join(ch for ch in value.lower() if ch.isalnum())


def make_filename(title):
    """Create a safe filesystem name from a title."""
    safe = title.lower()
    safe = "".join(c if c.isalnum() or c in (" ", "-") else "" for c in safe)
    safe = safe.strip().replace(" ", "_").replace("--", "-")
    return safe[:60] + ".jpg"


def load_library():
    with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_overrides():
    if not OVERRIDES_PATH.exists():
        return {}
    try:
        with open(OVERRIDES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _load_fonts():
    """Load fonts with system → bundled fallback chain."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, 22), ImageFont.truetype(path, 13)
            except Exception:
                continue
    # Pillow 10+ bundled font
    try:
        return ImageFont.load_default(size=22), ImageFont.load_default(size=13)
    except TypeError:
        f = ImageFont.load_default()
        return f, f


# ═══════════════════════════════════════════════════════════
#  OMDB API
# ═══════════════════════════════════════════════════════════

def fetch_omdb_by_id(imdb_id):
    if not OMDB_API_KEY or not imdb_id:
        return None
    return _omdb_get({"apikey": OMDB_API_KEY, "i": imdb_id, "plot": "short"})


def fetch_omdb(title, media_type=None):
    """Fetch metadata from OMDB with multi-strategy fallback."""
    if not OMDB_API_KEY:
        return None

    base = {"apikey": OMDB_API_KEY, "plot": "short"}

    # Strategy 1: exact title + type
    params = {**base, "t": title}
    if media_type:
        params["type"] = media_type
    data = _omdb_get(params)
    if data:
        return data

    # Strategy 2: exact title, no type constraint
    if media_type:
        data = _omdb_get({**base, "t": title})
        if data:
            return data

    # Strategy 3: strip subtitle after colon
    if ":" in title:
        shorter = title.split(":")[0].strip()
        data = _omdb_get({**base, "t": shorter})
        if data:
            return data

    # Strategy 4: search endpoint + best match
    result = search_omdb(title, media_type)
    if result:
        return result

    return None


def _omdb_get(params):
    """Single OMDB request. Returns dict or None."""
    try:
        resp = requests.get("https://www.omdbapi.com/", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("Response") == "True":
            return data
    except Exception:
        pass
    return None


def wikidata_search(title, media_type):
    try:
        params = {
            "action": "wbsearchentities",
            "search": title,
            "language": "en",
            "format": "json",
            "limit": 5,
        }
        r = requests.get(WIKIDATA_SEARCH, params=params, timeout=10)
        r.raise_for_status()
        results = r.json().get("search", [])
        if not results:
            return None

        for item in results:
            desc = (item.get("description") or "").lower()
            if media_type == "Movie" and "film" in desc:
                return item.get("id")
            if media_type == "Series" and ("television" in desc or "tv" in desc or "series" in desc):
                return item.get("id")

        return results[0].get("id")
    except Exception:
        return None


def wikidata_entity(qid):
    try:
        r = requests.get(WIKIDATA_ENTITY.format(qid=qid), timeout=10)
        r.raise_for_status()
        return r.json()["entities"][qid]
    except Exception:
        return None


def wikipedia_summary(title):
    try:
        r = requests.get(WIKIPEDIA_SUMMARY.format(title=title.replace(" ", "%20")), timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


def entity_claim(claims, pid):
    claim = claims.get(pid, [])
    if not claim:
        return None
    mainsnak = claim[0].get("mainsnak", {})
    datavalue = mainsnak.get("datavalue", {})
    return datavalue.get("value")


def fetch_wikidata_fallback(title, media_type):
    qid = wikidata_search(title, media_type)
    if not qid:
        return {}
    entity = wikidata_entity(qid)
    if not entity:
        return {}

    claims = entity.get("claims", {})
    imdb_id = entity_claim(claims, "P345")
    runtime = entity_claim(claims, "P2047")
    sitelinks = entity.get("sitelinks", {})
    wikipedia_title = sitelinks.get("enwiki", {}).get("title")

    meta = {}
    if imdb_id:
        meta["imdb_id"] = imdb_id
    if wikipedia_title:
        meta["wikipedia"] = f"https://en.wikipedia.org/wiki/{wikipedia_title.replace(' ', '_')}"
        summary = wikipedia_summary(wikipedia_title)
        if summary and summary.get("extract"):
            meta["plot"] = summary.get("extract")
    if runtime and isinstance(runtime, dict):
        amount = runtime.get("amount")
        if amount:
            meta["runtime"] = f"{amount.replace('+', '')} min"

    return meta


def search_omdb(title, media_type=None):
    """Use OMDB search endpoint and pick best fuzzy match by title."""
    try:
        params = {"apikey": OMDB_API_KEY, "s": title}
        if media_type:
            params["type"] = media_type
        resp = requests.get("https://www.omdbapi.com/", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("Response") != "True":
            return None

        candidates = data.get("Search", [])
        if not candidates:
            return None

        target = normalize_title(title)
        best = None
        best_score = 0
        for c in candidates:
            score = SequenceMatcher(None, target, normalize_title(c.get("Title", ""))).ratio()
            if score > best_score:
                best_score = score
                best = c

        if best and best_score >= 0.72:
            imdb_id = best.get("imdbID")
            if imdb_id:
                return _omdb_get({"apikey": OMDB_API_KEY, "i": imdb_id, "plot": "short"})
    except Exception:
        return None
    return None


# ═══════════════════════════════════════════════════════════
#  IMAGE HANDLING
# ═══════════════════════════════════════════════════════════

def download_poster(url, save_path):
    """Download a poster, resize to target width, save as optimized JPEG."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content))
        if img.mode != "RGB":
            img = img.convert("RGB")
        ratio = TARGET_WIDTH / img.width
        new_h = int(img.height * ratio)
        img = img.resize((TARGET_WIDTH, new_h), Image.Resampling.LANCZOS)
        img.save(save_path, "JPEG", quality=85, optimize=True)
        return img.width, img.height
    except Exception as e:
        print(f"    ⚠ Download failed: {e}")
        return None


def generate_placeholder(title, media_type, save_path):
    """Generate a styled placeholder poster card using Pillow."""
    w, h = TARGET_WIDTH, TARGET_HEIGHT
    idx = sum(ord(c) for c in title) % len(PALETTE)
    bg = PALETTE[idx]
    accent = ACCENTS[idx % len(ACCENTS)]

    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)
    font_lg, font_sm = _load_fonts()

    # Accent bar at top
    draw.rectangle([0, 0, w, 4], fill=accent)

    # Type badge (upper‑right corner)
    badge = "FILM" if media_type == "Movie" else "SERIES"
    bb = draw.textbbox((0, 0), badge, font=font_sm)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    bx, by = w - bw - 16, 16
    draw.rounded_rectangle(
        [bx - 6, by - 4, bx + bw + 6, by + bh + 4],
        radius=4, fill=accent,
    )
    draw.text((bx, by), badge, fill="#ffffff", font=font_sm)

    # Centered title
    wrapped = textwrap.wrap(title, width=16)
    line_h = 30
    y = (h - len(wrapped) * line_h) // 2
    for line in wrapped:
        lb = draw.textbbox((0, 0), line, font=font_lg)
        lw = lb[2] - lb[0]
        x = (w - lw) // 2
        draw.text((x + 1, y + 1), line, fill="#000000", font=font_lg)
        draw.text((x, y), line, fill="#ffffff", font=font_lg)
        y += line_h

    img.save(save_path, "JPEG", quality=85, optimize=True)
    return w, h


# ═══════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(description="Generate posters + manifest from library.json")
    parser.add_argument("--refresh", action="store_true", help="Re-download posters even if cached")
    parser.add_argument("--limit", type=int, help="Process only the first N entries")
    return parser.parse_args()


def run_pipeline():
    args = parse_args()
    print("=" * 60)
    print("  🎬  STATIC SITE GENERATOR — ASSET PIPELINE")
    print("=" * 60)

    if not OMDB_API_KEY:
        print("\n⚠  NO OMDB_API_KEY DETECTED")
        print("   → Running in placeholder-only mode.")
        print("   → Set it:  export OMDB_API_KEY=your_key")
        print("   → Get one: https://www.omdbapi.com/apikey.aspx\n")
    else:
        print(f"\n✓  OMDB API key detected (…{OMDB_API_KEY[-4:]})")

    library = load_library()
    overrides_file = load_overrides()
    if args.limit:
        library = library[: args.limit]
    total = len(library)
    print(f"✓  Loaded {total} entries from library.json\n")
    if args.refresh:
        print("↻  Refresh enabled — cached posters will be re-downloaded\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []
    stats = {"api": 0, "cached": 0, "placeholder": 0, "failed": []}

    for i, entry in enumerate(library, 1):
        title = entry["title"]
        media_type = entry.get("type", "Movie")
        omdb_type = "movie" if media_type == "Movie" else "series"
        filename = make_filename(title)
        save_path = OUTPUT_DIR / filename

        print(f"[{i:02d}/{total}] {title}")

        # ── Cache Check ──────────────────────────────────
        if not args.refresh and save_path.exists() and save_path.stat().st_size > 1000:
            print("    ✓ Cached (skip)")
            try:
                with Image.open(save_path) as ci:
                    cw, ch = ci.size
            except Exception:
                cw, ch = TARGET_WIDTH, TARGET_HEIGHT
            stats["cached"] += 1
            manifest.append(_build_entry(entry, filename, cw, ch, "cached"))
            continue

        # ── API Lookup ───────────────────────────────────
        poster_url = None
        omdb_meta = {}

        if OMDB_API_KEY:
            search_title = clean_title(title)
            if search_title is None:
                print("    ⊘ Override → placeholder")
            else:
                if search_title != title:
                    print(f'    → Searching as: "{search_title}"')
                data = None
                if entry.get("imdbID"):
                    data = fetch_omdb_by_id(entry.get("imdbID"))
                    if data:
                        print(f"    ✓ OMDB (by ID): {data.get('Title')} ({data.get('Year')})")
                if not data:
                    data = fetch_omdb(search_title, omdb_type)
                if data:
                    poster_url = data.get("Poster")
                    if poster_url and poster_url != "N/A":
                        ratings = {r.get("Source"): r.get("Value") for r in data.get("Ratings", [])}
                        omdb_meta = {
                            "year": data.get("Year", ""),
                            "imdb_rating": data.get("imdbRating", ""),
                            "metascore": data.get("Metascore", ""),
                            "rotten_tomatoes": ratings.get("Rotten Tomatoes", ""),
                            "plot": data.get("Plot", ""),
                            "runtime": data.get("Runtime", ""),
                            "imdb_id": data.get("imdbID", ""),
                        }
                        print(f"    ✓ OMDB: {data.get('Title')} ({data.get('Year')})")
                    else:
                        poster_url = None
                        print(f"    ⚠ OMDB matched \"{data.get('Title')}\" — no poster")
                else:
                    print("    ✗ No OMDB result")
                time.sleep(REQUEST_DELAY)

        if not omdb_meta:
            fallback_meta = fetch_wikidata_fallback(title, media_type)
            if fallback_meta:
                omdb_meta.update(fallback_meta)
                print("    ↪ Wikidata fallback metadata applied")

        # ── Download or Generate ─────────────────────────
        if poster_url:
            result = download_poster(poster_url, save_path)
            if result:
                w, h = result
                source = "omdb"
                stats["api"] += 1
            else:
                w, h = generate_placeholder(title, media_type, save_path)
                source = "placeholder"
                stats["placeholder"] += 1
                stats["failed"].append(title)
        else:
            w, h = generate_placeholder(title, media_type, save_path)
            source = "placeholder"
            stats["placeholder"] += 1
            if OMDB_API_KEY and clean_title(title) is not None:
                stats["failed"].append(title)

        overrides = METADATA_OVERRIDES.get(title, {})
        file_override = overrides_file.get(title, {})
        manifest.append({**_build_entry(entry, filename, w, h, source), **omdb_meta, **overrides, **file_override})

    # ── Write Manifest ───────────────────────────────────
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # ── Summary ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  📊  PIPELINE SUMMARY")
    print("=" * 60)
    print(f"  Total entries:      {total}")
    print(f"  Real posters (API): {stats['api']}")
    print(f"  Cached (skipped):   {stats['cached']}")
    print(f"  Placeholders:       {stats['placeholder']}")
    print(f"  Manifest written:   {MANIFEST_PATH}")

    if stats["failed"]:
        print(f"\n  ⚠  TITLES NEEDING MANUAL REVIEW ({len(stats['failed'])}):")
        for t in stats["failed"]:
            print(f"     • {t}")
        print("\n  💡 Fix: Add overrides in TITLE_OVERRIDES dict in this script.")

    print(f"\n✓  Done. Preview with:  cd {PROJECT_ROOT} && python3 -m http.server 8000\n")


def _build_entry(entry, filename, w, h, source):
    """Build a manifest entry dict."""
    return {
        "id":            entry["id"],
        "title":         entry["title"],
        "src":           filename,
        "type":          entry.get("type", "Movie"),
        "status":        entry.get("status", "Plan to Watch"),
        "language":      entry.get("language", ""),
        "genres":        entry.get("genres", []),
        "tags":          entry.get("tags", []),
        "rating":        entry.get("rating", 0),
        "streaming_name": entry.get("streaming_name", ""),
        "streaming_url":  entry.get("streaming_url", ""),
        "wikipedia":      entry.get("wikipedia", ""),
        "width":         w,
        "height":        h,
        "poster_source": source,
    }


if __name__ == "__main__":
    run_pipeline()

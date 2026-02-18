#!/usr/bin/env python3
"""
Cinemascope Asset Pipeline v3 — Multi-Source, Indian-First
===========================================================
Poster search priority:
  1. iTunes India (country=in)  — best coverage of Bollywood / South Indian cinema
  2. iTunes US   (country=us)  — Hollywood, anime, international
  3. Wikipedia REST API         — free, no key, official infobox images for most films
  4. OMDB API                   — requires OMDB_API_KEY env var
  5. SVG Geometric Placeholder  — always succeeds

Run:
    python3 scripts/fetch_assets.py
    OMDB_API_KEY=abc123 python3 scripts/fetch_assets.py

Set FORCE_REFRESH=1 to re-fetch all posters (even cached ones).
Set MIN_BYTES=10240 to re-fetch all posters below a size threshold (default 10 KB).
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent.parent
DATA_FILE     = BASE_DIR / "data"   / "library.json"
ASSETS_DIR    = BASE_DIR / "assets" / "posters"
MANIFEST_FILE = BASE_DIR / "assets" / "manifest.json"

OMDB_KEY      = os.environ.get("OMDB_API_KEY", "")
FORCE_REFRESH = os.environ.get("FORCE_REFRESH", "0") == "1"
MIN_BYTES     = int(os.environ.get("MIN_BYTES", "10240"))   # treat files smaller than this as bad

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")

ASSETS_DIR.mkdir(parents=True, exist_ok=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _get(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def _get_json(url, timeout=10):
    return json.loads(_get(url, timeout))

def _fuzzy_match(a, b):
    """Rough title similarity — normalise case, strip punctuation."""
    def n(s): return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()
    a, b = n(a), n(b)
    return a == b or a in b or b in a


# ─── Source 1 & 2 : iTunes ────────────────────────────────────────────────────
def _itunes(title, country):
    """Return best poster URL from iTunes for the given country store."""
    try:
        term = urllib.parse.quote(title)
        for media in ("movie", "tvSeason"):
            url = (f"https://itunes.apple.com/search"
                   f"?term={term}&country={country}&media={media}&limit=8&lang=en_us")
            data = _get_json(url)
            results = data.get("results", [])
            # prefer exact-match first
            for r in results:
                name = r.get("trackName") or r.get("collectionName") or ""
                if _fuzzy_match(title, name):
                    art = r.get("artworkUrl100", "")
                    if art:
                        # bump to highest available resolution
                        art = re.sub(r"(\d+)x(\d+)bb", "600x900bb", art)
                        return art
            # accept first result if nothing matched exactly
            if results:
                art = results[0].get("artworkUrl100", "")
                if art:
                    return re.sub(r"(\d+)x(\d+)bb", "600x900bb", art)
    except Exception as e:
        pass
    return None

def fetch_itunes_india(title):  return _itunes(title, "in")
def fetch_itunes_us(title):     return _itunes(title, "us")


# ─── Source 3 : Wikipedia REST API ────────────────────────────────────────────
def fetch_wikipedia(title):
    """
    Tries multiple Wikipedia page-name variations and returns the thumbnail
    URL if the page exists and has an image.
    """
    variants = [
        title,
        title + " film",
        title + " (film)",
        title + " (TV series)",
        title + " (miniseries)",
    ]
    for v in variants:
        try:
            slug = urllib.parse.quote(v.replace(" ", "_"))
            data = _get_json(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}",
                timeout=8
            )
            thumb = data.get("thumbnail", {}).get("source", "")
            if thumb:
                # request a larger size
                thumb = re.sub(r"/\d+px-", "/600px-", thumb)
                return thumb
        except Exception:
            pass
    return None


# ─── Source 4 : OMDB ──────────────────────────────────────────────────────────
def fetch_omdb(title):
    if not OMDB_KEY:
        return None
    try:
        url = (f"https://www.omdbapi.com/"
               f"?apikey={OMDB_KEY}&t={urllib.parse.quote(title)}&plot=short")
        data = _get_json(url)
        poster = data.get("Poster", "N/A")
        if poster and poster != "N/A":
            return poster
    except Exception:
        pass
    return None


# ─── Source 5 : SVG Placeholder ───────────────────────────────────────────────
def write_placeholder(title, path):
    h = sum(ord(c) for c in title) % 360
    c1 = f"hsl({h},60%,20%)"
    c2 = f"hsl({(h+45)%360},55%,10%)"
    lines = title.split()
    text_lines = []
    row, buf = [], 0
    for w in lines:
        if buf + len(w) > 14 and buf:
            text_lines.append(" ".join(row)); row, buf = [w], len(w)
        else:
            row.append(w); buf += len(w) + 1
    if row: text_lines.append(" ".join(row))
    tsvg = "".join(
        f'<text x="150" y="{220 + i*28}" font-family="sans-serif" '
        f'font-size="20" fill="rgba(255,255,255,.7)" text-anchor="middle">{l}</text>'
        for i, l in enumerate(text_lines)
    )
    svg = f"""<svg width="300" height="450" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1">
    <stop offset="0%" stop-color="{c1}"/>
    <stop offset="100%" stop-color="{c2}"/>
  </linearGradient></defs>
  <rect width="300" height="450" fill="url(#g)" rx="8"/>
  <text x="150" y="180" font-family="sans-serif" font-size="48"
        text-anchor="middle" fill="rgba(255,255,255,.15)">🎬</text>
  {tsvg}
</svg>"""
    path.with_suffix(".svg").write_text(svg, encoding="utf-8")
    return path.with_suffix(".svg")


# ─── Download ─────────────────────────────────────────────────────────────────
def download(url, path):
    try:
        data = _get(url)
        if len(data) < 2048:          # sanity: reject suspiciously tiny responses
            return False
        path.write_bytes(data)
        return True
    except Exception as e:
        print(f"      ↳ download error: {e}")
        return False


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("🎬  Cinemascope Asset Pipeline v3 — Indian-First\n")

    with open(DATA_FILE, encoding="utf-8") as f:
        library = json.load(f)

    SOURCES = [
        ("iTunes India",  fetch_itunes_india),
        ("iTunes US",     fetch_itunes_us),
        ("Wikipedia",     fetch_wikipedia),
        ("OMDB",          fetch_omdb),
    ]

    manifest = []
    stats = {"cached": 0, "downloaded": 0, "placeholder": 0, "errors": 0}

    for item in library:
        title = item["title"]
        safe  = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_").lower()
        jpg   = ASSETS_DIR / f"{safe}.jpg"
        svg   = ASSETS_DIR / f"{safe}.svg"

        # Decide whether to skip / re-fetch
        is_bad = (
            (jpg.exists() and jpg.stat().st_size < MIN_BYTES) or
            svg.exists()      # svg = was a placeholder last time
        )

        if not FORCE_REFRESH and jpg.exists() and not is_bad:
            print(f"  ✅  {title:<45}  (cached {jpg.stat().st_size//1024} KB)")
            stats["cached"] += 1
            manifest.append({**item, "src": jpg.name, "has_poster": True})
            continue

        # Delete stale/bad file so we start fresh
        for p in (jpg, svg):
            if p.exists(): p.unlink()

        print(f"  🔍  {title:<45}", end="", flush=True)

        url, source_name = None, None
        for name, fn in SOURCES:
            try:
                u = fn(title)
                if u:
                    url, source_name = u, name
                    break
            except Exception:
                pass

        if url:
            ok = download(url, jpg)
            if ok:
                print(f"  ⬇   {source_name} ({jpg.stat().st_size//1024} KB)")
                stats["downloaded"] += 1
                manifest.append({**item, "src": jpg.name, "has_poster": True})
                time.sleep(0.4)
                continue

        # All sources failed — write placeholder
        ph = write_placeholder(title, jpg)
        print(f"  🎨  placeholder")
        stats["placeholder"] += 1
        manifest.append({**item, "src": ph.name, "has_poster": False})
        time.sleep(0.2)

    # Write manifest
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n✨  Done: {stats['cached']} cached · "
          f"{stats['downloaded']} downloaded · "
          f"{stats['placeholder']} placeholders\n")

if __name__ == "__main__":
    main()

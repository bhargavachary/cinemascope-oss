#!/usr/bin/env python3
"""
Phase 3 — India-First OTT Discovery
=====================================
Uses TMDB's official "Watch Providers" endpoint (backed by JustWatch data)
to find which streaming platforms carry each title in India (region=IN).

Provider types:
  flatrate — subscription (Netflix, Prime, Hotstar, JioCinema, SonyLIV …)
  free     — ad-supported (YouTube, MX Player, Zee5 free tier …)
  ads      — ad-supported (alternative classification some providers use)
  rent     — digital rental (Apple TV, Google Play …)
  buy      — digital purchase

A `streaming_in` array is written to every item in the staging file.
Items that have no India availability get an empty array.

Usage:
    TMDB_API_KEY=... python3 scripts/ott_locator.py

Run after data_harvester.py so temp_enrichment.json already exists.
Falls back to library.json if the staging file is absent.
"""

import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests")
    sys.exit(1)

BASE_DIR      = Path(__file__).parent.parent
STAGING_FILE  = BASE_DIR / "data" / "temp_enrichment.json"
LIBRARY_FILE  = BASE_DIR / "data" / "library.json"

TMDB_KEY  = os.environ.get("TMDB_API_KEY", "")
TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_LOGO = "https://image.tmdb.org/t/p/original"

# ─── India-market provider catalogue (TMDB provider_id → display name) ────────
# Source: https://www.themoviedb.org/tv/network — filtered for IN availability.
# Updated May 2026.  Extend this dict as new platforms enter India.
INDIA_PROVIDERS: dict[int, str] = {
    8:   "Netflix",
    119: "Amazon Prime Video",
    122: "Disney+ Hotstar",
    220: "JioCinema",
    237: "SonyLIV",
    232: "Zee5",
    121: "Voot",
    505: "MX Player",
    532: "Aha",
    350: "Apple TV+",
    2:   "Apple TV",
    191: "MUBI",
    337: "Disney+",
    531: "Paramount+",
    588: "Lionsgate Play",
    11:  "MUBI",       # alternate ID
    615: "Sun NXT",
    444: "Hoichoi",
    315: "ShemarooMe",
}

# Provider-type labels for UI display
TYPE_LABEL: dict[str, str] = {
    "flatrate": "Subscription",
    "free":     "Free",
    "ads":      "Free (Ads)",
    "rent":     "Rent",
    "buy":      "Buy",
}


# ─── TMDB helpers ─────────────────────────────────────────────────────────────

def _tmdb_get(path: str, params: dict | None = None) -> dict:
    p = {"api_key": TMDB_KEY, **(params or {})}
    r = requests.get(f"{TMDB_BASE}{path}", params=p, timeout=10)
    r.raise_for_status()
    return r.json()


def get_ott_india(tmdb_id: int, media_type: str) -> tuple[list, str]:
    """
    Query TMDB watch/providers for India.
    Returns (list_of_options, justwatch_link_url).
    Each option dict: {provider, provider_id, type, type_label, logo_url}
    """
    media = "movie" if media_type == "Movie" else "tv"
    try:
        data    = _tmdb_get(f"/{media}/{tmdb_id}/watch/providers")
        in_data = data.get("results", {}).get("IN", {})
        jw_link = in_data.get("link", "")

        options = []
        seen_providers: set[int] = set()

        for ott_type in ("flatrate", "free", "ads", "rent", "buy"):
            for p in in_data.get(ott_type, []):
                pid = p.get("provider_id")
                if pid in seen_providers:
                    continue
                seen_providers.add(pid)

                name = INDIA_PROVIDERS.get(pid) or p.get("provider_name", f"Provider {pid}")
                logo = (TMDB_LOGO + p["logo_path"]) if p.get("logo_path") else None

                options.append({
                    "provider":    name,
                    "provider_id": pid,
                    "type":        ott_type,
                    "type_label":  TYPE_LABEL.get(ott_type, ott_type.title()),
                    "logo_url":    logo,
                })

        return options, jw_link

    except Exception as exc:
        return [], ""


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    if not TMDB_KEY:
        print("Error: TMDB_API_KEY environment variable not set.")
        sys.exit(1)

    # Prefer staging file (run after data_harvester); fall back to library
    source = STAGING_FILE if STAGING_FILE.exists() else LIBRARY_FILE
    with open(source, encoding="utf-8") as fh:
        library = json.load(fh)

    print(f"📺  OTT Locator — India (IN) — {len(library)} items\n")

    updated  = 0
    skipped  = 0
    no_match = 0

    for item in library:
        tmdb_id = item.get("tmdb_id")
        if not tmdb_id:
            skipped += 1
            continue

        options, link = get_ott_india(int(tmdb_id), item.get("type", "Movie"))
        item["streaming_in"] = options

        if link:
            item["justwatch_url"] = link

        if options:
            updated += 1
            # Summarise flatrate providers for log readability
            flat = [o["provider"] for o in options if o["type"] == "flatrate"]
            free = [o["provider"] for o in options if o["type"] in ("free", "ads")]
            summary = ", ".join(flat + [f"{p} (free)" for p in free]) or "rent/buy only"
            print(f"  ✔  {item['title']:<45}  →  {summary}")
        else:
            no_match += 1

        time.sleep(0.3)   # polite rate-limit

    STAGING_FILE.write_text(
        json.dumps(library, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\n✓  {updated} titles with IN streaming data.")
    if skipped:
        print(f"   {skipped} skipped (no tmdb_id — run id_resolver.py first).")
    if no_match:
        print(f"   {no_match} titles not yet available on Indian platforms.")
    print(f"   Staging file updated → {STAGING_FILE.name}")
    print("   Next: python3 scripts/enrich_library.py")


if __name__ == "__main__":
    main()

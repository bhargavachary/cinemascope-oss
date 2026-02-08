#!/usr/bin/env python3
"""
Backup Metadata Resolver (No Scraping)
======================================
Uses Wikidata + Wikipedia APIs to fill gaps when OMDB mismatches.
Writes results into data/overrides.json (merged by title).

Usage:
    python3 scripts/fetch_metadata_backup.py
    python3 scripts/fetch_metadata_backup.py --limit 10
"""

import argparse
import json
import time
from pathlib import Path
import requests

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR
LIBRARY_PATH = PROJECT_ROOT / "data" / "library.json"
OVERRIDES_PATH = PROJECT_ROOT / "data" / "overrides.json"

WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
WIKIPEDIA_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

REQUEST_DELAY = 0.2


def parse_args():
    parser = argparse.ArgumentParser(description="Resolve metadata via Wikidata/Wikipedia")
    parser.add_argument("--limit", type=int, help="Process only the first N entries")
    return parser.parse_args()


def load_library():
    with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_overrides():
    if not OVERRIDES_PATH.exists():
        return {}
    with open(OVERRIDES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def save_overrides(data):
    with open(OVERRIDES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def wikidata_search(title, media_type):
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

    # Prefer items tagged as film or television series when possible
    for item in results:
        desc = (item.get("description") or "").lower()
        if media_type == "Movie" and "film" in desc:
            return item.get("id")
        if media_type == "Series" and ("television" in desc or "tv" in desc or "series" in desc):
            return item.get("id")

    return results[0].get("id")


def entity_claim(claims, pid):
    claim = claims.get(pid, [])
    if not claim:
        return None
    mainsnak = claim[0].get("mainsnak", {})
    datavalue = mainsnak.get("datavalue", {})
    return datavalue.get("value")


def wikidata_entity(qid):
    r = requests.get(WIKIDATA_ENTITY.format(qid=qid), timeout=10)
    r.raise_for_status()
    return r.json()["entities"][qid]


def wikipedia_summary(title):
    r = requests.get(WIKIPEDIA_SUMMARY.format(title=title.replace(" ", "%20")), timeout=10)
    if r.status_code != 200:
        return None
    return r.json()


def extract_metadata(entity):
    claims = entity.get("claims", {})
    imdb_id = entity_claim(claims, "P345")
    image = entity_claim(claims, "P18")
    runtime = entity_claim(claims, "P2047")
    wikipedia_title = None

    sitelinks = entity.get("sitelinks", {})
    if "enwiki" in sitelinks:
        wikipedia_title = sitelinks["enwiki"].get("title")

    meta = {}
    if imdb_id:
        meta["imdb_id"] = imdb_id
    if wikipedia_title:
        meta["wikipedia"] = f"https://en.wikipedia.org/wiki/{wikipedia_title.replace(' ', '_')}"

    if runtime and isinstance(runtime, dict):
        amount = runtime.get("amount")
        if amount:
            meta["runtime"] = f"{amount.replace('+','')} min"

    if image:
        meta["wikidata_image"] = image

    if wikipedia_title:
        summary = wikipedia_summary(wikipedia_title)
        if summary and summary.get("extract"):
            meta["plot"] = summary.get("extract")

    return meta


def main():
    args = parse_args()
    library = load_library()
    if args.limit:
        library = library[: args.limit]

    overrides = load_overrides()

    for entry in library:
        title = entry["title"]
        media_type = entry.get("type", "Movie")

        if title in overrides:
            continue

        try:
            qid = wikidata_search(title, media_type)
            if not qid:
                continue
            entity = wikidata_entity(qid)
            meta = extract_metadata(entity)
            if meta:
                overrides[title] = meta
                print(f"✓ {title} → {qid} ({len(meta)} fields)")
        except Exception:
            pass

        time.sleep(REQUEST_DELAY)

    save_overrides(overrides)
    print(f"\nSaved overrides to {OVERRIDES_PATH}")


if __name__ == "__main__":
    main()

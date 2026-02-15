#!/usr/bin/env python3
"""
Local Admin Server (Flask)
==========================
Serves the static site locally and exposes admin API endpoints for
metadata refresh and library edits.

Usage:
    OMDB_API_KEY=your_key python3 server.py
    Then open http://localhost:8080
"""

import json
import os
from pathlib import Path
from difflib import SequenceMatcher

import requests
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).parent.resolve()
DATA_FILE = BASE_DIR / "data" / "library.json"

OMDB_API_KEY = os.environ.get("OMDB_API_KEY", "")

WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
WIKIPEDIA_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

app = Flask(__name__, static_folder=None)


def load_library():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_library(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")


def normalize_title(value):
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _omdb_get(params):
    if not OMDB_API_KEY:
        return None
    try:
        resp = requests.get("https://www.omdbapi.com/", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("Response") == "True":
            return data
    except Exception:
        return None
    return None


def fetch_omdb_by_id(imdb_id):
    if not imdb_id:
        return None
    return _omdb_get({"apikey": OMDB_API_KEY, "i": imdb_id, "plot": "short"})


def fetch_omdb_by_title(title, media_type):
    params = {"apikey": OMDB_API_KEY, "t": title, "plot": "short"}
    if media_type:
        params["type"] = media_type
    data = _omdb_get(params)
    if data:
        return data

    try:
        params = {"apikey": OMDB_API_KEY, "s": title}
        if media_type:
            params["type"] = media_type
        resp = requests.get("https://www.omdbapi.com/", params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("Response") != "True":
            return None
        candidates = payload.get("Search", [])
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
            return fetch_omdb_by_id(best.get("imdbID"))
    except Exception:
        return None
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
            if media_type == "movie" and "film" in desc:
                return item.get("id")
            if media_type == "series" and ("television" in desc or "tv" in desc or "series" in desc):
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


def entity_claim(claims, pid):
    claim = claims.get(pid, [])
    if not claim:
        return None
    mainsnak = claim[0].get("mainsnak", {})
    datavalue = mainsnak.get("datavalue", {})
    return datavalue.get("value")


def wikipedia_summary(title):
    try:
        r = requests.get(WIKIPEDIA_SUMMARY.format(title=title.replace(" ", "%20")), timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


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


def refresh_metadata(item):
    title = item.get("title", "")
    media_type = "movie" if item.get("type", "Movie") == "Movie" else "series"

    omdb = None
    if OMDB_API_KEY:
        if item.get("imdbID"):
            omdb = fetch_omdb_by_id(item.get("imdbID"))
        if not omdb:
            omdb = fetch_omdb_by_title(title, media_type)

    ratings = {}
    if omdb:
        ratings = {r.get("Source"): r.get("Value") for r in omdb.get("Ratings", [])}

    meta = {
        "imdbID": omdb.get("imdbID") if omdb else item.get("imdbID"),
        "imdb_rating": omdb.get("imdbRating") if omdb else "",
        "metascore": omdb.get("Metascore") if omdb else "",
        "rotten_tomatoes": ratings.get("Rotten Tomatoes", ""),
        "plot": omdb.get("Plot") if omdb else "",
        "runtime": omdb.get("Runtime") if omdb else "",
    }

    # Fallback/Enhancement via Wikidata (The "custom script" logic)
    # We try this if we are missing data OR if the user asked for a refresh (which is this function).
    # We prioritize Wikidata for Plot if OMDB's is short or missing.
    wiki_meta = fetch_wikidata_fallback(title, media_type)
    
    if wiki_meta:
        # Fill missing fields
        for key, value in wiki_meta.items():
            if not meta.get(key):
                meta[key] = value
        
        # specific overwrite logic
        if wiki_meta.get("plot") and len(wiki_meta.get("plot")) > len(meta.get("plot", "")):
            meta["plot"] = wiki_meta["plot"]
        if wiki_meta.get("wikipedia"):
             meta["wikipedia"] = wiki_meta["wikipedia"]

    meta["imdb_id"] = meta.get("imdbID") or meta.get("imdb_id")

    item["imdbID"] = meta.get("imdbID") or item.get("imdbID")
    item["plot"] = meta.get("plot") or item.get("plot")
    item["runtime"] = meta.get("runtime") or item.get("runtime")
    item["imdbRating"] = meta.get("imdb_rating") or item.get("imdbRating")
    item["metascore"] = meta.get("metascore") or item.get("metascore")
    item["rottenTomatoes"] = meta.get("rotten_tomatoes") or item.get("rottenTomatoes")
    item["wikipedia"] = meta.get("wikipedia") or item.get("wikipedia")

    return meta


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR), "table.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(str(BASE_DIR), path)


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "mode": "local"})


@app.route("/api/library", methods=["GET"])
def api_library():
    return jsonify(load_library())


@app.route("/api/library", methods=["POST"])
def api_add_item():
    library = load_library()
    body = request.json or {}
    max_id = max((item["id"] for item in library), default=0)
    body["id"] = max_id + 1
    if not body.get("title"):
        return jsonify({"error": "Title is required"}), 400
    item = {
        "id": body["id"],
        "title": body["title"],
        "type": body.get("type", "Movie"),
        "status": body.get("status", "Plan to Watch"),
        "language": body.get("language", "English"),
        "rating": body.get("rating", 0),
        "genres": body.get("genres", []),
        "imdbID": body.get("imdbID"),
        "tags": body.get("tags", [])
    }
    library.append(item)
    save_library(library)
    return jsonify(item), 201


@app.route("/api/library/<int:item_id>", methods=["PUT"])
def api_update_item(item_id):
    library = load_library()
    body = request.json or {}
    for i, item in enumerate(library):
        if item["id"] == item_id:
            library[i] = {
                **item,
                "title": body.get("title", item["title"]),
                "type": body.get("type", item["type"]),
                "status": body.get("status", item["status"]),
                "language": body.get("language", item.get("language", "English")),
                "rating": body.get("rating", item.get("rating", 0)),
                "genres": body.get("genres", item.get("genres", [])),
                "imdbID": body.get("imdbID", item.get("imdbID")),
                "tags": body.get("tags", item.get("tags", []))
            }
            save_library(library)
            return jsonify(library[i])
    return jsonify({"error": "Item not found"}), 404


@app.route("/api/library/<int:item_id>", methods=["DELETE"])
def api_delete_item(item_id):
    library = load_library()
    new_library = [item for item in library if item["id"] != item_id]
    if len(new_library) == len(library):
        return jsonify({"error": "Item not found"}), 404
    save_library(new_library)
    return jsonify({"deleted": item_id})


@app.route("/api/refresh_metadata/<int:item_id>", methods=["POST"])
def api_refresh_metadata(item_id):
    library = load_library()
    for item in library:
        if item["id"] == item_id:
            meta = refresh_metadata(item)
            save_library(library)
            return jsonify({"item": meta})
    return jsonify({"error": "Item not found"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\nLocal admin server running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port)

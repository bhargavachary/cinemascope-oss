#!/usr/bin/env python3
"""
Phase 4+5 — Enrichment Orchestrator & Merge
=============================================
Ties the full pipeline together and writes the final enriched library.

What it does
------------
1. (Optional) Runs id_resolver → data_harvester → ott_locator as subprocesses
   when --run-pipeline is given.
2. Reads data/temp_enrichment.json (staging file produced by the above scripts).
3. Normalises all ratings to a 0–10 scale:
     IMDb        — already /10
     Metacritic  — /100 → /10
     Rotten Tomatoes — "85%" → 8.5
     Letterboxd  — /5 → /10
4. Computes a weighted_score per entry; weights are genre-adjusted:
     Documentaries → critics (RT) weighted higher
     Action        → IMDb weighted higher
     Default       → (IMDb×0.4) + (RT×0.3) + (Letterboxd×0.3)
5. Expands hidden_tags from HIDDEN_TAGS_MAP based on genres.
6. Adds / refreshes the `last_enriched` ISO-8601 UTC timestamp.
7. Merges staging → library.json with the override protocol:
     overrides.json fields  >  existing non-null library fields  >  scraped data
   Pass --force-overwrite to let scraped data overwrite existing library fields.
8. Removes the staging file after a successful merge.

Usage (full pipeline, auto mode):
    TMDB_API_KEY=... OMDB_API_KEY=... python3 scripts/enrich_library.py \\
        --run-pipeline --auto

Usage (merge-only, after individual stage scripts):
    python3 scripts/enrich_library.py

Stale-data check (default 7 days):
    python3 scripts/enrich_library.py --stale-days 14
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR       = Path(__file__).parent.parent
LIBRARY_FILE   = BASE_DIR / "data" / "library.json"
STAGING_FILE   = BASE_DIR / "data" / "temp_enrichment.json"
OVERRIDES_FILE = BASE_DIR / "data" / "overrides.json"


# ─── Genre → hidden tag classifier ────────────────────────────────────────────
# Extend this dict to add cinephile sub-genre tags automatically.
HIDDEN_TAGS_MAP: dict[str, list[str]] = {
    "Horror":            ["Folk Horror", "Slow Burn"],
    "Crime":             ["Neo-Noir", "Gritty Realism"],
    "Science Fiction":   ["Hard Sci-Fi", "Dystopian"],
    "Thriller":          ["Psychological Thriller"],
    "Documentary":       ["Non-Fiction", "Essay Film"],
    "Animation":         ["Adult Animation"],
    "Drama":             ["Character Study"],
    "Mystery":           ["Whodunit"],
    "Romance":           ["Melodrama"],
    "History":           ["Period Drama"],
    "War":               ["Anti-War Cinema"],
    "Music":             ["Concert Film"],
    "Family":            ["Coming-of-Age"],
    "Fantasy":           ["Mythological"],
}

# Genre-specific weighting: (imdb_w, rt_w, letterboxd_w)
GENRE_WEIGHTS: dict[str, tuple[float, float, float]] = {
    "Documentary":     (0.30, 0.50, 0.20),
    "Action":          (0.50, 0.20, 0.30),
    "Horror":          (0.35, 0.25, 0.40),
    "Animation":       (0.35, 0.35, 0.30),
    "default":         (0.40, 0.30, 0.30),
}


# ─── Rating normalisation ─────────────────────────────────────────────────────

def _to_float(v) -> float | None:
    if v is None:
        return None
    s = str(v).replace("%", "").replace(",", "").strip()
    if s in ("", "N/A", "—", "null", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def normalise_ratings(item: dict) -> dict:
    """Return a dict of norm_* keys (all on a 0–10 scale)."""
    imdb     = _to_float(item.get("imdb_rating") or item.get("imdbRating"))
    meta_raw = _to_float(item.get("metascore"))
    rt_raw   = _to_float(item.get("rotten_tomatoes") or item.get("rottenTomatoes"))
    lb_raw   = _to_float(item.get("letterboxd_rating"))

    meta_n = round(meta_raw / 10, 2) if meta_raw is not None else None
    rt_n   = round(rt_raw  / 10, 2) if rt_raw   is not None else None
    lb_n   = round(lb_raw  *  2, 2) if lb_raw   is not None else None

    return {
        "norm_imdb":       imdb,
        "norm_metascore":  meta_n,
        "norm_rt":         rt_n,
        "norm_letterboxd": lb_n,
    }


def compute_weighted_score(item: dict, norms: dict) -> float | None:
    """
    Weighted recommendation score (0–10).
    Genre-adjusted weights; re-normalises when a source is missing.
    """
    genres = item.get("genres", [])
    primary = genres[0] if genres else "default"
    w_imdb, w_rt, w_lb = GENRE_WEIGHTS.get(primary, GENRE_WEIGHTS["default"])

    parts: list[tuple[float, float]] = []   # (value * weight, weight)
    if norms["norm_imdb"]       is not None:
        parts.append((norms["norm_imdb"]       * w_imdb, w_imdb))
    if norms["norm_rt"]         is not None:
        parts.append((norms["norm_rt"]         * w_rt,   w_rt))
    if norms["norm_letterboxd"] is not None:
        parts.append((norms["norm_letterboxd"] * w_lb,   w_lb))

    if not parts:
        return None

    total_weighted = sum(p[0] for p in parts)
    total_weight   = sum(p[1] for p in parts)
    # Rescale to the declared full weight sum so score stays on 0-10
    full_weight = w_imdb + w_rt + w_lb
    score = (total_weighted / total_weight) * full_weight / full_weight * 10
    # Simpler: weighted average already gives 0-10 value
    score = total_weighted / total_weight
    return round(min(score, 10.0), 2)


def expand_hidden_tags(item: dict) -> list[str]:
    hidden = set(item.get("hidden_tags") or [])
    for genre in item.get("genres", []):
        hidden.update(HIDDEN_TAGS_MAP.get(genre, []))
    return sorted(hidden)


# ─── Stale check ──────────────────────────────────────────────────────────────

def is_stale(item: dict, stale_days: int) -> bool:
    ts = item.get("last_enriched")
    if not ts:
        return True
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt) > timedelta(days=stale_days)
    except Exception:
        return True


# ─── Override / merge protocol ────────────────────────────────────────────────

def load_overrides() -> dict:
    if OVERRIDES_FILE.exists():
        with open(OVERRIDES_FILE, encoding="utf-8") as fh:
            try:
                return json.load(fh)
            except json.JSONDecodeError:
                return {}
    return {}


NULL_LIKE = {None, "", "N/A", "—", 0, []}


def _lifecycle_streaming_providers(
    lib_item: dict,
    new_providers: list[dict],
    status: str,
) -> None:
    """
    Apply the "Prune with a Memory" lifecycle for streaming availability.

    Strategy:
    ─────────
    Plan to Watch (strict):
      - Use only current providers from TMDB API
      - Prune disappeared providers silently
      - Keep UI high-trust: no stale data
    
    Watched (archival):
      - Use current providers (same as Plan to Watch)
      - BUT: if providers disappeared, archive them to metadata_history
      - Later, you can build "Subscription Audit" to track value
    
    Mutates lib_item in-place: sets streaming_in and optionally metadata_history.
    """
    if not new_providers:
        # API returned nothing; keep old data as-is (temporary API failure)
        return

    old_providers = lib_item.get("streaming_in", [])
    old_provider_names = {
        p.get("provider")
        for p in old_providers
        if isinstance(p, dict) and p.get("provider")
    }
    new_provider_names = {
        p.get("provider")
        for p in new_providers
        if isinstance(p, dict) and p.get("provider")
    }

    disappeared = old_provider_names - new_provider_names

    if disappeared and status == "Watched":
        # For watched items, preserve history of what was available
        if "metadata_history" not in lib_item:
            lib_item["metadata_history"] = {}
        lib_item["metadata_history"]["past_providers"] = sorted(list(disappeared))
        lib_item["metadata_history"]["last_pruned"] = (
            datetime.now(timezone.utc).isoformat()
        )
        # (Silent prune for Plan to Watch; just history for Watched)

    # Always use new providers (strict or archival, both are current)
    lib_item["streaming_in"] = new_providers


def merge_item(
    lib_item: dict,
    enriched: dict,
    overrides: dict,
    *,
    force: bool,
) -> dict:
    """
    Merge enriched fields into lib_item.
    Priority: overrides > (existing if not force) > enriched.
    
    Special handling for streaming_in:
      - Applies lifecycle pruning based on item status (Plan to Watch vs Watched)
      - See _lifecycle_streaming_providers() for detail
    """
    result  = {**lib_item}
    title   = lib_item.get("title", "")
    ov      = overrides.get(title, {})

    # ─── Special: streaming_in lifecycle (prune with memory) ───────────────────
    if "streaming_in" in enriched:
        status = result.get("status", "Watched")  # default to Watched if absent
        _lifecycle_streaming_providers(result, enriched["streaming_in"], status)
        # Mark as handled so we skip it in the main loop
        enriched_without_streaming = {
            k: v for k, v in enriched.items() if k != "streaming_in"
        }
    else:
        enriched_without_streaming = enriched

    # ─── Main merge loop for all other fields ──────────────────────────────────
    for key, value in enriched_without_streaming.items():
        if key in ov:
            result[key] = ov[key]            # override always wins
        elif force or result.get(key) in NULL_LIKE:
            result[key] = value              # fill gap or force

    # Apply overrides for keys not covered by enriched data
    for key, value in ov.items():
        result[key] = value

    return result


# ─── Pipeline runner ──────────────────────────────────────────────────────────

def _run_stage(script: str, extra_args: list[str] | None = None) -> None:
    cmd = [sys.executable, str(BASE_DIR / "scripts" / script)] + (extra_args or [])
    env = os.environ.copy()
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        print(f"⚠️   {script} exited with code {result.returncode} — continuing.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich, normalise, score, and merge library data."
    )
    parser.add_argument(
        "--run-pipeline", action="store_true",
        help="Run id_resolver → data_harvester → ott_locator before merging",
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Pass --auto to id_resolver (non-interactive, CI-safe)",
    )
    parser.add_argument(
        "--force-overwrite", action="store_true",
        help="Scraped data overwrites existing non-null fields",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Compute and print changes without writing library.json",
    )
    parser.add_argument(
        "--stale-days", type=int, default=7,
        help="Skip entries enriched within N days (default: 7)",
    )
    args = parser.parse_args()

    # ── Step 1: Run upstream scripts if requested ──────────────────────────
    if args.run_pipeline:
        print("🚀  Running full enrichment pipeline …\n")
        resolver_flags = ["--auto"] if args.auto else []
        _run_stage("id_resolver.py",    resolver_flags)
        _run_stage("data_harvester.py")
        _run_stage("ott_locator.py")
        print()

    # ── Step 2: Load files ─────────────────────────────────────────────────
    with open(LIBRARY_FILE, encoding="utf-8") as fh:
        library: list[dict] = json.load(fh)

    if not STAGING_FILE.exists():
        print(
            f"Error: {STAGING_FILE.name} not found.\n"
            "Run  --run-pipeline  or the individual stage scripts first."
        )
        sys.exit(1)

    with open(STAGING_FILE, encoding="utf-8") as fh:
        enriched_list: list[dict] = json.load(fh)

    overrides = load_overrides()

    # Index enriched entries by id for O(1) lookup
    enriched_by_id = {e["id"]: e for e in enriched_list}

    now_ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # ── Step 3: Merge + post-process ──────────────────────────────────────
    final: list[dict]  = []
    merged_count       = 0
    skipped_count      = 0

    for item in library:
        enriched = enriched_by_id.get(item["id"], item)

        if not is_stale(item, args.stale_days):
            final.append(item)
            skipped_count += 1
            continue

        merged = merge_item(item, enriched, overrides, force=args.force_overwrite)

        # Phase 4: normalise + score
        norms = normalise_ratings(merged)
        merged.update(norms)

        ws = compute_weighted_score(merged, norms)
        if ws is not None:
            merged["weighted_score"] = ws

        merged["hidden_tags"]   = expand_hidden_tags(merged)
        merged["last_enriched"] = now_ts

        final.append(merged)
        merged_count += 1

    # ── Step 4: Write ─────────────────────────────────────────────────────
    prefix = "[dry-run] " if args.dry_run else ""
    print(
        f"{prefix}Merged {merged_count} entries, "
        f"skipped {skipped_count} (fresh within {args.stale_days}d)."
    )

    if not args.dry_run:
        with open(LIBRARY_FILE, "w", encoding="utf-8") as fh:
            json.dump(final, fh, indent=4, ensure_ascii=False)
            fh.write("\n")
        print(f"✓  library.json updated.")

        if STAGING_FILE.exists():
            STAGING_FILE.unlink()
            print(f"✓  Staging file removed.")

    print(
        "\n✨  Done.\n"
        "   Run  python3 scripts/fetch_assets.py  to refresh assets/manifest.json\n"
        "   so the frontend picks up the new streaming and score data."
    )


if __name__ == "__main__":
    main()

"""
tests/test_data_integrity.py
Validates the static dataset, manifest, and asset integrity for CinemaScope.
"""

import json
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"


class TestDataIntegrity(unittest.TestCase):

    def test_library_json_schema(self):
        library_path = DATA_DIR / "library.json"
        self.assertTrue(library_path.exists(), "library.json must exist")
        
        with open(library_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0, "library.json should not be empty")

        valid_types = {"Movie", "Series"}
        valid_statuses = {"Watched", "Plan to Watch", "Recommended"}

        seen_ids = set()
        for idx, item in enumerate(data):
            # ID check
            item_id = item.get("id")
            self.assertIsNotNone(item_id, f"Item at index {idx} missing id")
            self.assertNotIn(item_id, seen_ids, f"Duplicate id {item_id} found")
            seen_ids.add(item_id)

            # Title check
            title = item.get("title")
            self.assertTrue(title and isinstance(title, str), f"Item {item_id} has invalid title")

            # Type check
            item_type = item.get("type")
            self.assertIn(item_type, valid_types, f"Item '{title}' has invalid type: {item_type}")

            # Status check
            status = item.get("status")
            self.assertIn(status, valid_statuses, f"Item '{title}' has invalid status: {status}")

            # Tags check
            tags = item.get("tags")
            if tags is not None:
                self.assertIsInstance(tags, list, f"Item '{title}' tags should be a list")

    def test_assets_manifest_and_posters(self):
        manifest_path = ASSETS_DIR / "manifest.json"
        self.assertTrue(manifest_path.exists(), "manifest.json must exist")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertIsInstance(manifest, list)

        posters_dir = ASSETS_DIR / "posters"
        self.assertTrue(posters_dir.is_dir(), "assets/posters directory must exist")

        checked_count = 0
        for entry in manifest:
            if entry.get("has_poster") and entry.get("src"):
                poster_file = posters_dir / entry["src"]
                self.assertTrue(poster_file.exists(), f"Poster asset missing: {entry['src']}")
                self.assertGreater(poster_file.stat().st_size, 0, f"Poster asset is empty: {entry['src']}")
                checked_count += 1

        self.assertGreater(checked_count, 0, "Should have verified at least one poster asset")

    def test_overrides_json_validity(self):
        overrides_path = DATA_DIR / "overrides.json"
        if overrides_path.exists():
            with open(overrides_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIsInstance(data, dict, "overrides.json must be a JSON object")

    def test_library_field_types_and_ranges(self):
        library_path = DATA_DIR / "library.json"
        with open(library_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            # Title check
            title = item.get("title", "")
            self.assertTrue(len(title) > 0, f"Title missing or empty in item {item.get('id')}")

            # Rating bounds
            rating = item.get("rating")
            if rating not in ("NR", None, ""):
                try:
                    r_val = float(rating)
                    self.assertTrue(0.0 <= r_val <= 10.0, f"Rating out of bounds in {title}: {r_val}")
                except ValueError:
                    pass

            # IMDb ID format check if present
            imdb_id = item.get("imdbID")
            if imdb_id:
                self.assertTrue(imdb_id.startswith("tt"), f"Invalid IMDb ID in {title}: {imdb_id}")

    def test_atomic_readme_generation(self):
        """Verify update_readme generates a valid non-empty markdown output."""
        from scripts.update_readme import calculate_stats, generate_readme
        library_path = DATA_DIR / "library.json"
        with open(library_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        stats = calculate_stats(data)
        content = generate_readme(data, stats)
        self.assertIn("# CinemaScope", content)
        self.assertIn("Total Library Titles", content)
        self.assertGreater(len(content), 100)


if __name__ == "__main__":
    unittest.main()

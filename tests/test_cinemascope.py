#!/usr/bin/env python3
"""
Unit and integration tests for CinemaScope:
- Validates data/library.json schema and invariants.
- Validates server.py routes and API responses.
- Validates helper functions in scripts/update_readme.py.
"""

import json
import os
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_FILE = BASE_DIR / "data" / "library.json"

import server
from scripts.update_readme import calculate_stats, categorize_by_status, categorize_by_type


class TestLibraryData(unittest.TestCase):
    def setUp(self):
        self.assertTrue(DATA_FILE.exists(), f"Missing library file at {DATA_FILE}")
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            self.library = json.load(f)

    def test_library_is_non_empty_list(self):
        self.assertIsInstance(self.library, list)
        self.assertGreater(len(self.library), 0)

    def test_item_required_fields(self):
        required_keys = {"id", "title", "type", "status"}
        valid_types = {"Movie", "Series"}
        valid_statuses = {"Watched", "Plan to Watch", "Watching", "Recommended"}

        seen_ids = set()
        for idx, item in enumerate(self.library):
            missing = required_keys - set(item.keys())
            self.assertFalse(missing, f"Item index {idx} ({item.get('title')}) missing keys: {missing}")
            self.assertIn(item["type"], valid_types, f"Item {item['title']} has invalid type: {item['type']}")
            self.assertIn(item["status"], valid_statuses, f"Item {item['title']} has invalid status: {item['status']}")
            self.assertNotIn(item["id"], seen_ids, f"Duplicate ID found: {item['id']}")
            seen_ids.add(item["id"])


class TestServerRoutes(unittest.TestCase):
    def setUp(self):
        server.app.config["TESTING"] = True
        self.client = server.app.test_client()

    def test_health_check(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("mode"), "local")

    def test_get_library(self):
        resp = self.client.get("/api/library")
        self.assertEqual(resp.status_code, 200)
        items = resp.get_json()
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)

    def test_index_route_serves_html(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"CINEMASCOPE", resp.data)

    def test_title_normalization(self):
        self.assertEqual(server.normalize_title("Kantara: Chapter 1!"), "kantarachapter1")
        self.assertEqual(server.normalize_title("  The   Shawshank Redemption "), "theshawshankredemption")


class TestReadmeStats(unittest.TestCase):
    def test_calculate_stats(self):
        sample = [
            {"id": 1, "title": "A", "type": "Movie", "status": "Watched", "rating": 9.0},
            {"id": 2, "title": "B", "type": "Series", "status": "Watched", "rating": 8.0},
            {"id": 3, "title": "C", "type": "Movie", "status": "Plan to Watch", "rating": 0},
            {"id": 4, "title": "D", "type": "Series", "status": "Recommended", "rating": 0},
        ]
        stats = calculate_stats(sample)
        self.assertEqual(stats["total"], 4)
        self.assertEqual(stats["watched"], 2)
        self.assertEqual(stats["plan_to_watch"], 1)
        self.assertEqual(stats["recommended"], 1)
        self.assertEqual(stats["movies"], 2)
        self.assertEqual(stats["series"], 2)
        self.assertEqual(stats["avg_rating"], 8.5)


if __name__ == "__main__":
    unittest.main()

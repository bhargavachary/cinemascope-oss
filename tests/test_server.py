"""
tests/test_server.py
Unit and integration tests for CinemaScope's local admin backend (server.py).
Tests REST APIs, input sanitization, data handling, and weighted score algorithm.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import server


class TestServerAPIs(unittest.TestCase):

    def setUp(self):
        # Create an isolated temporary data file for testing
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_data_file = Path(self.tmp_dir) / "test_library.json"
        
        self.sample_data = [
            {
                "id": 1,
                "title": "Interstellar",
                "type": "Movie",
                "status": "Watched",
                "language": "English",
                "rating": 9.0,
                "genres": ["Sci-Fi", "Adventure"],
                "imdbID": "tt0816692",
                "tags": ["Space"]
            },
            {
                "id": 2,
                "title": "Severance",
                "type": "Series",
                "status": "Plan to Watch",
                "language": "English",
                "rating": 8.7,
                "genres": ["Drama", "Mystery"],
                "imdbID": "tt11280740",
                "tags": ["Dystopian"]
            }
        ]
        self.tmp_data_file.write_text(json.dumps(self.sample_data, indent=2))
        
        # Monkey-patch DATA_FILE in server module
        self._orig_data_file = server.DATA_FILE
        server.DATA_FILE = self.tmp_data_file
        
        server.app.config["TESTING"] = True
        self.client = server.app.test_client()

    def tearDown(self):
        server.DATA_FILE = self._orig_data_file
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_health_check(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("mode"), "local")
        self.assertEqual(data.get("library_count"), 2)
        self.assertIn("omdb_configured", data)
        self.assertIn("tmdb_configured", data)

    def test_cors_headers_present(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")

    def test_get_library(self):
        resp = self.client.get("/api/library")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "Interstellar")

    def test_add_item_success(self):
        payload = {
            "title": "Kantara",
            "type": "Movie",
            "status": "Plan to Watch",
            "rating": 8.5,
            "language": "Kannada",
            "genres": ["Action", "Folklore"],
            "imdbID": "tt15327088"
        }
        resp = self.client.post("/api/library", json=payload)
        self.assertEqual(resp.status_code, 201)
        created = resp.get_json()
        self.assertEqual(created["id"], 3)
        self.assertEqual(created["title"], "Kantara")
        self.assertEqual(created["rating"], 8.5)

        # Verify persisted to file
        persisted = server.load_library()
        self.assertEqual(len(persisted), 3)

    def test_add_item_validation(self):
        # Empty title
        resp = self.client.post("/api/library", json={"title": ""})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Title is required", resp.get_json().get("error", ""))

        # Non-JSON payload
        resp = self.client.post("/api/library", data="not json", content_type="text/plain")
        self.assertEqual(resp.status_code, 400)

        # Rating clamp validation
        resp = self.client.post("/api/library", json={"title": "Clamped Rating Movie", "rating": 99})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["rating"], 10.0)

    def test_update_item_success(self):
        update_payload = {
            "title": "Interstellar (IMAX)",
            "rating": 9.5,
            "status": "Watched"
        }
        resp = self.client.put("/api/library/1", json=update_payload)
        self.assertEqual(resp.status_code, 200)
        updated = resp.get_json()
        self.assertEqual(updated["title"], "Interstellar (IMAX)")
        self.assertEqual(updated["rating"], 9.5)

    def test_update_item_not_found(self):
        resp = self.client.put("/api/library/999", json={"title": "Missing"})
        self.assertEqual(resp.status_code, 404)

    def test_delete_item_success(self):
        resp = self.client.delete("/api/library/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"deleted": 1})

        # Verify removal
        remaining = server.load_library()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["id"], 2)

    def test_delete_item_not_found(self):
        resp = self.client.delete("/api/library/999")
        self.assertEqual(resp.status_code, 404)


class TestWeightedScore(unittest.TestCase):

    def test_balanced_score(self):
        # imdb: 8.0 (40%), rt: 80% -> 8.0 (30%), letterboxd: 4.0 -> 8.0 (30%)
        # total = 8.0
        item = {
            "imdb_rating": "8.0",
            "rotten_tomatoes": "80%",
            "letterboxd_rating": 4.0
        }
        score = server._compute_weighted_score(item)
        self.assertEqual(score, 8.0)

    def test_missing_sources_renormalized(self):
        # Only IMDb present
        item = {"imdb_rating": "7.5"}
        score = server._compute_weighted_score(item)
        self.assertEqual(score, 7.5)

    def test_all_empty_or_na(self):
        item = {
            "imdb_rating": "N/A",
            "rotten_tomatoes": "—",
            "letterboxd_rating": None
        }
        score = server._compute_weighted_score(item)
        self.assertIsNone(score)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
Local development server for Entertainment Tracker.
Serves the static web app and provides REST API endpoints for:
- CRUD operations on data/library.json
- Fetching recommendations from OMDB API (IMDB, Rotten Tomatoes, Metacritic data)

Usage:
    python server.py
    Then open http://localhost:8080 in your browser.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
DATA_FILE = BASE_DIR / 'data' / 'library.json'

# OMDB API key - free tier at https://www.omdbapi.com/apikey.aspx
# Set via environment variable or use the demo key
OMDB_API_KEY = os.environ.get('OMDB_API_KEY', '')

CONTENT_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
}


def load_library():
    """Load the library data from JSON file."""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_library(data):
    """Save the library data to JSON file."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        f.write('\n')


def fetch_omdb(title, content_type='Movie'):
    """Fetch movie/series info from OMDB API (includes IMDB, RT, Metacritic)."""
    if not OMDB_API_KEY:
        return None

    media_type = 'movie' if content_type == 'Movie' else 'series'
    params = urllib.parse.urlencode({
        't': title,
        'type': media_type,
        'apikey': OMDB_API_KEY,
        'plot': 'short'
    })
    url = 'https://www.omdbapi.com/?' + params

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'EntertainmentTracker/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('Response') == 'True':
                return data
    except Exception as e:
        print(f"OMDB fetch error for '{title}': {e}")
    return None


class TrackerHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with REST API support."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # API routes
        if path == '/api/health':
            self.send_json({'status': 'ok', 'mode': 'local'})
        elif path == '/api/library':
            self.send_json(load_library())
        elif path.startswith('/api/recommendations/'):
            title = urllib.parse.unquote(path[len('/api/recommendations/'):])
            query = urllib.parse.parse_qs(parsed.query)
            content_type = query.get('type', ['Movie'])[0]
            self.handle_recommendations(title, content_type)
        else:
            # Serve static files
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/library':
            self.handle_add_item()
        else:
            self.send_error(404)

    def do_PUT(self):
        if self.path.startswith('/api/library/'):
            try:
                item_id = int(self.path.split('/')[-1])
                self.handle_update_item(item_id)
            except ValueError:
                self.send_error(400, 'Invalid item ID')
        else:
            self.send_error(404)

    def do_DELETE(self):
        if self.path.startswith('/api/library/'):
            try:
                item_id = int(self.path.split('/')[-1])
                self.handle_delete_item(item_id)
            except ValueError:
                self.send_error(400, 'Invalid item ID')
        else:
            self.send_error(404)

    def handle_add_item(self):
        """Add a new item to the library."""
        body = self.read_body()
        if body is None:
            return

        library = load_library()
        max_id = max((item['id'] for item in library), default=0)
        body['id'] = max_id + 1

        # Validate required fields
        if not body.get('title'):
            self.send_error(400, 'Title is required')
            return

        item = {
            'id': body['id'],
            'title': body['title'],
            'type': body.get('type', 'Movie'),
            'status': body.get('status', 'Plan to Watch'),
            'language': body.get('language', 'English'),
            'rating': body.get('rating', 0),
            'genres': body.get('genres', []),
            'imdbID': body.get('imdbID'),
            'tags': body.get('tags', [])
        }

        library.append(item)
        save_library(library)
        self.send_json(item, status=201)

    def handle_update_item(self, item_id):
        """Update an existing item in the library."""
        body = self.read_body()
        if body is None:
            return

        library = load_library()
        for i, item in enumerate(library):
            if item['id'] == item_id:
                library[i] = {
                    'id': item_id,
                    'title': body.get('title', item['title']),
                    'type': body.get('type', item['type']),
                    'status': body.get('status', item['status']),
                    'language': body.get('language', item.get('language', 'English')),
                    'rating': body.get('rating', item['rating']),
                    'genres': body.get('genres', item.get('genres', [])),
                    'imdbID': body.get('imdbID', item.get('imdbID')),
                    'tags': body.get('tags', item['tags'])
                }
                save_library(library)
                self.send_json(library[i])
                return

        self.send_error(404, 'Item not found')

    def handle_delete_item(self, item_id):
        """Delete an item from the library."""
        library = load_library()
        new_library = [item for item in library if item['id'] != item_id]
        if len(new_library) == len(library):
            self.send_error(404, 'Item not found')
            return
        save_library(new_library)
        self.send_json({'deleted': item_id})

    def handle_recommendations(self, title, content_type):
        """Fetch recommendations from OMDB (includes IMDB, Rotten Tomatoes, Metacritic)."""
        result = {}

        omdb_data = fetch_omdb(title, content_type)
        if omdb_data:
            result['omdb'] = omdb_data

        if not result:
            result['error'] = 'No data found. Set OMDB_API_KEY environment variable for full data.'
            if not OMDB_API_KEY:
                result['hint'] = 'Get a free API key at https://www.omdbapi.com/apikey.aspx and run: OMDB_API_KEY=your_key python server.py'

        self.send_json(result)

    def read_body(self):
        """Read and parse JSON request body."""
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length)
            return json.loads(raw.decode('utf-8'))
        except (ValueError, json.JSONDecodeError) as e:
            self.send_error(400, f'Invalid JSON: {e}')
            return None

    def send_json(self, data, status=200):
        """Send a JSON response."""
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """Suppress noisy request logging, show only API calls."""
        if '/api/' in (args[0] if args else ''):
            super().log_message(format, *args)


def main():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), TrackerHandler)
    print(f"""
╔══════════════════════════════════════════════════════════╗
║          🎬 Entertainment Tracker - Local Server         ║
╠══════════════════════════════════════════════════════════╣
║  Open in browser:  http://localhost:{port:<20}   ║
║                                                          ║
║  API Endpoints:                                          ║
║    GET    /api/library          - List all items         ║
║    POST   /api/library          - Add new item           ║
║    PUT    /api/library/<id>     - Update item            ║
║    DELETE /api/library/<id>     - Delete item            ║
║    GET    /api/recommendations/<title> - Get ratings     ║
║                                                          ║
║  For IMDB/RT/Metacritic data, set OMDB_API_KEY:         ║
║    OMDB_API_KEY=your_key python server.py                ║
║    Get free key: https://www.omdbapi.com/apikey.aspx     ║
║                                                          ║
║  Press Ctrl+C to stop                                    ║
╚══════════════════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
        server.server_close()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Update README.md with entertainment library statistics and categorized content.
"""
import json
from pathlib import Path
from collections import defaultdict


def load_library(json_path):
    """Load the library data from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def calculate_stats(library):
    """Calculate statistics from the library."""
    stats = {
        'total': len(library),
        'watched': sum(1 for item in library if item['status'] == 'Watched'),
        'watching': sum(1 for item in library if item['status'] == 'Watching'),
        'plan_to_watch': sum(1 for item in library if item['status'] == 'Plan to Watch'),
        'recommended': sum(1 for item in library if item['status'] == 'Recommended'),
        'movies': sum(1 for item in library if item['type'] == 'Movie'),
        'series': sum(1 for item in library if item['type'] == 'Series'),
    }
    
    # Calculate average rating for watched items
    watched_ratings = [item['rating'] for item in library if item['status'] == 'Watched' and item['rating'] > 0]
    stats['avg_rating'] = round(sum(watched_ratings) / len(watched_ratings), 1) if watched_ratings else 0
    
    return stats


def format_item_section(item):
    """Format an item for display in README."""
    lines = []
    tags_str = ", ".join(item['tags']) if item['tags'] else ""
    lines.append(f"### {item['title']}")
    lines.append(f"- **Type**: {item['type']}")
    if tags_str:
        lines.append(f"- **Tags**: {tags_str}")
    lines.append("")
    return lines


def categorize_by_status(library):
    """Categorize library items by status."""
    categories = defaultdict(list)
    for item in library:
        categories[item['status']].append(item)
    return categories


def categorize_by_type(library):
    """Categorize library items by type."""
    categories = defaultdict(list)
    for item in library:
        categories[item['type']].append(item)
    return categories


def generate_readme(library, stats):
    """Generate the full comprehensive README.md content."""
    readme = []
    
    # Header & Badges
    readme.append("# CinemaScope")
    readme.append("")
    readme.append("> **Personal, zero-bloat movies & TV series watchlist manager with an Indian-first regional lens.**")
    readme.append("")
    readme.append("[![Frontend](https://img.shields.io/badge/frontend-vanilla%20HTML%2FCSS%2FJS-brightgreen.svg)](index.html)")
    readme.append("[![Backend](https://img.shields.io/badge/backend-Flask%20%28Python%203%29-blue.svg)](server.py)")
    readme.append("[![Tests](https://img.shields.io/badge/tests-24%20passed-brightgreen.svg)](tests/)")
    readme.append("[![Architecture](https://img.shields.io/badge/architecture-no%20build%20step%20%7C%20static%20ready-orange.svg)](AGENTS.md)")
    readme.append("[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)")
    readme.append("")
    readme.append("---")
    readme.append("")
    readme.append("## 1. What CinemaScope Does")
    readme.append("")
    readme.append("CinemaScope is a personal entertainment library and watchlist manager designed for cinephiles who value speed, aesthetics, and privacy. It features dual viewing modes:")
    readme.append("")
    readme.append("- **Mosaic View (Poster-First):** Immersive, high-resolution poster wall with ambient glassmorphism, responsive grid layout, and instant interactive modals.")
    readme.append("- **Table / List View:** Dense, sortable data table for rapid sorting by IMDb rating, runtime, release year, or watch status.")
    readme.append("- **OTT Availability Locator:** Tracks streaming platforms in India (Netflix, Amazon Prime, Disney+ Hotstar, JioCinema, SonyLIV, Zee5, Aha, Sun NXT, Hoichoi, etc.).")
    readme.append("- **Multi-Source Enrichment:** Enriches titles with Rotten Tomatoes critic consensus, IMDb scores, awards, and regional language tags.")
    readme.append("")
    readme.append("---")
    readme.append("")
    readme.append("## 2. Why It Exists")
    readme.append("")
    readme.append("Commercial watchlist platforms (IMDb, Letterboxd, Trakt) are heavily cluttered with ads, tracking scripts, slow single-page framework bundles, and generic international recommendations that bury regional Indian cinema gems (Odia, Malayalam, Tamil, Telugu, Marathi).")
    readme.append("")
    readme.append("**CinemaScope's Philosophy:**")
    readme.append("- **Zero Build Step:** Plain HTML, CSS, and vanilla JS. No Webpack, Vite, or node_modules.")
    readme.append("- **Single Source of Truth:** `data/library.json` drives the entire platform. Edit the JSON directly or via the local Flask admin GUI.")
    readme.append("- **Offline & Resilience First:** Seamlessly operates offline with built-in metadata fallbacks even when external APIs are unreachable.")
    readme.append("- **Regional First:** Prioritizes authentic regional language cinema alongside global classics.")
    readme.append("")
    readme.append("---")
    readme.append("")
    readme.append("## 3. Implementation Status")
    readme.append("")
    readme.append("| Feature | Status | Description |")
    readme.append("|---|---|---|")
    readme.append("| **Mosaic / Grid View** | **Production-Ready** | Responsive CSS grid with poster fallback cascade, status chips, and glass hover effects. |")
    readme.append("| **Table / List View** | **Production-Ready** | Compact sortable view toggled in-place without page reload. |")
    readme.append("| **Local Admin Server** | **Production-Ready** | Lightweight Flask API (`server.py`) on port 8080 with CRUD and metadata endpoints. |")
    readme.append("| **Metadata Enrichment** | **Production-Ready** | Multi-source pipeline (`scripts/enrich_library.py`, `scripts/ott_locator.py`). |")
    readme.append("| **Static Hosting** | **Production-Ready** | Fully hostable on GitHub Pages or Cloudflare Pages without a server. |")
    readme.append("| **Poster Harvester** | *Stable* | Indian-first poster scraping with TMDB CDN fallback. |")
    readme.append("")
    readme.append("---")
    readme.append("")
    readme.append("## 4. Architecture")
    readme.append("")
    readme.append("```text")
    readme.append("┌────────────────────────────────────────────────────────┐")
    readme.append("│                 data/library.json                      │")
    readme.append("│              (Single Source of Truth)                  │")
    readme.append("└───────────────┬────────────────────────┬───────────────┘")
    readme.append("                │                        │")
    readme.append("   (Direct read)│                        │(Admin CRUD / refresh)")
    readme.append("                ▼                        ▼")
    readme.append("┌───────────────────────────┐    ┌───────────────────────────┐")
    readme.append("│    Static Web Client      │    │    server.py (Flask API)  │")
    readme.append("│  index.html · script.js   │    │    localhost:8080         │")
    readme.append("│  (Mosaic & List Views)    │    └─────────────┬─────────────┘")
    readme.append("└───────────────────────────┘                  │")
    readme.append("                                               ▼")
    readme.append("                                 ┌───────────────────────────┐")
    readme.append("                                 │    Enrichment Pipeline    │")
    readme.append("                                 │  scripts/id_resolver.py   │")
    readme.append("                                 │  scripts/data_harvester.py│")
    readme.append("                                 │  scripts/ott_locator.py   │")
    readme.append("                                 └───────────────────────────┘")
    readme.append("```")
    readme.append("")
    readme.append("---")
    readme.append("")
    readme.append("## 5. Quick Start & Usage")
    readme.append("")
    readme.append("### Option A: Static Mode (Zero Installation)")
    readme.append("Simply open `index.html` in any modern web browser or serve via Python's built-in HTTP server:")
    readme.append("```bash")
    readme.append("python3 -m http.server 8000")
    readme.append("# Open http://localhost:8000")
    readme.append("```")
    readme.append("")
    readme.append("### Option B: Local Admin Server (With Live Enrichment)")
    readme.append("To enable on-the-fly metadata fetching, OTT lookup, and browser editing:")
    readme.append("```bash")
    readme.append("pip install -r requirements.txt")
    readme.append("OMDB_API_KEY=your_key_here python3 server.py")
    readme.append("# Open http://localhost:8080")
    readme.append("```")
    readme.append("")
    readme.append("### Running Automated Tests")
    readme.append("```bash")
    readme.append("python3 -m unittest discover -s tests -v")
    readme.append("```")
    readme.append("")
    readme.append("---")
    readme.append("")
    readme.append("## 6. Library Statistics")
    readme.append("")
    readme.append(f"- **Total Library Titles**: {stats['total']}")
    readme.append(f"- **Watched**: {stats['watched']}")
    readme.append(f"- **Plan to Watch**: {stats['plan_to_watch']}")
    readme.append(f"- **Recommended**: {stats['recommended']}")
    readme.append(f"- **Currently Watching**: {stats['watching']}")
    readme.append(f"- **Movies**: {stats['movies']}")
    readme.append(f"- **Series**: {stats['series']}")
    if stats['avg_rating'] > 0:
        readme.append(f"- **Average IMDb Rating (Watched)**: ⭐ {stats['avg_rating']}/10")
    readme.append("")
    readme.append("---")
    readme.append("")
    readme.append("## 7. Curated Library Highlights")
    readme.append("")
    
    # Categorize by status
    categories = categorize_by_status(library)
    
    # Watched section
    if 'Watched' in categories:
        readme.append("## ✅ Watched")
        readme.append("")
        for item in sorted(categories['Watched'], key=lambda x: x['rating'], reverse=True):
            tags_str = ", ".join(item['tags']) if item['tags'] else ""
            rating_str = f"⭐ {item['rating']}/10" if item['rating'] > 0 else ""
            readme.append(f"### {item['title']}")
            readme.append(f"- **Type**: {item['type']}")
            if rating_str:
                readme.append(f"- **Rating**: {rating_str}")
            if tags_str:
                readme.append(f"- **Tags**: {tags_str}")
            readme.append("")
    
    # Currently Watching section
    if 'Watching' in categories:
        readme.append("## 🎬 Currently Watching")
        readme.append("")
        for item in categories['Watching']:
            readme.extend(format_item_section(item))
    
    # Recommended section
    if 'Recommended' in categories:
        readme.append("## 🌟 Recommended")
        readme.append("")
        for item in categories['Recommended']:
            readme.extend(format_item_section(item))
    
    # Plan to Watch section
    if 'Plan to Watch' in categories:
        readme.append("## 📝 Plan to Watch")
        readme.append("")
        for item in categories['Plan to Watch']:
            readme.extend(format_item_section(item))
    
    # Contributing & Security
    readme.append("---")
    readme.append("")
    readme.append("## 8. Contributing & Security")
    readme.append("")
    readme.append("- **Contributing:** Review our [Contributing Guide](CONTRIBUTING.md) for data schema invariants and local testing procedures.")
    readme.append("- **Security Policy:** Review our [Security Policy](SECURITY.md) for XSS boundaries, API key protection, and vulnerability disclosures.")
    readme.append("- **Changelog:** See [CHANGELOG.md](CHANGELOG.md) for version history.")
    readme.append("")
    readme.append("---")
    readme.append("")
    readme.append("## 9. License & Poster Copyright")
    readme.append("")
    readme.append("Code released under the [MIT License](LICENSE). Copyright © D K Bhargav Achary.")
    readme.append("Movie and television metadata, titles, and poster artworks are the copyrighted property of their respective production companies, studios, and distributors. CinemaScope uses these assets for non-commercial, personal commentary and organization purposes.")
    readme.append("")
    readme.append("---")
    readme.append("")
    readme.append("*This README is automatically generated from `data/library.json`*")
    readme.append("")
    
    return "\n".join(readme)


def main():
    """Main function to update README."""
    # Get paths
    base_path = Path(__file__).parent.parent
    json_path = base_path / 'data' / 'library.json'
    readme_path = base_path / 'README.md'
    
    # Load library
    library = load_library(json_path)
    
    # Calculate statistics
    stats = calculate_stats(library)
    
    # Generate README content
    readme_content = generate_readme(library, stats)
    
    # Write README atomically
    tmp_readme = readme_path.with_suffix(".tmp")
    with open(tmp_readme, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    tmp_readme.replace(readme_path)
    
    print(f"✅ README.md updated successfully!")
    print(f"   Total items: {stats['total']}")
    print(f"   Watched: {stats['watched']}")


if __name__ == "__main__":
    main()

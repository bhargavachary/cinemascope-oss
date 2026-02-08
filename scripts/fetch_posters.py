#!/usr/bin/env python3
"""
Asset Pipeline Script for Movie/Series Tracker
Fetch, process, and optimize poster images for local storage.
Usage: python3 scripts/fetch_posters.py
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Configuration
ASSETS_DIR = Path("images")
DATA_FILE = Path("data/library.json")
OMDB_API_KEY = os.environ.get("OMDB_API_KEY")

# Create assets directory if it doesn't exist
ASSETS_DIR.mkdir(exist_ok=True, parents=True)

def setup_pillow():
    """Ensure Pillow is installed for image processing"""
    try:
        from PIL import Image, ImageOps
        return Image, ImageOps
    except ImportError:
        print("❌ Pillow (PIL) library not found.")
        print("   Please run: pip install Pillow")
        sys.exit(1)

Image, ImageOps = setup_pillow()

def optim_image(image_path, output_path, max_width=600):
    """Resize and compress image to WebP"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB (in case of RGBA/P)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calculate new height to maintain aspect ratio
            w_percent = (max_width / float(img.size[0]))
            if w_percent < 1: # Only downscale
                h_size = int((float(img.size[1]) * float(w_percent)))
                img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)
            
            # Save as optimized WebP
            img.save(output_path, 'WEBP', quality=80, optimize=True)
            return True
    except Exception as e:
        print(f"   ⚠️ Error processing image {image_path}: {e}")
        return False

def fetch_poster(item):
    """Fetch poster for a single library item"""
    item_id = item.get('id')
    title = item.get('title')
    imdb_id = item.get('imdbID')
    
    # Target filename
    target_filename = f"{item_id}.webp"
    target_path = ASSETS_DIR / target_filename
    
    if target_path.exists():
        print(f"   ✅ Exists: {title}")
        return True

    poster_url = None
    
    # Strategy 1: Use OMDB if API Key exists and we have an IMDb ID or Title
    if OMDB_API_KEY:
        try:
            query = f"i={imdb_id}" if imdb_id else f"t={urllib.parse.quote(title)}"
            url = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&{query}"
            
            with urllib.request.urlopen(url) as resp:
                data = json.load(resp)
                if data.get('Response') == 'True' and data.get('Poster') != 'N/A':
                    poster_url = data.get('Poster')
        except Exception as e:
            print(f"   ⚠️ OMDB Fetch Error for {title}: {e}")

    # Strategy 2: Fallback (Not implemented to avoid pure scraping without consent, 
    # but this is where one might add other sources)
    
    if not poster_url:
        print(f"   ⏭️  Skipped (No URL): {title}")
        return False

    # Download and Optimize
    print(f"   ⬇️  Downloading: {title}...")
    try:
        temp_path = ASSETS_DIR / f"temp_{item_id}.jpg"
        
        # Download
        req = urllib.request.Request(poster_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(temp_path, 'wb') as out_file:
            out_file.write(response.read())
            
        # Optimize
        success = optim_image(temp_path, target_path)
        
        # Cleanup temp
        if temp_path.exists():
            os.remove(temp_path)
            
        if success:
            print(f"   ✨ Saved: {target_filename}")
            return True
            
    except Exception as e:
        print(f"   ❌ Download Failed for {title}: {e}")
        return False

def main():
    print(f"🎬 Movie Tracker Asset Pipeline")
    print(f"   Target Dir: {ASSETS_DIR}")
    print(f"   Data Source: {DATA_FILE}")
    print("-" * 40)

    if not DATA_FILE.exists():
        print("❌ Library data file not found.")
        return

    with open(DATA_FILE, 'r') as f:
        library = json.load(f)

    if not OMDB_API_KEY:
        print("⚠️  OMDB_API_KEY not set. Will only process existing downloads or manual URLs if implemented.")
        print("   (Run with: OMDB_API_KEY=yourkey python3 scripts/fetch_posters.py)")
    
    count = 0
    for item in library:
        if fetch_poster(item):
            count += 1
            # Be nice to APIs
            time.sleep(0.1)
            
    print("-" * 40)
    print(f"Done. Processed {len(library)} items. {count} images available locally.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Take headless screenshots of the app (desktop + mobile, dark + light).

Saves images to `assets/screenshots/`:
  - desktop-dark.png
  - desktop-light.png
  - mobile-dark.png
  - mobile-light.png

Requires `playwright` (the script will detect if not installed).
Usage:
  python3 scripts/screenshot_preview.py
"""
import os
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / 'assets' / 'screenshots'
OUT_DIR.mkdir(parents=True, exist_ok=True)
INDEX = Path(__file__).parent.parent / 'index.html'

# If playwright is not installed, instruct the caller.
try:
    from playwright.sync_api import sync_playwright
except Exception as exc:
    print("Playwright not available. Install with: pip install playwright && playwright install chromium")
    raise

VIEWPORTS = {
    'desktop': {'width': 1280, 'height': 820},
    'mobile':  {'width': 390,  'height': 844, 'is_mobile': True, 'device_scale_factor': 2}
}

def capture():
    url = INDEX.as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, cfg in VIEWPORTS.items():
            context = browser.new_context(**{k: v for k, v in cfg.items() if k in ('width','height','is_mobile','device_scale_factor')})
            page = context.new_page()

            # Dark (default)
            page.goto(url)
            page.wait_for_timeout(300)
            out_dark = OUT_DIR / f"{name}-dark.png"
            page.screenshot(path=str(out_dark), full_page=True)
            print(f"Saved: {out_dark}")

            # Light theme
            page.evaluate("() => document.documentElement.setAttribute('data-theme','light')")
            page.wait_for_timeout(200)
            out_light = OUT_DIR / f"{name}-light.png"
            page.screenshot(path=str(out_light), full_page=True)
            print(f"Saved: {out_light}")

            # reset theme
            page.evaluate("() => document.documentElement.setAttribute('data-theme','dark')")
            context.close()
        browser.close()

if __name__ == '__main__':
    capture()

# Contributing to CinemaScope

Thank you for contributing to CinemaScope! CinemaScope is a personal entertainment watchlist manager with an Indian-first regional lens, designed to be fast, elegant, and maintainable without complex build tools.

---

## Operating Principles

1. **Zero-Build Architecture:** The frontend (`index.html`, `script.js`, `style.css`) must remain vanilla HTML, CSS, and modern JavaScript. No bundlers, transpilers, or node_modules.
2. **Single Source of Truth:** `data/library.json` is the sole source of truth for all movie and television data. All scripts read and write to this file atomically.
3. **Regional Cinema First:** Ensure regional Indian cinema (Odia, Malayalam, Tamil, Telugu, Kannada, Bengali, Marathi, Hindi) is given equal prominence alongside international cinema.
4. **Security & Sanitization:** All dynamic metadata, titles, awards, and OTT provider strings rendered in DOM innerHTML must pass through `escapeHtml()` to guarantee XSS prevention.
5. **No Embedded API Keys:** Never hardcode OMDB or TMDB API keys in client-side code or git commits.

---

## Local Development Setup

```bash
# Clone repository
git clone https://github.com/bhargavachary/cinemascope.git
cd cinemascope

# Install Python requirements
pip install -r requirements.txt

# Run syntax check and unit test suite
make lint
make test

# Launch local admin server
OMDB_API_KEY=your_key_here make serve
# Or static viewer: make serve-static
```

---

## Testing & Invariant Checks

Before submitting a Pull Request:
1. Run syntax verification:
   ```bash
   make lint
   ```
2. Run the test suite:
   ```bash
   make test
   ```
3. Update and verify the README catalog:
   ```bash
   make update-readme
   ```
4. Verify that `data/library.json` contains valid JSON and conforms to the schema validated by `tests/test_data_integrity.py`.

---

## Pull Request Guidelines

1. Create a descriptive feature branch:
   ```bash
   git checkout -b feat/your-feature
   ```
2. Keep commits atomic and logically separated.
3. Fill out the Pull Request template completely.

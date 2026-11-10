# Changelog

All notable changes to CinemaScope will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **DOM XSS Sanitization:** Sanitized all modal HTML fields (awards, OTT streaming providers, and JustWatch URLs with `rel="noopener noreferrer"`) via `escapeHtml()`.
- **Atomic File Writing:** Implemented atomic temporary file replacement across `scripts/update_readme.py`, `scripts/enhance_library.py`, and `scripts/fetch_ratings.py`.
- **Data Integrity Tests:** Added schema tests asserting title presence, rating bounds, and IMDb ID formats (`tt\d+`) in `tests/test_data_integrity.py` (expanding test suite from 22 to 24 passing tests).
- **Open Source Governance Documentation:** Added comprehensive `CONTRIBUTING.md`, `SECURITY.md`, PR template, and GitHub issue templates.

### Security
- **CI Minimal Permissions:** Added explicit `permissions: contents: read` to `.github/workflows/ci.yml`.
- **Automated Workflow Permissions:** Added explicit `permissions: contents: write` to `.github/workflows/update-readme.yml`.

---

## [0.2.0] - 2026-11-08

### Added
- Standardized Makefile with targets: `test`, `lint`, `serve`, `serve-static`, `validate`, `update-readme`, `clean`.
- GitHub Actions CI workflow running across Python 3.9 through 3.12.
- MIT License file and clean repository licensing documentation.

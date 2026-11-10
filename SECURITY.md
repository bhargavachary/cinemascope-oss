# Security Policy

CinemaScope provides both a static web dashboard and a local Flask administrative backend. Security and input validation are treated with care.

---

## Supported Versions

| Version | Supported |
|---|---|
| `main` (v0.2.x) | Yes |
| < v0.2.0 | No |

---

## Security Boundaries & Defenses

1. **XSS Prevention:**
   - All dynamic metadata inserted into HTML (`script.js`), including titles, years, ratings, award descriptions, OTT providers, and external links, are sanitized using `escapeHtml()`.
   - External URLs (such as JustWatch links) are validated to ensure they conform strictly to `https://` schemes before being rendered in anchor tags with `rel="noopener noreferrer"`.

2. **Secret & Key Protection:**
   - External API keys (e.g. `OMDB_API_KEY`) must only be supplied via environment variables to the local Python server (`server.py`).
   - The static frontend (`index.html`) does not store or require any API keys.

3. **Atomic Data Persistence:**
   - Modifying `data/library.json` or `README.md` utilizes atomic write-and-replace routines (`tmp_file.replace(...)` / `os.replace(...)`) to prevent file corruption during interrupted writes.

---

## Reporting a Security Vulnerability

If you identify a security defect or Cross-Site Scripting (XSS) vulnerability:
- Please disclose it responsibly via email to **`contact@bhargavachary.com`** or via the contact form at [`https://bhargav.work/contact/`](https://bhargav.work/contact/).
- Do not open a public issue for sensitive security vulnerabilities.
- We acknowledge security reports within 48 hours and work with you to coordinate a timely resolution.

# 0278 — Add a favicon to every served page

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: TBD

## Context

The browser console shows "Failed to load resource" (404 on `/favicon.ico`) on the pages the
CLI serves (home page, `review`, `review-sort`, `places`): no favicon exists. Add one (the
meerkat of the new look, small SVG/ICO), declared with `<link rel="icon">` in the templates and
served by each local HTTP server.

## Acceptance

- [ ] A favicon asset lives under a `static/` or `templates/` directory (no inline long text).
- [ ] Every served page declares it and `/favicon.ico` answers 200 (no 404 in the console).
- [ ] The CSP of each server still allows it; a test checks the route on each server.

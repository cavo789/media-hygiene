# 0443 — On the phone (HTTPS), search shows "No preview" on every tile

- **Priority**: High
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/search/pictures.py`, `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/lan_paths.py`, `src/media_hygiene/review/serving.py`, `src/media_hygiene/search/templates/search.js.j2`
- **Needs maintainer**: (1) do the same search's tiles show previews on the PC? (2) on the phone, what does `https://<PC address>:8088/thumb/1.jpg` show when opened directly in Chrome (a photo, or which error)?

## Why

The maintainer, 2026-10-27, on the phone over HTTPS (0430): search found 41 758 files, every
tile says *No preview* (the `img` error fallback of `search.js.j2`), yet the large view
(`/preview/…`) shows the photo. `phone_may` allows `GET /thumb/…` (checked). Differences
between the two answers to look at: `/thumb/` is `cacheable=True` (RUN_TAG, 304 path) and
rendered at `GRID_EDGE` through `PreviewPool`; ~240 requests at once, each on its own TLS
connection (no keep-alive, see 0442).

## What

- Reproduce over the home network's door (TLS) with the demo tree, then fix.
- A test that a paired phone gets a JPEG for `/thumb/<key>.jpg` through `LanApp`.

# 0446 — Review of the 2026-10-28 iterate (PR #45): six questions, captures, what was not run

- **Priority**: High
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/`, `documentation/en/commands/review-sort.md`, `documentation/fr/commands/review-sort.md`
- **Needs maintainer**: one run of `docs_screenshots` (the six questions answered 2026-10-29: 0457–0460 filed)

## Why

PR #45 (0437, 0433, 0434, 0438, 0439) was merged on 2026-10-28 with its CI green, before its questions were answered.
The run was stopped at the maintainer's request after the *search* lot.

## Questions (one answer each, then file or close)

1. *🗂 Events* in search: a tab, or the collapsible section as now?
2. EXIF in the large view (key I): also the town of the GPS position (offline gazetteer), not only coordinates?
3. search: a filter or a *shortest first* sort for videos?
4. Key **T** to take back an Events choice made in search: keep it?
5. `review-sort` in the next version: remove it, or keep it as a hidden alias like `browse`
   (its pages, menu entry and site nav stay until then)?
6. The 3 s threshold of the red video-length badge: a constant (now) or a `config.toml` setting?

## Also waiting

- `docs_screenshots`: the search page, the large view and `review-sort --help` captures are stale.
- Not ported in 0438: prefetching the next event's thumbnails, and remembering the last event shown.
- Not run in that iterate: lot *home* (0359, 0417, 0361) and 0444, 0374, 0418, 0420, 0440 — the next `/todo:iterate`.
- 0443 and 0435: done on `main` (PR #46).

## Done when

Each question answered in a `## Decided` section, the follow-ups filed as TODOs, the captures refreshed.

## Decided

1. → A tab (Photos / Events) instead of the collapsible section: follow-up TODO (2026-10-29)
2. → Add the town of the GPS position (offline gazetteer) next to the coordinates: follow-up TODO (2026-10-29)
3. → A *shortest first* sort for videos (no new filter): follow-up TODO (2026-10-29)
4. → Keep key T (2026-10-29)
5. → Remove `review-sort` in the next version (no hidden alias): its pages, menu entry and site nav go with it: follow-up TODO (2026-10-29)
6. → Keep the 3 s threshold a named constant (2026-10-29)

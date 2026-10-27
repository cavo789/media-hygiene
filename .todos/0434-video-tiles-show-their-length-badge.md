# 0434 — video tiles show their length as a badge on the preview

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/search/templates/browse.js.j2`, `src/media_hygiene/review/templates/pick_*` (the shared tile CSS), `src/media_hygiene/search/hits.py`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

The maintainer, 2026-10-27, sorting videos in `mh search`: the length is only a grey line
under the tile (`facts`, 0408), easy to miss; a two-second video is rarely worth keeping
and should stand out.

## What

- A badge on the bottom-right corner of every video's preview, as video sites do: `▶ 0:02`,
  `1:45`, `1:05:10` (length from the index's video metadata, `with_facts`).
- A very short video (below a named constant, e.g. 3 s; say in the close-out whether it
  should be a setting — memory `few-settings`) gets an accented badge, so it is seen at a
  glance; optionally a filter or a sort "shortest first" in search (to decide with the
  maintainer: a question in the report, not built unasked).
- The same badge on every tile page (`browse`, search, the reviews): skill
  `photo-picking-pages` — one tile, one look.
- Docs en+fr.

## Explicit NON-goals

- Deleting short videos automatically (set aside stays the user's choice).

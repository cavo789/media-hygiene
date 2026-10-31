# 0555 — Tags typed by hand on a selection, kept in `tags/<word>.toml`

- **Priority**: Medium
- **Batch**: search
- **Depends**: 0551
- **Files**: `src/media_hygiene/tags/models.py`, `src/media_hygiene/tags/producers.py`, `src/media_hygiene/config/`, `src/media_hygiene/search/`, `src/media_hygiene/review/templates/pick_*`, `src/media_hygiene/tags/xmp_merge.py`, `documentation/en/`, `documentation/fr/`

## Why

The maintainer, 2026-10-31: people and places are the user's decisions (files in `/config`);
tags are computed (index in `/cache`, recomputable). A word the user types on photos
("anniversaire Léa") is a decision: lost with the cache, no run would find it again. No such
tag exists today. Related: 0546 (drop a tag — the opposite gesture, same page).

## What

- New `TagSource.HAND`: words given by the user, read from `/config/tags/<word>.toml`
  (linked from `config.toml` like `people/`, 0300), each photo in the one form of 0551
  (`path` + `id`, path kept current).
- In the search pick bar (skill `photo-picking-pages`): *🏷 Tag…* on the selection: type a
  word or pick an existing one, saved, read back and shown; take a tag off a photo from its
  chips (large view).
- Searchable at once (`tag` words), written into `.xmp` by `xmp` like the others.
- Documentation en + fr; `docs_screenshots` to run afterwards.

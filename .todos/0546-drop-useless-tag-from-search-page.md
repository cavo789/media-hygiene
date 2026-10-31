# 0546 — Drop a useless tag everywhere, from the search page

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/config/tags_settings.py, src/media_hygiene/tags/normalize.py, src/media_hygiene/review/templates/pick_*, search page and its routes, tags index rows, XMP writers (`xmp_*`)
- **Needs maintainer**: the questions below, asked when the TODO runs

## Context

2026-10-31: searching `"panneau de signalisation"` finds 100 photos; the maintainer finds this
tag of no use and wants to get rid of it. Today the only way is `[tags] stop_words` in
`config.toml` (`config/tags_settings.py`, applied by `tags/normalize.py` to new tags
only): config-only, so missing for the user (memory: visible in web or nonexistent), and
the tags already stored stay.

## Wanted

From `/search` (and wherever tags are shown as chips on a tile or in the large view):
click a tag → "I do not need this tag" → a page/panel showing a few photos carrying it
and its count → confirm → the tag is removed **everywhere** (index rows, and the XMP
sidecars if tags are written there) and **added to the stop words**, so the next `mh tags`
run does not bring it back. Proven by reading back from disk and showing it (product
rule: never "Saved" from memory). A way back: the list of dropped tags with "restore"
(remove from the stop words; the photos get it again at the next `mh tags` run, or
right away if the removed rows were kept aside).

Same layout and keys as the other tile pages (skill `photo-picking-pages`).

## Questions for the maintainer (ask at run time)

- ~~Where to keep the dropped tags~~ — answered 2026-10-31: remove the tag from every
  photo **and** add it to `config.toml`'s `[tags] stop_words` (tomlkit, comments kept,
  atomic, like `places`), so it is never used again.
- Also remove it from the XMP sidecars already written (other tools would lose it too)?
- Several tags at once (a list of the most frequent tags, tick the useless ones)?
- Also offer "merge into another tag" (synonyms: `panneau` → `panneau de signalisation`)?

## Acceptance

- [ ] A tag can be dropped from the search page after seeing a few of its photos
- [ ] It disappears from every photo and does not come back at the next `mh tags`
- [ ] Dropped tags can be listed and restored
- [ ] Both languages of the docs updated; `docs_screenshots` flagged as stale

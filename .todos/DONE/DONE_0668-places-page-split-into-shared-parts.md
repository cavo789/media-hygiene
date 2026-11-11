# 0668 — Places page: its 1,154-line template split, dialogs and keys from the shared parts

- **Priority**: Low
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/review/templates/page_frame.html.j2`, `tests/unit/test_page_frame.py`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

`places.html.j2` extends the frame but is one file of **1,154 lines** (*measured*, `wc -l`,
2026-11-10) holding its style, markup and all its script, with 2 `window.confirm` and its
own dialogs. The 200-line cap applies to `src/` Python only, so nothing flags it; yet every
shared improvement (ask dialog, busy state, view in the URL, menus) must be redone by hand
in it, which is how pages drift apart.

## Proposal

- Split as the other pages: `places.html.j2` (blocks), `places.css.j2`, `places_map.js.j2`,
  `places_list.js.j2`, `places_dialogs.html.j2`; no behaviour change (the headless walk of
  the page before and after gives the same DOM for the same mocked API).
- A soft size check for templates in the frame's test (e.g. a list of the files over 400
  lines, which may only shrink), so that the next monolith is seen.

## Acceptance

- [ ] No template of `places/templates/` over 400 lines; the page behaves the same (test)
- [ ] The list of oversized templates in the test, with their sizes

## Where the user gains

Indirect: each shared UX change reaches Places at the same time as the other pages
(estimated from this review: 4 of the UX TODOs filed today touch this file).

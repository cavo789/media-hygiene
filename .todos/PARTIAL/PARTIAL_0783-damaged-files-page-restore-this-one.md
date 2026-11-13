# 0783 — Damaged files: a *Restore this one* page, offered by the safety card

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/services/good_copy.py`, `src/media_hygiene/services/repair.py`, `src/media_hygiene/cli/safety_more.py`, `src/media_hygiene/cli/menu_catalog_clean_more.py`, `src/media_hygiene/review/templates/`, `documentation/en/reference-safety.md`, `documentation/fr/reference-safety.md`, `documentation/en/commands/clean.md`, `documentation/fr/commands/clean.md`

Left by 0777 (from 0690). To do once PR #80 (one tile view on 12 pages) is merged: this is a
page of photos shown as tiles, and the run of 2026-11-12 held every tile page back for it.

## Context

`mh audit --reread` finds a file whose content changed while its size and date did not, and
`mh clean --repair` (`cli/reread_flow.py`) lists each damaged file with its good copy, asks, then
restores it, journaled (the damaged file kept in the quarantine, `undo` brings it back). The home
card's *Damaged files* line says how many, with no button: the console is the only way. A card
offer alone (a step running `clean --repair` in `mh`'s window) would be a fast path without its
visual twin, which the *seeing first* rule (0524) forbids: both come together.

## Proposal

- A page (home server, under the page shell): each damaged file beside its good copy (where it is:
  a duplicate, the quarantine), since when, *Restore this one* per file and *Restore these N* for
  the shown ones, then read back from the disk and shown. Built from the shared `pick_*` templates
  (skill `photo-picking-pages`), with *Apply now* where the contract asks for it.
- The card's *Damaged files* line offers the page first; the console line stays the fast path.

## Acceptance

- [ ] Test flipping one byte of a demo photo keeping its mtime: listed on the page, restored from
      it, disk identical to before the flip, `undo` puts the damaged file back
- [ ] A file whose good copy is gone meanwhile: refused, said, nothing moved
- [ ] Docs EN + FR; French strings

## Status — PARTIAL (2026-11-13)

Done: the page `/repair/` in the home server (`services/repair_pick.py`, `review/repair_app.py`,
`services/repair_serving.py`, `review/templates/repair*.j2`), built on the shared `pick_*` parts
like the quarantine's page: each damaged file beside its good copy (two previews, since when,
where the copy is), *Restore these files* on the tiles picked, every copy proven again at that
moment, one journaled run (`services/repair.repair`), each file read back, the page read again;
the toast's Undo (or Z) runs `mh undo` of that run (`/api/undo-run`). A copy gone meanwhile:
refused, said, nothing moved. Catalog step `repair` (`clean --repair`, served here by
`SERVED_MORE`); the safety card's *Damaged files* line opens it, the console line stays the fast
path. Tests `tests/integration/test_repair_page.py` (flip → listed → restored identical → Undo;
copy gone; card). Docs en + fr (`reference-safety.md`, `commands/clean.md`); French strings.
No *Apply now*: nothing is set aside to apply, each restore acts at once, journaled.

Left:
- The Chromium walk of the page (gestures of the photo-picking contract, no `pageerror`, the
  grid's top unchanged by a pick) was not run here: add `repair.html.j2` to the e2e browser
  walks (`tests/e2e/test_ask_dialog_browser.py` pattern) and to `tests/integration/tags/test_pick_pages.py`.
- `docs_screenshots` to run (the card's line changed; a new page).
